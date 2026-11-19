// The Get maps screen's back end: runs the pack tool to download a state.
import Cocoa
import WebKit

// MARK: - Setup: get a state's map from inside the app (no Terminal)
// The app runs its own map pack tool (Resources/Tools/offgrid-pack.py) with the Mac's Python.
// Downloads only ever start from a button the user presses on the Setup screen.
let supportDir = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask)[0].appendingPathComponent("Off-Grid")
let packsHome = supportDir.appendingPathComponent("packs")
let toolsDir: URL = env["OFFGRID_TOOLS"].map { URL(fileURLWithPath: $0) } ?? Bundle.main.resourceURL!.appendingPathComponent("Tools")
let packLevels = ["lite", "standard", "full"]

/// A real Python 3, or nil. /usr/bin/python3 is only real once Apple's command line tools are installed.
func findPython() -> String? {
    let fm = FileManager.default
    let clt = Process(); clt.executableURL = URL(fileURLWithPath: "/usr/bin/xcode-select"); clt.arguments = ["-p"]
    clt.standardOutput = FileHandle.nullDevice; clt.standardError = FileHandle.nullDevice
    if (try? clt.run()) != nil { clt.waitUntilExit(); if clt.terminationStatus == 0 && fm.isExecutableFile(atPath: "/usr/bin/python3") { return "/usr/bin/python3" } }
    return ["/opt/homebrew/bin/python3", "/usr/local/bin/python3"].first { fm.isExecutableFile(atPath: $0) }
}
func knownRegion(_ slug: String) -> Bool {
    guard dataNameOK(slug), !slug.contains(".") else { return false }
    if slug == "usa-overview" { return true }
    guard let d = try? Data(contentsOf: toolsDir.appendingPathComponent("regions.json")),
          let o = try? JSONSerialization.jsonObject(with: d) as? [String: Any], let rs = o["regions"] as? [[String: Any]] else { return false }
    return rs.contains { ($0["slug"] as? String) == slug }
}
func packTool(_ python: String, _ args: [String]) -> Process {
    let p = Process()
    p.executableURL = URL(fileURLWithPath: python)
    p.arguments = ["-I", toolsDir.appendingPathComponent("offgrid-pack.py").path] + args
    var e = ProcessInfo.processInfo.environment
    e["PYTHONUNBUFFERED"] = "1"
    e["OFFGRID_VENV"] = supportDir.appendingPathComponent("venv").path
    e["OFFGRID_LAYERS_SCRIPT"] = toolsDir.appendingPathComponent("build-survival-layers.py").path
    p.environment = e
    return p
}

/// One download at a time. The Setup screen polls this for progress.
final class SetupJob {
    static let shared = SetupJob()
    private let lock = NSLock()
    private var proc: Process?
    private var lines: [String] = []
    private var title = "", running = false, cancelled = false
    private var exitCode: Int32? = nil

    private func add(_ text: String) {
        lock.lock(); defer { lock.unlock() }
        for l in text.split(whereSeparator: { $0 == "\n" || $0 == "\r" }) where !l.trimmingCharacters(in: .whitespaces).isEmpty { lines.append(String(l)) }
        if lines.count > 300 { lines.removeFirst(lines.count - 300) }
    }
    func snapshot() -> [String: Any] {
        lock.lock(); defer { lock.unlock() }
        return ["running": running, "title": title, "lines": Array(lines.suffix(60)), "exit": exitCode.map { Int($0) } as Any? ?? NSNull()]
    }
    func cancel() { lock.lock(); cancelled = true; let p = proc; lock.unlock(); if let p, p.isRunning { p.terminate() } }

