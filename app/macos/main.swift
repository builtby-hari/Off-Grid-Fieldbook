// Off-Grid: a small native Mac app that shows the offline kit in one window.
// - Serves Contents/Resources/Content over http://127.0.0.1:47321, or a free port if that one is taken (with Range support for PMTiles maps)
// - Starts the bundled kiwix-serve for the .zim libraries
// - Shows everything in a WKWebView
// Built by Hari. Run with --serve-only to start just the server (for testing).
// Launch options (Launch.swift): --port <n> (or OFFGRID_PORT), --open <screen> [--pack <slug>],
// and offgrid://open?view=map&pack=texas links, which also work while the app is running.
import Cocoa
import WebKit

// The parts: Files.swift (content), Records.swift (your data), Packs.swift (state maps), Setup.swift (Get maps),
// Server.swift (local web server), Kiwix.swift (wiki reader), Window.swift (the window). This file only starts things.

// MARK: - Entry

signal(SIGPIPE, SIG_IGN)
if CommandLine.arguments.contains("--serve-only") {
    let s = try Server()
    s.start { p in print("http://127.0.0.1:\(p)/"); fflush(stdout) }
    atexit { stopKiwix() }
    dispatchMain()
}

let app = NSApplication.shared
let delegate = AppDelegate()
app.delegate = delegate
app.setActivationPolicy(.regular)
app.run()
