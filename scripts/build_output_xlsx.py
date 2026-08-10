import json
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl.utils import get_column_letter

RESULTS = "/tmp/claude-0/-home-user-comfort-choice-helper/df71759e-1127-5ed0-ab07-ff2e70e7a1bc/scratchpad/coding_results_random80_v2.json"
OUT = "/tmp/claude-0/-home-user-comfort-choice-helper/df71759e-1127-5ed0-ab07-ff2e70e7a1bc/scratchpad/missed_abortion_coded_random80_v2.xlsx"
TEXT_DIRS = {
    "RNDEP": "/tmp/claude-0/-home-user-comfort-choice-helper/df71759e-1127-5ed0-ab07-ff2e70e7a1bc/scratchpad/episode_texts_random",
    "RND2EP": "/tmp/claude-0/-home-user-comfort-choice-helper/df71759e-1127-5ed0-ab07-ff2e70e7a1bc/scratchpad/episode_texts_random2",
}


def text_dir_for(episode_id):
    return TEXT_DIRS["RND2EP"] if episode_id.startswith("RND2EP") else TEXT_DIRS["RNDEP"]

FIELDS = ["G","P","NVD","CS","Ab_total","prev_D_C","IVF","smoking","Rh","HGB","PLT","WBC",
          "hcg_value","hcg_qualitative","GA_LMP_weeks","GA_US_weeks","US_finding",
          "medical_treatment","D_C_treatment","elective_D_C","emergency_D_C","hysteroscopy",
          "FU1_gestational","FU1_lining_over15mm","FU1_bleeding","FU1_pain",
          "FU2_gestational","FU2_lining_over15mm","FU2_bleeding","FU2_pain",
          "exclusion_reason","delayed_decision_followup"]

OUTCOME_HE = {
    "open": "פתוח",
    "not_applicable": "לא רלוונטי",
    "success": "הצלחה",
    "failure": "כישלון",
    "not_missed_abortion": "לא הפלה נדחית (החרגה)",
    None: None,
}

results = json.load(open(RESULTS, encoding="utf-8"))

wb = openpyxl.Workbook()

FONT = "Arial"
header_font = Font(name=FONT, bold=True, size=10)
cell_font = Font(name=FONT, size=10)
success_row_fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
failure_row_fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
review_row_fill = PatternFill(start_color="FFD966", end_color="FFD966", fill_type="solid")
mixup_row_fill = PatternFill(start_color="B4A7D6", end_color="B4A7D6", fill_type="solid")
diff_cell_fill = PatternFill(start_color="FFA500", end_color="FFA500", fill_type="solid")


def write_header(ws, headers):
    for j, h in enumerate(headers, start=1):
        c = ws.cell(row=1, column=j, value=h)
        c.font = header_font


# ---------------------------------------------------------------------------
# Sheet 1: overview — one row per episode, kept lean (no 120-column field grid,
# no long free-text columns) so it opens fast in any viewer.
# ---------------------------------------------------------------------------
ws_main = wb.active
ws_main.title = "קידוד - סקירה"
ws_main.sheet_view.rightToLeft = True
ws_main.freeze_panes = "A2"

main_headers = ["episode_id", "admission_nos", "linked_admission", "age", "entry_date", "discharge_date",
                "חשד_לערבוב_רשומות__קודד1", "חשד_לערבוב_רשומות__קודד2", "חשד_לערבוב_רשומות__קודד3",
                "חשד_לערבוב_רשומות__הכרעה",
                "סוג_הרשומה__קודד1", "סוג_הרשומה__קודד2", "סוג_הרשומה__קודד3", "סוג_הרשומה__הכרעה",
                "אחידות_דעים_סוג_רשומה",
                "n_disagreements", "disagreement_fields", "מדגם_בדיקה_גם_בהסכמה_מלאה"]
write_header(ws_main, main_headers)

main_widths = {"A": 10, "B": 16, "C": 10, "D": 6, "E": 20, "F": 20,
               "G": 12, "H": 12, "I": 12, "J": 14,
               "K": 12, "L": 12, "M": 12, "N": 14,
               "O": 22, "P": 8, "Q": 25, "R": 26}

# Stratified sample of fully-unanimous episodes (0 field disagreements, no mixup flag),
# spread across outcome categories, so reviewers also spot-check extraction accuracy
# on records where all 3 coders already agreed — agreement is not proof of correctness.
AGREEMENT_SAMPLE_IDS = {
    "RNDEP003", "RNDEP005", "RNDEP009",
    "RNDEP010", "RNDEP018", "RNDEP021",
    "RNDEP030",
    "RND2EP005", "RND2EP028",
    "RND2EP010",
}
agreement_sample_fill = PatternFill(start_color="ADD8E6", end_color="ADD8E6", fill_type="solid")
for letter, w in main_widths.items():
    ws_main.column_dimensions[letter].width = w

# ---------------------------------------------------------------------------
# Sheet 2: coding detail — LONG format (one row per episode x source), so the
# 30-field x 4-source grid never turns into 120+ columns. Notes/quotes live
# here, not on the overview sheet.
# ---------------------------------------------------------------------------
ws_detail = wb.create_sheet("קידוד - פירוט")
ws_detail.sheet_view.rightToLeft = True
ws_detail.freeze_panes = "A2"
detail_headers = ["episode_id", "מקור"] + FIELDS + ["outcome_category", "outcome_evidence_quote",
                   "possible_record_mixup", "record_mixup_note", "notes"]
