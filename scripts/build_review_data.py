import json, os

SCRATCH = "/tmp/claude-0/-home-user-comfort-choice-helper/df71759e-1127-5ed0-ab07-ff2e70e7a1bc/scratchpad"
RESULTS = os.path.join(SCRATCH, "coding_results_random80_v2.json")
OUT = os.path.join(SCRATCH, "review_app", "review_data.json")

FIELD_LABELS = {
    "G": "הריונות (G)", "P": "לידות (P)", "NVD": "לידות רגילות", "CS": "ניתוחים קיסריים",
    "Ab_total": "סה\"כ הפלות", "prev_D_C": "גרידות בעבר", "IVF": "IVF", "smoking": "עישון",
    "Rh": "סוג דם", "HGB": "המוגלובין", "PLT": "טסיות", "WBC": "לויקוציטים",
    "hcg_value": "BHCG כמותי", "hcg_qualitative": "BHCG איכותי",
    "GA_LMP_weeks": "שבוע הריון (LMP)", "GA_US_weeks": "שבוע הריון (סונר)",
    "US_finding": "ממצא סונר", "medical_treatment": "טיפול תרופתי", "D_C_treatment": "גרידה בוצעה",
    "elective_D_C": "גרידה מתוכננת", "emergency_D_C": "גרידה דחופה", "hysteroscopy": "היסטרוסקופיה",
    "FU1_gestational": "מעקב1: שק הריון", "FU1_lining_over15mm": "מעקב1: רירית>15מ\"מ",
    "FU1_bleeding": "מעקב1: דימום", "FU1_pain": "מעקב1: כאב",
    "FU2_gestational": "מעקב2: שק הריון", "FU2_lining_over15mm": "מעקב2: רירית>15מ\"מ",
    "FU2_bleeding": "מעקב2: דימום", "FU2_pain": "מעקב2: כאב",
    "delayed_decision_followup": "החלטה נדחית", "possible_record_mixup": "חשד לערבוב רשומות",
}

OUTCOME_HE = {
    "open": "פתוח (אין תיעוד המשך)", "not_applicable": "לא רלוונטי (גרידה מלכתחילה)",
    "success": "הצלחה (טיפול תרופתי הצליח)", "failure": "כישלון (טיפול תרופתי נכשל, גרידה)",
    "not_missed_abortion": "לא הפלה נדחית (הוחרג)",
}

EXCLUSION_HE = {
    "duplicate": "כפילות רשומה", "other_diagnosis": "אבחנה אחרת", "ectopic_pregnancy": "הריון חוץ רחמי",
    "twins": "הריון תאומים", "did_not_attend_followup": "לא הגיעה לביקורת",
    "did_not_receive_treatment": "לא קיבלה טיפול בפועל", "late_abortion_dc": "הפלה מאוחרת + גרידה",
    "operative_hysteroscopy": "היסטרוסקופיה ניתוחית", "curettage_removal": "הוצאת תוכן בקראוזה",
    "elective_termination": "הפסקת הריון יזומה", "other": "אחר",
}

BOOL_FIELDS = {
    "smoking", "medical_treatment", "D_C_treatment", "elective_D_C", "emergency_D_C", "hysteroscopy",
    "FU1_gestational", "FU1_lining_over15mm", "FU1_bleeding", "FU1_pain",
    "FU2_gestational", "FU2_lining_over15mm", "FU2_bleeding", "FU2_pain", "delayed_decision_followup",
}
INT_FIELDS = {"G", "P", "NVD", "CS", "Ab_total", "prev_D_C", "IVF"}
NUMBER_FIELDS = {"HGB", "PLT", "WBC", "hcg_value", "GA_LMP_weeks", "GA_US_weeks"}
SELECT_FIELDS = {
    "hcg_qualitative": [("positive", "חיובי"), ("negative", "שלילי")],
    "US_finding": [
        ("1", "1 — שק הריון בלבד"), ("2", "2 — שק חלמון, ללא קוטב עוברי"),
        ("3", "3 — קוטב עוברי, דופק לא תועד מעולם"), ("4", "4 — קוטב עוברי, דופק תועד ונעלם"),
    ],
}


def field_type(f):
    if f in BOOL_FIELDS:
        return "bool"
    if f in SELECT_FIELDS:
        return "select"
    if f in INT_FIELDS:
        return "int"
    if f in NUMBER_FIELDS:
        return "number"
    return "text"

def text_path(episode_id):
    if episode_id.startswith("RND2EP"):
        d = "episode_texts_random2"
    else:
        d = "episode_texts_random"
    return os.path.join(SCRATCH, d, episode_id + ".txt")

episodes = json.load(open(RESULTS, encoding="utf-8"))
out = []
for ep in episodes:
    coders = {c["coder"]: c for c in ep["coders"]}
    consensus = ep["consensus"]
    disagree_fields = {d["field"] for d in ep["disagreements"]}
    text = ""
    tp = text_path(ep["episode_id"])
    if os.path.exists(tp):
        text = open(tp, encoding="utf-8").read()

    field_rows = []
    for f, label in FIELD_LABELS.items():
        if f == "possible_record_mixup":
            continue
        field_rows.append({
            "field": f,
            "label": label,
            "value": consensus.get(f),
            "coders": [coders.get(i, {}).get(f) for i in (1, 2, 3)],
            "disagree": f in disagree_fields,
            "type": field_type(f),
            "options": SELECT_FIELDS.get(f),
        })

    out.append({
        "episode_id": ep["episode_id"],
        "admission_nos": ep["admission_nos"],
        "age": ep.get("age"),
        "entry_date": ep.get("entry_date"),
        "text": text,
        "outcome_category": consensus.get("outcome_category"),
        "outcome_he": OUTCOME_HE.get(consensus.get("outcome_category"), consensus.get("outcome_category")),
        "exclusion_reason": consensus.get("exclusion_reason"),
        "exclusion_he": EXCLUSION_HE.get(consensus.get("exclusion_reason")),
        "outcome_evidence_quote": consensus.get("outcome_evidence_quote"),
        "coders_outcome": [coders.get(i, {}).get("outcome_category") for i in (1, 2, 3)],
        "outcome_unanimous": len({coders.get(i, {}).get("outcome_category") for i in (1, 2, 3)}) == 1,
        "possible_record_mixup": bool(consensus.get("possible_record_mixup")),
        "record_mixup_note": consensus.get("record_mixup_note"),
        "notes": consensus.get("notes"),
        "phase2": consensus.get("outcome_category") in ("success", "failure"),
        "fields": field_rows,
    })

json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False)
print(f"{len(out)} episodes, phase2 count: {sum(1 for e in out if e['phase2'])}")
print("output size:", os.path.getsize(OUT) / 1024, "KB")
