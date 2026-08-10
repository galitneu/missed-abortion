import json

SRC = "/tmp/claude-0/-home-user-comfort-choice-helper/df71759e-1127-5ed0-ab07-ff2e70e7a1bc/scratchpad/coding_results_random80.json"
OUT = "/tmp/claude-0/-home-user-comfort-choice-helper/df71759e-1127-5ed0-ab07-ff2e70e7a1bc/scratchpad/coding_results_random80_v2.json"

FREE_TEXT_FIELDS = {"outcome_evidence_quote", "notes", "record_mixup_note"}

# Confirmed wrong-majority fixes from the disagreement-analysis agent (verified against source text).
MANUAL_FIXES = {
    "RNDEP022": {"G": 7},
    "RNDEP038": {"Ab_total": 1, "prev_D_C": 1},
}


def compare_key(v):
    return v.strip().lower() if isinstance(v, str) else v


def key(v):
    return json.dumps(compare_key(v), sort_keys=True, ensure_ascii=False)


def majority_merge(coders):
    all_fields = [f for f in coders[0].keys() if f != "coder"] if coders else []
    consensus = {}
    disagreements = []
    structured_fields = [f for f in all_fields if f not in FREE_TEXT_FIELDS]
    for field in structured_fields:
        raw_vals = [c.get(field) for c in coders]
        keys = [key(v) for v in raw_vals]
        counts = {}
        for k in keys:
            counts[k] = counts.get(k, 0) + 1
        winner_key, winner_count = None, 0
        for k, c in counts.items():
            if c > winner_count:
                winner_key, winner_count = k, c
        winner_value = raw_vals[keys.index(winner_key)] if winner_key is not None else None
        consensus[field] = winner_value if winner_count >= 2 else None
        if winner_count < 3:
            disagreements.append({"field": field, "coder_values": raw_vals})

    majority_coder = next((c for c in coders if key(c.get("outcome_category")) == key(consensus.get("outcome_category"))), coders[0])
    for field in FREE_TEXT_FIELDS:
        consensus[field] = majority_coder.get(field)

    return consensus, disagreements


data = json.load(open(SRC, encoding="utf-8"))

old_total = new_total = 0
newly_hidden_removed = {}

for ep in data:
    coders = ep["coders"]
    old_fields = {d["field"] for d in ep["disagreements"]}
    old_total += len(ep["disagreements"])

    consensus, disagreements = majority_merge(coders)

    if ep["episode_id"] in MANUAL_FIXES:
        for field, value in MANUAL_FIXES[ep["episode_id"]].items():
            consensus[field] = value
            existing_note = consensus.get("notes") or ""
            consensus["notes"] = existing_note + f" [תוקן ידנית: {field}={value} לפי בדיקת סוכן-ניתוח]"

    ep["consensus"] = consensus
    ep["disagreements"] = disagreements
    ep["n_disagreements"] = len(disagreements)
    new_total += len(disagreements)

    new_fields = {d["field"] for d in disagreements}
    removed = old_fields - new_fields
    for f in removed:
        newly_hidden_removed[f] = newly_hidden_removed.get(f, 0) + 1

json.dump(data, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

print(f"old total disagreement-entries: {old_total}")
print(f"new total disagreement-entries: {new_total}")
print("fields where disagreements were removed by the case/whitespace-insensitive fix:")
for f, c in sorted(newly_hidden_removed.items(), key=lambda x: -x[1]):
    print(f"  {f}: {c}")
print(f"manual fixes applied: {list(MANUAL_FIXES.keys())}")
print(f"saved: {OUT}")
