# Off-Grid search audit (runSearch, side worktree)

Port: port.py. Runner: audit.py. Raw data: raw.json. Plants from main repo downloads/extra/plants/plants.json (not in side worktree). Plan pages from main repo plans/. Records skipped.

## Summary table

| query | today's top result | right answer in top 3? | why |
|---|---|---|---|
| generator co | What to do now: Hard freeze | yes | Hard freeze scenario first (it names generator and CO). Power out scenario never says CO, so it is missing. |
| carbon monoxide | What to do now: Hard freeze | yes | Hard freeze scenario, then Power Outage sheet. Power out scenario does not mention CO. |
| generater | (no results) | no | Typo, zero results anywhere. |
| no power | Manuals: PROTECT YOURSELF FROM A POWER OUTAGE (Power Outage Information Sheet · page 1) | yes, by luck | 'no' matches inside not/now/know (278 hits). Power out scenario is dropped because it has no 'no'. Outage sheet wins only because it is first in the index. |
| power out | What to do now: Power out | yes | Power out scenario, then outage sheet. 'out' also matches 'outside', 'about'. |
| blackout | What to do now: Power out | yes | Only through the scenario keyword. Zero manual hits: the corpus never says blackout. |
| burn | Manuals: Survive DURING (Power Outage Information Sheet · page 2) | no | 384 manual hits all tied at score 1. #1 is 'wood-burning stoves', #2-3 Filtration of River Waters (1869). 71 Where There Is No Doctor burn pages hidden. Plants: Laburnum. |
| battery | Manuals: Prepare NOW (Power Outage Information Sheet · page 2) | yes | Outage sheet #1-2, then Filtration of River Waters ('battery of nine boilers'). Power guide sits at row 9. |
| wound | What to do now: Someone is hurt | yes (scenario only) | Manual rows: Unsafe Water p3, Farm Blacksmithing ('wound with twine'). 52 WTND wound pages hidden. Woundwort plants. |
| bleeding | What to do now: Someone is hurt | yes (scenario only) | Manual #1-2 are Building Toilets ('monthly bleeding'). 68 WTND pages hidden. |
| tourniquet | What to do now: Someone is hurt | yes | Hurt scenario, then All Hazards p3, WTND p129. MARCH guide never appears (not indexed). |
| boil water | What to do now: Boil-water notice or no water | yes | Boil-water scenario. 752 manual ties, outage sheet and rainwater manual next. |
| bleach water | What to do now: Boil-water notice or no water | yes | Boil-water scenario, then Texas rainwater, WTND water sheet. |
| how much bleach per gallon | (no results) | no | Zero results: every word must match and 'how', 'much' are not in the scenario that says '8 drops of 6% bleach per gallon'. |
| frozen pipes | Manuals: Home Canning 1: Principles of home canning (page 26) | no | Only 2 hits, both canning ('jars could be frozen'). Hard freeze scenario and Winter Storm sheet say 'freeze' + 'pipes'. |
| fridge food safe | What to do now: Power out | yes | Power out scenario only. Manuals say 'refrigerator', so 0 manual hits. |
| heat stroke | What to do now: Extreme heat | yes | Extreme heat scenario, then Filtration of River Waters (engine 'stroke') at #2. |
| diarrhea kid | Manuals: Health Problems from Unsafe Water (page 3) | no | 'kid' matches 'kidneys'. All 12 hits are kidney pages. WTND says child/baby. |
| oral rehydration | Manuals: Where There Is No Doctor (page 23) | yes | WTND p23, p44 (and p430 index). |
| tornado | What to do now: Tornado warning | yes | Tornado scenario, then 4 All Hazards duplicate pages before the Tornado sheet. |
| co | What to do now: Tornado warning | no | 5,968 hits. Matches cover, coolest, cold, could. Hard freeze only at #3 by accident. |
| water storage | Manuals: Texas Manual on Rainwater Harvesting (page 2) | no | 8 Texas Rainwater pages. Water guide and the 'stored water' scenario step never match 'storage'. |
| first aid kit | Manuals: Emergency Supply Checklist (page 1) | yes | Supply Checklist p1-2, then Dehydrating Foods 1920 ('kitchen'). WTND says 'medicine kit'. |
| canning tomatoes | Manuals: Complete Guide to Home Canning: Intro (page 4) | no | Intro and Principles pages tie first. The Tomatoes chapter scores 6 in Library but shows at row 9, below eight score-1 manual rows. |
| radio | What to do now: Radiation or chemical release | yes, weak | #1 'Radiation or chemical release' (title looks wrong, step mentions NOAA radio). Radio guide at row 10. |
| snake bite | Manuals: American Blacksmithing and Toolsmithing (page 184) | yes (#2) | #1 American Blacksmithing p184 (horse rattlesnake bite). WTND spells it 'snakebite'. |
| cpr | What to do now: Someone is hurt | yes (scenario only) | Only manual hit is 'CCPR' in a human-rights list. Corpus never says CPR, it says 'rescue breathing'. |
| purify water | Manuals: Filtration of River Waters (page 165) | no | Filtration of River Waters #1-2. Corpus says disinfect; guide is titled 'Make water safe to drink'. |

## Detail per query

### generator co
- hits per group: What to do now 1, Manuals 27
- 1. [What to do now] Hard freeze (score 2, scenario:freeze)
- 2. [Manuals] PROTECT YOURSELF FROM A POWER OUTAGE, Power Outage Information Sheet · page 1 (score 1, ready-power-outage)
- 3. [Manuals] Prepare NOW, Power Outage Information Sheet · page 2 (score 1, ready-power-outage)
- manual rows tied at top score: 27 of 27; old/off-topic manual rows in the visible 8: 0; loose substring hits in visible rows: 9; Library first row position: None; right-answer rows hidden past the cap of 8: 3

### carbon monoxide
- hits per group: What to do now 1, Manuals 21, Library 1
- 1. [What to do now] Hard freeze (score 2, scenario:freeze)
- 2. [Manuals] Prepare NOW, Power Outage Information Sheet · page 2 (score 1, ready-power-outage)
- 3. [Manuals] Survive DURING, Power Outage Information Sheet · page 2 (score 1, ready-power-outage)
- manual rows tied at top score: 21 of 21; old/off-topic manual rows in the visible 8: 0; loose substring hits in visible rows: 0; Library first row position: 10; right-answer rows hidden past the cap of 8: 1

### generater
- hits per group: none
- manual rows tied at top score: 0 of 0; old/off-topic manual rows in the visible 8: 0; loose substring hits in visible rows: 0; Library first row position: None; right-answer rows hidden past the cap of 8: 0

### no power
- hits per group: Manuals 278
- 1. [Manuals] PROTECT YOURSELF FROM A POWER OUTAGE, Power Outage Information Sheet · page 1 (score 2, ready-power-outage)
- 2. [Manuals] Prepare NOW, Power Outage Information Sheet · page 2 (score 2, ready-power-outage)
- 3. [Manuals] Survive DURING, Power Outage Information Sheet · page 2 (score 1, ready-power-outage)
- manual rows tied at top score: 2 of 278; old/off-topic manual rows in the visible 8: 3; loose substring hits in visible rows: 8; Library first row position: None; right-answer rows hidden past the cap of 8: 2

### power out
- hits per group: What to do now 1, Manuals 199, Library 1
- 1. [What to do now] Power out (score 7, scenario:power)
- 2. [Manuals] Power Outage Information Sheet, Power Outage Information Sheet · page 1 (score 6, ready-power-outage)
- 3. [Manuals] POWER OUTAGE, Power Outage Information Sheet · page 1 (score 6, ready-power-outage)
- manual rows tied at top score: 4 of 199; old/off-topic manual rows in the visible 8: 0; loose substring hits in visible rows: 8; Library first row position: 10; right-answer rows hidden past the cap of 8: 2

### blackout
- hits per group: What to do now 1
- 1. [What to do now] Power out (score 2, scenario:power)
- manual rows tied at top score: 0 of 0; old/off-topic manual rows in the visible 8: 0; loose substring hits in visible rows: 0; Library first row position: None; right-answer rows hidden past the cap of 8: 0

### burn
- hits per group: Manuals 384, Plants 37
- 1. [Manuals] Survive DURING, Power Outage Information Sheet · page 2 (score 1, ready-power-outage)
- 2. [Manuals] Filtration of River Waters, page 94 (score 1, filtration-river-waters-1869)
- 3. [Manuals] Filtration of River Waters, page 102 (score 1, filtration-river-waters-1869)
- manual rows tied at top score: 384 of 384; old/off-topic manual rows in the visible 8: 2; loose substring hits in visible rows: 7; Library first row position: None; right-answer rows hidden past the cap of 8: 71

### battery
- hits per group: Manuals 29, Library 1
- 1. [Manuals] Prepare NOW, Power Outage Information Sheet · page 2 (score 1, ready-power-outage)
- 2. [Manuals] Survive DURING, Power Outage Information Sheet · page 2 (score 1, ready-power-outage)
- 3. [Manuals] Filtration of River Waters, page 45 (score 1, filtration-river-waters-1869)
- manual rows tied at top score: 29 of 29; old/off-topic manual rows in the visible 8: 5; loose substring hits in visible rows: 0; Library first row position: 9; right-answer rows hidden past the cap of 8: 2

### wound
- hits per group: What to do now 1, Manuals 110, Plants 3
- 1. [What to do now] Someone is hurt (score 2, scenario:hurt)
- 2. [Manuals] Health Problems from Unsafe Water, page 3 (score 1, community-guide-ch05-unsafe-water)
- 3. [Manuals] Farm Blacksmithing, page 78 (score 1, farm-blacksmithing-1904)
- manual rows tied at top score: 110 of 110; old/off-topic manual rows in the visible 8: 7; loose substring hits in visible rows: 3; Library first row position: None; right-answer rows hidden past the cap of 8: 52

### bleeding
- hits per group: What to do now 1, Manuals 222, Plants 1
- 1. [What to do now] Someone is hurt (score 2, scenario:hurt)
- 2. [Manuals] Building Toilets, page 9 (score 1, community-guide-ch07-toilets)
- 3. [Manuals] Building Toilets, page 32 (score 1, community-guide-ch07-toilets)
- manual rows tied at top score: 222 of 222; old/off-topic manual rows in the visible 8: 0; loose substring hits in visible rows: 0; Library first row position: None; right-answer rows hidden past the cap of 8: 68

### tourniquet
- hits per group: What to do now 1, Manuals 7
- 1. [What to do now] Someone is hurt (score 2, scenario:hurt)
- 2. [Manuals] All Hazard Sheets (full set), page 3 (score 1, ready-all-hazards)
- 3. [Manuals] Where There Is No Doctor, page 129 (score 1, where-no-doctor-2025)
- manual rows tied at top score: 7 of 7; old/off-topic manual rows in the visible 8: 5; loose substring hits in visible rows: 0; Library first row position: None; right-answer rows hidden past the cap of 8: 0

### boil water
- hits per group: What to do now 1, Manuals 752, Library 1
- 1. [What to do now] Boil-water notice or no water (score 7, scenario:water)
- 2. [Manuals] Survive DURING, Power Outage Information Sheet · page 2 (score 1, ready-power-outage)
- 3. [Manuals] Texas Manual on Rainwater Harvesting, page 29 (score 1, texas-rainwater-manual)
- manual rows tied at top score: 752 of 752; old/off-topic manual rows in the visible 8: 6; loose substring hits in visible rows: 6; Library first row position: 10; right-answer rows hidden past the cap of 8: 4

### bleach water
- hits per group: What to do now 1, Manuals 40, Library 1
- 1. [What to do now] Boil-water notice or no water (score 3, scenario:water)
- 2. [Manuals] Texas Manual on Rainwater Harvesting, page 30 (score 1, texas-rainwater-manual)
- 3. [Manuals] Water and Sanitation: Keys to Staying Healthy, page 23 (score 1, where-no-doctor-2011-water-sanitation)
- manual rows tied at top score: 40 of 40; old/off-topic manual rows in the visible 8: 2; loose substring hits in visible rows: 0; Library first row position: 10; right-answer rows hidden past the cap of 8: 15

### how much bleach per gallon
- hits per group: none
- manual rows tied at top score: 0 of 0; old/off-topic manual rows in the visible 8: 0; loose substring hits in visible rows: 0; Library first row position: None; right-answer rows hidden past the cap of 8: 0

### frozen pipes
- hits per group: Manuals 2
- 1. [Manuals] Home Canning 1: Principles of home canning, page 26 (score 1, usda-canning-1-principles)
- 2. [Manuals] USDA Complete Guide to Home Canning, page 38 (score 1, usda-canning-complete-2015)
- manual rows tied at top score: 2 of 2; old/off-topic manual rows in the visible 8: 0; loose substring hits in visible rows: 0; Library first row position: None; right-answer rows hidden past the cap of 8: 0

### fridge food safe
- hits per group: What to do now 1
- 1. [What to do now] Power out (score 2, scenario:power)
- manual rows tied at top score: 0 of 0; old/off-topic manual rows in the visible 8: 0; loose substring hits in visible rows: 0; Library first row position: None; right-answer rows hidden past the cap of 8: 0

### heat stroke
- hits per group: What to do now 1, Manuals 17
- 1. [What to do now] Extreme heat (score 3, scenario:heat)
- 2. [Manuals] Filtration of River Waters, page 84 (score 1, filtration-river-waters-1869)
- 3. [Manuals] All Hazard Sheets (full set), page 10 (score 1, ready-all-hazards)
- manual rows tied at top score: 17 of 17; old/off-topic manual rows in the visible 8: 6; loose substring hits in visible rows: 0; Library first row position: None; right-answer rows hidden past the cap of 8: 4

### diarrhea kid
- hits per group: Manuals 12
- 1. [Manuals] Health Problems from Unsafe Water, page 3 (score 1, community-guide-ch05-unsafe-water)
- 2. [Manuals] Where Women Have No Doctor, page 367 (score 1, where-women-no-doctor-2024)
- 3. [Manuals] Where Women Have No Doctor, page 502 (score 1, where-women-no-doctor-2024)
- manual rows tied at top score: 12 of 12; old/off-topic manual rows in the visible 8: 0; loose substring hits in visible rows: 8; Library first row position: None; right-answer rows hidden past the cap of 8: 2

### oral rehydration
- hits per group: Manuals 3
- 1. [Manuals] Where There Is No Doctor, page 23 (score 1, where-no-doctor-2025)
- 2. [Manuals] Where There Is No Doctor, page 44 (score 1, where-no-doctor-2025)
- 3. [Manuals] Where There Is No Doctor, page 430 (score 1, where-no-doctor-2025)
- manual rows tied at top score: 3 of 3; old/off-topic manual rows in the visible 8: 0; loose substring hits in visible rows: 0; Library first row position: None; right-answer rows hidden past the cap of 8: 0

### tornado
- hits per group: What to do now 1, Manuals 9, Library 1
- 1. [What to do now] Tornado warning (score 6, scenario:tornado)
- 2. [Manuals] All Hazard Sheets (full set), page 14 (score 1, ready-all-hazards)
- 3. [Manuals] All Hazard Sheets (full set), page 24 (score 1, ready-all-hazards)
- manual rows tied at top score: 9 of 9; old/off-topic manual rows in the visible 8: 0; loose substring hits in visible rows: 0; Library first row position: 10; right-answer rows hidden past the cap of 8: 0

### co
- hits per group: What to do now 7, Manuals 5026, Library 11, Your plan 1, Plants 914
- 1. [What to do now] Tornado warning (score 2, scenario:tornado)
- 2. [What to do now] Extreme heat (score 2, scenario:heat)
- 3. [What to do now] Hard freeze (score 2, scenario:freeze)
- manual rows tied at top score: 5026 of 5026; old/off-topic manual rows in the visible 8: 0; loose substring hits in visible rows: 32; Library first row position: 16; right-answer rows hidden past the cap of 8: 4

### water storage
- hits per group: Manuals 118, Library 1
- 1. [Manuals] Texas Manual on Rainwater Harvesting, page 2 (score 1, texas-rainwater-manual)
- 2. [Manuals] Texas Manual on Rainwater Harvesting, page 7 (score 1, texas-rainwater-manual)
- 3. [Manuals] Texas Manual on Rainwater Harvesting, page 8 (score 1, texas-rainwater-manual)
- manual rows tied at top score: 118 of 118; old/off-topic manual rows in the visible 8: 0; loose substring hits in visible rows: 1; Library first row position: 9; right-answer rows hidden past the cap of 8: 0

### first aid kit
- hits per group: Manuals 9
- 1. [Manuals] Emergency Supply Checklist, page 1 (score 1, ready-supply-checklist)
- 2. [Manuals] Emergency Supply Checklist, page 2 (score 1, ready-supply-checklist)
- 3. [Manuals] Dehydrating Foods, page 71 (score 1, dehydrating-foods-1920)
- manual rows tied at top score: 9 of 9; old/off-topic manual rows in the visible 8: 2; loose substring hits in visible rows: 2; Library first row position: None; right-answer rows hidden past the cap of 8: 0

### canning tomatoes
- hits per group: Manuals 79, Library 1
- 1. [Manuals] Complete Guide to Home Canning: Intro, page 4 (score 1, usda-canning-intro)
- 2. [Manuals] Home Canning 1: Principles of home canning, page 6 (score 1, usda-canning-1-principles)
- 3. [Manuals] Home Canning 1: Principles of home canning, page 13 (score 1, usda-canning-1-principles)
- manual rows tied at top score: 79 of 79; old/off-topic manual rows in the visible 8: 0; loose substring hits in visible rows: 0; Library first row position: 9; right-answer rows hidden past the cap of 8: 27

### radio
- hits per group: What to do now 1, Manuals 36, Library 1
- 1. [What to do now] Radiation or chemical release (score 2, scenario:radiation)
- 2. [Manuals] All Hazard Sheets (full set), page 15 (score 1, ready-all-hazards)
- 3. [Manuals] All Hazard Sheets (full set), page 17 (score 1, ready-all-hazards)
- manual rows tied at top score: 36 of 36; old/off-topic manual rows in the visible 8: 0; loose substring hits in visible rows: 1; Library first row position: 10; right-answer rows hidden past the cap of 8: 2

### snake bite
- hits per group: Manuals 23
- 1. [Manuals] American Blacksmithing and Toolsmithing, page 184 (score 1, american-blacksmithing-1911)
- 2. [Manuals] Where There Is No Doctor, page 7 (score 1, where-no-doctor-2025)
- 3. [Manuals] Where There Is No Doctor, page 51 (score 1, where-no-doctor-2025)
- manual rows tied at top score: 23 of 23; old/off-topic manual rows in the visible 8: 1; loose substring hits in visible rows: 4; Library first row position: None; right-answer rows hidden past the cap of 8: 14

### cpr
- hits per group: What to do now 1, Manuals 1
- 1. [What to do now] Someone is hurt (score 2, scenario:hurt)
- 2. [Manuals] Community Guide to Environmental Health: water and sanitation, page 581 (score 1, community-guide-env-health-2012)
- manual rows tied at top score: 1 of 1; old/off-topic manual rows in the visible 8: 0; loose substring hits in visible rows: 1; Library first row position: None; right-answer rows hidden past the cap of 8: 0

### purify water
- hits per group: Manuals 14
- 1. [Manuals] Filtration of River Waters, page 165 (score 1, filtration-river-waters-1869)
- 2. [Manuals] Filtration of River Waters, page 169 (score 1, filtration-river-waters-1869)
- 3. [Manuals] Where Women Have No Doctor, page 167 (score 1, where-women-no-doctor-2024)
- manual rows tied at top score: 14 of 14; old/off-topic manual rows in the visible 8: 2; loose substring hits in visible rows: 0; Library first row position: None; right-answer rows hidden past the cap of 8: 0

## Five biggest weaknesses

1. **No real ranking inside Manuals.** 5,359 of 5,370 index sections (99.8%) have heading "Page N", so the title boost never fires. In 22 of 24 queries with manual hits, every manual hit ties at score 1, so the order is just file order in search-index.json. Filtration of River Waters (1869) is doc 3 of 44; Where There Is No Doctor is doc 41. Result: 41 old or off-topic rows in the visible 8 across 11 queries, and one in the top 3 for 7 queries.
2. **Group order beats score, and the app's own guides are barely searchable.** Library rows score 5 to 6 but always sit below up to 8 score-1 manual rows (Library first row at position 9 to 16 in 10 queries). The six Off-Grid guides (MARCH, purify, radio, water, power, food) are not in search-index.json at all, only their title and one-line "why".
3. **Every word must match, no stop words.** 2 of 28 queries return nothing ("generater", "how much bleach per gallon"). "no power" drops the Power out scenario because it lacks the word "no".
4. **Substring matching makes false hits.** 7 queries: "co" 5,968 hits (cover, cold, could), "kid" matches kidneys (12 of 12 hits), "burn" matches Laburnum, "kit" matches kitchen, "cpr" matches CCPR, "wound" matches woundwort, "no" matches not/now/know.
5. **No typo, stem or synonym help.** 9 queries hurt. Words the corpus never uses: blackout 0, fridge 0, cpr 0, heatstroke 0, diarrhoea 0. Stems: frozen vs freeze, storage vs stored, snake bite vs snakebite, purify vs disinfect.

Also: three omnibus docs duplicate eleven single docs (All Hazard Sheets, USDA Complete Guide, Community Guide full book), so "tornado" shows 4 All Hazards pages before the Tornado sheet.

## Synonym / alias list (query term -> also search)

| typed | expand to |
|---|---|
| generater, genarator, generatr | generator |
| co (whole word only) | carbon monoxide |
| blackout, power failure, no power, power cut | power outage, outage |
| fridge | refrigerator |
| freezer food | freezer, refrigerator |
| frozen, freezing | freeze |
| burst pipe | pipes, freeze |
| burn (whole word) | burns, scald |
| kid, kids, toddler | child, children |
| infant, newborn | baby |
| diarrhoea, runs | diarrhea |
| ors, electrolyte | rehydration drink, oral rehydration |
| dehydrated (person) | dehydration |
| cpr | rescue breathing |
| snake bite | snakebite |
| heatstroke, sunstroke | heat stroke |
| heat exhaustion | heat stroke, extreme heat |
| purify, clean water, treat water | disinfect, bleach, boil, chlorine |
| bleach | chlorine |
| water storage, store water | stored water, storage |
| first aid kit, med kit | medicine kit, supply checklist |
| tourniquet, bleed | bleeding, MARCH |
| hemorrhage | bleeding |
| cut, laceration | wound |
| broken bone, broke arm | fracture, splint |
| twister | tornado |
| weather radio, ham, gmrs | radio, NOAA |
| torch | flashlight |
| hypothermia | cold, winter storm |
| frostbite | winter storm |
| bug out, leave home | evacuate, go bag |
| go bag, bug out bag | emergency supply kit |
| gal | gallon |
| tap water | faucet, boil water |
| boil notice | boil water |
| heart attack | chest pain |
| anaphylaxis, allergy | allergic |
| canning tomatoes | tomatoes (Home Canning 3) |

## Down-weight as historical / background

| doc | why |
|---|---|
| filtration-river-waters-1869 | 1869 engineering report; top-3 in burn, battery, heat stroke, purify water |
| practical-blacksmithing-vol3-1889, american-blacksmithing-1911, farm-blacksmithing-1904 | off-topic; won snake bite, wound |
| farm-machinery-motors-1908, farm-motors-windmills-1917 | off-topic engine text ("stroke", "battery") |
| soap-manufacture-handbook-1908, soap-makers-handbook-1912 | off-topic, matches "bleach", "burn" |
| canning-preserving-1887, food-conservation-canning-1917, home-farm-food-preservation-1918 | flagged old_safety_rules; must never outrank USDA 2015 canning |
| dehydrating-foods-1920 | "dehydration" means food drying here, not a sick person |
| well-digging-pump-work-1860, potable-water-1906 | old water engineering (Library only) |
| fm-21-76-survival-1957 | light down-weight: useful but dated medical advice |
| ready-all-hazards, usda-canning-complete-2015, community-guide-env-health-2012 | not old, but duplicates: collapse with the single-chapter docs |
