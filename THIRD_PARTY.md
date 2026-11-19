# Third-party code and data

This file lists the code and data that come from other people. Where a file does not say its license, that is stated here. Check the upstream project before you reuse anything.

## Code in this repo

| File | What it is | License |
|---|---|---|
| `app/web/map/lib/maplibre-gl.js` | MapLibre GL JS, version 5.6.0 per its URL | 3-Clause BSD, from the file header. Full text: https://github.com/maplibre/maplibre-gl-js/blob/v5.6.0/LICENSE.txt |
| `app/web/map/lib/maplibre-gl.css` | MapLibre GL stylesheet | No license text found in the file. Check upstream. |
| `app/web/map/lib/maplibre-contour.min.js` | maplibre-contour, with a helper library bundled | The header has a Microsoft Corporation copyright notice and permission text. The file does not name the license. Check upstream. |
| `app/web/map/lib/pmtiles.js` | PMTiles reader for the browser (module name `pmtiles`) | No license text found in the file. Check upstream. |
| `app/web/map/lib/basemaps.js` | Basemap style code (module name `basemaps`) | No license text found in the file. Check upstream. |

## Fonts and sprites

| Files | What they are | License |
|---|---|---|
| `app/web/map/fonts/Noto Sans Regular`, `Noto Sans Italic`, `Noto Sans Medium` (`.pbf` glyph files) | Map label fonts, named after Noto Sans | No license text found in the files. Check upstream for the Noto Sans license. |
| `app/web/map/sprites/light.png`, `light.json`, `light@2x.png`, `light@2x.json` | Map icons | No license text found in the files. Check upstream. |

## Data sources

| Source | Used for | License or terms (as noted in the project) | Shipped in this repo? |
|---|---|---|---|
| OpenStreetMap | base map, survival layers, railroads | ODbL. Written as "ODbL (OpenStreetMap contributors)" in each pack's `pack.json`. | No |
| Protomaps daily builds | base map (PMTiles) | ODbL, as written in each pack's `pack.json` | No |
| AWS Terrain Tiles (terrarium) | hill shading and elevation lines | "open data. Credit the source in the app" (project notes). Check upstream for the exact terms. | No |
| USGS | imagery and elevation | US federal, treated as public domain in the project notes. Credit USGS. | No |
| Kiwix ZIM collections | library reader | Each collection has its own license. Check each file. | No |
| Ready.gov and FEMA hazard sheets | Learn | US federal, public domain | Yes, one folder: `content/library/ready-power-outage/` |
| USDA home canning guides | Learn | USDA publication, public domain | No |
| Plants For A Future (PFAF) | plant guide | Personal use only, under PFAF's terms. Not shipped. | No |
| Hesperian health guides | Learn | Personal use only, under Hesperian's terms. Not shipped. | No |
| Texas Manual on Rainwater Harvesting (TWDB) | Learn | No license stated. Personal use only. Not shipped. | No |

## License for the repo itself

The code written for this project is under the MIT License. See `LICENSE`. That license does not cover the third-party files and data listed above. Those keep their own terms.
