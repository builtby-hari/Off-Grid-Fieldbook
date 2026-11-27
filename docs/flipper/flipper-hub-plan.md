# Off-Grid on the Flipper Zero: plan (2026-11-27)

Hari's answers to 20 questions, turned into a build plan. No personal data ever goes on the Flipper.

## Audit change (2026-11-27): two layers on one SD card
The official Mass Storage app caps images at 2 GB and Flipper USB is about 1 MB/s. Hari chose:
- **Starter drive** (under 2 GB image, through the Flipper's USB): Off-Grid Portable, emergency guides, PDFs, a light Texas road map, installers, START HERE page.
- **Full hub** (a folder on the same SD card, read with a small USB-C card reader): satellite, full maps, Wikipedia, the whole library.
- Portable says "Full hub not connected" when only the starter is there.

Audit fixes to build in: START HERE page with the "allow this app" clicks (unsigned app), Windows = guides and library until its map server is checked, Bad USB for Hari's own use only, checksums plus "Repair Flipper hub", fresh card backup before any change, printable one-page cheat sheet, phone notes (Lightning adapter, exFAT), a points file export for the GPS compass, stage only the satellite file on the Mac.

## The two jobs
1. **Hub drive** (first): the Flipper's SD card holds one exFAT disk image. The Flipper's Mass Storage app shares it as a USB drive named OFFGRID. It holds Off-Grid Portable, maps, the library and installers.
2. **On-Flipper app** (second): a native .fap with a normal menu. It holds emergency steps, Learn guides, tools, a frequency sheet, and GPS compass and coordinates. Its text comes from the app automatically.

## Hub drive contents (Texas now, USA later)
| Part | Size |
|---|---|
| Texas road map (full detail) | 1.5 GB |
| Texas terrain, packed as one WebP file (lossless, 28% smaller) | ~1.7 GB |
| Texas satellite z14 + one metro area at z17 (USGS, public domain) | ~11 GB |
| Texas survival layers | 34 MB |
| Wikipedia Top full text (keep) | 2.6 GB |
| Wikipedia Medicine with pictures (swap for the no-pic version) | ~2-3 GB |
| Science and plants topic packs (chemistry, physics, botany, geography) | ~1-4 GB |
| Other survival ZIMs (iFixit, DIY, electronics, gardening, cooking, mechanics, outdoors, ham, post-disaster, CDC, military medicine, NHS meds, knots, water, food prep) | ~13 GB |
| Books (PDF) plus a Phone folder (PDFs that iPhone and Android Files can open) | ~0.1 GB |
| Installers: Kiwix (Mac, Windows, Android), Organic Maps APK | ~0.5 GB |
| Off-Grid Portable (Mac app, Windows version) | small |
| "Get more" list: bigger versions (all-articles Wikipedia, USA maps) to download when online | tiny |

Dropped from the Flipper: Wikipedia mini (duplicate), coding docs, My Plan (personal).

## Map views
Road, Satellite and Hybrid (satellite with roads and names on top), in the app and on the hub.

## Plug-in flows
- **Hari's Mac:** start Mass Storage on the Flipper. A background helper sees OFFGRID mount and opens Off-Grid on the Texas map.
- **Any other Mac or PC:** run Bad USB, which types one line that waits for the OFFGRID drive. Then switch the Flipper to Mass Storage. Off-Grid Portable opens from the drive, and it has an "Install Fieldbook on this computer" button that copies from the drive with no internet needed.
- **Phones:** Files app, using the PDFs in the Phone folder, plus the Kiwix and Organic Maps installers.
- **Updates:** when the Flipper is plugged into Hari's Mac, Off-Grid asks "Update Flipper?". Big loads go through a USB-C card reader.

## On-Flipper app (phase 2)
- Normal menu: Something happening?, Learn guides, Tools, Radio, Location.
- Tools: CPR metronome, tourniquet timer, water bleach calculator, SOS on the LED and buzzer, weather sensor reader.
- Radio: frequency cheat sheet (NOAA, GMRS/FRS, MURS, ham), Meshtastic notes.
- NFC emergency card: generic first-aid steps on an NTAG215 sticker.
- Location (needs a GPS add-on): coordinates, compass and distance to points (water, shelter, hospital). With a computer plugged in, one click shows that spot on the big map.

## Hardware to buy
GPS module, Meshtastic LoRa node (x2+), NOAA weather radio, NTAG215 stickers, USB-C card reader. These are in FlipperSetup/docs/Buy-List.md.

## Sharing
The public Off-Grid repo gets the Flipper app, the launcher scripts and a "build your own hub" script. Friends download the content themselves.

## Known limits
- Flipper USB is about 1 MB/s, so maps and articles load a bit slower than from a stick.
- NOAA is at 162 MHz, which the Flipper can't receive.
- Meshtastic needs its own LoRa board.
- Mass Storage shares only the image file. Hari's Sub-GHz and NFC captures stay hidden.
- Still to verify on the device: whether Bad USB and Mass Storage can run together, the image size limit, and whether a Mac app runs from exFAT.

## Build order
1. Texas terrain → one WebP file. App serves packed terrain and gets the satellite and hybrid switcher. Test.
2. Off-Grid Portable: the app finds packs and the library on the drive it runs from. Install button.
3. Launchers: Bad USB wait-for-drive (Mac and Windows), auto-open helper on Hari's Mac.
4. Hub builder script: makes the image on the card (card reader) and copies everything.
5. Test on the real Flipper: Mac, a "fresh" user account, then phone Files.
6. FlipperSetup repo and public Off-Grid repo (ask before pushing).
7. On-Flipper .fap app.
