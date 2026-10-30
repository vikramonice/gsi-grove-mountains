# How the field weather notes are written

The **field weather notes** on the [GSI Grove Mountains Meteograms page](https://vikramonice.github.io/gsi-grove-mountains/)
are the meteogram in words. They are written **automatically, by fixed rules**, from the numbers of
the AMPS weather model for each site. There is no forecaster in the loop and no free text: every
sentence is a template that appears only when a number crosses a threshold. This page lists every
rule, where it comes from, and its limits, so anyone can check what the notes mean.

Code: [`amps/amps_summary.py`](amps/amps_summary.py) (rules), [`amps/amps_meteogram.py`](amps/amps_meteogram.py)
(how the numbers are read from AMPS), [`amps/amps_verify.py`](amps/amps_verify.py) (check against
station reports).

## Source

**International Antarctic Weather Forecasting Handbook** (J. Turner and S. Pendlebury, eds.,
British Antarctic Survey, 2004):

- section 7.8.1 *The Larsemann Hills and Law Base* (Bharati is in the Larsemann Hills),
- section 7.8.2 *Progress Station and Druzhnaya-IV Base*,
- section 7.8.3 *Zhongshan Station*,
- section 7.7.2 *Prince Charles Mountains*: the inland side of the Lambert basin, used for the
  inland sites (the handbook has **no section on the Grove Mountains**; this is the nearest guidance),
- sections 6.6.5–6.6.6 *surface contrast and horizon*.

Grain of salt: the handbook describes the physics and typical behaviour; several exact cut-off
values below are our own practical choices. The table marks which is which.

## Site groups

| Group | Sites | Elevation (Bedmap3) | Rules from |
|---|---|---|---|
| Coast | Bharati | 83 m | Larsemann Hills, Zhongshan, Progress |
| Slope | R1 | 1480 m | Zhongshan (katabatic, storms) and Prince Charles Mountains |
| Inland | R2, R3, Grove Area | 2000–2580 m | Prince Charles Mountains; Grove Area also as a nunatak site |

## The numbers the rules use

AMPS (Antarctic Mesoscale Prediction System, NCAR; Polar WRF on an 8 km grid) runs at 00 and
12 UTC and forecasts 5 days ahead. For each site the page takes the **nearest 8 km grid point**,
every **3 hours**:

| Quantity | How it is obtained |
|---|---|
| Wind speed and direction | 10 m wind, rotated from the model grid to true north. **Mean wind only: AMPS publishes no gusts.** |
| Temperature | 2 m air temperature |
| Wind chill | Standard wind-chill formula (Environment Canada / US NWS) with the 10 m wind, when wind > 4.8 km/h |
| Snowfall | Precipitation in the 3 h step, mm of water |
| Pressure | Sea-level pressure (on the plateau reduced from 2–2.6 km: a rough guide only) |
| Low-cloud humidity | Highest relative humidity **over ice** in the lowest 1.5 km above the model ground (converted from the model's humidity over water with the Magnus formula, Alduchov & Eskridge 1996) |
| Thick low cloud | Depth of the saturated layer (humidity over ice ≥ 95 %) whose base is within 1.5 km of the ground |

A **day** is the eight 3-hourly values ending within that UTC day (03, 06, … 21, 24 UTC).

## The rules

| Topic | Rule (exactly as coded) | What appears in the notes | Basis |
|---|---|---|---|
| **Drifting snow** | Mean wind ≥ **10 m/s (20 kt)**; ≥ **7 m/s (14 kt)** if ≥ **0.5 mm** of snow fell in the previous 48 h | "Drifting snow likely HH–HH UTC" (+ "fresh snow drifts from about 14 kt") · amber | Handbook: drift from about 10 m/s, earlier on fresh snow. **7 m/s and 0.5 mm: our choice** |
| **Blowing snow** | Mean wind ≥ **18 m/s (35 kt)** | "Blowing snow likely …: visibility poor to nil" · red | Handbook: blowing snow from about 18 m/s |
| **Wind line** | Prevailing direction (vector mean of winds > 2 m/s), daily range, time and direction of the strongest wind | "E 19–29 kt (10–15 m/s), strongest around 03 UTC from E" | Description only |
| **Storm pattern** (coast, slope) | Wind ≥ 5 m/s from **45–135°** (north-east to south-east) **and** (pressure fell ≥ 2 hPa in 12 h **or** ≥ 0.2 mm of snow that day) | "East to north-easterly wind … a depression or front over Prydz Bay. This is the gale and snowstorm pattern here; gales can last a few days." · amber | Handbook (Zhongshan): pressure drop, temperature and humidity rise with a snowstorm as a low turns over Prydz Bay; gales last a few days. (Law Base): east to north-east winds strengthen after a front. **Thresholds: our choice** |
| **Katabatic wind** (coast, slope) | No storm pattern; wind ≥ 5 m/s from **67.5–157.5°** (east to south-east) in the steps ending **21, 00, 03 or 06 UTC** | "East to south-easterly katabatic wind …, usually with clear skies. It peaks in the morning (around 02–07 UTC) and afternoons are usually calm; channelled katabatics can reach 33–48 kt." · amber if the day's wind reaches 7 m/s | Handbook (Law Base): katabatic of 9–10 m/s peaking after about 02 UTC, onset 15–22 UTC, calm afternoons. (Zhongshan): katabatic gales 07–12 local time in summer, steady east-south-east wind under clear skies; gully-channelled katabatics 17–25 m/s. (Progress): easterly at night up to 10 m/s, dropping in the afternoon |
| **Northerly** (coast) | No storm pattern, day's wind < 10 m/s, strongest from 300–30° | "Light northerly: moist maritime air over Prydz Bay. Small lows just off the coast can drift onshore with moderate snow, and cloud damps the morning katabatic." | Handbook (Law Base): light northerly maritime flow; mesocyclones off the coast drift onshore with moderate snow; cloud damps the katabatic |
| **Strong drainage wind** (inland) | Wind ≥ 10 m/s | "Strong drainage wind … Inland it strengthens when a weather system tightens the pressure gradient or a front approaches from the east; its direction changes little." · amber | Handbook (Prince Charles Mountains): winds strengthen, keeping their direction, when the inland high intensifies, gradients increase or fronts approach from the east |
| **Nunatak gusts** (Grove Area) | Wind ≥ **13 m/s (25 kt)** | "Near the nunataks gusts can be 1.5–2 times the mean wind, with turbulence and rotors." · amber | Handbook (Prince Charles Mountains, Mount Kirkby): gusts 1.5–2 times the average wind, severe mechanical turbulence and rotors in strong winds. **13 m/s: our choice** |
| **Snow** | Daily total < 0.2 mm → "None expected"; otherwise amount and timing; ≥ **0.5 mm** → amber + "loose fresh snow drifts at lower wind speeds for the next two days"; snow falling with wind < 5 m/s → "lies loose"; ≥ **2 mm** away from the coast → "Mark depots and the route." | "1.2 mm water (about 1 cm of fresh snow) …" | 1 mm of water ≈ 1 cm of fresh snow (density about 100 kg/m³). **Levels: our choice** |
| **Low cloud** | Share of the day's steps with low-cloud humidity ≥ 95 %: ≥ 60 % "likely most of the day", ≥ 25 % "at times", else "unlikely" | "Low cloud likely most of the day." | **Our choice** (no cloud-cover output in AMPS GRIB) |
| **Poor contrast** (coast) | Thick low cloud: saturated layer ≥ **1.5 km** deep, based within 1.5 km of the ground | "Thick low cloud …: poor surface contrast and horizon likely" · amber | Handbook 6.6.5–6.6.6: contrast and horizon are lost under deep, featureless low cloud. (Larsemann Hills): white-out is rarely a problem over the rock of the hills, but serious over the continental ice. **95 %, 1.5 km: our choice** |
| **Poor contrast** (slope, inland) | **Any** saturated low layer (humidity over ice ≥ 95 % within 1.5 km of the ground) | "Low cloud …: over the featureless ice even thin cloud can give poor surface definition." · amber | Handbook (Prince Charles Mountains): even apparently thin stratocumulus can cause white-out over the featureless ice |
| **Whiteout risk** | Poor-contrast cloud (as above) **and** (snow ≥ 0.2 mm or drifting snow) in the same step | "Whiteout risk … (thick / low cloud with snowfall or drift)" · red | Handbook: whiteout = no contrast with falling or drifting snow |
| **Cloud caveat** | Added whenever low cloud is mentioned | "Cloud is the model's weakest field." | Known weakness of models in Antarctica |
| **Temperature** | Daily minimum and maximum, lowest wind chill | "−36 to −28 °C, wind chill down to −59 °C" | Description only |
| **Pressure falling** (coast, slope) | Fall ≥ **4 hPa in 12 h** | "Falling fast … A sign of worsening weather." · amber; with ≥ 5 °C of warming: "the classic sign of a depression arriving" | Handbook (Zhongshan): pressure drops while temperature and humidity rise as a low arrives. **4 hPa/12 h, 5 °C: our choice** |
| **Pressure rising** (coast, slope) | Rise ≥ **4 hPa in 12 h** | "Rising fast … wind easing and skies clearing." | Handbook: steep rise after a storm = clearing |
| **No pressure rule inland** | R2, R3, Grove Area | — | Sea-level pressure reduced from 2–2.6 km is unreliable; the handbook (Prince Charles Mountains) found pressure a poor guide there |
| **Last run** | Same day in the previous AMPS run (12 h older): strongest wind within 3 m/s and snow on the same side of 0.5 mm → "consistent"; otherwise "changed … treat as uncertain" | "Previous run (29 Oct 00 UTC): strongest wind 30 kt, snow 0.4 mm. Consistent with this run." | **Our choice**: a hazard in two runs in a row is more reliable |
| **Lead time** | Forecast day 4 and later | "lower confidence (forecast day 4)" | Model skill falls with lead time |

Each site also carries a short standing note from the handbook (coast, slope or inland).

## Check against real weather

Bharati sends no SYNOP. Every update compares what the page showed with the SYNOP reports of
**Zhongshan** (WMO 89573, 3 km east of Bharati, on the same 8 km grid point) and **Progress** (89574,
1 km from Zhongshan), from [Ogimet](https://www.ogimet.com). Each Zhongshan report is compared with
the AMPS Bharati value from the **newest run that was on the page at that time** (run start + 10 h
before the report), i.e. what the field team actually saw; once stored, a comparison is never changed.

- **Bias** = AMPS minus observed (temperature, wind speed); **mean absolute error** alongside.
- Shown for the last 7 days and the whole record (kept 120 days).
- Coast only: there is no station inland to check the R1–Grove Area charts against.

Read it as a correction: for example "AMPS about 3 °C too cold" means expect it warmer than shown.

## Limits

- The notes are only as good as AMPS, and AMPS is only as good as an 8 km model can be near the
  coast, on the ice-sheet slope and around nunataks.
- **Mean wind only.** Gusts are stronger than any wind given here.
- **Cloud is the model's weakest field;** contrast and whiteout are inferred from humidity, not
  observed cloud.
- Inland rules borrow from the Prince Charles Mountains section; the handbook has no Grove Mountains
  section.
- Cut-off values marked "our choice" are reasonable starting points, not tuned to this area.
- **What you see on site comes first.**

## Change log

- 2026-10-30: page set up from the MINIS Meteograms site; rules rewritten for the Bharati – Grove
  Mountains traverse from handbook sections 7.8.1–7.8.3 and 7.7.2.
