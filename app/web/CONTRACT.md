# How Off-Grid screens talk to the shell

The shell is `index.html`. It owns the sidebar, the search box and the address. Each screen is its own page in a frame: `now.html`, `learn.html`, `place.html`, and the map (`/maps/index.html`). Frames stay loaded when you switch tabs.

Every screen loads, in this order: `ui.css`, `og.js`, `ui.js` (and `md.js` if it renders Markdown). No screen defines its own colors or copies a helper that lives in those files.

## Addresses

The address is `#<tab>/<rest>` or `#<tab>?<rest>`. The shell reads the tab. The rest is handed to the screen as that frame's own hash.

| Address | Opens |
|---|---|
| `#now` | Now, scenario picker |
| `#now/<scenario id>` | One scenario, for example `#now/power` |
| `#map` | The map |
| `#map?fly=<lng>,<lat>` | Map, centred on a point with a marker |
| `#map?pick=<record id>` | Map, waiting for a click to set that record's point |
| `#map?q=<text>` | Map, with the search box filled in and run |
| `#place` | My Place overview |
| `#place/r=<record id>` | One record |
| `#place/calc` | Supplies calculator |
| `#learn` | Library by topic |
| `#learn/<slug>` | One manual or guide |
| `#learn/<slug>/<section id>` | A section of it |
| `#learn/plants?q=<text>` | Plants, searched |
| `#wiki/<kiwix path>` | Wiki library, for example `#wiki/search?pattern=water` |
| `#plan/<page title>` | A plan page |
| `#search/<text>` | Search everything |
| `#setup` | Get maps: download a state's map from inside the app |
| `#check` | Offline check: opens real files and says what is ready |
| `#help` | Help |

A screen reads its part with `UI.onRoute(rest => ...)`. It runs once on load and again whenever the shell changes it. Back and Forward work because every move changes the address.

## Screen to shell

A screen never reaches into another screen. It calls `UI.go("<address without #>")`, which posts `{ og: "go", route }` to the shell.

Other messages, all sent with `UI.tell(...)`:

| Message | Meaning |
|---|---|
| `{ og: "pickLocation", id }` | Ask the map for a point for this record |
| `{ og: "showOnMap", lng, lat }` | Show this point on the map |
| `{ og: "locationPicked", id, lng, lat }` | The map answers a pick. The shell passes it to My Place |
| `{ og: "openRecord", id }` | Open a record in My Place |
| `{ og: "recordsChanged" }` | This screen just saved records. The shell tells the other screens so they read them again |
| `{ og: "shown" }` | Sent by the shell to a screen each time it is shown |
| `{ og: "openGuide", href }` | Old guide links saved in records. The shell translates them to new addresses |

## Rules

- Messages are sent to `location.origin`, never `*`.
- The shell only accepts messages from its own frames. A screen only accepts messages from its parent (`UI.onMessage`).
- Records are read and written only through `og.js`. `OG.save()` merges with the file on disk first, so two screens can never overwrite each other. After another screen may have saved, call `OG.load({ fresh: true })`.
- Theme: `ui.js` applies the saved theme on load and follows changes live. Screens do nothing.
