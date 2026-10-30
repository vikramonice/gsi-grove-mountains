"""
amps_summary.py
===============
Plain-language MODEL GUIDANCE for each site of the GSI Grove Mountains traverse (Bharati to the
Grove Mountains), day by day, written by fixed rules from the AMPS point forecast (amps_meteogram.py).
AMPS only: it is the model tuned for Antarctica (Polar WRF, 8 km), and the product stays with it.

This is not a forecast. There is no forecaster in the loop: every sentence is a threshold
applied to AMPS numbers. Nothing is generated freely.

The rules follow the International Antarctic Weather Forecasting Handbook (Turner & Pendlebury,
eds., 2004, British Antarctic Survey): 7.8.1 The Larsemann Hills and Law Base, 7.8.2 Progress
Station, 7.8.3 Zhongshan Station (the coast at Bharati), 7.7.2 Prince Charles Mountains (the
inland side of the Lambert basin; the handbook has no section on the Grove Mountains), and
6.6.5-6.6.6 surface contrast and horizon. Site groups: coast = Bharati; slope = R1; inland =
R2, R3, Grove Area (nunataks: Grove Area).

  drift      drifting snow starts at about 10 m/s (20 kt); blowing snow at about 18 m/s (35 kt);
             earlier on recently fallen snow (here: 7 m/s / 14 kt when >= 0.5 mm fell in the
             previous 48 h). Thresholds apply to the AMPS mean wind; gusts are stronger.
  storm      coast and slope: easterly to north-easterly wind with falling pressure or snow = a
             depression or front over Prydz Bay, the gale and snowstorm pattern; gales can last a
             few days (Zhongshan; Law Base: E-NE winds strengthen after a front).
  katabatic  coast and slope: east to south-easterly wind at night and in the morning (18-06 UTC,
             23:30-11:30 IST), peaking around 02-07 UTC (07:30-12:30 IST), afternoons usually calm; gully-channelled katabatics reach
             17-25 m/s (33-48 kt) in stable conditions (Law Base, Zhongshan, Progress).
  northerly  coast: light northerly = moist maritime air over Prydz Bay; small lows just off the
             coast can drift onshore with moderate snow, and cloud damps the katabatic (Law Base).
  inland     the wind is the drainage flow (east to north-east on this side of the Lambert basin);
             weather systems change its speed more than its direction, and it strengthens with a
             tighter pressure gradient or a front approaching from the east. Near nunataks gusts are
             1.5-2 times the mean wind, with turbulence and rotors (Prince Charles Mountains).
  contrast   surface contrast and horizon are lost under deep, featureless low cloud: a saturated
             layer (RH over ice >= 95 %) based in the lowest 1.5 km and >= 1.5 km deep. Inland and
             on the slope even thin low cloud can cause white-out over the featureless ice (PCM),
             so any saturated low layer counts there. With snowfall or drift: whiteout.
  pressure   coast and slope only: pressure falling while temperature rises = depression arriving
             (Zhongshan); steep rise = clearing. Not used inland, where reduced sea-level pressure on
             the plateau is unreliable (PCM).
  snow       daily total (mm water ~ cm of snow); >= 0.5 mm flagged; >= 2 mm away from the coast:
             mark depots and the route.
Confidence from AMPS itself:
  run-to-run  the same day in the previous AMPS run (12 h older)
  lead time   forecast day 4 and later: "lower confidence"

Outputs (outputs/field/amps/):  <cycle>_<site>_summary.json  (and text on stdout)

Run (icepyx2 env), after amps_meteogram.py for the cycle:
    python amps_summary.py --cycle 2026101712 [--from "2026-10-18 09:00"]
The previous run is read from outputs/field/amps/<prev>_<site>.csv, or from the viewer manifest
(viewer_manifest.json embeds each run's CSV) in a fresh clone.
"""
import argparse
import csv
import datetime as dt
import io
import json

import numpy as np

from amps_meteogram import OUT, TZ_NAME, TZ_OFF

