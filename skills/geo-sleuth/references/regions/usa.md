# United States — clue sheet

Use with `clues.py lookup <kind> <value> --country US` and `board.py apply ... --country US`.
Items marked *(verify)* are field knowledge: use them to rank, never to exclude.

## Read first

| Clue | What it gives | Command |
|---|---|---|
| State name or slogan on a plate ("Sunshine State", "Live Free or Die", "Land of Lincoln") | state | `clues.py lookup plate "LIVE FREE OR DIE" --country US` |
| Plate serial only (e.g. 7ABC123) | states that issue that format; often 1–12 | `clues.py lookup plate 7ABC123 --country US` |
| Phone number on a sign, truck or storefront | state + area (e.g. 212 = Manhattan) | `clues.py lookup area-code "(305) 555-0100"` (+1 auto-selects US) |
| Toll-free 800/833/844/855/866/877/888 | country only | — |
| Business, school, church, motel name | coordinates | `poi.py "<name>" --city <city> --country us` |

Plates: a car's state is where it is registered, not where it is; near state lines and in tourist areas expect mixed plates. Commercial vans and trucks carry the company phone, which often names the metro area — and businesses list their home market's area code, so a phone number is strong evidence for a local shop and weak for a national chain.
Phone numbers are portable: a mobile number keeps its area code after its owner moves. Landlines on old signage are the strongest.

## Region signals *(verify)*

| Seen in photo | Points to |
|---|---|
| Only a rear plate on parked cars | a rear-plate-only state (e.g. Florida, Georgia, Pennsylvania, Michigan, Arizona, the Carolinas); front plates are required in most of the Northeast, Midwest and West Coast |
| Interstate shield (red/white/blue) with number | even = east–west, odd = north–south; 3-digit = loop or spur of the 2-digit route |
| State route marker shape (spade in California, square in many states, state outline in others) | the state |
| Mile markers (small green posts) | count from the state line at the south or west end of the route |
| Speed in mph, yellow centre lines | US (Canada also has yellow centre lines but km/h; Liberia and UK use mph) |
| Bilingual French/English signs | not US: Quebec / New Brunswick |
| Red-roofed adobe, flat roofs, saguaro / Joshua trees | Southwest (AZ, NM, southern CA/NV) |
| Spanish moss, live oaks, raised houses on piers | Gulf coast / Deep South |
| Grain elevators, section-line grid roads every mile | Great Plains / Midwest |

## Geometry that works well here

- The Public Land Survey grid (1-mile sections) makes rural road layouts in most states west of Ohio easy to match on satellite imagery; road bearings close to N–S / E–W are normal there, not a clue.
- Strip-mall storefront sequences match well against Google Street View: `gsv.py` and `match.py`.
- County names appear on some plates (e.g. Florida, Tennessee, Indiana historically) — treat as a county candidate, then `board.py children <state>` for neighbours.
