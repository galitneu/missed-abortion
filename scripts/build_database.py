"""Build/rebuild the SQLite database from the JSON coding-result files under data/.

Run from the repo root: python3 scripts/build_database.py
"""
import json
import os
import sqlite3

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(ROOT, "db", "missed_abortion.sqlite")

BATCHES = [
    ("chronological_40", os.path.join(ROOT, "data", "coding_results", "chronological_40.json"),
     os.path.join(ROOT, "data", "raw_text", "chronological_40")),
    ("random_80", os.path.join(ROOT, "data", "coding_results", "random_80.json"),
     None),  # mixed episode_id prefixes map to two raw_text dirs, resolved per-episode below
]

RAW_TEXT_DIRS = {
    "V2EP": os.path.join(ROOT, "data", "raw_text", "chronological_40"),
    "RND2EP": os.path.join(ROOT, "data", "raw_text", "random_40_batch2"),
    "RNDEP": os.path.join(ROOT, "data", "raw_text", "random_40_batch1"),
}


def raw_text_dir_for(episode_id):
    for prefix, d in RAW_TEXT_DIRS.items():
        if episode_id.startswith(prefix):
            return d
    return None


SCHEMA = """
CREATE TABLE IF NOT EXISTS episodes (
    episode_id TEXT PRIMARY KEY,
    batch TEXT,
    admission_nos TEXT,
    linked INTEGER,
    age INTEGER,
    entry_date TEXT,
    discharge_date TEXT,
    full_text TEXT,
    coder1_json TEXT,
    coder2_json TEXT,
    coder3_json TEXT,
    consensus_json TEXT,
    disagreements_json TEXT,
    n_disagreements INTEGER,
    outcome_category TEXT,
    exclusion_reason TEXT,
    possible_record_mixup INTEGER
);

CREATE TABLE IF NOT EXISTS physician_review (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    episode_id TEXT NOT NULL REFERENCES episodes(episode_id),
    reviewer_name TEXT,
    review_stage TEXT CHECK(review_stage IN ('outcome_classification', 'field_extraction')),
    field_name TEXT,
    verdict TEXT CHECK(verdict IN ('correct', 'incorrect', 'unsure')),
    correction_value TEXT,
    comment TEXT,
    reviewed_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_review_episode ON physician_review(episode_id);
CREATE INDEX IF NOT EXISTS idx_episodes_outcome ON episodes(outcome_category);
"""


def main():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)

    total = 0
    for batch_name, results_path, _ in BATCHES:
        if not os.path.exists(results_path):
            print(f"skip {batch_name}: {results_path} not found")
            continue
        episodes = json.load(open(results_path, encoding="utf-8"))
        for ep in episodes:
            coders = {c["coder"]: c for c in ep["coders"]}
            text_dir = raw_text_dir_for(ep["episode_id"])
            full_text = ""
            if text_dir:
                text_path = os.path.join(text_dir, ep["episode_id"] + ".txt")
                if os.path.exists(text_path):
                    full_text = open(text_path, encoding="utf-8").read()
            consensus = ep["consensus"]
            conn.execute(
                """INSERT OR REPLACE INTO episodes
                   (episode_id, batch, admission_nos, linked, age, entry_date, discharge_date,
                    full_text, coder1_json, coder2_json, coder3_json, consensus_json,
                    disagreements_json, n_disagreements, outcome_category, exclusion_reason,
                    possible_record_mixup)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    ep["episode_id"], batch_name, json.dumps(ep["admission_nos"]),
                    int(bool(ep.get("linked"))), ep.get("age"), ep.get("entry_date"), ep.get("discharge_date"),
                    full_text,
                    json.dumps(coders.get(1), ensure_ascii=False),
                    json.dumps(coders.get(2), ensure_ascii=False),
                    json.dumps(coders.get(3), ensure_ascii=False),
                    json.dumps(consensus, ensure_ascii=False),
                    json.dumps(ep["disagreements"], ensure_ascii=False),
                    ep["n_disagreements"],
                    consensus.get("outcome_category"),
                    consensus.get("exclusion_reason"),
                    int(bool(consensus.get("possible_record_mixup"))),
                ),
            )
            total += 1
    conn.commit()
    conn.close()
    print(f"built {DB_PATH} with {total} episodes")


if __name__ == "__main__":
    main()