KN = 1.94384
CONST = dict(drift=10.0, drift_fresh=7.0, blow=18.0, fresh_mm=0.5, snow=0.5, snow_trace=0.2, snow_mark=2.0,
             rhi_cloud=95.0, thick=1500.0, pfall=4.0, prise=4.0, warm=5.0,
             same_wind=3.0)          # run-to-run: daily max wind within 3 m/s (6 kt) = consistent
DIR8 = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
COAST = {"bharati"}
SLOPE = {"r1"}
INLAND = {"r2", "r3", "grove_area"}
NUNATAK = {"grove_area"}
SITE_NOTE = {
    "coast": "At the coast, easterly winds prevail. Gales come with depressions over Prydz Bay and can last a few "
             "days; in summer an east to south-easterly katabatic often blows at night and in the morning, with "
             "calm afternoons (handbook, Larsemann Hills and Zhongshan).",
    "slope": "On the ice-sheet slope inland of the Larsemann Hills the wind is mainly the downslope (katabatic) "
             "flow from the east to south-east; depressions over Prydz Bay bring gales and snow here too "
             "(handbook, Zhongshan and Prince Charles Mountains).",
    "inland": "Inland the wind is mainly the downslope drainage flow, from the east to north-east on this side of "
              "the Lambert basin; weather systems change its speed more than its direction. Lows moving into the "
              "basin bring cloud and snow that can last several days (handbook, Prince Charles Mountains).",
    "nunatak": " Near the nunataks, gusts can be 1.5-2 times the mean wind, with turbulence and rotors.",
}


def kn(v):
    return int(round(v * KN))


def hours(times):
    """Merge a sorted list of datetimes (3-hourly, IST) into 'HH:MM-HH:MM IST' spans."""
    if not times:
        return ""
    spans, a, b = [], times[0], times[0]
    for t in times[1:]:
        if t - b <= dt.timedelta(hours=3):
            b = t
        else:
            spans.append((a, b)); a = b = t
    spans.append((a, b))
    # values are 3-h steps ending at 02:30, 05:30 ... 23:30 IST (the 00, 03 ... 21 UTC model steps)
    one = lambda t: "around %s %s" % (t.strftime("%H:%M"), TZ_NAME)
    two = lambda a, b: "%s-%s %s" % (a.strftime("%H:%M"), b.strftime("%H:%M"), TZ_NAME)
    return ", ".join(one(a) if a == b else two(a, b) for a, b in spans)


def parse(text):
    rows = list(csv.DictReader(io.StringIO(text)))
    # CSV times are UTC; the notes work in IST (days and hours as the team lives them)
    A = {"time": np.array([dt.datetime.strptime(r["time"], "%Y-%m-%d %H:%M") + TZ_OFF for r in rows])}
    for k in ("t2", "wchill", "wspd", "wdir", "mslp", "apcp", "rhi_low", "cld_depth"):
        A[k] = np.array([float(r.get(k) or "nan") for r in rows])
    return A


def previous(cycle, slug):
    """AMPS series of the run 12 h before `cycle`, or None."""
    prev = (dt.datetime.strptime(cycle, "%Y%m%d%H") - dt.timedelta(hours=12)).strftime("%Y%m%d%H")
    f = OUT / ("%s_%s.csv" % (prev, slug))
    if f.exists():
        return prev, parse(f.read_text())
    man = OUT / "viewer_manifest.json"
    if man.exists():
        for r in json.loads(man.read_text()):
            if r["cycle"] == prev:
                for s in r["sites"]:
                    if s["slug"] == slug and s.get("csv"):
                        return prev, parse(s["csv"])
    return prev, None


