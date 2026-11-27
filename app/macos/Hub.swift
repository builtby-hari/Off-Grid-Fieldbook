// Hub drives: a removable drive (the Flipper's starter image, or its SD card in a card reader)
// that carries map packs. The app only ever reads from these drives. It never writes to them.
import Foundation

// A drive counts as a hub only when it has a marker file, offgrid-hub.json:
//   starter: /Volumes/<name>/offgrid-hub.json             packs in /Volumes/<name>/packs
//   full:    /Volumes/<name>/OffGrid-Hub/offgrid-hub.json packs in /Volumes/<name>/OffGrid-Hub/packs
// Marker shape (see app/web/CONTRACT.md):
//   { "name": "Off-Grid Flipper hub", "kind": "starter" | "full", "version": 1, "built": "2026-11-27" }
// "version" is the marker format. This app reads version 1 and ignores keys it does not know.

let hubMarkerName = "offgrid-hub.json"
let hubFolderName = "OffGrid-Hub"
let hubKinds = ["full", "starter"]   // search order: a full hub beats a starter for the same pack

struct Hub {
    let id: String        // "OFFGRID" for a starter, "FlipperZero/OffGrid-Hub" for a full hub
    let name: String
    let kind: String
    let version: Int
    let built: String?
    let volume: String    // the drive's name, as shown in Finder
    let root: URL         // the folder that holds offgrid-hub.json
    var packs: URL { root.appendingPathComponent("packs") }
    var json: [String: Any] {
        var o: [String: Any] = ["id": id, "name": name, "kind": kind, "version": version, "volume": volume]
        if let built { o["built"] = built }
        return o
    }
}

/// Mount points of local drives under /Volumes, read from the kernel's mount table.
/// MNT_NOWAIT means this never touches the drives, so a slow or dead drive can't stall it.
/// Network shares are skipped: checking a file on a dead share can hang for minutes.
/// OFFGRID_VOLUMES=<folder> lists that folder's subfolders instead (for tests without real drives).
func localVolumes() -> [(path: String, key: String)] {
    if let fake = env["OFFGRID_VOLUMES"] {
        let names = (try? FileManager.default.contentsOfDirectory(atPath: fake)) ?? []
        return names.filter { !$0.hasPrefix(".") }.sorted().map { let p = fake + "/" + $0; return (p, p) }
    }
    let n = getfsstat(nil, 0, MNT_NOWAIT)
    guard n > 0 else { return [] }
    let cap = Int(n) + 8
    let buf = UnsafeMutablePointer<statfs>.allocate(capacity: cap)
    defer { buf.deallocate() }
    let got = getfsstat(buf, Int32(cap * MemoryLayout<statfs>.stride), MNT_NOWAIT)
    guard got > 0 else { return [] }
    var out: [(String, String)] = []
    for i in 0..<min(Int(got), cap) {
        var s = buf[i]
        guard s.f_flags & UInt32(MNT_LOCAL) != 0 else { continue }
        let path = withUnsafeBytes(of: &s.f_mntonname) { String(decoding: $0.prefix(while: { $0 != 0 }), as: UTF8.self) }
        guard path.hasPrefix("/Volumes/"), !path.dropFirst(9).contains("/") else { continue }
        out.append((path, "\(path)|\(s.f_fsid.val.0)|\(s.f_fsid.val.1)"))
    }
    return out.sorted { $0.0 < $1.0 }
}

/// Reads a marker file, or nil if it is missing, too big, not JSON or not a kind this app knows.
func readHubMarker(_ root: URL, id: String, volume: String) -> Hub? {
    let f = root.appendingPathComponent(hubMarkerName)
    guard let attrs = try? FileManager.default.attributesOfItem(atPath: f.path),
          (attrs[.type] as? FileAttributeType) == .typeRegular,
          ((attrs[.size] as? NSNumber)?.intValue ?? 0) <= 64 << 10,
          let d = try? Data(contentsOf: f),
          let o = (try? JSONSerialization.jsonObject(with: d)) as? [String: Any],
          let kind = o["kind"] as? String, hubKinds.contains(kind) else { return nil }
    let clean = { (s: String?) -> String? in
        s.map { String($0.unicodeScalars.filter { !CharacterSet.controlCharacters.contains($0) }.prefix(80)) }
    }
    return Hub(id: id, name: clean(o["name"] as? String) ?? volume, kind: kind,
               version: (o["version"] as? NSNumber)?.intValue ?? 1, built: clean(o["built"] as? String),
               volume: volume, root: root.standardizedFileURL)
}

private let hubLock = NSLock()
private var hubCache: (key: String, at: Date, hubs: [Hub])?

/// Connected hubs, full ones first. Cheap enough to call on every request: the mount table is read
/// each time (so plugging in or pulling a drive shows up at once), and the marker files are read again
/// only when the set of drives changes, or every 10 seconds.
func connectedHubs() -> [Hub] {
    let vols = localVolumes()
    let key = vols.map { $0.key }.joined(separator: "\n")
    hubLock.lock()
    if let c = hubCache, c.key == key, Date().timeIntervalSince(c.at) < 10 { hubLock.unlock(); return c.hubs }
    hubLock.unlock()
    var found: [Hub] = []
    for v in vols {
        let vol = URL(fileURLWithPath: v.path, isDirectory: true)
        let name = vol.lastPathComponent
        if let h = readHubMarker(vol, id: name, volume: name) { found.append(h) }
        if let h = readHubMarker(vol.appendingPathComponent(hubFolderName), id: name + "/" + hubFolderName, volume: name) { found.append(h) }
    }
    let rank = { (h: Hub) in hubKinds.firstIndex(of: h.kind) ?? hubKinds.count }
    found.sort { rank($0) != rank($1) ? rank($0) < rank($1) : $0.id < $1.id }
    hubLock.lock(); hubCache = (key, Date(), found); hubLock.unlock()
    return found
}

/// GET /api/hub: which hubs are plugged in, and where each pack the app can see comes from.
func hubState() -> Data {
    let roots = taggedPackRoots()
    let hubs = connectedHubs().map { h -> [String: Any] in
        var o = h.json
        o["packs"] = packSlugs(in: h.packs)
        return o
    }
    let packs = packOrigins(roots).map { p -> [String: Any] in
        var o: [String: Any] = ["slug": p.slug, "origin": p.origin]
        if let h = p.root.hub { o["hub"] = h.id }
        if !p.also.isEmpty { o["also"] = p.also }
        return o
    }
    return (try? JSONSerialization.data(withJSONObject: ["hubs": hubs, "packs": packs])) ?? Data("{}".utf8)
}
