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
| `#map?pack=<slug>` | Map, switched to that pack (region `pack:<slug>`) and fitted to its `bbox`. If no such pack is listed, the map stays as it is. Sent by launch links, see below |
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

## Opening the app on a screen

The Mac app can be told which screen to open, from outside the page:

| Way | Example | Notes |
|---|---|---|
| Link | `open "offgrid://open?view=map&pack=texas"` | Works whether the app is running or not. Short form: `offgrid://map?pack=texas` |
| Link to one copy | `open -b com.builtbyhari.offgrid "offgrid://open?view=map&pack=texas"` | When more than one edition is installed |
| Arguments | `open -a "Off-Grid Fieldbook" --args --open map --pack texas` | Only when the app is not running yet (macOS drops arguments for a running app) |

`view` is one of `home`, `map`, `place`, `learn`, `setup`, `check`, `help`. `pack` is a pack slug and only applies to `map`. Anything else is ignored. The app turns it into the shell address `#map?pack=texas` (or `#<view>`), and brings its window forward. If the shell is already open it changes the address in place, so open screens keep their state.

For testing: `OFFGRID_PORT=<n>` (or `--port <n>`) makes the server use only that port, and `0` means any free port. Without it the app prefers 127.0.0.1:47321.

## Hub drives

A hub drive is a removable drive that carries map packs (and later the library). The app reads it and never writes to it. A drive counts as a hub only if it has a marker file:

| Kind | Marker | Packs |
|---|---|---|
| `starter` (the Flipper's small OFFGRID image, over USB) | `/Volumes/<drive>/offgrid-hub.json` | `/Volumes/<drive>/packs/<slug>/` |
| `full` (the Flipper's SD card, in a card reader) | `/Volumes/<drive>/OffGrid-Hub/offgrid-hub.json` | `/Volumes/<drive>/OffGrid-Hub/packs/<slug>/` |

Marker shape (JSON, under 64 KB):

```json
{ "name": "Off-Grid Flipper hub", "kind": "full", "version": 1, "built": "2026-11-27" }
```

`kind` must be `starter` or `full`, or the marker is ignored. `version` is the marker format (this app reads 1). `name` and `built` are shown to people and are optional. Unknown keys are ignored. Only local drives are checked, never network shares.

Pack search order: full hubs, then starter hubs, then this Mac's own pack folders. The first one that has `<slug>/pack.json` wins, so a hub's copy (with satellite) is used while it is plugged in, and the Mac's copy takes over as soon as it is pulled. Pack files carry an `ETag`, so the map's PMTiles reader notices when the file behind a pack changes and rereads it.

`GET /api/packs` returns each pack's `pack.json` with three keys added:

| Key | Meaning |
|---|---|
| `origin` | `"hub"` or `"local"` |
| `hub` | The hub id it comes from, for example `"FlipperZero/OffGrid-Hub"` or `"OFFGRID"` (only when `origin` is `hub`) |
| `also` | Other places with the same pack, for example `["local"]`: what takes over if the drive is pulled (only when there are any) |

`GET /api/hub` returns the drives:

```json
{ "hubs": [ { "id": "FlipperZero/OffGrid-Hub", "name": "Off-Grid Flipper hub", "kind": "full", "version": 1,
              "volume": "FlipperZero", "built": "2026-11-27", "packs": ["texas"] } ],
  "packs": [ { "slug": "texas", "origin": "hub", "hub": "FlipperZero/OffGrid-Hub", "also": ["local"] } ] }
```

Both are cheap to call. Plugging in or pulling a drive shows up on the next call. A screen that wants to react can poll `/api/hub` every few seconds while it is shown.

## Rules

- Messages are sent to `location.origin`, never `*`.
- The shell only accepts messages from its own frames. A screen only accepts messages from its parent (`UI.onMessage`).
- Records are read and written only through `og.js`. `OG.save()` merges with the file on disk first, so two screens can never overwrite each other. After another screen may have saved, call `OG.load({ fresh: true })`.
- Theme: `ui.js` applies the saved theme on load and follows changes live. Screens do nothing.