def dir8(deg):
    return DIR8[int(((deg % 360) + 22.5) // 45) % 8]


def prevailing(spd, d):
    ok = spd > 2
    if not ok.any():
        return "variable"
    u = np.sum(-spd[ok] * np.sin(np.radians(d[ok])))
    v = np.sum(-spd[ok] * np.cos(np.radians(d[ok])))
    return dir8(np.degrees(np.arctan2(-u, -v)))


def in_day(A, day):
    return (A["time"] > day) & (A["time"] <= day + dt.timedelta(days=1))   # 3-h values ending in the day


def change12(A, i, key):
    """Change of A[key] over the 12 h ending at index i (nan if not available)."""
    j = np.flatnonzero(A["time"] == A["time"][i] - dt.timedelta(hours=12))
    return A[key][i] - A[key][j[0]] if j.size else np.nan


def day_summary(day, A, P, prev_label, lead_day, slug):
    c = CONST
    ia = in_day(A, day)
    idx = np.flatnonzero(ia)
    ta = list(A["time"][ia])
    w, d, T, wc, pr, rh, dep = (A[k][ia] for k in ("wspd", "wdir", "t2", "wchill", "apcp", "rhi_low", "cld_depth"))
    items, flags = [], []

    # fresh snow in the previous 48 h lowers the drift threshold
    def fresh(i):
        t = A["time"][i]
        m = (A["time"] > t - dt.timedelta(hours=48)) & (A["time"] <= t)
        return np.nansum(A["apcp"][m]) >= c["fresh_mm"]
    thr = np.array([c["drift_fresh"] if fresh(i) else c["drift"] for i in idx])

    # --- wind and drift
    k = int(np.nanargmax(w))
    txt = "%s %d-%d kt (%.0f-%.0f m/s), strongest %s from %s." % (
        prevailing(w, d), kn(np.nanmin(w)), kn(np.nanmax(w)), np.nanmin(w), np.nanmax(w), hours([ta[k]]), dir8(d[k]))
    level = "ok"
    blow = [t for t, x in zip(ta, w) if x >= c["blow"]]
    drift = [t for t, x, h in zip(ta, w, thr) if h <= x < c["blow"]]
    if blow:
        txt += " Blowing snow likely %s: visibility poor to nil." % hours(blow)
        level = "warn"; flags.append("blowing snow")
    if drift:
        low = any(h < c["drift"] for x, h in zip(w, thr) if x >= h)
        txt += " Drifting snow likely %s%s." % (hours(drift), " (fresh snow drifts from about 14 kt)" if low else "")
        level = level if blow else "watch"; flags.append("drifting snow")
    items.append(dict(kind="Wind", text=txt, level=level))

    # --- weather pattern (handbook: Zhongshan, Law Base, Progress at the coast; Prince Charles Mountains inland)
    pf = np.nanmax([-change12(A, i, "mslp") for i in idx])
    if slug in COAST or slug in SLOPE:
        cyc = [t for t, x, y in zip(ta, w, d) if x >= 5 and 45 <= y < 135]
        storm = bool(cyc) and (pf >= 2 or np.nansum(pr) >= c["snow_trace"])
        if storm:
            items.append(dict(kind="Pattern", level="watch",
                              text="East to north-easterly wind %s with falling pressure or snow: a depression or front "
                                   "over Prydz Bay. This is the gale and snowstorm pattern here; gales can last a few "
                                   "days." % hours(cyc)))
        kat = [t for t, x, y in zip(ta, w, d) if x >= 5 and 67.5 <= y <= 157.5 and (t - TZ_OFF).hour in (21, 0, 3, 6)]
        if kat and not storm:
            items.append(dict(kind="Pattern", level="watch" if np.nanmax(w) >= c["drift_fresh"] else "ok",
                              text="East to south-easterly katabatic wind %s, usually with clear skies. It peaks in the "
                                   "morning (around 07:30-12:30 IST) and afternoons are usually calm; channelled katabatics "
                                   "can reach 33-48 kt." % hours(kat)))
        if slug in COAST and not storm and np.nanmax(w) < 10 and (w >= 3).any() and (d[k] >= 300 or d[k] <= 30):
            items.append(dict(kind="Pattern", level="ok",
                              text="Light northerly: moist maritime air over Prydz Bay. Small lows just off the coast can "
                                   "drift onshore with moderate snow, and cloud damps the morning katabatic."))
    else:
        strong = [t for t, x in zip(ta, w) if x >= c["drift"]]
        if strong:
            items.append(dict(kind="Pattern", level="watch",
                              text="Strong drainage wind %s. Inland it strengthens when a weather system tightens the "
                                   "pressure gradient or a front approaches from the east; its direction changes "
                                   "little." % hours(strong)))
        if slug in NUNATAK and np.nanmax(w) >= 13:
            items.append(dict(kind="Pattern", level="watch",
                              text="Near the nunataks gusts can be 1.5-2 times the mean wind, with turbulence and "
                                   "rotors."))

    # --- snow
    tot = float(np.nansum(pr))
    if tot < c["snow_trace"]:
        items.append(dict(kind="Snow", text="None expected.", level="ok"))
    else:
        when = hours([t for t, x in zip(ta, pr) if x >= 0.1])
        txt = "%.1f mm water (%s of fresh snow), %s." % (
            tot, "under 1 cm" if tot < 1 else "about %.0f cm" % tot, ("mainly " + when) if when else "spread thinly through the day")
        lev = "ok"
        if tot >= c["snow"]:
            lev = "watch"; flags.append("snow")
            txt += " Loose fresh snow drifts at lower wind speeds for the next two days."
            falling = pr >= 0.1
            if falling.any() and np.nanmax(w[falling]) < 5:
                txt += " It falls with light wind, so it lies loose."
        if tot >= c["snow_mark"] and slug not in COAST:
            txt += " Mark depots and the route."
        items.append(dict(kind="Snow", text=txt, level=lev))

    # --- cloud, surface contrast and whiteout
    lowc = rh >= c["rhi_cloud"]
    # inland and on the slope even thin low cloud can white out the featureless ice (handbook, PCM)
    thick = lowc if slug not in COAST else dep >= c["thick"]
    frac = float(np.mean(lowc)) if len(lowc) else 0
    txt = "Low cloud %s." % ("likely most of the day" if frac >= 0.6 else "at times" if frac >= 0.25 else "unlikely")
    lev = "ok"
    tk = [t for t, x in zip(ta, thick) if x]
    if tk:
        txt += (" Thick low cloud %s: poor surface contrast and horizon likely." if slug in COAST else
                " Low cloud %s: over the featureless ice even thin cloud can give poor surface definition.") % hours(tk)
        lev = "watch"; flags.append("poor contrast")
    wo = [t for t, a_, x, y, h in zip(ta, thick, pr, w, thr) if a_ and (x >= c["snow_trace"] or y >= h)]
    if wo:
        txt += " Whiteout risk %s (%s cloud with snowfall or drift)." % (hours(wo), "thick" if slug in COAST else "low")
        lev = "warn"; flags.append("whiteout risk")
    if frac >= 0.25 or tk:
        txt += " Cloud is the model's weakest field."
    items.append(dict(kind="Cloud", text=txt, level=lev))

    # --- temperature
    items.append(dict(kind="Temperature", level="ok",
                      text="%.0f to %.0f °C, wind chill down to %.0f °C." % (np.nanmin(T), np.nanmax(T), np.nanmin(wc))))

    # --- pressure: storm arrival (fall + warming) and clearing (steep rise)
    dp = np.array([change12(A, i, "mslp") for i in idx])
    dT = np.array([change12(A, i, "t2") for i in idx])
    if slug in INLAND:
        pass                                   # sea-level pressure on the plateau is unreliable (handbook, PCM)
    elif np.nanmin(dp) <= -c["pfall"]:
        i = int(np.nanargmin(dp))
        txt = "Falling fast: %.0f hPa in the 12 h to %s %s." % (-dp[i], ta[i].strftime("%H:%M"), TZ_NAME)
        if dT[i] >= c["warm"]:
            txt += " With %.0f °C of warming: the classic sign of a depression arriving. Expect wind to rise." % dT[i]
        else:
            txt += " A sign of worsening weather."
        items.append(dict(kind="Pressure", level="watch", text=txt))
        flags.append("pressure falling")
    elif np.nanmax(dp) >= c["prise"]:
        items.append(dict(kind="Pressure", level="ok",
                          text="Rising fast: %.0f hPa in 12 h. After a storm this usually means wind easing and "
                               "skies clearing." % np.nanmax(dp)))

    # --- run-to-run consistency (same day, previous AMPS run)
    if P is not None and in_day(P, day).sum() >= len(ta):
        ip = in_day(P, day)
        pw, pt = np.nanmax(P["wspd"][ip]), float(np.nansum(P["apcp"][ip]))
        same_w = abs(pw - np.nanmax(w)) <= c["same_wind"]
        same_s = (pt >= c["snow"]) == (tot >= c["snow"])
        txt = "Previous run (%s): strongest wind %d kt, snow %.1f mm. " % (prev_label, kn(pw), pt)
        if same_w and same_s:
            txt += "Consistent with this run."
        else:
            ch = []
            if not same_w:
                ch.append("wind %s" % ("stronger now" if np.nanmax(w) > pw else "weaker now"))
            if not same_s:
                ch.append("snow %s" % ("new in this run" if tot >= c["snow"] else "dropped in this run"))
            txt += "Changed: %s. Treat as uncertain." % ", ".join(ch)
        items.append(dict(kind="Last run", text=txt, level="ok" if same_w and same_s else "watch"))

    return dict(date=day.strftime("%Y-%m-%d"), label=day.strftime("%a %d %b"), items=items, flags=flags,
                note="lower confidence (forecast day %d)" % (lead_day + 1) if lead_day >= 3 else None)


def summarise(cycle, slug, start):
    A = parse((OUT / ("%s_%s.csv" % (cycle, slug))).read_text())
    prev, P = previous(cycle, slug)
    pl = (dt.datetime.strptime(prev, "%Y%m%d%H") + TZ_OFF).strftime("%d %b %H:%M " + TZ_NAME)
    c0 = dt.datetime.strptime(cycle, "%Y%m%d%H") + TZ_OFF
    start = start + TZ_OFF                          # `start` comes in UTC
    d = dt.datetime(start.year, start.month, start.day)
    days = []
    while d + dt.timedelta(hours=12) <= A["time"][-1]:
        days.append(day_summary(d, A, P, pl, (d - dt.datetime(c0.year, c0.month, c0.day)).days, slug))
        d += dt.timedelta(days=1)
    watch = ["%s: %s" % (x["label"][:3], ", ".join(x["flags"])) for x in days if x["flags"]]
    head = ("Watch: " + "; ".join(watch) + ".") if watch else "No hazards flagged by AMPS."
    note = (SITE_NOTE["coast"] if slug in COAST else SITE_NOTE["slope"] if slug in SLOPE else
            SITE_NOTE["inland"] + (SITE_NOTE["nunatak"] if slug in NUNATAK else "") if slug in INLAND else "")
    return dict(cycle=cycle, site=slug, made=start.strftime("%Y-%m-%d %H:%M"), headline=head, site_note=note,
                days=days,
                disclaimer="Written automatically from AMPS by handbook rules (Larsemann Hills, Zhongshan, Prince Charles Mountains). Mean wind only; gusts are stronger.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cycle")
    ap.add_argument("--from", dest="start", help="UTC 'YYYY-mm-dd HH:MM'; default now")
    a = ap.parse_args()
    cycle = a.cycle or sorted({p.name[:10] for p in OUT.glob("??????????_sites.json")})[-1]
    start = (dt.datetime.strptime(a.start, "%Y-%m-%d %H:%M") if a.start
             else dt.datetime.now(dt.timezone.utc).replace(tzinfo=None))
    start = max(start, dt.datetime.strptime(cycle, "%Y%m%d%H"))
    for s in json.loads((OUT / ("%s_sites.json" % cycle)).read_text()):
        S = summarise(cycle, s["slug"], start)
        (OUT / ("%s_%s_summary.json" % (cycle, s["slug"]))).write_text(json.dumps(S, indent=1, ensure_ascii=False),
                                                                      encoding="utf-8")
        print("\n=== %s  (AMPS %s)\n%s\n%s" % (s["name"], cycle, S["headline"], S["site_note"]))
        for dday in S["days"]:
            print("\n%s%s" % (dday["label"], "  [%s]" % dday["note"] if dday["note"] else ""))
            for it in dday["items"]:
                print("  %-11s %s%s" % (it["kind"], {"warn": "!! ", "watch": "! "}.get(it["level"], ""), it["text"]))


if __name__ == "__main__":
    main()
