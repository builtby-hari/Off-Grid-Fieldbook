// Your records on disk: where they live, the revision check and the backups kept on every save.
import Cocoa
import WebKit

// Your own records (equipment, places, supplies, logs, photos) live outside the app bundle,
// so rebuilding or replacing the app never touches them.
let dataDir: URL = {
    if let p = env["OFFGRID_DATA"] { return URL(fileURLWithPath: p).standardizedFileURL }
    let base = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask)[0]
    return base.appendingPathComponent(Bundle.main.bundleIdentifier ?? "com.builtbyhari.offgrid").standardizedFileURL
}()
let dataNameOK: (String) -> Bool = { n in !n.isEmpty && n.count < 80 && n.allSatisfy { $0.isLetter || $0.isNumber || $0 == "-" || $0 == "_" || $0 == "." } && !n.hasPrefix(".") }
/// The revision of a data file: a fingerprint of its bytes. "0" means there is no file yet.
/// A screen sends back the revision it last read. If the file changed since, the save is refused
/// and the screen reads again, merges and retries. So two screens can never overwrite each other.
let dataLock = NSLock()
func revision(_ d: Data?) -> String {
    guard let d else { return "0" }
    var h: UInt64 = 0xcbf29ce484222325
    for b in d { h ^= UInt64(b); h = h &* 0x100000001b3 }
    return String(h, radix: 16)
}
func currentRevision(_ name: String) -> String { revision(try? Data(contentsOf: dataDir.appendingPathComponent(name))) }

func saveData(_ name: String, _ body: Data) -> Bool {
    let fm = FileManager.default
    let dir = dataDir, bak = dir.appendingPathComponent("backups")
    try? fm.createDirectory(at: bak, withIntermediateDirectories: true)
    let file = dir.appendingPathComponent(name)
    if fm.fileExists(atPath: file.path) {
        // Keep the last 40 versions of every file, so a bad save can be rolled back.
        let stamp = ISO8601DateFormatter().string(from: Date()).replacingOccurrences(of: ":", with: "")
        try? fm.copyItem(at: file, to: bak.appendingPathComponent("\(stamp)-\(name)"))
        let old = ((try? fm.contentsOfDirectory(atPath: bak.path)) ?? []).filter { $0.hasSuffix("-" + name) }.sorted()
        for f in old.dropLast(40) { try? fm.removeItem(at: bak.appendingPathComponent(f)) }
    }
    return (try? body.write(to: file, options: .atomic)) != nil
}
