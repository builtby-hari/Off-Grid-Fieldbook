// Region packs: map files for each state, kept outside the app.
import Cocoa
import WebKit

// MARK: - Region packs (maps for other states, kept outside the app, e.g. on an external drive)
/// Folders that hold packs: those listed by the offgrid-pack tool, plus <data>/packs.
func packRoots() -> [URL] {
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
func packDir(_ slug: String) -> URL? {
    guard dataNameOK(slug) else { return nil }
    for r in packRoots() {
        let d = r.appendingPathComponent(slug)
        if FileManager.default.fileExists(atPath: d.appendingPathComponent("pack.json").path) { return d }
    }
    return nil
}
func packList() -> Data {
    var seen = Set<String>(), out: [Any] = []
    for r in packRoots() {
        for slug in ((try? FileManager.default.contentsOfDirectory(atPath: r.path)) ?? []).sorted() where !seen.contains(slug) && dataNameOK(slug) {
            guard let d = try? Data(contentsOf: r.appendingPathComponent(slug).appendingPathComponent("pack.json")),
                  let o = try? JSONSerialization.jsonObject(with: d) else { continue }
            seen.insert(slug); out.append(o)
        }
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
