// The local web server every screen talks to. 127.0.0.1 only.
import Cocoa
import WebKit

// MARK: - Tiny HTTP server (127.0.0.1 only, plain BSD sockets)

final class Server {
    let fd: Int32
    let port: UInt16
    var source: DispatchSourceRead?
    let queue = DispatchQueue(label: "offgrid.http", attributes: .concurrent)

    /// Listens on 127.0.0.1 only, on a free port picked by the system.
    init() throws {
        let fd = socket(AF_INET, SOCK_STREAM, 0)
        guard fd >= 0 else { throw POSIXError(.EIO) }
        var yes: Int32 = 1
        setsockopt(fd, SOL_SOCKET, SO_REUSEADDR, &yes, socklen_t(MemoryLayout<Int32>.size))
        setsockopt(fd, SOL_SOCKET, SO_NOSIGPIPE, &yes, socklen_t(MemoryLayout<Int32>.size))
        var addr = sockaddr_in()
        addr.sin_family = sa_family_t(AF_INET)
        addr.sin_addr.s_addr = inet_addr("127.0.0.1")
        var len = socklen_t(MemoryLayout<sockaddr_in>.size)
        // Same port every launch when it's free, so saved ticks and settings stick. Else any free port.
        let ok = [UInt16(47321), 0].contains { want in
            addr.sin_port = want.bigEndian
            return withUnsafeMutablePointer(to: &addr) {
                $0.withMemoryRebound(to: sockaddr.self, capacity: 1) { bind(fd, $0, len) == 0 }
            }
        } && withUnsafeMutablePointer(to: &addr) {
            $0.withMemoryRebound(to: sockaddr.self, capacity: 1) { listen(fd, 64) == 0 && getsockname(fd, $0, &len) == 0 }
        }
        guard ok else { close(fd); throw POSIXError(.EADDRINUSE) }
        self.fd = fd
        port = UInt16(bigEndian: addr.sin_port)
    }

    func start(ready: @escaping (UInt16) -> Void) {
        let src = DispatchSource.makeReadSource(fileDescriptor: fd, queue: queue)
        src.setEventHandler { [weak self] in
            guard let self else { return }
            let c = accept(self.fd, nil, nil)
            guard c >= 0 else { return }
            var yes: Int32 = 1
            setsockopt(c, SOL_SOCKET, SO_NOSIGPIPE, &yes, socklen_t(MemoryLayout<Int32>.size))
            var tv = timeval(tv_sec: 15, tv_usec: 0)
            setsockopt(c, SOL_SOCKET, SO_RCVTIMEO, &tv, socklen_t(MemoryLayout<timeval>.size))
            self.queue.async { self.handle(c); close(c) }
        }
        src.resume()
        source = src
        ready(port)
    }

    private func writeAll(_ c: Int32, _ d: Data) -> Bool {
        d.withUnsafeBytes { (p: UnsafeRawBufferPointer) -> Bool in
            var off = 0
            while off < d.count {
                let n = Darwin.write(c, p.baseAddress! + off, d.count - off)
                if n <= 0 { return false }
                off += n
            }
            return true
        }
    }

    private func handle(_ c: Int32) {
        var buf = Data()
        var tmp = [UInt8](repeating: 0, count: 65536)
        while buf.range(of: Data("\r\n\r\n".utf8)) == nil {
            let n = read(c, &tmp, tmp.count)
            if n <= 0 || buf.count > 65536 { return }
            buf.append(contentsOf: tmp[0..<n])
        }
        let end = buf.range(of: Data("\r\n\r\n".utf8))!
        let head = String(decoding: buf[..<end.lowerBound], as: UTF8.self)
        var body = Data(buf[end.upperBound...])
        // Read a request body (saves and photo uploads), up to 40 MB.
        if let cl = head.components(separatedBy: "\r\n").first(where: { $0.lowercased().hasPrefix("content-length:") }),
           let want = Int(cl.split(separator: ":")[1].trimmingCharacters(in: .whitespaces)) {
            // Too big: say so. Never store part of a file and call it saved.
            guard want <= 40 << 20 else { return send(c, 413, "text/plain", Data("That file is over 40 MB.".utf8)) }
            while body.count < want {
                let n = read(c, &tmp, min(tmp.count, want - body.count))
                if n <= 0 { return }
                body.append(contentsOf: tmp[0..<n])
            }
        }
        respond(c, head, body)
    }

