"""Merge a physician review export (from the web review app) into:
  1. db/missed_abortion.sqlite -> physician_review table (full audit trail, every verdict)
  2. data/coding_results/random_80_reviewed.json -> a copy of random_80.json with physician
     corrections applied where she marked something "incorrect" and gave a corrected value.

Run from repo root: python3 scripts/merge_physician_review.py data/physician_reviews/<file>.json
"""
import json
import os
import sqlite3
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(ROOT, "db", "missed_abortion.sqlite")
RESULTS_PATH = os.path.join(ROOT, "data", "coding_results", "random_80.json")
OUT_PATH = os.path.join(ROOT, "data", "coding_results", "random_80_reviewed.json")


def main(review_path):
    review = json.load(open(review_path, encoding="utf-8"))
    reviewer = review["reviewer_name"]
    exported_at = review["exported_at"]

    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM physician_review WHERE reviewer_name = ?", (reviewer,))

    for p1 in review["phase1"]:
        conn.execute(
            """INSERT INTO physician_review
               (episode_id, reviewer_name, review_stage, field_name, verdict, correction_value, comment, reviewed_at)
               VALUES (?,?,?,?,?,?,?,?)""",
            (
                p1["episode_id"], reviewer, "outcome_classification", None,
                p1.get("verdict"),
                json.dumps({"outcome": p1.get("corrected_outcome"), "exclusion_reason": p1.get("corrected_exclusion_reason")})
                if p1.get("corrected_outcome") else None,
                p1.get("note") or None, exported_at,
            ),
        )

    for p2 in review["phase2"]:
        for f in p2["fields"]:
            verdict = "incorrect" if f["flagged"] else ("correct" if f["confirmed"] else None)
            conn.execute(
                """INSERT INTO physician_review
                   (episode_id, reviewer_name, review_stage, field_name, verdict, correction_value, comment, reviewed_at)
                   VALUES (?,?,?,?,?,?,?,?)""",
                (
                    p2["episode_id"], reviewer, "field_extraction", f["field"],
                    verdict, f.get("correct_value"), f.get("note") or None, exported_at,
                ),
            )
    conn.commit()

    n = conn.execute("SELECT count(*) FROM physician_review WHERE reviewer_name = ?", (reviewer,)).fetchone()[0]
    print(f"inserted {n} review rows for {reviewer}")

    # --- build the corrected dataset ---
    episodes = json.load(open(RESULTS_PATH, encoding="utf-8"))
    by_id = {e["episode_id"]: e for e in episodes}

    applied = []
    for p1 in review["phase1"]:
        if p1.get("verdict") == "incorrect" and p1.get("corrected_outcome"):
            ep = by_id.get(p1["episode_id"])
            if not ep:
                continue
            old = ep["consensus"].get("outcome_category")
            ep["consensus"]["outcome_category"] = p1["corrected_outcome"]
            ep["consensus"]["exclusion_reason"] = p1.get("corrected_exclusion_reason")
            ep["consensus"]["notes"] = (ep["consensus"].get("notes") or "") + \
                f" [תוקן ע\"י {reviewer}: {old} -> {p1['corrected_outcome']}. {p1.get('note') or ''}]"
            applied.append((p1["episode_id"], "outcome_category", old, p1["corrected_outcome"]))

    for p2 in review["phase2"]:
        ep = by_id.get(p2["episode_id"])
        if not ep:
            continue
        for f in p2["fields"]:
            if f["flagged"] and f.get("correct_value") is not None:
                field = f["field"]
                old = ep["consensus"].get(field)
                raw = f["correct_value"]
                if raw == "true":
                    new_val = True
                elif raw == "false":
                    new_val = False
                elif raw == "null":
                    new_val = None
                else:
                    try:
                        new_val = float(raw) if "." in raw else int(raw)
                    except (ValueError, TypeError):
                        new_val = raw
                ep["consensus"][field] = new_val
                applied.append((p2["episode_id"], field, old, new_val))

    json.dump(episodes, open(OUT_PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"\napplied {len(applied)} corrections -> {OUT_PATH}")
    for eid, field, old, new in applied:
        print(f"  {eid}.{field}: {old!r} -> {new!r}")

    unreviewed_p1 = [p["episode_id"] for p in review["phase1"] if p.get("verdict") is None]
    all_p2_eligible = {e["episode_id"] for e in episodes if e["consensus"].get("outcome_category") in ("success", "failure")}
    reviewed_p2 = {p["episode_id"] for p in review["phase2"]}
    missing_p2 = sorted(all_p2_eligible - reviewed_p2)
    print(f"\nphase1 not reviewed (no verdict): {unreviewed_p1}")
    print(f"phase2-eligible but not reviewed: {missing_p2}")

    conn.close()


if __name__ == "__main__":
    main(sys.argv[1])