write_header(ws_detail, detail_headers)
detail_col_of = {h: j for j, h in enumerate(detail_headers, start=1)}
for j, h in enumerate(detail_headers, start=1):
    letter = get_column_letter(j)
    if h in ("outcome_evidence_quote", "record_mixup_note", "notes"):
        ws_detail.column_dimensions[letter].width = 55
    elif h in ("episode_id", "מקור"):
        ws_detail.column_dimensions[letter].width = 12
    else:
        ws_detail.column_dimensions[letter].width = 13

# ---------------------------------------------------------------------------
# Sheet 3: full text — one row per episode, NOT wrapped (avoids huge
# auto-computed row heights; open the cell / formula bar to read it fully).
# ---------------------------------------------------------------------------
ws_text = wb.create_sheet("טקסט מלא")
ws_text.sheet_view.rightToLeft = True
ws_text.freeze_panes = "A2"
write_header(ws_text, ["episode_id", "admission_nos", "full_text"])
ws_text.column_dimensions["A"].width = 10
ws_text.column_dimensions["B"].width = 16
ws_text.column_dimensions["C"].width = 100

# ---------------------------------------------------------------------------
main_row = 2
detail_row = 2
for ep in results:
    coders = {c["coder"]: c for c in ep["coders"]}
    c1, c2, c3 = coders.get(1, {}), coders.get(2, {}), coders.get(3, {})
    consensus = ep["consensus"]
    disagree_fields = [d["field"] for d in ep["disagreements"]]

    consensus_outcome = consensus.get("outcome_category")
    outcome_values = [c1.get("outcome_category"), c2.get("outcome_category"), c3.get("outcome_category")]
    unanimous = len(set(outcome_values)) == 1

    mixup_consensus = consensus.get("possible_record_mixup")

    if mixup_consensus:
        row_fill = mixup_row_fill
    elif not unanimous:
        row_fill = review_row_fill
    elif consensus_outcome == "success":
        row_fill = success_row_fill
    elif consensus_outcome == "failure":
        row_fill = failure_row_fill
    else:
        row_fill = None

    # --- overview row ---
    row = [
        ep["episode_id"],
        ", ".join(str(a) for a in ep["admission_nos"]),
        ep["linked"],
        ep["age"],
        ep["entry_date"],
        ep["discharge_date"],
        "כן" if c1.get("possible_record_mixup") else "לא",
        "כן" if c2.get("possible_record_mixup") else "לא",
        "כן" if c3.get("possible_record_mixup") else "לא",
        "כן" if mixup_consensus else "לא",
        OUTCOME_HE.get(c1.get("outcome_category"), c1.get("outcome_category")),
        OUTCOME_HE.get(c2.get("outcome_category"), c2.get("outcome_category")),
        OUTCOME_HE.get(c3.get("outcome_category"), c3.get("outcome_category")),
        OUTCOME_HE.get(consensus_outcome, consensus_outcome),
        "כן" if unanimous else "לא - נדרשת בדיקת רופא/ה",
        ep["n_disagreements"],
        ", ".join(disagree_fields),
        "כן" if ep["episode_id"] in AGREEMENT_SAMPLE_IDS else "",
    ]
    for j, val in enumerate(row, start=1):
        cell = ws_main.cell(row=main_row, column=j, value=val)
        cell.font = cell_font
        cell.alignment = Alignment(wrap_text=False, vertical="top", horizontal="right", readingOrder=2)
        if row_fill is not None:
            cell.fill = row_fill
    if ep["episode_id"] in AGREEMENT_SAMPLE_IDS:
        ws_main.cell(row=main_row, column=len(main_headers)).fill = agreement_sample_fill
    main_row += 1

    # --- detail rows: coder1, coder2, coder3, consensus ---
    diff_field_set = set(disagree_fields)
    for label, c in (("קודד1", c1), ("קודד2", c2), ("קודד3", c3), ("הכרעה", consensus)):
        drow = [ep["episode_id"], label] + [c.get(f) for f in FIELDS] + [
            c.get("outcome_category"), c.get("outcome_evidence_quote"),
            c.get("possible_record_mixup"), c.get("record_mixup_note"), c.get("notes"),
        ]
        for j, val in enumerate(drow, start=1):
            cell = ws_detail.cell(row=detail_row, column=j, value=val)
            cell.font = cell_font
            cell.alignment = Alignment(wrap_text=False, vertical="top", horizontal="right", readingOrder=2)
        detail_row += 1
    for field in diff_field_set:
        col = detail_col_of.get(field)
        if col is None:
            continue
        for r in range(detail_row - 4, detail_row):
            ws_detail.cell(row=r, column=col).fill = diff_cell_fill

    # --- full text sheet ---
    full_text_path = f"{text_dir_for(ep['episode_id'])}/{ep['episode_id']}.txt"
    with open(full_text_path, encoding="utf-8") as f:
        full_text = f.read()
    r = ws_text.max_row + 1
    ws_text.cell(row=r, column=1, value=ep["episode_id"]).font = cell_font
    ws_text.cell(row=r, column=2, value=", ".join(str(a) for a in ep["admission_nos"])).font = cell_font
    text_cell = ws_text.cell(row=r, column=3, value=full_text)
    text_cell.font = cell_font
    text_cell.alignment = Alignment(wrap_text=False, vertical="top", horizontal="right", readingOrder=2)

wb.save(OUT)
print("saved", OUT)