    private func respond(_ c: Int32, _ head: String, _ body: Data) {
        let lines = head.components(separatedBy: "\r\n")
        let parts = (lines.first ?? "").split(separator: " ")
        guard parts.count >= 2, ["GET", "HEAD", "PUT", "POST"].contains(String(parts[0])) else {
            return send(c, 405, "text/plain", Data("Method not allowed".utf8))
        }
        let isHead = parts[0] == "HEAD"
        var headers: [String: String] = [:]
        for l in lines.dropFirst() {
            if let i = l.firstIndex(of: ":") {
                headers[l[..<i].lowercased()] = l[l.index(after: i)...].trimmingCharacters(in: .whitespaces)
            }
        }
        var path = String(parts[1].split(separator: "?", maxSplits: 1).first ?? "/")
        if path == "/" { path = "/hub/index.html" }
        if path.hasSuffix("/") { path += "index.html" }

        if path == "/api/manifest" { return send(c, 200, "application/json", manifest()) }

        // Your records: GET /api/data/<name> reads, PUT saves (with backups). POST /api/media stores a photo.
        // Writes need the X-OffGrid header, which a web page on another site can't send to this server.
        if path.hasPrefix("/api/data/") {
            let name = String(path.dropFirst(10))
            guard dataNameOK(name) else { return send(c, 400, "text/plain", Data("bad name".utf8)) }
            if parts[0] == "PUT" {
                guard headers["x-offgrid"] == "1", (try? JSONSerialization.jsonObject(with: body)) != nil else {
                    return send(c, 403, "text/plain", Data("refused".utf8)) }
                // Check the revision and write as one step, so two saves can't slip past each other.
                dataLock.lock(); defer { dataLock.unlock() }
                let now = currentRevision(name)
                if let base = headers["x-offgrid-base"], base != now {
                    return send(c, 409, "application/json", Data("{\"error\":\"changed\"}".utf8), extra: ["X-Rev": now])
                }
                let ok = saveData(name, body)
                return send(c, ok ? 200 : 500, "application/json", Data("{\"ok\":true}".utf8), extra: ["X-Rev": revision(body)])
            }
            dataLock.lock(); let file = try? Data(contentsOf: dataDir.appendingPathComponent(name)); dataLock.unlock()
            return send(c, 200, "application/json", file ?? Data("null".utf8), extra: ["X-Rev": revision(file)])
        }
        if path == "/api/media", parts[0] == "POST" {
            guard headers["x-offgrid"] == "1", !body.isEmpty else { return send(c, 403, "text/plain", Data("refused".utf8)) }
            let ext = ["image/png": "png", "image/jpeg": "jpg", "application/pdf": "pdf", "video/mp4": "mp4",
                       "audio/mp4": "m4a", "image/heic": "heic", "video/quicktime": "mov"][headers["content-type"] ?? ""] ?? "bin"
            let dir = dataDir.appendingPathComponent("media")
            try? FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
            let name = UUID().uuidString.lowercased() + "." + ext
            guard (try? body.write(to: dir.appendingPathComponent(name))) != nil else { return send(c, 500, "text/plain", Data()) }
            return send(c, 200, "application/json", Data("{\"url\":\"/media/\(name)\"}".utf8))
        }
        if path.hasPrefix("/api/setup/") {
            let (code, data) = setupAPI(String(path.dropFirst(11)), String(parts[0]), body, trusted: headers["x-offgrid"] == "1")
            return send(c, code, "application/json", data)
        }
        guard parts[0] == "GET" || parts[0] == "HEAD" else { return send(c, 405, "text/plain", Data("Method not allowed".utf8)) }
        if path == "/maps/maps.json" {
            let list = files(in: "maps", ext: "pmtiles").map { $0.lastPathComponent }
            return send(c, 200, "application/json", (try? JSONSerialization.data(withJSONObject: list)) ?? Data("[]".utf8))
        }
        if path == "/api/packs" { return send(c, 200, "application/json", packList()) }
        if path.hasPrefix("/packs/") && packFile(path) == nil { return send(c, 404, "text/plain", Data("Not found".utf8)) }
        let mediaFile: URL? = path.hasPrefix("/packs/") ? packFile(path) : path.hasPrefix("/media/") && dataNameOK(String(path.dropFirst(7)))
            ? dataDir.appendingPathComponent("media").appendingPathComponent(String(path.dropFirst(7))) : nil
        guard let file = mediaFile ?? resolve(path),
              let attrs = try? FileManager.default.attributesOfItem(atPath: file.path),
              (attrs[.type] as? FileAttributeType) == .typeRegular,
              let fh = try? FileHandle(forReadingFrom: file) else {
            return send(c, 404, "text/plain", Data("Not found".utf8))
        }
        defer { try? fh.close() }
        let size = (attrs[.size] as? NSNumber)?.intValue ?? 0
        let mime = mimeTypes[file.pathExtension.lowercased()] ?? "application/octet-stream"

        var start = 0, end = size - 1, status = 200
        if let r = headers["range"], r.hasPrefix("bytes="), !r.contains(",") {
            let spec = r.dropFirst(6).split(separator: "-", omittingEmptySubsequences: false)
            if spec.count == 2 {
                if spec[0].isEmpty, let n = Int(spec[1]) { start = max(0, size - n) }
                else if let s = Int(spec[0]) { start = s; if let e = Int(spec[1]) { end = min(e, size - 1) } }
                status = 206
            }
            if start > end || start >= size {
                return send(c, 416, "text/plain", Data(), extra: ["Content-Range": "bytes */\(size)"])
            }
        }
        let length = max(0, end - start + 1)
        var extra = ["Accept-Ranges": "bytes"]
        if status == 206 { extra["Content-Range"] = "bytes \(start)-\(end)/\(size)" }
        guard sendHeader(c, status, mime, length, extra), !isHead else { return }
        try? fh.seek(toOffset: UInt64(start))
        var remaining = length
        while remaining > 0 {
            guard let chunk = try? fh.read(upToCount: min(remaining, 1 << 20)), !chunk.isEmpty,
                  writeAll(c, chunk) else { return }
            remaining -= chunk.count
        }
    }

    @discardableResult
    private func sendHeader(_ c: Int32, _ status: Int, _ mime: String, _ length: Int, _ extra: [String: String]) -> Bool {
        let reason = [200: "OK", 206: "Partial Content", 400: "Bad Request", 403: "Forbidden", 404: "Not Found", 405: "Method Not Allowed", 409: "Conflict", 413: "Too Large", 502: "Bad Gateway", 500: "Server Error",
                      416: "Range Not Satisfiable"][status] ?? "OK"
        var h = "HTTP/1.1 \(status) \(reason)\r\nContent-Type: \(mime)\r\nContent-Length: \(length)\r\n"
        h += "Cache-Control: no-cache\r\nConnection: close\r\n"
        for (k, v) in extra { h += "\(k): \(v)\r\n" }
        return writeAll(c, Data((h + "\r\n").utf8))
    }

    private func send(_ c: Int32, _ status: Int, _ mime: String, _ body: Data, extra: [String: String] = [:]) {
        if sendHeader(c, status, mime, body.count, extra) { _ = writeAll(c, body) }
    }
}
