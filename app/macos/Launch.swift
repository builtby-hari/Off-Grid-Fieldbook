// Launch options: which port to use, and which screen to open first.
import Foundation

/// The value after a flag in the launch arguments, e.g. "--pack texas".
func launchArg(_ flag: String, _ args: [String] = CommandLine.arguments) -> String? {
    guard let i = args.firstIndex(of: flag), i + 1 < args.count else { return nil }
    return args[i + 1]
}

/// Ports to try, in order. Normally 47321 (so saved settings stick), then any free one.
/// OFFGRID_PORT=<n> or --port <n> uses only that port, and 0 means any free port.
func serverPorts() -> [UInt16] {
    if let s = launchArg("--port") ?? env["OFFGRID_PORT"], let p = UInt16(s) { return [p] }
    return [47321, 0]
}

/// Screens a launch can open. Anything else is ignored.
let launchViews = ["home", "map", "place", "learn", "setup", "check", "help"]

/// A shell address (see app/web/CONTRACT.md) for a screen and an optional map pack, or nil if invalid.
func launchRoute(view: String, pack: String?) -> String? {
    let v = view.lowercased()
    guard launchViews.contains(v) else { return nil }
    if v == "map", let p = pack, !p.isEmpty { return dataNameOK(p) ? "map?pack=" + p : nil }
    return v
}

/// From the command line: --open map --pack texas -> "map?pack=texas".
func launchRouteFromArgs(_ args: [String] = CommandLine.arguments) -> String? {
    guard let v = launchArg("--open", args) else { return nil }
    return launchRoute(view: v, pack: launchArg("--pack", args))
}

/// From a link: offgrid://open?view=map&pack=texas, or the short form offgrid://map?pack=texas.
func launchRoute(url: URL) -> String? {
    guard url.scheme?.lowercased() == "offgrid", let c = URLComponents(url: url, resolvingAgainstBaseURL: false) else { return nil }
    var q: [String: String] = [:]
    for i in c.queryItems ?? [] where q[i.name] == nil { q[i.name] = i.value }
    let host = (c.host ?? "").lowercased()
    let view = host.isEmpty || host == "open" ? (q["view"] ?? "home") : host
    return launchRoute(view: view, pack: q["pack"])
}
