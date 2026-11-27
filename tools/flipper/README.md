# Flipper hub launchers (Mac)

Mac only for now. `OffGrid-Windows.txt` is old and not maintained, so don't copy it to the Flipper.

The Flipper's SD card carries Off-Grid two ways. Both have a marker file, `offgrid-hub.json`, so the app and
these scripts know it is an Off-Grid drive and ignore every other drive:

| Drive | How it reaches the Mac | Marker |
|---|---|---|
| Starter (OFFGRID, under 2 GB) | Flipper > Mass Storage, over USB | `offgrid-hub.json` at the drive root |
| Full hub | The SD card in a USB card reader | `OffGrid-Hub/offgrid-hub.json` on the card |

The marker shape is in `app/web/CONTRACT.md` (Hub drives). Nothing personal is ever written to these drives.

## Your own Mac: open Off-Grid when the hub is plugged in

```bash
tools/flipper/install-helper.sh          # opens on the Texas map; add a pack name for another state
tools/flipper/uninstall-helper.sh        # removes it again
```

It installs a LaunchAgent (`com.builtbyhari.offgrid.hubhelper`) for your user only. macOS runs the helper each
time any drive mounts. The helper looks for a hub marker and:
- no hub: does nothing.
- a hub: opens `offgrid://open?view=map&pack=texas` in Off-Grid Fieldbook (the main edition, or the share
  edition if that's the one installed), then sleeps until the hub is unplugged. Other drives mounting in the
  meantime can't open the app again. Unplug and replug the hub and it opens again.

The first time, macOS may say a background item was added, and may ask whether `bash` can read files on a
removable volume. Allow it, or the helper can't see the hub. Its log is `~/Library/Logs/Off-Grid-hub-helper.log`.

## Someone else's Mac: Bad USB, then Mass Storage

1. Copy `OffGrid-Mac.txt` to the Flipper SD card in `badusb/` (qFlipper > SD Card > badusb).
2. Plug the Flipper into the Mac. On the Flipper: Bad USB, pick the script, press OK.
3. It opens Terminal with Spotlight and types one line that waits up to 3 minutes for the Off-Grid drive.
4. When Terminal says so, switch the Flipper to Mass Storage (the OFFGRID image).
5. The line opens `Start Here.html` from the drive and closes. If no drive shows up, it says so.

Keyboard layout must be US (Bad USB types as a US keyboard). Spotlight must be on.
Only run it on your own computers, or with the owner sitting there and saying yes.

## Opening the app on a place

```bash
open "offgrid://open?view=map&pack=texas"                       # running or not
open -b com.builtbyhari.offgrid "offgrid://map?pack=texas"     # pick the edition
open -a "Off-Grid Fieldbook" --args --open map --pack texas     # only when it's not running yet
```

## Tests

`bash tests/hub.test.sh` builds the app into a temp folder, fakes drives, and checks hub discovery, pack order,
unplugging, the launch links and the helper (dry run). It never touches a real drive or port 47321.
