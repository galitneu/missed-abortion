import csv
import json
import os

ROOT = "/workspace/missed-abortion"
RESULTS = os.path.join(ROOT, "data", "coding_results", "random_80.json")
OUT = os.path.join(ROOT, "output", "random_80_manual_review.csv")

RAW_TEXT_DIRS = {
    "RND2EP": os.path.join(ROOT, "data", "raw_text", "random_40_batch2"),
    "RNDEP": os.path.join(ROOT, "data", "raw_text", "random_40_batch1"),
}


def text_dir_for(episode_id):
    for prefix, d in RAW_TEXT_DIRS.items():
        if episode_id.startswith(prefix):
            return d
    return None


FIELDS = ["G", "P", "NVD", "CS", "Ab_total", "prev_D_C", "IVF", "smoking", "Rh", "HGB", "PLT", "WBC",
          "hcg_value", "hcg_qualitative", "GA_LMP_weeks", "GA_US_weeks", "US_finding",
          "medical_treatment", "D_C_treatment", "elective_D_C", "emergency_D_C", "hysteroscopy",
          "FU1_gestational", "FU1_lining_over15mm", "FU1_bleeding", "FU1_pain",
          "FU2_gestational", "FU2_lining_over15mm", "FU2_bleeding", "FU2_pain",
          "delayed_decision_followup"]

OUTCOME_HE = {
    "open": "פתוח", "not_applicable": "לא רלוונטי", "success": "הצלחה",
    "failure": "כישלון", "not_missed_abortion": "הוחרג (לא הפלה נדחית)",
}

episodes = json.load(open(RESULTS, encoding="utf-8"))

header = [
    "episode_id", "admission_nos", "age", "entry_date", "discharge_date",
    "הכרעה_סוג_תוצאה", "הכרעה_סיבת_החרגה", "הכרעה_ציטוט_תומך",
    "קודד1_סוג_תוצאה", "קודד2_סוג_תוצאה", "קודד3_סוג_תוצאה", "הסכמה_מלאה_בסיווג",
    "חשד_לערבוב_רשומות", "הערת_ערבוב_רשומות", "הערת_קודד",
]
for f in FIELDS:
    header.append(f"{f}__הכרעה")
    header.append(f"{f}__קודד1_2_3")
header += ["מספר_אי_הסכמות", "שדות_עם_אי_הסכמה", "האם_נכון_(למילוי_ע\"י_רופא/ה)",
           "אם_לא_נכון__הערך_הנכון", "הערת_רופא/ה", "טקסט_קליני_מקורי_מלא"]

rows = []
for ep in episodes:
    coders = {c["coder"]: c for c in ep["coders"]}
    c1, c2, c3 = coders.get(1, {}), coders.get(2, {}), coders.get(3, {})
    consensus = ep["consensus"]
    disagree_fields = {d["field"] for d in ep["disagreements"]}

    outcome_vals = [c1.get("outcome_category"), c2.get("outcome_category"), c3.get("outcome_category")]
    unanimous = "כן" if len(set(outcome_vals)) == 1 else "לא"

    text_dir = text_dir_for(ep["episode_id"])
    full_text = ""
    if text_dir:
        p = os.path.join(text_dir, ep["episode_id"] + ".txt")
        if os.path.exists(p):
            full_text = open(p, encoding="utf-8").read()

    row = [
        ep["episode_id"], ", ".join(str(a) for a in ep["admission_nos"]), ep.get("age"),
        ep.get("entry_date"), ep.get("discharge_date"),
        OUTCOME_HE.get(consensus.get("outcome_category"), consensus.get("outcome_category")),
        consensus.get("exclusion_reason") or "",
        consensus.get("outcome_evidence_quote") or "",
        OUTCOME_HE.get(c1.get("outcome_category"), c1.get("outcome_category")),
        OUTCOME_HE.get(c2.get("outcome_category"), c2.get("outcome_category")),
        OUTCOME_HE.get(c3.get("outcome_category"), c3.get("outcome_category")),
        unanimous,
        "כן" if consensus.get("possible_record_mixup") else "לא",
        consensus.get("record_mixup_note") or "",
        consensus.get("notes") or "",
    ]
    for f in FIELDS:
        row.append(consensus.get(f))
        row.append(" / ".join(str(coders.get(i, {}).get(f)) for i in (1, 2, 3)))
    row += [len(ep["disagreements"]), ", ".join(sorted(disagree_fields)), "", "", "", full_text]
    rows.append(row)

with open(OUT, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(header)
    w.writerows(rows)

print(f"wrote {len(rows)} rows to {OUT}")
