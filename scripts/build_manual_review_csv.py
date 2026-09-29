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
    "טקסט_קליני_מקורי_מלא",
    "episode_id", "admission_nos", "age", "entry_date", "discharge_date",
    "רלוונטי_למחקר", "סיבת_אי_רלוונטיות",
    "עדיפות_בדיקה", "סיבת_עדיפות",
    "הכרעה_סוג_תוצאה", "הכרעה_סיבת_החרגה", "הכרעה_ציטוט_תומך",
    "קודד1_סוג_תוצאה", "קודד2_סוג_תוצאה", "קודד3_סוג_תוצאה", "הסכמה_מלאה_בסיווג",
    "חשד_לערבוב_רשומות", "הערת_ערבוב_רשומות", "הערת_קודד",
]
for f in FIELDS:
    header.append(f"{f}__הכרעה")
    header.append(f"{f}__קודד1_2_3")
header += ["מספר_אי_הסכמות", "שדות_עם_אי_הסכמה", "האם_נכון_(למילוי_ע\"י_רופא/ה)",
           "אם_לא_נכון__הערך_הנכון", "הערת_רופא/ה"]

# "Relevant to the study" = she actually attempted medical treatment first (success/failure/open),
# as opposed to choosing D&C from the outset (not_applicable) or turning out not to be a genuine
# missed-abortion case at all (not_missed_abortion / excluded).
NOT_RELEVANT_REASONS = {
    "not_applicable": "גרידה נבחרה מלכתחילה, ללא ניסיון טיפול תרופתי",
    "not_missed_abortion": "הוחרגה — לא מקרה של הפלה נדחית",
}

rows = []
for ep in episodes:
    coders = {c["coder"]: c for c in ep["coders"]}
    c1, c2, c3 = coders.get(1, {}), coders.get(2, {}), coders.get(3, {})
    consensus = ep["consensus"]
    disagree_fields = {d["field"] for d in ep["disagreements"]}
    outcome = consensus.get("outcome_category")

    outcome_vals = [c1.get("outcome_category"), c2.get("outcome_category"), c3.get("outcome_category")]
    unanimous = len(set(outcome_vals)) == 1
    mixup = bool(consensus.get("possible_record_mixup"))
    n_disagree = len(ep["disagreements"])

    relevant = outcome not in NOT_RELEVANT_REASONS
    not_relevant_reason = NOT_RELEVANT_REASONS.get(outcome, "")

    # Priority: flag cases most likely to need a human judgment call, so reviewers with limited
    # time can triage instead of reading all 80 top to bottom.
    priority_reasons = []
    if mixup:
        priority_reasons.append("חשד לערבוב רשומות")
    if not unanimous:
        priority_reasons.append("אי-הסכמה בסיווג הראשי בין הקודדים")
    if n_disagree >= 3:
        priority_reasons.append(f"{n_disagree} אי-הסכמות בשדות")
    if priority_reasons:
        priority = "גבוהה" if (mixup or not unanimous) else "בינונית"
    else:
        priority = "רגילה"

    text_dir = text_dir_for(ep["episode_id"])
    full_text = ""
    if text_dir:
        p = os.path.join(text_dir, ep["episode_id"] + ".txt")
        if os.path.exists(p):
            full_text = open(p, encoding="utf-8").read()

    row = [
        full_text,
        ep["episode_id"], ", ".join(str(a) for a in ep["admission_nos"]), ep.get("age"),
        ep.get("entry_date"), ep.get("discharge_date"),
        "כן" if relevant else "לא", not_relevant_reason,
        priority, "; ".join(priority_reasons),
        OUTCOME_HE.get(outcome, outcome),
        consensus.get("exclusion_reason") or "",
        consensus.get("outcome_evidence_quote") or "",
        OUTCOME_HE.get(c1.get("outcome_category"), c1.get("outcome_category")),
        OUTCOME_HE.get(c2.get("outcome_category"), c2.get("outcome_category")),
        OUTCOME_HE.get(c3.get("outcome_category"), c3.get("outcome_category")),
        "כן" if unanimous else "לא",
        "כן" if mixup else "לא",
        consensus.get("record_mixup_note") or "",
        consensus.get("notes") or "",
    ]
    for f in FIELDS:
        row.append(consensus.get(f))
        row.append(" / ".join(str(coders.get(i, {}).get(f)) for i in (1, 2, 3)))
    row += [n_disagree, ", ".join(sorted(disagree_fields)), "", "", ""]
    rows.append(row)

with open(OUT, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(header)
    w.writerows(rows)

print(f"wrote {len(rows)} rows to {OUT}")
