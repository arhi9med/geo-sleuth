# UAE — clue sheet

Use with `clues.py lookup <kind> <value> --country AE` and `board.py apply ... --country AE`.
Everything marked *(verify)* is field knowledge, not table data: use it to generate candidates or down-weight, never to exclude.

## Read first (strongest, readable clues)

| Clue | What it gives | Command |
|---|---|---|
| Plate with emirate name (DUBAI / دبي, ABU DHABI / A.D., SHARJAH, AJMAN, UAQ, RAK, FUJAIRAH) | emirate | `clues.py lookup plate "DUBAI A 12345" --country AE` |
| Plate code only (letter or number) | 1–3 emirates (codes overlap) | same; number code 1, 4–22, 50 → Abu Dhabi; 1–4 or none → Sharjah |
| Landline 02 / 03 / 04 / 06 / 07 / 08 / 09 | emirate (06 = Sharjah, Ajman or UAQ; 03 = Al Ain; 08 = Al Dhafra) | `clues.py lookup area-code "+971 4 ..."` |
| Mobile 050–058, 800, 600, 200 | country only | — |
| Dubai 3-digit community number in an address (e.g. 373) | Dubai community | `clues.py lookup admin 373 --country AE` |
| Dubai community name | community + sector | `clues.py lookup admin "Al Barsha" --country AE` |
| Hotel, tower, mall, residence name | coordinates | `poi.py "<name>" --city Dubai --country ae` |

A plate tells you where the car is registered, not where it is. Dubai plates are everywhere in the northern emirates; rental cars and company fleets travel. Use plates as support (`--lr` lower than default when only one car is visible), not as proof.

## Emirate-specific infrastructure *(verify)*

| Seen in photo | Points to |
|---|---|
| Dubai Metro (elevated, Red/Green lines), Dubai Tram (Al Sufouh, Marina, JBR) | Dubai |
| Salik toll gate gantries | Dubai |
| Darb toll gates | Abu Dhabi |
| RTA logo on signs, buses, taxis, bus shelters | Dubai |
| DEWA (electricity/water) | Dubai; ADDC/AADC/TAQA → Abu Dhabi; SEWA → Sharjah; Etihad WE (ex-FEWA) → northern emirates |
| Makani number plate on a building (10 digits) | Dubai; convert on makani.ae |
| Onwani address plate | Abu Dhabi |
| Taxi with cream body and coloured roof (RTA / Dubai Taxi; pink roof = ladies and families) | Dubai |
| Silver taxi with yellow roof sign | Abu Dhabi |
| Al Ain: oasis palm groves, Jebel Hafeet ridge to the south | Al Ain (Abu Dhabi) |
| Hajar mountains close behind the town, east coast sea | Fujairah, Khor Fakkan (Sharjah exclave), Dibba |

Sharjah has exclaves on the east coast (Khor Fakkan, Kalba, Dibba Al Hisn); Ajman has inland exclaves (Masfout, Manama). Do not assume an emirate is one contiguous area.

## Geometry that works well here

- **Skyline anchors**: Burj Khalifa, Burj Al Arab, Ain Dubai, Museum of the Future, Etihad Towers, Aldar HQ. Once one is identified, bearings from it (`geo.py bearings`) pin the camera quickly.
- **Sun**: low latitude (24–26° N); midday sun is near overhead in summer, so shadow length gives time of day well and azimuth less so. `sun.py` handles it.
- **Street grid**: Dubai's older areas (Deira, Bur Dubai, Karama) are irregular; newer master communities (Marina, JLT, Downtown, Business Bay, Al Barsha) have distinctive OSM footprints that are fast to match from satellite.
- **Satellite age**: these areas change fast. Towers in the photo may not exist in older imagery (or vice versa) — a mismatch is a date clue, not an exclusion.

## Search tips

- Search Arabic and English names; transliterations vary (Al Barsha / Barsha, Umm Suqeim / Umm Suqaim, Jumeirah / Jumeira).
- Property portals (Bayut, Property Finder) and Google Maps photos cover almost every residential tower with exterior shots; Google Lens on the building often names it.
- Dubai Statistics Center community codes match the `admin` table and Dubai addresses.
