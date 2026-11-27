// Region packs: map files for each state, kept outside the app.
import Cocoa
import WebKit

// MARK: - Region packs (maps for other states, kept outside the app, e.g. on an external drive)
/// A folder that holds packs, and the hub drive it is on (nil for a folder on this Mac).
struct PackRoot { let url: URL; let hub: Hub? }

/// Folders on this Mac that hold packs: those listed by the offgrid-pack tool, OFFGRID_PACKS, then <data>/packs.
func localPackRoots() -> [URL] {
    let base = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask)[0]
    var roots: [URL] = []
    if let d = try? Data(contentsOf: base.appendingPathComponent("Off-Grid/packs.json")),
       let o = try? JSONSerialization.jsonObject(with: d) as? [String: Any], let a = o["roots"] as? [String] {
        roots += a.map { URL(fileURLWithPath: $0).standardizedFileURL }
    }
    if let p = env["OFFGRID_PACKS"] { roots.append(URL(fileURLWithPath: p).standardizedFileURL) }
    roots.append(dataDir.appendingPathComponent("packs"))
    return roots
}
/// Hub drives come first, so while a hub is plugged in its pack (with satellite) wins over a
/// same-name pack on this Mac. Pull the drive and the Mac's own copy takes over on the next request.
func taggedPackRoots() -> [PackRoot] {
    connectedHubs().map { PackRoot(url: $0.packs, hub: $0) } + localPackRoots().map { PackRoot(url: $0, hub: nil) }
}
func packRoots() -> [URL] { taggedPackRoots().map { $0.url } }

/// Pack folders (ones with a pack.json) in one root. A missing or vanished root just has none.
func packSlugs(in root: URL) -> [String] {
    ((try? FileManager.default.contentsOfDirectory(atPath: root.path)) ?? []).sorted().filter {
        dataNameOK($0) && FileManager.default.fileExists(atPath: root.appendingPathComponent($0).appendingPathComponent("pack.json").path)
    }
}
func packDir(_ slug: String) -> URL? {
    guard dataNameOK(slug) else { return nil }
    for r in packRoots() {
        let d = r.appendingPathComponent(slug)
        if FileManager.default.fileExists(atPath: d.appendingPathComponent("pack.json").path) { return d }
    }
    return nil
}

/// Where each pack comes from: the first root that has it wins. "also" lists the other places with the
/// same pack ("local" or a hub id), so the page can say the Mac's own copy takes over after unplugging.
struct PackOrigin {
    let slug: String, root: PackRoot, also: [String]
    var origin: String { root.hub == nil ? "local" : "hub" }
}
func packOrigins(_ roots: [PackRoot]) -> [PackOrigin] {
    var order: [String] = [], first: [String: PackRoot] = [:], also: [String: [String]] = [:]
    for r in roots {
        for slug in packSlugs(in: r.url) {
            guard let f = first[slug] else { first[slug] = r; order.append(slug); continue }
            let place = r.hub?.id ?? "local"
            if place != (f.hub?.id ?? "local"), !(also[slug] ?? []).contains(place) { also[slug, default: []].append(place) }
        }
    }
    return order.map { PackOrigin(slug: $0, root: first[$0]!, also: also[$0] ?? []) }
}

/// GET /api/packs: each pack's pack.json, plus "origin" ("local" or "hub"), "hub" (the hub id) and "also".
func packList() -> Data {
    var out: [Any] = []
    for p in packOrigins(taggedPackRoots()) {
        guard let d = try? Data(contentsOf: p.root.url.appendingPathComponent(p.slug).appendingPathComponent("pack.json")),
              let o = try? JSONSerialization.jsonObject(with: d) else { continue }
        guard var m = o as? [String: Any] else { out.append(o); continue }
        m["origin"] = p.origin
        if let h = p.root.hub { m["hub"] = h.id }
        if !p.also.isEmpty { m["also"] = p.also }
        out.append(m)
    }
    return (try? JSONSerialization.data(withJSONObject: out)) ?? Data("[]".utf8)
}
/// /packs/<slug>/<file> -> a file inside that pack folder, or nil if it escapes it.
func packFile(_ urlPath: String) -> URL? {
    let rest = (urlPath.removingPercentEncoding ?? urlPath).dropFirst("/packs/".count)
    guard let slash = rest.firstIndex(of: "/"), let dir = packDir(String(rest[..<slash])) else { return nil }
    let u = dir.appendingPathComponent(String(rest[rest.index(after: slash)...])).standardizedFileURL
    guard u.path.hasPrefix(dir.standardizedFileURL.path + "/"), !u.lastPathComponent.hasPrefix(".") else { return nil }
    return u
}