    /// Runs the steps in order. Returns false if a download is already going.
    func start(title t: String, python: String, steps: [(String, [String])]) -> Bool {
        lock.lock()
        if running { lock.unlock(); return false }
        running = true; cancelled = false; title = t; lines = []; exitCode = nil
        lock.unlock()
        DispatchQueue.global(qos: .utility).async {
            var last: Int32 = 0
            for (label, args) in steps {
                self.lock.lock(); let stop = self.cancelled; self.lock.unlock()
                if stop { break }
                self.add(label)
                let p = packTool(python, args), pipe = Pipe()
                p.standardOutput = pipe; p.standardError = pipe
                pipe.fileHandleForReading.readabilityHandler = { h in let d = h.availableData; if !d.isEmpty { self.add(String(decoding: d, as: UTF8.self)) } }
                do { try p.run() } catch { self.add("Could not start: \(error.localizedDescription)"); last = 1; break }
                self.lock.lock(); self.proc = p; self.lock.unlock()
                p.waitUntilExit()
                pipe.fileHandleForReading.readabilityHandler = nil
                last = p.terminationStatus
                // The layer builder's one-time setup may fail (no network, old Python). The map itself can still download.
                if last != 0 && !(args.first == "setup") { break }
                if last != 0 { self.add("The layer builder could not be set up. The base map and terrain will still download."); last = 0 }
            }
            self.lock.lock()
            if self.cancelled { self.lines.append("Stopped. Press Download again to pick up where it left off.") }
            self.running = false; self.proc = nil; self.exitCode = self.cancelled ? -1 : last
            self.lock.unlock()
        }
        return true
    }
}

/// Handles /api/setup/*. Returns (status, JSON body).
func setupAPI(_ sub: String, _ method: String, _ body: Data, trusted: Bool) -> (Int, Data) {
    func json(_ o: Any) -> Data { (try? JSONSerialization.data(withJSONObject: o)) ?? Data("{}".utf8) }
    func fail(_ code: Int, _ msg: String) -> (Int, Data) { (code, json(["error": msg])) }
    let python = findPython()
    if sub == "status", method == "GET" {
        let free = (try? FileManager.default.attributesOfFileSystem(forPath: NSHomeDirectory())[.systemFreeSize] as? NSNumber)?.int64Value ?? 0
        let packs = (try? JSONSerialization.jsonObject(with: packList())) ?? []
        let tools = FileManager.default.fileExists(atPath: toolsDir.appendingPathComponent("offgrid-pack.py").path)
        return (200, json(["python": python != nil, "tools": tools, "free": free, "packs": packs, "packsDir": packsHome.path, "job": SetupJob.shared.snapshot()]))
    }
    guard method == "POST", trusted else { return fail(403, "refused") }
    if sub == "cancel" { SetupJob.shared.cancel(); return (200, json(["ok": true])) }
    if sub == "tools" {   // opens Apple's own installer window for the command line tools
        let p = Process(); p.executableURL = URL(fileURLWithPath: "/usr/bin/xcode-select"); p.arguments = ["--install"]
        p.standardOutput = FileHandle.nullDevice; p.standardError = FileHandle.nullDevice
        try? p.run(); return (200, json(["ok": true]))
    }
    guard let o = try? JSONSerialization.jsonObject(with: body) as? [String: Any],
          let region = o["region"] as? String, knownRegion(region),
          let level = o["level"] as? String, packLevels.contains(level) else { return fail(400, "Pick a state and a size.") }
    guard let py = python else { return fail(409, "Python is not installed yet.") }
    try? FileManager.default.createDirectory(at: packsHome, withIntermediateDirectories: true)
    if sub == "plan" {
        let p = packTool(py, ["plan", region, "--level", level, "--json", "--to", packsHome.path]), out = Pipe()
        p.standardOutput = out; p.standardError = FileHandle.nullDevice
        guard (try? p.run()) != nil else { return fail(500, "The map tool could not start.") }
        let d = out.fileHandleForReading.readDataToEndOfFile(); p.waitUntilExit()
        guard p.terminationStatus == 0, (try? JSONSerialization.jsonObject(with: d)) != nil else {
            return fail(502, "Could not check the size. This step needs the internet.") }
        return (200, d)
    }
    if sub == "get" {
        var steps: [(String, [String])] = []
        let wantLayers = (o["layers"] as? Bool) ?? true
        if wantLayers { steps.append(("Getting the map layer builder ready (one time)", ["setup"])) }
        steps.append(("Downloading the map", ["get", region, "--level", level, "--to", packsHome.path, "--parts", wantLayers ? "basemap,terrain,layers" : "basemap,terrain"]))
        return SetupJob.shared.start(title: "\(region) (\(level))", python: py, steps: steps)
            ? (200, json(["ok": true])) : fail(409, "A download is already running.")
    }
    return fail(404, "not found")
}
