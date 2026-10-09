# Europe — clue sheet

Tables: `--country EU` (distinguishing sign on the blue band), `DE`, `FR`, `GB`, `IT`. Russia has its own sheet (`russia.md`).
Items marked *(verify)* are field knowledge: use them to rank, never to exclude.

## Plates — what each country prints

| Country | Where the place is on the plate | Command | Strength |
|---|---|---|---|
| any EU/EEA | letters on the blue band (D, F, I, E, NL, PL, CZ, A, B…), or an oval sticker | `clues.py lookup plate D --country EU` | country of registration |
| Germany | 1–3 letters before the gap/hyphen (B, M, HH, K, F, S…) = district | `clues.py lookup plate "M-AB 1234" --country DE` | strong: plates follow the owner's address, re-registered on moving (keeping the old one is allowed since 2015) |
| France | number on the right band (75, 13, 69, 2A…) = department | `clues.py lookup plate "AB-123-CD 75" --country FR` | weak: the owner chooses the department, usually but not always home |
| UK | first two letters (memory tag) = DVLA office region | `clues.py lookup plate "LA21 ABC" --country GB` | weak: the dealer's office, not where the car lives |
| Italy | province code on the right band (optional since 1999), ROMA for Rome | `clues.py lookup plate "AB 123 CD MI" --country IT` | medium, when present |
| Spain, Netherlands, Belgium, Portugal | no regional code on current plates | — | country only |
| Austria, Switzerland, Poland, Czechia | regional prefixes exist (not yet tabled) | — | — |

German plates without a visible gap (`HHAB123`) are ambiguous: the lookup lists every prefix that is a real district code.

## Phones

| Country | Command | Gives |
|---|---|---|
| France | `clues.py lookup area-code "+33 1 …"` | zone 01–05 (Paris / NW / NE / SE / SW); 06/07 mobile |
| Germany, UK, Italy | not tabled yet | use the calling code table for the country |

## Region signals *(verify)*

| Seen in photo | Points to |
|---|---|
| Yellow rear plate, white front | UK (and Netherlands has yellow plates) |
| Bollards: white post with red reflector (DE/AT/NL), white with black band (FR), black-and-white (IT has varied) | country — compare against a reference photo, do not rely on memory |
| Driving on the left | UK, Ireland, Malta, Cyprus |
| Bilingual signs | Belgium (NL/FR), Switzerland (DE/FR/IT), Wales (cy/en), Basque Country, Catalonia, South Tyrol |
| Street name plates with arrondissement number | Paris |

## Search tips

- Search in the local language. Google Lens is strongest for European street scenes; Yandex for Eastern Europe.
- `poi.py "<name>" --city <city> --country <cc>` uses Photon + Nominatim.
- Mapillary has good rural coverage where Google Street View is thin (Germany outside cities); it needs a free token.
