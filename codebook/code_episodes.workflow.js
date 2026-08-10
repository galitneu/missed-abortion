export const meta = {
  name: 'code-missed-abortion-episodes',
  description: 'Three independent coder agents classify missed-abortion clinical episodes per the coding protocol; a deterministic merge stage produces majority-vote consensus per episode.',
  phases: [
    { title: 'Code', detail: 'each episode coded independently by 3 agents' },
    { title: 'Merge', detail: 'majority vote + disagreement flags per field' },
  ],
}

const CODEBOOK = `פרוטוקול קידוד — סקירת מקרי הפלה נדחית (Missed Abortion). קודדו את האפיזודה הבאה בהתאם לכללים הבאים בלבד. אל תנחשו ערך שאינו נתמך במפורש בטקסט — אם לא ניתן לקבוע, החזירו null.

סיווג התוצאה הראשי (outcome_category) — 5 קטגוריות, השתמשו בניסוח המדויק לפי ההגדרות:
- not_missed_abortion: האבחנה הסופית אינה הפלה נדחית קלאסית (למשל הריון צווארי, הפלה בלתי שלמה עם רקמה בנרתיק, הריון חוץ רחמי, כפילות רשומה, אבחנה מבדלת אחרת).
- not_applicable: אבחנת הפלה נדחית ודאית, אך האישה בחרה בגרידה מלכתחילה ולא ניסתה טיפול תרופתי.
- success: קיבלה טיפול תרופתי (מייפיג'ין/ציטוטק); ביקורת מאוחרת מראה "ללא שק הריון" — הושלם בלי גרידה.
- failure: קיבלה טיפול תרופתי, אך בסופו של דבר עברה גרידה (elective או emergency).
- open: קיבלה/הופנתה לטיפול תרופתי, אך אין תיעוד המשך/החלטה סופית בטקסט. הניסוח המדויק המקובל: "לא ניתן לדעת - לא הגיעה לביקורת".
שימו לב: "החלטה נדחית" (המטופלת מבקשת לחשוב ולחזור מחר) אינה open ואינה not_applicable — סמנו delayed_decision_followup=true במקרה כזה.

exclusion_reason (רק אם outcome_category=not_missed_abortion), לפי הרשימה הידועה: duplicate (כפילות רשומה), other_diagnosis (לא הפלה נדחית - אבחנה אחרת), ectopic_pregnancy (הריון חוץ רחמי), twins (הריון תאומים), did_not_attend_followup (לא הגיעה לביקורת - מתאים בעצם ל-open ולא כאן), did_not_receive_treatment (לא קיבלה בפועל את הטיפול שתוכנן), late_abortion_dc (הפלה מאוחרת עם גרידה — תקף רק כאשר שבוע ההריון בזמן האבחנה הוא 14+0 ומעלה; אם הטקסט עצמו מכנה את המקרה במפורש "הפלה נדחית" והוא מתחת לשבוע 14, קדדו לפי הקטגוריה הרגילה (not_applicable/success/failure/open) ולא כהחרגה, גם אם צוין גיל הריון גבולי), operative_hysteroscopy (תקף רק כאשר ההיסטרוסקופיה היא עצמה האבחנה/הסיבה לפנייה, שאינה קשורה למסלול טיפול קלאסי של הפלה נדחית — למשל פוליפ אנדומטריאלי או ממצא מבני אחר שהתגלה בבירור; אם ההיסטרוסקופיה בוצעה כפעולה כירורגית מסכמת אחרי כישלון טיפול תרופתי מתועד בהפלה נדחית ודאית, אין להשתמש בהחרגה זו — קדדו failure וסמנו hysteroscopy=true כפרט טיפולי), curettage_removal (הוצאת תוכן הריוני עם קראוזה), elective_termination (הפסקת הריון יזומה — ראו הכלל הייעודי להלן), other.

הפסקת הריון יזומה לעומת הפלה נדחית (קריטי, שימו לב היטב): אם המטופלת פנתה/התקבלה במפורש כדי "להפסיק הריון" (למשל "פנתה היום להפסקת הריון תרופתית") — כלומר זו הייתה הבקשה/הסיבה המקורית לפנייה עצמה — קדדו outcome_category=not_missed_abortion, exclusion_reason=elective_termination. זה תקף **גם אם בהמשך אותו רישום מופיע ניסוח קליני כמו "הפלה נדחית" או ניתן פרוטוקול טיפול זהה** (מייפיג'ין/ציטוטק) — הקובע הוא הבקשה/הסיבה המקורית לפנייה כפי שתועדה בתחילת הרישום, לא ניסוח קליני מאוחר יותר. לעומת זאת, אזכור של "הפסקת הריון" כחלק מהיסטוריה מיילדותית של אירוע עבר (למשל "ב-2012 עברה הפסקת הריון בשבוע 22 בשל מומים", או ברשימת רקע מיילדותי כגון G/P/AA) אינו רלוונטי לסיווג האפיזודה הנוכחית ואין להתייחס אליו. אם אינו ברור מהטקסט האם הפנייה הנוכחית הייתה יזומה מלכתחילה או גילוי של הריון לא מתפתח — קדדו לפי שאר הכללים הרגילים, אך ציינו זאת ב-notes לבדיקת רופא/ה (למשל: "לא ברור אם הפסקת הריון יזומה או הפלה נדחית - נדרשת בדיקה").

שדות היסטוריה מיילדותית: G=הריונות, P=לידות מעבר לכשירות חיים (כולל CS, לא כולל הפלות), NVD=לידות רגילות בלבד, CS=ניתוחים קיסריים, Ab_total=סכום כל תתי-סוגי ההפלות (AA+MA+SA+TOP), prev_D_C=מספר תתי-מקרים בהיסטוריה שמתויגים במפורש "עם גרידה"/"גרידה" (לא לנחש אם לא צוין גרידה במפורש).

ברירת מחדל בהיעדר אזכור (חשוב, חל על שדות בוליאניים/מונים רבים): אם הטקסט כולו שותק לגמרי בנושא מסוים ואין שום אזכור שלו — לא ברקע, לא בהיסטוריה, לא בתיאור הטיפול — קבעו ערך ברירת מחדל שלילי (0/false), לא null. זה חל על: IVF, smoking, hysteroscopy, prev_D_C, Ab_total, D_C_treatment (אם ברור שלא בוצעה גרידה כלל, לא רק שלא תועד ביצוע), emergency_D_C, delayed_decision_followup, medical_treatment. לעומת זאת, השתמשו ב-null כאשר השדה תלוי בקיום אירוע/ביקור שלא קרה או לא מתועד באפיזודה (למשל FU2 כשלא הייתה ביקורת שנייה בכלל, D_C_treatment כשנקבע תור לגרידה אך אין שום אזכור אם היא בוצעה בפועל, hcg_value/HGB/PLT/WBC כשלא נבדקו). כלל אצבע: "לא הוזכר בכלל, והיה מוזכר לו קרה" → 0/false. "לא ניתן לדעת כי החלק הרלוונטי של הסיפור חסר לגמרי" → null.

רקע: IVF (0=לא, 1=IVF רגיל, 2=IVF PGD אם צוין), smoking (בוליאני, "הרגלים-0"=false, "עישון"/"מעשנת" מפורש=true).

מעבדה: Rh — החזירו את סוג הדם המלא כפי שמופיע במקור, כולל האות (לדוגמה "A+", "O-", "AB+"), לא רק את הסימן +/- בלבד. לדוגמה: "O NEG"→"O-", "A POS"→"A+", "סוג דם B חיובי"→"B+". HGB/PLT/WBC כערכים מספריים כשמופיעים. HCG: hcg_value אם יש ערך מספרי (BHCG כמותי), hcg_qualitative="positive"/"negative" אם רק צוין איכותי (בטא חיובית/שלילית) בלי מספר.

גיל הריון: GA_LMP_weeks ו-GA_US_weeks מיוצגים כ"שבועות.ימים" — הספרה/הספרות אחרי הנקודה הן מספר הימים (0-6), ולא שבר עשרוני אמיתי. לדוגמה: 8 שבועות ו-2 ימים = 8.2 (ולא 8.29=8+2/7). אם הטקסט נותן ישירות "שבוע X.Y" או "שבוע X+Y" — Y הם הימים, השתמשו בהם ישירות (X+Y ⇒ X.Y). GA_LMP_weeks לפי וסת אחרונה. GA_US_weeks לפי הסונר הפורמלי/מפורט האחרון לפני האבחנה (CRL). אם אין קוטב עוברי (רק שק ריק/עם שק חלמון) אל תחשבו GA_US מגודל השק — השאירו null. US_finding (סודרי): 1=שק הריון בלבד; 2=+שק חלמון בלי קוטב עוברי; 3=קוטב עוברי, דופק מעולם לא תועד; 4=קוטב עוברי, דופק תועד בעבר ונעלם. קראו את כל היסטוריית הסונרים באפיזודה כדי להבחין בין 3 ל-4, לא רק את הסונר האחרון.
שימו לב: רישום קליני בודד מצטט לעיתים כמה סונרים בתאריכים שונים — למשל סונר ישן יותר שמובא כרקע/היסטוריה (עם תאריך מפורש, למשל "בסונר 22.12.24 הודגם...") ולצידו סונר של הביקור הנוכחי ("בסונר היום..."/"בסונר אצל רופאה מטפלת הודגם..."). לצורך GA_US_weeks ו-US_finding יש להשתמש אך ורק בסונר של הביקור/האבחנה הנוכחיים (בד"כ ה-CRL המוזכר אחרון, בסמוך לתיאור הבדיקה הפיזית או לסיכום), ולא בסונר הישן המצוטט להשוואה/היסטוריה — גם אם הסונר הישן מתואר בפירוט רב יותר.

טיפול ותוצאה: medical_treatment=מתן ציטוטק/מייפיג'ין מתועד. D_C_treatment=גרידה בוצעה בפועל. elective_D_C=נקבע תור לגרידה מתוכננת/לא דחופה — בין אם כבחירה ראשונית של המטופלת מלכתחילה (מסלול not_applicable) ובין אם כתוצאה מכישלון טיפול תרופתי (מסלול failure); לא תלוי במסלול, רק בכך שהגרידה מתוכננת ולא דחופה. emergency_D_C=דימום/חוסר יציבות → גרידה דחופה. hysteroscopy=היסטרוסקופיה בוצעה.

מעקבים: FU1/FU2_gestational=ביקורת המשך מראה שק הריון עדיין קיים (בוליאני). FU1/FU2_lining_over15mm=עובי רירית בביקורת מעל/מתחת 15 מ"מ (true=מעל 15, false=מתחת, null=לא צוין). FU1/FU2_bleeding, FU1/FU2_pain=דימום/כאב בביקורת (בוליאני).

חשוב: הטקסט הגולמי עשוי לכלול כמה גרסאות/רישומים כרונולוגיים לאותה אפיזודה (מעריכה מתקדמת של אותה רשומה, או ביקורים נפרדים). קראו את כל ההיסטוריה. אם גרסה מאוחרת מכילה "@@@" במקום ערך שהופיע בגרסה מוקדמת יותר (כלומר הערך נמחק/הוחלף), השתמשו בערך מהגרסה המוקדמת יותר לצורך חילוץ השדה המבוקש. שימו לב שגם ללא סימון @@@ מפורש, גרסה מאוחרת יכולה להסיר פסקה שלמה שהופיעה בגרסה מוקדמת יותר (למשל טקסט תבנית שגוי/סותר שהוסר בעריכה) — במקרה כזה התייחסו לגרסה המאוחרת כמדויקת יותר, וכביטול התוכן שהוסר ממנה, אלא אם יש עדות ברורה בטקסט שמדובר בשגיאת שמירה מקרית ולא בעריכה מכוונת. לצורך קביעת outcome_category ופרטי ההמשך, התבססו על הרישום הכרונולוגי האחרון הזמין.

outcome_evidence_quote: ציטוט קצר (משפט אחד, עד כ-25 מילים) מהטקסט המקורי שתומך ישירות בסיווג outcome_category שבחרתם. אל תעתיקו קטעים ארוכים.
notes: הערה קצרה (עד כ-30 מילים) לכל דבר גבולי/לא חד-משמעי שדורש בדיקה אנושית, או null אם אין. לא נדרש הסבר מלא — רק ציון הנקודה הבעייתית.

בדיקת עקביות פנימית (חובה, בצעו כקריאה כללית ראשונה — לפני שאתם ממלאים שדות): קראו את כל הרישומים הכרונולוגיים באפיזודה מקצה לקצה פעם אחת, במטרה ספציפית לזהות אם אחד מהם הוא בעצם ציטוט/שריד של רשומה ישנה שאינה שייכת לאבחנה/לביקור הנוכחיים — לא רק "אותה אישה, אירוע אחר", אלא גם המקרה הנפוץ יותר שבו רשומה בודדת בתוך הצרור (בדרך כלל, אך לא תמיד, הראשונה) מתארת בפועל אירוע רפואי ישן (למשל תאריך מפורש בגוף הטקסט שקודם בהרבה לתאריך הרישום עצמו, כגון "8 ימים לאחר מתן ציטוטק" ביחס לתאריך שונה מתאריך האשפוז הנוכחי, או הריון תקין/עם דופק בעוד רשומות סמוכות בזמן מתעדות כבר הפלה נדחית) שהודבק בטעות למסמך האשפוז הנוכחי. סימנים נוספים לחשד כזה: היסטוריה מיילדותית שונה בין רישומים (G/P שונים) שלא מוסברת בפער זמן, שבוע הריון שקופץ בצורה שלא מתיישבת עם הפרש השעות/הימים בין הרישומים, סוג דם שונה, גיל שונה, או תיאור קליני של אבחנה/החלטה שונה לגמרי (למשל "הפלה שלמה"/"ללא שק הריון בביקורת" ברישום אחד מול "הפלה נדחית חדשה"/"מעוניינת בגרידה" ברישום אחר סמוך בזמן) ללא רצף לוגי ביניהם. אם זיהיתם חשד כזה: possible_record_mixup=true, ותארו ב-record_mixup_note בקצרה (עד כ-40 מילים) אילו רישומים (לפי שעת הרישום) נראים שייכים לאירוע/אישה שונים ומה ההבדל המרכזי — ללא פירוט מלא של כל הממצאים. חשוב במיוחד: outcome_category (וכל שאר השדות) חייב להתבסס אך ורק על הרישום העדכני/העקבי ביותר שמתאר את האבחנה וההחלטה בפועל של האשפוז הנוכחי — לעולם אל תבססו את outcome_category על רשומה שזיהיתם כשריד/ציטוט של אירוע ישן, גם אם היא נראית "מלאה" או "מסודרת" יותר. אם אין חשד כזה: possible_record_mixup=false, record_mixup_note=null.

חשוב לגבי אורך: כל שדות הטקסט החופשי (outcome_evidence_quote, notes, record_mixup_note) חייבים להיות תמציתיים ככל האפשר — משפט או חלק ממשפט, לא פסקה. המטרה היא לאפשר בדיקה אנושית מהירה, לא תיעוד מלא של תהליך החשיבה.`

