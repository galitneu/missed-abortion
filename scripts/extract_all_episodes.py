import openpyxl
import pickle
import difflib
import os
from datetime import datetime, timedelta

SRC = "/tmp/data.xlsx"
START_DATE = datetime(2023, 12, 1)
OUT_DIR = "/tmp/claude-0/-home-user-comfort-choice-helper/df71759e-1127-5ed0-ab07-ff2e70e7a1bc/scratchpad"
CACHE_PATH = os.path.join(OUT_DIR, "all_episodes_cache.pkl")

wb = openpyxl.load_workbook(SRC, read_only=True)
ws = wb["מחלה נוכחית"]

rows = []
for i, r in enumerate(ws.iter_rows(min_row=2, values_only=True)):
    mr, adm, unit, unit_name, field, text, entry_date, update_date, age = r
    if not entry_date:
        continue
    rows.append(dict(
        row_index=i, medical_record=mr, admission_no=adm, unit_name=unit_name,
        text=text or "", entry_date=entry_date, age=age,
    ))

episodes = {}
for r in rows:
    episodes.setdefault(r["admission_no"], []).append(r)
for adm, rs in episodes.items():
    rs.sort(key=lambda x: x["entry_date"])

def first_dt(rs):
    return min(r["entry_date"] for r in rs)

OR_UNITS = {"חדר ניתוח", "חדר ניתוח אמבולטורי", "חדר ניתוח כללי"}

adm_list = list(episodes.keys())
by_day = {}
for adm, rs in episodes.items():
    d = first_dt(rs).date()
    by_day.setdefault(d, []).append(adm)

links = []
for adm in adm_list:
    rs = episodes[adm]
    units_here = set(r["unit_name"] for r in rs)
    if not (units_here & OR_UNITS):
        continue
    dt_a = first_dt(rs)
    candidates = set()
    for delta in range(-10, 11):
        d = dt_a.date() + timedelta(days=delta)
        candidates.update(by_day.get(d, []))
    for other in candidates:
        if other == adm:
            continue
        rs_b = episodes[other]
        best_ratio = 0.0
        for ra in rs:
            for rb in rs_b:
                ratio = difflib.SequenceMatcher(None, ra["text"], rb["text"]).ratio()
                best_ratio = max(best_ratio, ratio)
                if best_ratio >= 0.999:
                    break
            if best_ratio >= 0.999:
                break
        if best_ratio >= 0.6:
            links.append((adm, other, round(best_ratio, 3)))

confident_links = [(a, b, r) for a, b, r in links if r >= 0.85]
borderline_links = [(a, b, r) for a, b, r in links if 0.6 <= r < 0.85]

parent = {a: a for a in adm_list}
def find(x):
    while parent[x] != x:
        x = parent[x]
    return x
def union(x, y):
    rx, ry = find(x), find(y)
    if rx != ry:
        parent[rx] = ry
for a, b, r in confident_links:
    union(a, b)

groups = {}
for adm in adm_list:
    root = find(adm)
    groups.setdefault(root, []).append(adm)

all_episodes = []
for root, adms in groups.items():
    all_rows = []
    for a in adms:
        all_rows.extend(episodes[a])
    all_rows.sort(key=lambda x: x["entry_date"])
    start = min(r["entry_date"] for r in all_rows)
    end = max(r["entry_date"] for r in all_rows)
    ages = [r["age"] for r in all_rows if r["age"] is not None]
    ep_borderline = [l for l in borderline_links if l[0] in adms or l[1] in adms]
    all_episodes.append(dict(
        admission_nos=sorted(adms),
        linked=len(adms) > 1,
        link_confidence=[r for a, b, r in confident_links if a in adms and b in adms] or None,
        borderline_flags=ep_borderline or None,
        age=ages[0] if ages else None,
        start=start, end=end,
        rows=all_rows,
    ))

all_episodes.sort(key=lambda e: e["start"])
filtered = [e for e in all_episodes if e["start"] >= START_DATE]

with open(CACHE_PATH, "wb") as f:
    pickle.dump(filtered, f)

print(f"total distinct Admission_No in file: {len(adm_list)}")
print(f"confident cross-links found: {len(confident_links)}")
print(f"episodes at/after {START_DATE.date()}: {len(filtered)}")
print(f"cached to {CACHE_PATH}")
