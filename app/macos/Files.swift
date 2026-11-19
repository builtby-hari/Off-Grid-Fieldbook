// Where the app's content lives, and how files are found and listed.
import Cocoa
import WebKit

let env = ProcessInfo.processInfo.environment
let contentRoot: URL = {
    if let p = env["OFFGRID_CONTENT"] { return URL(fileURLWithPath: p).standardizedFileURL }
    return Bundle.main.resourceURL!.appendingPathComponent("Content").standardizedFileURL
}()

// MARK: - Files

let mimeTypes: [String: String] = [
    "html": "text/html; charset=utf-8", "js": "text/javascript", "css": "text/css",
    "json": "application/json", "png": "image/png", "jpg": "image/jpeg", "svg": "image/svg+xml",
    "pdf": "application/pdf", "pbf": "application/x-protobuf", "md": "text/plain; charset=utf-8",
    "txt": "text/plain; charset=utf-8", "geojson": "application/geo+json", "gpx": "application/gpx+xml",
    "mp4": "video/mp4", "m4a": "audio/mp4", "mov": "video/quicktime", "webp": "image/webp", "heic": "image/heic", "csv": "text/csv",
]

func files(in dir: String, ext: String) -> [URL] {
    let base = contentRoot.appendingPathComponent(dir)
    guard let e = FileManager.default.enumerator(at: base, includingPropertiesForKeys: [.fileSizeKey],
                                                 options: [.skipsHiddenFiles]) else { return [] }
    return e.compactMap { $0 as? URL }.filter { $0.pathExtension.lowercased() == ext }
        .sorted { $0.path.localizedStandardCompare($1.path) == .orderedAscending }
}

func sizeMB(_ u: URL) -> Int {
    ((try? u.resourceValues(forKeys: [.fileSizeKey]).fileSize) ?? 0) / 1_000_000
}

func relPath(_ u: URL) -> String {
    String(u.standardizedFileURL.path.dropFirst(contentRoot.path.count))
}

func manifest() -> Data {
    let books = files(in: "books", ext: "pdf").map { u -> [String: Any] in
        ["category": u.deletingLastPathComponent().lastPathComponent,
         "title": u.deletingPathExtension().lastPathComponent, "path": relPath(u), "mb": sizeMB(u)]
    }
    let zims = files(in: "library", ext: "zim").map { u -> [String: Any] in
        ["folder": u.deletingLastPathComponent().lastPathComponent,
         "name": u.deletingPathExtension().lastPathComponent, "mb": sizeMB(u)]
    }
    let maps = files(in: "maps", ext: "pmtiles").map { $0.lastPathComponent }
    let docs = (files(in: "docs", ext: "html") + files(in: "docs", ext: "md")).map { u -> [String: Any] in
        ["title": u.deletingPathExtension().lastPathComponent, "path": relPath(u), "kind": u.pathExtension]
    }
    let obj: [String: Any] = ["books": books, "zims": zims, "maps": maps, "docs": docs, "kiwix": kiwixURL]
    return (try? JSONSerialization.data(withJSONObject: obj)) ?? Data("{}".utf8)
}

/// Maps a URL path to a file inside contentRoot, or nil if it escapes the root.
func resolve(_ urlPath: String) -> URL? {
    let decoded = urlPath.removingPercentEncoding ?? urlPath
    let u = contentRoot.appendingPathComponent(decoded).standardizedFileURL
    guard u.path == contentRoot.path || u.path.hasPrefix(contentRoot.path + "/") else { return nil }
    return u
}
