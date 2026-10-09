# Russia — clue sheet

Use with `clues.py lookup <kind> <value> --country RU` and `board.py apply ... --country RU`.
Items marked *(verify)* are field knowledge: use them to rank, never to exclude.

## Read first

| Clue | What it gives | Command |
|---|---|---|
| Region number on a plate (the small 2–3 digits on the right, next to RUS) | federal subject | `clues.py lookup plate "А123ВС 777" --country RU` (Cyrillic or Latin letters both work) |
| Landline code (495/499 Moscow, 812 St Petersburg, 843 Kazan…) | federal subject | `clues.py lookup area-code "+7 495 123-45-67"` (+7 auto-selects Russia) |
| Mobile 9xx, 800 | country only | — |
| Shop, ЖК, business-centre name | coordinates | `poi.py "<name>" --city <city> --country ru` (Photon + Nominatim; Yandex Maps in the browser is stronger for Russian POIs) |

A plate shows where the car was registered, and since 2020 owners keep their plates when they move: Moscow (77/97/99/177/197/199/777/797/799/977) and Moscow Oblast (50/90/150/190/750…) plates are everywhere in central Russia. Treat a plate as support unless several cars agree.
Some codes were reassigned (82: old Koryak plates under Kamchatka, now Crimea); the lookup returns both.
+7 6xx / 7xx numbers are Kazakhstan, not Russia.

## Region signals *(verify)*

| Seen in photo | Points to |
|---|---|
| Moscow Metro "M" in red, MCD/MCC signage, Moscow-style street name plates (white on blue with house number) | Moscow |
| St Petersburg: granite embankments, drawbridges, low uniform 19th-century facades | St Petersburg |
| Yandex Taxi yellow cars | big cities everywhere: weak |
| Panel blocks (khrushchyovka, series 1-464, P-44) | everywhere from Kaliningrad to Vladivostok: not a region clue |
| Signs in a second script (Tatar, Bashkir, Chuvash, Yakut…) | the corresponding republic |
| Dense birch/pine taiga vs steppe vs mountains | latitude band and region; combine with sun elevation |

## Search tips

- Search in Russian. Yandex reverse image search is the strongest engine for Russian content (it is already in `revimg.py --engines yandex`).
- Yandex Panoramas cover more Russian streets than Google Street View; open them in the browser and compare by hand.
- Long east–west extent: use `sun.py` with the photo time. Time zones run UTC+2 to UTC+12, so a timestamp plus sun position narrows the longitude band quickly.
