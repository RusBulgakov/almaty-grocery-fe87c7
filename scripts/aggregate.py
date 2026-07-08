"""Aggregate rep check-in files from inbox/ into data/state.json.
Each inbox/*.json is a snapshot from one rep for one district (schema checkin.v1).
Newest exported_at per district wins. Runs in GitHub Actions on push to inbox/**."""
import json, glob, os, datetime

TOTALS = {"district1": 331, "district2": 336, "district3": 318}
NAMES = {"district1": "Район 1 · Розыбакиева–Байзакова",
         "district2": "Район 2 · Байзакова–Желтоксан",
         "district3": "Район 3 · Желтоксан–восток"}

def main():
    best = {}  # district -> payload with max exported_at
    for path in sorted(glob.glob("inbox/*.json")):
        try:
            p = json.load(open(path, encoding="utf-8"))
        except Exception as e:
            print("skip", path, e); continue
        if p.get("schema") != "checkin.v1":
            continue
        dk = p.get("district")
        if dk not in TOTALS:
            continue
        if dk not in best or (p.get("exported_at", 0) > best[dk].get("exported_at", 0)):
            best[dk] = p

    districts = {}
    for dk, tot in TOTALS.items():
        p = best.get(dk)
        visited = p.get("visited", []) if p else []
        by_day = {}
        near = far = nogps = 0
        for v in visited:
            by_day[v.get("day")] = by_day.get(v.get("day"), 0) + 1
            d = v.get("dist")
            if d is None: nogps += 1
            elif d <= 150: near += 1
            elif d <= 600: near += 1
            else: far += 1
        districts[dk] = {
            "name": NAMES[dk], "total": tot,
            "done": len(visited),
            "rep": p.get("rep") if p else None,
            "exported_at": p.get("exported_at") if p else None,
            "by_day": by_day, "gps_far": far, "gps_none": nogps,
            "visited": visited,
        }
    state = {"updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "districts": districts}
    os.makedirs("data", exist_ok=True)
    json.dump(state, open("data/state.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("aggregated:", {k: f'{v["done"]}/{v["total"]}' for k, v in districts.items()})

if __name__ == "__main__":
    main()
