// The app window, menus and the web view.
import Cocoa
import WebKit

// MARK: - Window

final class AppDelegate: NSObject, NSApplicationDelegate, WKNavigationDelegate, WKUIDelegate, WKScriptMessageHandler {
    var window: NSWindow!
    var web: WKWebView!
    var server: Server!
    var port: UInt16 = 0

    func applicationDidFinishLaunching(_ n: Notification) {
        buildMenu()
        let cfg = WKWebViewConfiguration()
        cfg.userContentController.add(self, name: "offgrid")
        cfg.preferences.setValue(true, forKey: "developerExtrasEnabled")
        web = WKWebView(frame: .zero, configuration: cfg)
        web.navigationDelegate = self
        web.uiDelegate = self

        window = NSWindow(contentRect: NSRect(x: 0, y: 0, width: 1280, height: 820),
                          styleMask: [.titled, .closable, .miniaturizable, .resizable], backing: .buffered, defer: false)
        window.title = "Off-Grid Fieldbook"
        window.minSize = NSSize(width: 820, height: 560)
        window.contentView = web
        window.center()
        window.setFrameAutosaveName("OffGridMain")
        window.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)

        do {
            server = try Server()
            server.start { [weak self] p in
                DispatchQueue.main.async {
                    guard let self, self.port == 0 else { return }
                    self.port = p
                    self.web.load(URLRequest(url: URL(string: "http://127.0.0.1:\(p)/hub/index.html")!))
                }
            }
        } catch {
            web.loadHTMLString("<h2>Off-Grid could not start its local server.</h2><p>\(error)</p>", baseURL: nil)
        }
    }

    func applicationShouldTerminateAfterLastWindowClosed(_ s: NSApplication) -> Bool { true }
    func applicationWillTerminate(_ n: Notification) { stopKiwix(); SetupJob.shared.cancel() }

    func isLocal(_ u: URL?) -> Bool { u?.host == "127.0.0.1" || u?.scheme == "about" || u?.scheme == "blob" || u?.scheme == "data" }

    // Anything that leaves this Mac opens in the normal browser instead.
    func webView(_ w: WKWebView, decidePolicyFor a: WKNavigationAction, decisionHandler: @escaping (WKNavigationActionPolicy) -> Void) {
        if let u = a.request.url, !isLocal(u) { NSWorkspace.shared.open(u); return decisionHandler(.cancel) }
        decisionHandler(.allow)
    }

    func webView(_ w: WKWebView, createWebViewWith c: WKWebViewConfiguration, for a: WKNavigationAction, windowFeatures f: WKWindowFeatures) -> WKWebView? {
        if let u = a.request.url { NSWorkspace.shared.open(u) }
        return nil
    }

    // Messages from the page: open a book in Preview, or reveal it in Finder.
    func userContentController(_ uc: WKUserContentController, didReceive m: WKScriptMessage) {
        guard let body = m.body as? [String: String], let action = body["action"] else { return }
        switch action {
        case "openFile", "reveal":
            guard let path = body["path"], let f = resolve(path),
                  FileManager.default.fileExists(atPath: f.path) else { return }
            if action == "reveal" { NSWorkspace.shared.activateFileViewerSelecting([f]) }
            else { NSWorkspace.shared.open(f) }
        case "kiwix":
            startKiwix()
            let js = "window.onKiwix && window.onKiwix(\(kiwixURL.isEmpty ? "''" : "'\(kiwixURL)'"))"
            web.evaluateJavaScript(js, completionHandler: nil)
        case "openBrowser":
            if let s = body["url"], let u = URL(string: s), u.host == "127.0.0.1" { NSWorkspace.shared.open(u) }
        default: break
        }
    }

    func buildMenu() {
        let main = NSMenu()
        let appItem = NSMenuItem(); main.addItem(appItem)
        let appMenu = NSMenu()
        appMenu.addItem(withTitle: "About Off-Grid Fieldbook", action: #selector(NSApplication.orderFrontStandardAboutPanel(_:)), keyEquivalent: "")
        appMenu.addItem(.separator())
        appMenu.addItem(withTitle: "Hide Off-Grid Fieldbook", action: #selector(NSApplication.hide(_:)), keyEquivalent: "h")
        appMenu.addItem(withTitle: "Quit Off-Grid Fieldbook", action: #selector(NSApplication.terminate(_:)), keyEquivalent: "q")
        appItem.submenu = appMenu

        let editItem = NSMenuItem(); main.addItem(editItem)
        let edit = NSMenu(title: "Edit")
        edit.addItem(withTitle: "Undo", action: Selector(("undo:")), keyEquivalent: "z")
        edit.addItem(withTitle: "Redo", action: Selector(("redo:")), keyEquivalent: "Z")
        edit.addItem(.separator())
        edit.addItem(withTitle: "Cut", action: #selector(NSText.cut(_:)), keyEquivalent: "x")
        edit.addItem(withTitle: "Copy", action: #selector(NSText.copy(_:)), keyEquivalent: "c")
        edit.addItem(withTitle: "Paste", action: #selector(NSText.paste(_:)), keyEquivalent: "v")
        edit.addItem(withTitle: "Select All", action: #selector(NSText.selectAll(_:)), keyEquivalent: "a")
        edit.addItem(withTitle: "Find", action: #selector(NSResponder.performTextFinderAction(_:)), keyEquivalent: "f").tag = 1
        editItem.submenu = edit

        let viewItem = NSMenuItem(); main.addItem(viewItem)
        let view = NSMenu(title: "View")
        view.addItem(withTitle: "Home", action: #selector(goHome), keyEquivalent: "1").target = self
        view.addItem(withTitle: "Reload", action: #selector(reload), keyEquivalent: "r").target = self
        view.addItem(withTitle: "Enter Full Screen", action: #selector(NSWindow.toggleFullScreen(_:)), keyEquivalent: "f").keyEquivalentModifierMask = [.command, .control]
        viewItem.submenu = view

        let winItem = NSMenuItem(); main.addItem(winItem)
        let win = NSMenu(title: "Window")
        win.addItem(withTitle: "Minimize", action: #selector(NSWindow.performMiniaturize(_:)), keyEquivalent: "m")
        win.addItem(withTitle: "Close", action: #selector(NSWindow.performClose(_:)), keyEquivalent: "w")
        winItem.submenu = win
        NSApp.windowsMenu = win
        NSApp.mainMenu = main
    }

    @objc func goHome() { if port > 0 { web.load(URLRequest(url: URL(string: "http://127.0.0.1:\(port)/hub/index.html")!)) } }
    @objc func reload() { web.reload() }
}
