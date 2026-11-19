# Roadmap

What's done, what's next, and what I'd like to get to. Each line is small enough to be its own issue. If you want to pick one up, say so in an issue first so two people don't do the same thing.

## Done

- Saves from two screens at the same moment both survive. The server owns a revision of the records file and refuses a stale save, and the screen reads, merges and retries.
- "Show on map", "Pick a location" and map search hand off correctly from the shell to the map.
- Water on hand only counts known volumes. "24 bottles" is not 24 gallons. Drinking water and wash water are compared separately.
- The water guide asks about fuel and chemicals first, before any treatment step, and gives the higher boiling time above 6,500 feet. Checked against the CDC and EPA pages.
- A copy built for someone else comes from one approved file list, and the build fails if anything else is found in it.
- Learn opens to what is actually on the computer. Titles you don't have are listed separately under "What can be added".
- A missing map leads to the Get maps screen.
- Offline check: one screen that reads a real map tile, opens a guide, checks the help layers, reads your records and finds the nearest hospital, water and shelter to Home. Each row says ready or missing, with a button to fix it.
- My Place is simpler: pick what you are adding, name it, pin it. The pin and a few basics come first and the rest is folded away. An edit that was not saved yet is no longer lost when the screen re-reads the records.
- The code is laid out by job: `app/web/` for every screen including the map, `app/macos/` for the Mac shell split into eight small Swift files, `tests/` for tests.

## Next

| # | Change | How you'll know it works |
|---|---|---|
| 2 | Choose your home base | A "Use as home base" button on any place record. "Parents' house" can be the origin for distances without being renamed Home |
| 3 | Say what a distance means | "4.2 mi straight-line from Parents' house". If the origin is the map centre, it says so |
| 4 | Home gets two main buttons | "Something is happening" and "Check my readiness" |
| 5 | Container sizes on supplies | Enter "24 bottles of 500 mL" or "2 jugs of 5 gal" and have it counted properly |
| 6 | Search inside plan pages | Searching "shutoff" opens the step, not only the page title |
| 7 | Plan steps you can edit in the app | Each step keeps a permanent ID, so a tick stays with its task after reordering |
| 8 | A repair action on every missing-content screen | A pack on an unplugged drive shows the drive name and "Check again" |

## Things I'd actually use in an outage

| # | Addition | First useful version |
|---|---|---|
| 9 | Fridge and battery runtime calculator | Pick a power station and a fridge from your records. Uses measured daily energy and usable battery capacity, shown next to your last real unplug test |
| 10 | Per-barrel water tracking | Each barrel has its own capacity, level, use, last cleaning and fitting notes. Stored rainwater and drinking water show as separate totals on Home |
| 11 | Household shutoff card | A photo, written directions and a map point for the water main, breaker panel and other controls. Someone who doesn't know the house can find them |
| 12 | Incident timeline | "Start power outage", then log what happened, who checked what and when. Print it or hand it off |
| 13 | Full backup with a restore preview | Records, photos, plan and ticks in one file. Before restoring it shows counts like "18 records, 7 photos, 2 plans" |
| 14 | Phone field packet | Pick contacts, meeting points, a map excerpt and key instructions. Export one dated file that opens in airplane mode |
| 15 | Radio check-in card | Who to contact, the agreed channel, the check-in time and the fallback. "Log check-in" adds to the timeline |
| 16 | A useful first launch with Wi-Fi off | A small starter collection, a blank contact card and a printable plan, so there's something to do before any download |

## Making the code easier to work on

| # | Change | First move |
|---|---|---|
| 18 | One file for household maths | Water totals, units and days remaining move out of the screens into one tested file that Home and My Place both call |
| 20 | A tiny demo household for tests | A made-up home, one barrel, one contact, one guide and a tiny map, so the whole flow can be tested without downloading a state |
| 21 | Windows | The screens are plain web pages. The shell and local server need a Windows version |
| 22 | A ready-made download | A packaged app on the Releases page, so nobody has to build it |
| 23 | Rewrite the map downloader in Swift | So Get maps doesn't need Python |