const SCHEMA = {
  type: 'object',
  properties: {
    G: { type: ['integer', 'null'] },
    P: { type: ['integer', 'null'] },
    NVD: { type: ['integer', 'null'] },
    CS: { type: ['integer', 'null'] },
    Ab_total: { type: ['integer', 'null'] },
    prev_D_C: { type: ['integer', 'null'] },
    IVF: { type: ['integer', 'null'] },
    smoking: { type: ['boolean', 'null'] },
    Rh: { type: ['string', 'null'] },
    HGB: { type: ['number', 'null'] },
    PLT: { type: ['number', 'null'] },
    WBC: { type: ['number', 'null'] },
    hcg_value: { type: ['number', 'null'] },
    hcg_qualitative: { type: ['string', 'null'] },
    GA_LMP_weeks: { type: ['number', 'null'] },
    GA_US_weeks: { type: ['number', 'null'] },
    US_finding: { type: ['integer', 'null'] },
    medical_treatment: { type: ['boolean', 'null'] },
    D_C_treatment: { type: ['boolean', 'null'] },
    elective_D_C: { type: ['boolean', 'null'] },
    emergency_D_C: { type: ['boolean', 'null'] },
    hysteroscopy: { type: ['boolean', 'null'] },
    FU1_gestational: { type: ['boolean', 'null'] },
    FU1_lining_over15mm: { type: ['boolean', 'null'] },
    FU1_bleeding: { type: ['boolean', 'null'] },
    FU1_pain: { type: ['boolean', 'null'] },
    FU2_gestational: { type: ['boolean', 'null'] },
    FU2_lining_over15mm: { type: ['boolean', 'null'] },
    FU2_bleeding: { type: ['boolean', 'null'] },
    FU2_pain: { type: ['boolean', 'null'] },
    outcome_category: { type: 'string', enum: ['not_missed_abortion', 'not_applicable', 'success', 'failure', 'open'] },
    outcome_evidence_quote: { type: 'string', maxLength: 220 },
    exclusion_reason: { type: ['string', 'null'] },
    delayed_decision_followup: { type: ['boolean', 'null'] },
    notes: { type: ['string', 'null'], maxLength: 260 },
    possible_record_mixup: { type: 'boolean' },
    record_mixup_note: { type: ['string', 'null'], maxLength: 350 },
  },
  required: ['outcome_category', 'outcome_evidence_quote', 'possible_record_mixup'],
}

