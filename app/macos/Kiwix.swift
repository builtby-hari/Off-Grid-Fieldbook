// Starts and stops kiwix-serve, the reader for .zim wiki files.
import Cocoa
import WebKit

var kiwixURL = ""
// MARK: - Kiwix (the .zim reader)

var kiwix: Process?

func freePort() -> UInt16? {
    let fd = socket(AF_INET, SOCK_STREAM, 0)
    guard fd >= 0 else { return nil }
    defer { close(fd) }
    var addr = sockaddr_in()
    addr.sin_family = sa_family_t(AF_INET)
    addr.sin_addr.s_addr = inet_addr("127.0.0.1")
    addr.sin_port = 0
    var len = socklen_t(MemoryLayout<sockaddr_in>.size)
    let ok = withUnsafeMutablePointer(to: &addr) {
        $0.withMemoryRebound(to: sockaddr.self, capacity: 1) {
            bind(fd, $0, len) == 0 && getsockname(fd, $0, &len) == 0
        }
    }
    return ok ? UInt16(bigEndian: addr.sin_port) : nil
}

/// Started only when the Library is first opened, so the app idles at near zero CPU otherwise.
func startKiwix() {
    guard env["OFFGRID_NO_KIWIX"] == nil, kiwix == nil else { return }
    let zims = files(in: "library", ext: "zim").map { $0.path }
    guard !zims.isEmpty,
          let bin = Bundle.main.url(forAuxiliaryExecutable: "kiwix-serve") ?? env["OFFGRID_KIWIX"].map({ URL(fileURLWithPath: $0) }),
          let port = freePort() else { return }
    let p = Process()
    p.executableURL = bin
    p.arguments = ["--address=127.0.0.1", "--port=\(port)"] + zims
    p.standardOutput = FileHandle.nullDevice
    p.standardError = FileHandle.nullDevice
    do { try p.run(); kiwix = p; kiwixURL = "http://127.0.0.1:\(port)/" }
    catch { NSLog("Off-Grid: kiwix-serve failed to start: \(error)") }
}

func stopKiwix() { if let k = kiwix, k.isRunning { k.terminate() } }
