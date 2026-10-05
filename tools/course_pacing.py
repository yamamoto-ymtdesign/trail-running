"""Course stats and aid-station targets from the official GPX.

Usage: python3 tools/course_pacing.py [target_minutes] [fade]
  target_minutes: finish time in minutes (default 500 = 8:20)
  fade: how much slower each km-effort gets from start to finish (default 0.15)
"""
import math
import re
import sys
from pathlib import Path

GPX = Path(__file__).resolve().parent.parent / "docs/course/wat2027_long.gpx"
OFFICIAL_KM = 49.8
AIDS = [("A1", 14, "11:00"), ("A2", 26, "13:00"), ("A3", 36, "14:30"), ("A4", 44, "16:00"), ("ゴール", 49.8, "18:00")]
START_MIN = 6 * 60
NOISE_M = 3  # ignore elevation wiggles smaller than this


def load():
    pts = [(float(a), float(b), float(e)) for a, b, e in
           re.findall(r'<trkpt lat="([\d.]+)" lon="([\d.]+)"><ele>([-\d.]+)</ele>', GPX.read_text())]
    dist = [0.0]
    for (la1, lo1, _), (la2, lo2, _) in zip(pts, pts[1:]):
        p1, p2, dl = map(math.radians, (la1, la2, lo2 - lo1))
        h = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
        dist.append(dist[-1] + 2 * 6371000 * math.asin(math.sqrt(h)))
    scale = OFFICIAL_KM / (dist[-1] / 1000)
    km = [d / 1000 * scale for d in dist]
    base, ele = pts[0][2], []
    for _, _, e in pts:
        if abs(e - base) >= NOISE_M:
            base = e
        ele.append(base)
    return km, ele


def segments(km, ele):
    out, start = [], 0.0
    for name, end, cutoff in AIDS:
        idx = [i for i, k in enumerate(km) if start <= k <= end]
        up = sum(max(0, ele[i] - ele[i - 1]) for i in idx[1:])
        down = sum(max(0, ele[i - 1] - ele[i]) for i in idx[1:])
        out.append(dict(name=name, km=end, dist=end - start, up=up, down=down, ke=end - start + up / 100, cutoff=cutoff))
        start = end
    return out


def hm(m):
    m = round(m)
    return f"{m // 60}:{m % 60:02d}"


def main():
    target = float(sys.argv[1]) if len(sys.argv) > 1 else 500
    fade = float(sys.argv[2]) if len(sys.argv) > 2 else 0.15
    segs = segments(*load())
    total_ke = sum(s["ke"] for s in segs)
    acc, weights = 0.0, []
    for s in segs:
        weights.append(s["ke"] * (1 + fade * (acc + s["ke"] / 2) / total_ke))
        acc += s["ke"]
    cum = 0.0
    print(f"target {hm(target)}  fade {fade:.0%}  total km-effort {total_ke:.1f}")
    for s, w in zip(segs, weights):
        seg = w / sum(weights) * target
        cum += seg
        h, m = map(int, s["cutoff"].split(":"))
        print(f'{s["name"]:4} {s["km"]:5.1f}km  +{s["up"]:4.0f}/-{s["down"]:4.0f}m  '
              f'{hm(cum)} ({hm(START_MIN + cum)})  cutoff {s["cutoff"]}  margin {hm(h * 60 + m - START_MIN - cum)}  '
              f'{seg / s["ke"]:.1f} min/km-effort')


if __name__ == "__main__":
    main()