const FIELDS = Object.keys(SCHEMA.properties)

// Free-text fields are independently-worded prose per coder — they almost never match
// verbatim even when coders agree in substance, so they are excluded from the structured
// disagreement count/flagging and merged by picking the majority-outcome coder's text instead.
const FREE_TEXT_FIELDS = new Set(['outcome_evidence_quote', 'notes', 'record_mixup_note'])

function buildPrompt(ep) {
  return `${CODEBOOK}\n\nהשתמשו בכלי Read כדי לקרוא את הקובץ הבא — הוא מכיל את כל רשומות הטקסט הגולמי (שדה Description_Text) עבור אפיזודה אחת (אישה אחת), בסדר כרונולוגי:\n\n${ep.text_file}\n\nלאחר קריאת הקובץ, קודדו אפיזודה זו והחזירו את כל השדות בסכימה.`
}

// Case/whitespace-insensitive comparison key so "O+" vs "o+" (or trailing spaces) don't
// register as a disagreement — string fields (Rh, hcg_qualitative, exclusion_reason, etc.)
// are compared normalized, but the actual consensus value keeps its original formatting.
function compareKey(v) {
  return typeof v === 'string' ? v.trim().toLowerCase() : v
}

function majorityMerge(coderResults) {
  const consensus = {}
  const disagreements = []
  const structuredFields = FIELDS.filter(f => !FREE_TEXT_FIELDS.has(f))
  for (const field of structuredFields) {
    const rawVals = coderResults.map(c => (c ? (c[field] ?? null) : null))
    const keys = rawVals.map(v => JSON.stringify(compareKey(v)))
    const counts = {}
    for (const k of keys) counts[k] = (counts[k] || 0) + 1
    let winnerKey = null, winnerCount = 0
    for (const [k, c] of Object.entries(counts)) {
      if (c > winnerCount) { winnerKey = k; winnerCount = c }
    }
    const winnerValue = winnerKey === null ? null : rawVals[keys.indexOf(winnerKey)]
    consensus[field] = winnerCount >= 2 ? winnerValue : null
    // Flag any non-unanimous field (2-1 splits included), not just true 3-way splits.
    if (winnerCount < 3) {
      disagreements.push({ field, coder_values: rawVals })
    }
  }
  // Free-text fields: take the text from whichever coder's outcome_category matches the
  // consensus outcome_category (the "majority coder"), rather than requiring verbatim match.
  const majorityCoder = coderResults.find(c => c && JSON.stringify(c.outcome_category ?? null) === JSON.stringify(consensus.outcome_category ?? null)) || coderResults.find(Boolean)
  for (const field of FREE_TEXT_FIELDS) {
    consensus[field] = majorityCoder ? (majorityCoder[field] ?? null) : null
  }
  return { consensus, disagreements }
}

const parsedArgs = typeof args === 'string' ? JSON.parse(args) : args
const episodes = Array.isArray(parsedArgs) ? parsedArgs : (parsedArgs && parsedArgs.episodes) || []
log(`typeof args=${typeof args}, isArray(args)=${Array.isArray(args)}, episodes.length=${episodes.length}`)
if (!episodes.length) throw new Error('episodes array is empty — args did not arrive as expected: ' + JSON.stringify(args).slice(0, 500))
const results = await pipeline(
  episodes,
  ep => parallel([1, 2, 3].map(n => () =>
    agent(buildPrompt(ep), { label: `${ep.episode_id}-coder${n}`, phase: 'Code', schema: SCHEMA })
      .then(r => (r ? { coder: n, ...r } : null))
  )),
  (coderResults, ep) => {
    const clean = coderResults.filter(Boolean)
    if (clean.length < 3) {
      log(`⚠ ${ep.episode_id}: only ${clean.length}/3 coders returned a result (some failed) — treat consensus with extra caution`)
    }
    const { consensus, disagreements } = majorityMerge(clean)
    const result = {
      episode_id: ep.episode_id,
      admission_nos: ep.admission_nos,
      linked: ep.linked,
      age: ep.age,
      entry_date: ep.entry_date,
      discharge_date: ep.discharge_date,
      coders: clean,
      consensus,
      disagreements,
      n_disagreements: disagreements.length,
    }
    log(`✓ ${ep.episode_id}: outcome=${consensus.outcome_category}, mixup=${consensus.possible_record_mixup}, disagreements=${disagreements.length}, coders=${clean.length}/3`)
    return result
  }
)

log(`Coded ${results.length} episodes.`)
return results
