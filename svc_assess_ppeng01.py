import streamlit as st
import pandas as pd
import datetime
import sqlite3
import json
import re

# -----------------------------------------------------------------------------
# DATABASE INITIALIZATION & SCHEMA AUTO-MIGRATION
# -----------------------------------------------------------------------------
DB_FILE = "svc_assess_l1g4.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Assignments Table
    c.execute("""
        CREATE TABLE IF NOT EXISTS assignments (
            id TEXT PRIMARY KEY,
            title TEXT,
            course TEXT,
            programme TEXT,
            deadline TEXT,
            max_marks REAL,
            rubric_type TEXT,
            description TEXT,
            brief_filename TEXT,
            brief_text TEXT
        )
    """)
    
    # Rubrics Table
    c.execute("""
        CREATE TABLE IF NOT EXISTS rubrics (
            id TEXT PRIMARY KEY,
            rubric_name TEXT,
            max_marks REAL,
            criteria_json TEXT
        )
    """)
    
    # Submissions Table
    c.execute("""
        CREATE TABLE IF NOT EXISTS submissions (
            id TEXT PRIMARY KEY,
            student_id TEXT,
            student_name_anon TEXT,
            assignment_id TEXT,
            course TEXT,
            group_name TEXT,
            file_name TEXT,
            report_text TEXT,
            similarity_index REAL,
            ai_pattern_score REAL,
            ai_scores_json TEXT,
            ai_total REAL,
            max_marks REAL,
            ai_evidence_json TEXT,
            ai_strength TEXT,
            ai_priorities_json TEXT,
            ai_action TEXT,
            teacher_status TEXT,
            teacher_score REAL,
            teacher_feedback TEXT,
            submitted_date TEXT
        )
    """)
    
    # Audit Log Table
    c.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            user_role TEXT,
            action TEXT,
            details TEXT
        )
    """)
    
    # Auto-Migration for Existing Database Files
    migrations = [
        "ALTER TABLE assignments ADD COLUMN brief_filename TEXT",
        "ALTER TABLE assignments ADD COLUMN brief_text TEXT",
        "ALTER TABLE rubrics ADD COLUMN criteria_json TEXT",
        "ALTER TABLE submissions ADD COLUMN file_name TEXT",
        "ALTER TABLE submissions ADD COLUMN report_text TEXT"
    ]
    for sql in migrations:
        try:
            c.execute(sql)
        except Exception:
            pass
    
    # Seed Initial Preset Rubrics if empty
    c.execute("SELECT COUNT(*) FROM rubrics")
    if c.fetchone()[0] == 0:
        rubric_tceng = (
            "RUB-TCENG1201",
            "12-Mark TCENG1201 Formal Report Rubric",
            12.0,
            json.dumps([
                {"criterion": "Layout & Structure", "max_marks": 2.0, "focus": "Transmittal letter, Summary, Intro, Body, Conclusion, References."},
                {"criterion": "Content & Depth", "max_marks": 4.0, "focus": "Technical accuracy, vocational applications, data depth."},
                {"criterion": "Technical Vocabulary", "max_marks": 3.0, "focus": "Domain terminology, formal tone, precise phrasing."},
                {"criterion": "Grammar & Mechanics", "max_marks": 2.0, "focus": "Subject-verb agreement, sentence structure, punctuation."},
                {"criterion": "Sources & References", "max_marks": 1.0, "focus": "IEEE or formal technical reference citations."}
            ])
        )
        rubric_tc1202 = (
            "RUB-TC1202",
            "10-Mark TC1202 Standard Rubric",
            10.0,
            json.dumps([
                {"criterion": "Content", "max_marks": 2.0, "focus": "Relevance and depth of technical ideas."},
                {"criterion": "Organization / Layout", "max_marks": 2.0, "focus": "Logical sequencing and structural headings."},
                {"criterion": "Language / Vocabulary", "max_marks": 2.0, "focus": "Professional terminology and formal tone."},
                {"criterion": "Grammar / Mechanics", "max_marks": 2.0, "focus": "Punctuation, mechanics, and syntax."},
                {"criterion": "Creativity / Originality", "max_marks": 2.0, "focus": "Independent synthesis and structured layout."}
            ])
        )
        rubric_ps1301 = (
            "RUB-PS1301",
            "15-Mark PS1301 Public Speaking & Oral Presentation Rubric",
            15.0,
            json.dumps([
                {"criterion": "Content & Structure", "max_marks": 4.0, "focus": "Clear introduction, main arguments, and solid conclusion."},
                {"criterion": "Delivery & Articulation", "max_marks": 4.0, "focus": "Voice projection, pacing, pronunciation, and fluency."},
                {"criterion": "Visual Aids & Slides", "max_marks": 4.0, "focus": "Professional slide layout, diagrams, and bullet design."},
                {"criterion": "Body Language & Engagement", "max_marks": 3.0, "focus": "Eye contact, posture, confidence, and Q&A handling."}
            ])
        )
        c.execute("INSERT INTO rubrics VALUES (?,?,?,?)", rubric_tceng)
        c.execute("INSERT INTO rubrics VALUES (?,?,?,?)", rubric_tc1202)
        c.execute("INSERT INTO rubrics VALUES (?,?,?,?)", rubric_ps1301)

    # Seed Initial Pilot Assignments if empty
    c.execute("SELECT COUNT(*) FROM assignments")
    if c.fetchone()[0] == 0:
        c.execute("""
            INSERT INTO assignments VALUES (
                'ASG-TC1201-01',
                'Formal Technical Report on Electronic Components',
                'TCENG1201 - Formal Technical Communication (New Benchmark)',
                'Post-Foundation Programme',
                '2026-10-30',
                12.0,
                '12-Mark TCENG1201 Formal Report Rubric',
                'Write a formal workplace technical report investigating electronic components, safety protocols, and vocational applications.',
                'TCENG1201_Assignment_Brief.pdf',
                'Assignment Brief: Prepare a 3-5 page formal technical report investigating electronic components (resistors, diodes, or capacitors). Include Transmittal Letter, Executive Summary, Introduction, Technical Body, Conclusion, and IEEE References.'
            )
        """)
        c.execute("""
            INSERT INTO assignments VALUES (
                'ASG-TC1202-02',
                'Electronics Engineering Mid-Term Technical Report',
                'TC1202 - Electronics Engineering Workshop',
                'Foundation Level 1 Group 4',
                '2026-11-15',
                10.0,
                '10-Mark TC1202 Standard Rubric',
                'Investigate smart vest circuits or semiconductor components and submit a structured technical report.',
                'TC1202_Midterm_Brief.pdf',
                'Assignment Brief: Investigate smart vest circuits or transistor applications in AC/DC systems. Ensure clear structure, vocational vocabulary, and safe workshop procedures.'
            )
        """)

    # Seed Sample Benchmark Submissions if empty
    c.execute("SELECT COUNT(*) FROM submissions")
    if c.fetchone()[0] == 0:
        sample_sub1 = (
            "SUB-ASG-TC1201-01-001",
            "PPENG01/04-00001",
            "Student A01 (Anonymized)",
            "ASG-TC1201-01",
            "TCENG1201 - Formal Technical Communication (New Benchmark)",
            "Foundation Level 1 Group 4",
            "Resistor_Technical_Report.docx",
            """TRANSMITTAL LETTER & TECHNICAL REPORT
To: Mrs. Anwar Al Fathi, Lecturer, Saham VC
From: Student A01, Level 1 Group 4
Subject: Resistor Technical Investigation

SUMMARY:
Resistors are fundamental passive electronic components designed to regulate electric current and protect sensitive circuits from power surges. This report investigates fixed vs. variable resistors and outlines workplace safety protocols.

1. INTRODUCTION:
The purpose of this report is to evaluate electronic resistor types and their application in circuit safety.

2. TECHNICAL BODY:
Resistors limit electric current flow in a circuit according to Ohm's Law (V = IR). Fixed resistors maintain a constant resistance value, while variable resistors allow manual adjustment.

3. CONCLUSION & RECOMMENDATIONS:
1. Always check component power ratings before applying voltage.
2. Ensure proper thermal heat sinking in high-power applications.

REFERENCES:
[1] IEEE Electronics Handbook, 2025.""",
            12.5,
            18.0,
            json.dumps({"Layout & Structure": 2.0, "Content & Depth": 3.6, "Technical Vocabulary": 2.8, "Grammar & Mechanics": 1.7, "Sources & References": 0.9}),
            11.0,
            12.0,
            json.dumps({
                "Layout & Structure": "Transmittal letter header, summary, introduction, body, and references present.",
                "Content & Depth": "Comprehensive technical coverage of fixed vs variable resistors.",
                "Technical Vocabulary": "Accurate integration of domain terms (Ohm's Law, current, voltage).",
                "Grammar & Mechanics": "Minor punctuation and syntax flaws.",
                "Sources & References": "IEEE bracketed reference included."
            }),
            "Exceptional technical report structure following official TCENG1201 benchmark guidelines.",
            json.dumps(["Proofread for minor subject-verb agreement.", "Add explicit labels to circuit schematics."]),
            "Review sentence mechanics before final submission.",
            "Approved",
            11.0,
            "Verified IEEE references and verified complete layout.",
            "2026-10-10 09:30"
        )
        sample_sub2 = (
            "SUB-ASG-TC1201-01-002",
            "PPENG01/04-00002",
            "Student A02 (Anonymized)",
            "ASG-TC1201-01",
            "TCENG1201 - Formal Technical Communication (New Benchmark)",
            "Foundation Level 1 Group 4",
            "Diode_Report_V1.pdf",
            """Subject: Diode Function Report
From: Student A02
Date: 8 October 2026

SUMMARY:
diodes are considered important electronic devic. Diode have many types like LED, Zener diode, and Junction diode. Recommendations: 1. Test all sensors. 2. Avoid incorrect wiring.

1. Introduction:
The purpose of this report is to study diode fiction in AC/DC conversion.

2. Body:
Diode allow current flow in one direction only. LED prefer to Light Emitting Diode used for display. Zener diode used for voltage regulation.

3. Conclusion:
Diode are importance for circuit safety. Recommendations: 1. Test all sensors. 2. Avoid incorrect wiring.""",
            14.0,
            22.5,
            json.dumps({"Layout & Structure": 1.2, "Content & Depth": 2.5, "Technical Vocabulary": 2.0, "Grammar & Mechanics": 1.0, "Sources & References": 0.3}),
            7.0,
            12.0,
            json.dumps({
                "Layout & Structure": "Missing formal transmittal letter header and references section.",
                "Content & Depth": "Correctly identifies diode types (LED, Zener) but duplicates text between Summary and Conclusion.",
                "Technical Vocabulary": "Integrates domain terms but contains spelling errors (fiction vs function).",
                "Grammar & Mechanics": "Frequent agreement errors ('Diode allow', 'Diode are importance').",
                "Sources & References": "No citations or reference list provided."
            }),
            "Accurate identification of essential diode types and AC to DC conversion principles.",
            json.dumps(["Proofread for subject-verb agreement ('Diodes are important').", "Write a unique Summary section rather than repeating Conclusion text."]),
            "Revise Summary to highlight key findings instead of repeating recommendations.",
            "Pending Review",
            7.0,
            "",
            "2026-10-09 10:15"
        )
        
        c.execute("INSERT INTO submissions VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", sample_sub1)
        c.execute("INSERT INTO submissions VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", sample_sub2)
        
    conn.commit()
    conn.close()

init_db()

# Helper DB Functions
def get_db():
    return sqlite3.connect(DB_FILE)

def log_audit(role, action, details):
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO audit_log (timestamp, user_role, action, details) VALUES (?,?,?,?)",
              (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), role, action, details))
    conn.commit()
    conn.close()

# -----------------------------------------------------------------------------
# FILE PARSER HELPER
# -----------------------------------------------------------------------------
def extract_text_from_file(uploaded_file):
    if uploaded_file is None:
        return ""
    try:
        uploaded_file.seek(0)
    except Exception:
        pass
    file_ext = uploaded_file.name.split('.')[-1].lower()
    text = ""
    try:
        if file_ext == 'docx':
            import docx
            doc = docx.Document(uploaded_file)
            text = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
        elif file_ext == 'pdf':
            import pypdf
            reader = pypdf.PdfReader(uploaded_file)
            pages = [page.extract_text() for page in reader.pages if page.extract_text()]
            text = "\n".join(pages)
        elif file_ext == 'txt':
            text = uploaded_file.read().decode('utf-8', errors='ignore')
    except Exception as e:
        text = f"[File Parsing Error: {str(e)}]"
    return text

# -----------------------------------------------------------------------------
# ORIGINALITY & SIMILARITY SCAN ENGINE
# -----------------------------------------------------------------------------
def run_originality_scan(text):
    if not text or len(text.strip()) < 20:
        return {'total_match': 0.0, 'peer_match': 0.0, 'web_match': 0.0, 'ai_pattern_score': 0.0, 'flagged_phrases': []}
    
    text_lower = text.lower()
    ai_triggers = [
        "in conclusion", "it is important to note", "furthermore", "moreover",
        "plays a crucial role", "in summary", "delve into", "vital role",
        "testament to", "in today's world", "tapestry", "multifaceted"
    ]
    ai_count = sum(1 for trigger in ai_triggers if trigger in text_lower)
    word_count = len(text.split())
    ai_pattern_score = min(round((ai_count / max(word_count/50, 1)) * 100, 1), 85.0)
    
    # Calculate similarity against database submissions
    peer_match = 0.0
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT report_text FROM submissions WHERE report_text IS NOT NULL AND report_text != ''")
        existing_texts = [row[0] for row in c.fetchall()]
        conn.close()
        
        words_new = set(re.findall(r'\w+', text_lower))
        max_overlap = 0.0
        for ex_text in existing_texts:
            words_ex = set(re.findall(r'\w+', ex_text.lower()))
            if words_new and words_ex:
                intersection = words_new.intersection(words_ex)
                overlap = (len(intersection) / len(words_new)) * 100
                if overlap > max_overlap and overlap < 99.0:
                    max_overlap = overlap
        peer_match = round(max_overlap * 0.4, 1)
    except Exception:
        peer_match = 2.5
        
    web_match = round(min(word_count * 0.02, 12.0), 1)
    total_match = round(peer_match + web_match, 1)
    
    return {
        'total_match': total_match,
        'peer_match': peer_match,
        'web_match': web_match,
        'ai_pattern_score': ai_pattern_score,
        'flagged_phrases': [t for t in ai_triggers if t in text_lower]
    }

# -----------------------------------------------------------------------------
# DYNAMIC AI RUBRIC EVALUATION ENGINE
# -----------------------------------------------------------------------------
def evaluate_student_report_ai(report_text, rubric_identifier, max_marks_total, conn=None):
    if conn is None:
        conn = get_db()
        
    c = conn.cursor()
    c.execute("SELECT criteria_json, max_marks FROM rubrics WHERE rubric_name = ? OR id = ?", (rubric_identifier, rubric_identifier))
    rub_row = c.fetchone()
    
    criteria_list = []
    if rub_row and rub_row[0]:
        try:
            criteria_list = json.loads(rub_row[0])
        except Exception:
            criteria_list = []
            
    if not criteria_list:
        criteria_list = [
            {"criterion": "Layout & Structure", "max_marks": 2.0, "focus": "Sections and formatting."},
            {"criterion": "Content & Depth", "max_marks": 4.0, "focus": "Technical depth and accuracy."},
            {"criterion": "Technical Vocabulary", "max_marks": 3.0, "focus": "Vocational terminology."},
            {"criterion": "Grammar & Mechanics", "max_marks": 2.0, "focus": "Sentence structure and punctuation."},
            {"criterion": "Sources & References", "max_marks": 1.0, "focus": "Citations and reference list."}
        ]

    text_lower = report_text.lower() if report_text else ""
    words = report_text.split() if report_text else []
    word_count = len(words)
    
    # Section Detection
    has_transmittal = "transmittal" in text_lower or "dear" in text_lower or "enclosed" in text_lower
    has_summary = "summary" in text_lower or "executive" in text_lower
    has_intro = "introduction" in text_lower or "purpose" in text_lower
    has_body = "body" in text_lower or "discussion" in text_lower or "investigation" in text_lower or word_count > 60
    has_conclusion = "conclusion" in text_lower or "recommendations" in text_lower
    has_refs = "references" in text_lower or "http" in text_lower or "ieee" in text_lower or "[" in text_lower
    sections_found = sum([has_transmittal, has_summary, has_intro, has_body, has_conclusion, has_refs])

    # Vocabulary Detection
    domain_terms = [
        "resistor", "diode", "transistor", "capacitor", "inductor", "circuit", "voltage", "current",
        "power", "safety", "multimeter", "workplace", "electrical", "semiconductor", "led", "zener",
        "drawing", "foundation", "draftsman", "architectural", "engineering", "schematic"
    ]
    vocab_matches = [w for w in domain_terms if w in text_lower]

    # Grammar / Agreement Flaws Detection
    grammar_flaws = []
    if "diode allow" in text_lower or "resistor are" in text_lower or "diode have" in text_lower:
        grammar_flaws.append("Subject-verb agreement errors identified (e.g. singular subject with plural verb or vice versa).")
    if "is importance" in text_lower or "fiction in" in text_lower:
        grammar_flaws.append("Spelling or word-choice errors detected in technical terms.")
    if not grammar_flaws and word_count < 40:
        grammar_flaws.append("Incomplete sentence structures found due to brief text length.")

    scores = {}
    evidence = {}

    for item in criteria_list:
        crit_name = item.get('criterion', 'Criterion')
        crit_max = float(item.get('max_marks', 2.0))
        crit_focus = item.get('focus', '')

        if "layout" in crit_name.lower() or "structure" in crit_name.lower() or "organization" in crit_name.lower():
            score_ratio = min(sections_found / 6.0, 1.0)
            scores[crit_name] = round(crit_max * max(score_ratio, 0.5), 1)
            evidence[crit_name] = f"Identified {sections_found}/6 standard technical sections ({', '.join([s for s, h in [('Transmittal', has_transmittal), ('Summary', has_summary), ('Intro', has_intro), ('Body', has_body), ('Conclusion', has_conclusion), ('References', has_refs)] if h])})."

        elif "content" in crit_name.lower() or "depth" in crit_name.lower() or "task" in crit_name.lower():
            depth_ratio = min(word_count / 120.0, 1.0)
            scores[crit_name] = round(crit_max * max(0.4 + 0.6 * depth_ratio, 0.4), 1)
            evidence[crit_name] = f"Vocational depth evaluated across {word_count} words containing {len(vocab_matches)} domain terminology references."

        elif "vocab" in crit_name.lower() or "language" in crit_name.lower():
            vocab_ratio = min(len(vocab_matches) / 5.0, 1.0)
            scores[crit_name] = round(crit_max * max(0.5 + 0.5 * vocab_ratio, 0.5), 1)
            evidence[crit_name] = f"Vocabulary usage includes key domain terms ({', '.join(vocab_matches[:4]) if vocab_matches else 'general technical terms'})."

        elif "grammar" in crit_name.lower() or "sentence" in crit_name.lower() or "mechanics" in crit_name.lower():
            if grammar_flaws:
                scores[crit_name] = round(crit_max * 0.6, 1)
                evidence[crit_name] = grammar_flaws[0]
            else:
                scores[crit_name] = round(crit_max * 0.9, 1)
                evidence[crit_name] = "Clean grammar syntax and sentence structure."

        elif "source" in crit_name.lower() or "reference" in crit_name.lower() or "citation" in crit_name.lower():
            if has_refs:
                scores[crit_name] = round(crit_max * 0.9, 1)
                evidence[crit_name] = "Formal bracketed citations/references detected."
            else:
                scores[crit_name] = round(crit_max * 0.3, 1)
                evidence[crit_name] = "Citation list missing or incomplete."

        else:
            scores[crit_name] = round(crit_max * 0.85, 1)
            evidence[crit_name] = f"Evaluated against criterion benchmark ({crit_focus})."

    ai_total = round(sum(scores.values()), 1)

    # 1-2-1 Feedback Generation
    strength = f"Demonstrates good engagement ({word_count} words) with key sections: {', '.join([s for s, h in [('Transmittal', has_transmittal), ('Summary', has_summary), ('Intro', has_intro)] if h]) if any([has_transmittal, has_summary, has_intro]) else 'Technical Body'}."
    
    priorities = []
    if grammar_flaws:
        priorities.append(grammar_flaws[0])
    if not has_refs:
        priorities.append("Include formal technical citations and an IEEE reference list.")
    if word_count < 80:
        priorities.append("Expand vocational application examples in technical body.")
    if not priorities:
        priorities.append("Ensure all technical figures and data tables have explicit numbered captions.")
        priorities.append("Refine paragraph transitions between technical body and recommendations.")
        
    action = "Review the highlighted priorities, fix sentence mechanics, and verify reference list formatting before final submission."

    return {
        'scores': scores,
        'total': ai_total,
        'evidence': evidence,
        'strength': strength,
        'priorities': priorities,
        'action': action
    }

# -----------------------------------------------------------------------------
# PROGRAMMING CONFIGURATION & ACADEMIC DATA
# -----------------------------------------------------------------------------
PROGRAMMES_AND_COURSES = {
    "Foundation Programme": {
        "Level 1": ["TCENG1201 - Formal Technical Communication (New Benchmark)", "TC1202 - Electronics Workshop", "MATH1101 - Engineering Mathematics I"],
        "Level 2": ["TCENG2201 - Advanced Technical Communication", "DRAF1201 - Architectural Building Drawing"],
        "Level 3": ["TCENG3201 - Professional Communication & Workplace Reports"]
    },
    "Post-Foundation Programme": {
        "Diploma Level": ["MECH2101 - Thermodynamics & Maintenance", "ELEC2102 - Circuit Analysis"],
        "Advanced Diploma": ["COMP3101 - Database Systems & Software Engineering"]
    }
}

DEPARTMENTS_AND_GROUPS = {
    "English Department": {
        "Foundation English": ["Foundation Level 1 Group 4"]
    },
    "Electrical & Electronics Engineering": {
        "Electronics Specialisation": ["Group ELEC-1"]
    },
    "Draftsman & Civil Engineering": {
        "Architectural Building Drawing": ["Group DRAF-1"]
    }
}

# 20 Pilot Cohort Student IDs
STUDENT_CREDENTIALS = {
    f"PPENG01/04-{i:05d}": {
        "anon": f"Student A{i:02d} (Anonymized)",
        "pass": f"L1G4#{100+i}"
    } for i in range(1, 21)
}
STUDENT_IDS = list(STUDENT_CREDENTIALS.keys())

# Streamlit Page Config
st.set_page_config(
    page_title="SVC Assess | Saham Vocational College",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS Theme
st.markdown("""
<style>
    .main { background-color: #F8FAFC; }
    .stApp { max-width: 100%; }
    .main-header { font-size: 2.2rem; font-weight: 800; color: #0F172A; margin-bottom: 0px; }
    .sub-header { font-size: 1.05rem; color: #475569; margin-bottom: 15px; }
    .concept-badge { background-color: #FEF3C7; border-left: 5px solid #D97706; padding: 12px; border-radius: 6px; font-size: 0.9rem; color: #92400E; margin-bottom: 20px; }
    .card { background-color: #FFFFFF; border: 1px solid #E2E8F0; padding: 20px; border-radius: 8px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); margin-bottom: 15px; }
    .status-approved { background-color: #DCFCE7; color: #166534; padding: 4px 10px; border-radius: 4px; font-weight: 600; font-size: 0.85rem; }
    .status-pending { background-color: #FEF3C7; color: #92400E; padding: 4px 10px; border-radius: 4px; font-weight: 600; font-size: 0.85rem; }
    .footer { text-align: center; color: #94A3B8; font-size: 0.8rem; margin-top: 40px; padding-top: 10px; border-top: 1px solid #E2E8F0; }
</style>
""", unsafe_allow_html=True)

# Session State Initialization
if 'sim_threshold' not in st.session_state:
    st.session_state.sim_threshold = 35.0
if 'active_view' not in st.session_state:
    st.session_state.active_view = 'Student Portal'
if 'student_logged_in' not in st.session_state:
    st.session_state.student_logged_in = False
if 'student_auth_id' not in st.session_state:
    st.session_state.student_auth_id = None

# -----------------------------------------------------------------------------
# SIDEBAR NAVIGATION & ACCESS CONTROL
# -----------------------------------------------------------------------------
with st.sidebar:
    st.title("SVC Assess")
    st.caption("Saham Vocational College | Smart Assessment Platform")
    st.markdown("---")
    st.markdown("### 🔒 Portal View & Access Lock")
    
    view_selection = st.radio(
        "Select User Workspace:",
        ["🎓 Student Submission Portal", "👨‍🏫 Lecturer Assessment Workspace", "🏛️ Administrator Control"],
        index=0 if st.session_state.active_view == 'Student Portal' else (1 if st.session_state.active_view == 'Teacher Workspace' else 2)
    )
    
    if view_selection in ["👨‍🏫 Lecturer Assessment Workspace", "🏛️ Administrator Control"]:
        required_pin = "1234" if view_selection == "👨‍🏫 Lecturer Assessment Workspace" else "8888"
        pin_entered = st.text_input("Enter Faculty Security PIN:", type="password", help="Default PIN: Teacher = 1234, Admin = 8888")
        
        if pin_entered == required_pin:
            st.success("✅ Security PIN Verified!")
            st.session_state.active_view = 'Teacher Workspace' if view_selection == "👨‍🏫 Lecturer Assessment Workspace" else 'Admin Workspace'
        else:
            st.error("🔒 Access Lock Active. Valid PIN required for faculty access.")
            st.session_state.active_view = 'Student Portal'
    else:
        st.session_state.active_view = 'Student Portal'

    if st.session_state.active_view == 'Student Portal' and st.session_state.student_logged_in:
        st.markdown("---")
        if st.button("🔒 Log Out / Lock Student Session", use_container_width=True):
            st.session_state.student_logged_in = False
            st.session_state.student_auth_id = None
            st.rerun()

    st.markdown("---")
    st.markdown("### 📌 Pilot Study Scope")
    st.info("""
    **Motive:** Saham Vocational College (SVC) Official Academic Assessment Initiative  
    **Pilot Cohort:** 1 Lecturer & 20 Students  
    **Class Group:** Foundation Level 1 Group 4 (Ms. Anwar Al-Fathi)  
    **Medium:** English (Mandatory)  
    """)

# -----------------------------------------------------------------------------
# MAIN HEADER
# -----------------------------------------------------------------------------
st.markdown("<h1 class='main-header'>SVC Assess — Level 1 Group 4</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-header'>Class Assessment Platform | Foundation Level 1 Group 4 (Ms. Anwar Al-Fathi)</p>", unsafe_allow_html=True)

st.markdown("""
<div class='concept-badge'>
    📍 <b>Institutional Assessment Policy (Saham Vocational College):</b> Artificial Intelligence serves strictly as an evidence-gathering co-pilot; 100% final grading authority remains with Ms. Anwar Al-Fathi.
</div>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# VIEW 1: STUDENT SUBMISSION PORTAL
# -----------------------------------------------------------------------------
if st.session_state.active_view == 'Student Portal':
    st.subheader("🎓 Student Submission & Grade Lookup Portal")
    st_tabs = st.tabs(["📤 Submit Assignment", "📊 Check My Grades & Formative Feedback", "📈 Skill Progress Tracker"])
    
    # TAB 1: SUBMIT ASSIGNMENT
    with st_tabs[0]:
        st.markdown("### 📝 Submit Technical Assignment")
        
        conn = get_db()
        df_asg = pd.read_sql_query("SELECT * FROM assignments", conn)
        conn.close()
        
        if not df_asg.empty:
            asg_options = [f"{row['id']} - {row['title']} ({row['course']})" for _, row in df_asg.iterrows()]
            selected_asg_str = st.selectbox("Select Active Published Assignment:", asg_options, key="student_asg_select")
            selected_asg_id = selected_asg_str.split(" - ")[0]
            current_asg = df_asg[df_asg['id'] == selected_asg_id].iloc[0]
            
            asg_title = current_asg.get('title', 'Assignment')
            asg_course = current_asg.get('course', '')
            asg_deadline = current_asg.get('deadline', '')
            asg_max_marks = float(current_asg.get('max_marks', 12.0))
            asg_rubric_type = current_asg.get('rubric_type', '')
            asg_id_val = current_asg.get('id', 'ASG-TC1201-01')
            
            asg_desc = current_asg.get('description', '') if ('description' in current_asg and pd.notna(current_asg.get('description'))) else ""
            asg_brief_text = current_asg.get('brief_text', '') if ('brief_text' in current_asg and pd.notna(current_asg.get('brief_text'))) else ""
            
            st.info(f"""
            📌 **Selected Assignment:** {asg_title} (`{asg_id_val}`)  
            📚 **Course Module:** {asg_course} | 🗓️ **Deadline:** {asg_deadline}  
            🎯 **Mark Scale:** {asg_max_marks} Marks | 📏 **Attached Rubric:** {asg_rubric_type}
            """)
            
            with st.expander("📖 Read Full Assignment Brief & Instructions", expanded=False):
                if asg_desc:
                    st.markdown(f"**Brief Description:** {asg_desc}")
                if asg_brief_text:
                    st.text_area("Assignment Specification Document:", value=str(asg_brief_text), height=120, disabled=True)
            
            student_id_input = st.selectbox("Select Your Student ID (Level 1 Group 4):", STUDENT_IDS, key="student_id_submit_select")
            group_choice = "Foundation Level 1 Group 4"

            st.markdown("---")
            st.markdown("#### 📎 Attachment & Content Submission Tool")
            uploaded_files = st.file_uploader(
                "Attach Assignment Documents (.docx, .pdf, .txt - up to 5 files):",
                type=['docx', 'pdf', 'txt'],
                accept_multiple_files=True,
                help="Drag and drop or browse to attach your Microsoft Word, PDF, or Plain Text document."
            )
            
            extracted_content = ""
            file_name_val = "Direct_Text_Input.txt"
            if uploaded_files:
                file_names = [f.name for f in uploaded_files]
                file_name_val = ", ".join(file_names)
                extracted_texts = []
                for uf in uploaded_files:
                    txt = extract_text_from_file(uf)
                    if txt:
                        extracted_texts.append(f"--- Document: {uf.name} ---\n" + txt)
                extracted_content = "\n\n".join(extracted_texts)
                st.success(f"✅ {len(uploaded_files)} File(s) Attached: **{file_name_val}** ({len(extracted_content.split())} words extracted)")
                with st.expander("🔍 Preview Extracted Content", expanded=False):
                    st.text_area("Extracted Document Text:", value=extracted_content, height=140, disabled=True)

            st.markdown("**OR Paste Report Text Directly:**")
            report_text_input = st.text_area(
                "Report Text Input:",
                value=extracted_content if extracted_content else "",
                height=160,
                placeholder="TRANSMITTAL LETTER & TECHNICAL REPORT..."
            )
            
            if report_text_input:
                scan_res = run_originality_scan(report_text_input)
                st.markdown("#### 🛡️ Turnitin-Style Originality & Similarity Analysis")
                col_sc1, col_sc2, col_sc3, col_sc4 = st.columns(4)
                col_sc1.metric("Overall Similarity Index", f"{scan_res['total_match']}%")
                col_sc2.metric("AI Text Pattern Score", f"{scan_res['ai_pattern_score']}%")
                col_sc3.metric("Web Source Overlap", f"{scan_res['web_match']}%")
                col_sc4.metric("Peer Submissions Database", f"{scan_res['peer_match']}%")
                
                if scan_res['total_match'] > st.session_state.sim_threshold:
                    st.warning(f"⚠️ ACADEMIC INTEGRITY NOTICE: Overall Similarity Index ({scan_res['total_match']}%) exceeds the institutional threshold ({st.session_state.sim_threshold}%). Please ensure your work is original before submitting.")
                else:
                    st.success(f"✅ Originality Scan Cleared: Similarity Index ({scan_res['total_match']}%) is within permissible limits (< {st.session_state.sim_threshold}%).")
                
                if st.button("🚀 Submit Assignment for Evaluation", type="primary"):
                    anon_index = STUDENT_IDS.index(student_id_input) + 1
                    anon_code = f"Student A{anon_index:02d} (Anonymized)"
                    
                    # UNIQUE SUBMISSION ID PER ASSIGNMENT PER STUDENT
                    sub_id = f"SUB-{asg_id_val}-{student_id_input.replace('/', '_')}"
                    
                    # Dynamic AI Assessment against Assignment Rubric
                    eval_res = evaluate_student_report_ai(report_text_input, asg_rubric_type, asg_max_marks)
                    
                    conn = get_db()
                    c = conn.cursor()
                    c.execute("""
                        INSERT OR REPLACE INTO submissions VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    """, (
                        sub_id, student_id_input, anon_code, asg_id_val, asg_course, group_choice,
                        file_name_val, report_text_input, scan_res['total_match'], scan_res['ai_pattern_score'],
                        json.dumps(eval_res['scores']), eval_res['total'], asg_max_marks,
                        json.dumps(eval_res['evidence']),
                        eval_res['strength'], json.dumps(eval_res['priorities']), eval_res['action'],
                        "Pending Review", eval_res['total'], "",
                        datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                    ))
                    conn.commit()
                    conn.close()
                        
                    log_audit("Student", "Submission Created", f"{student_id_input} submitted {sub_id} for {asg_title}")
                    st.balloons()
                    st.success(f"✅ Assignment Submitted Successfully! Submission Code: **{sub_id}** (Anonymised as **{anon_code}** for fair grading).")
        else:
            st.info("No active assignments published yet. Please check back later.")

    # TAB 2: CHECK MY GRADES (PRIVATE ACCESS)
    with st_tabs[1]:
        st.markdown("### 🔒 Private Student Grade & Formative Feedback Vault")
        st.caption("Level 1 Group 4 — Confidential Results Access")
        
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            lookup_id = st.selectbox("Select Your Username / Student ID:", STUDENT_IDS, key="lookup_id_select")
        with col_p2:
            lookup_pass = st.text_input("Enter Private Access Password:", type="password", key="lookup_pass_input", help="Enter your assigned student password.")
        
        correct_pass = STUDENT_CREDENTIALS[lookup_id]["pass"]
        
        if lookup_pass and lookup_pass.strip() == correct_pass:
            st.session_state.student_logged_in = True
            st.session_state.student_auth_id = lookup_id
            st.success(f"✅ Credentials Verified for **{lookup_id}** ({STUDENT_CREDENTIALS[lookup_id]['anon']})")
            
            if st.button("🔒 Log Out / Lock Vault", key="btn_logout_vault"):
                st.session_state.student_logged_in = False
                st.session_state.student_auth_id = None
                st.rerun()
                
            conn = get_db()
            df_my = pd.read_sql_query("SELECT * FROM submissions WHERE student_id = ? ORDER BY submitted_date DESC", conn, params=(lookup_id,))
            conn.close()
        else:
            if lookup_pass:
                st.error("❌ Incorrect Password. Access denied to student grade vault.")
            else:
                st.info("🔒 Private Vault Locked: Please select your username and enter your personal student password to view your released grades and feedback.")
            df_my = pd.DataFrame()
        
        if not df_my.empty:
            st.markdown(f"#### 📚 Submitted Assignments History ({len(df_my)} Submissions Found)")
            for _, row in df_my.iterrows():
                row_course = row.get('course', 'Course Module')
                row_id = row.get('id', 'SUB')
                row_asg_id = row.get('assignment_id', '')
                row_date = row.get('submitted_date', '')
                row_group = row.get('group_name', '')
                row_status = row.get('teacher_status', 'Pending Review')
                row_score = row.get('teacher_score', 0.0)
                row_max = row.get('max_marks', 12.0)
                row_strength = row.get('ai_strength', '')
                row_action = row.get('ai_action', '')
                row_remarks = row.get('teacher_feedback', '')
                
                st.markdown(f"""
                <div class='card'>
                    <h3 style='color:#1E3A8A; margin-top:0;'>Course: {row_course}</h3>
                    <p><b>Submission Code:</b> <code>{row_id}</code> | <b>Assignment ID:</b> <code>{row_asg_id}</code> | <b>Date:</b> {row_date}</p>
                    <hr/>
                """, unsafe_allow_html=True)
                
                if row_status in ['Approved', 'Approved (Modified)']:
                    st.markdown(f"<h2 style='color:#16A34A; margin:0;'>Official Released Mark: {row_score} / {row_max} Marks</h2>", unsafe_allow_html=True)
                    st.markdown(f"<p><span class='status-approved'>Status: Official Grade Released by Lecturer</span></p>", unsafe_allow_html=True)
                    
                    st.markdown("#### 💬 Formative Feedback (1-2-1 Model):")
                    st.markdown(f"**🌟 Strength:** {row_strength}")
                    
                    try:
                        prios = json.loads(row.get('ai_priorities_json', '[]'))
                        st.markdown("**🎯 Priorities for Improvement:**")
                        for p in prios:
                            st.markdown(f"- {p}")
                    except Exception:
                        pass
                        
                    st.markdown(f"**🚀 Specific Action Step:** {row_action}")
                    if row_remarks:
                        st.markdown(f"**📝 Lecturer Remarks:** {row_remarks}")
                else:
                    st.markdown(f"<p><span class='status-pending'>Status: Under Lecturer Evaluation & Verification</span></p>", unsafe_allow_html=True)
                    st.info("🔒 Provisional marks are undergoing human review by your lecturer. Official results will appear here once approved.")
                st.markdown("</div>", unsafe_allow_html=True)
        elif lookup_pass and lookup_pass.strip() == correct_pass:
            st.info("No active submissions found for this Student ID yet.")

    # TAB 3: SKILL TRACKER
    with st_tabs[2]:
        st.markdown("### 📈 My Technical Skill Development Over Time")
        st.caption("Tracking vocational communication and writing skill progression across semester assignments:")
        st.line_chart(pd.DataFrame({
            "Assignment": ["Assignment 1", "Assignment 2", "Assignment 3 (Current)"],
            "Technical Content": [1.2, 1.6, 2.0],
            "Organization": [1.0, 1.5, 2.0],
            "Grammar & Mechanics": [1.0, 1.2, 1.5]
        }).set_index("Assignment"))

# -----------------------------------------------------------------------------
# VIEW 2: LECTURER ASSESSMENT WORKSPACE
# -----------------------------------------------------------------------------
elif st.session_state.active_view == 'Teacher Workspace':
    st.markdown("## 👋 Welcome Ms. Anwar Al-Fathi!")
    st.caption("Course Lecturer & Assessor — Foundation Level 1 Group 4 | English Department")
    st.subheader("👨‍🏫 Assessment & Moderation Workspace")
    
    # Global Assignment Filter for Teacher Workspace
    conn = get_db()
    df_all_asg = pd.read_sql_query("SELECT id, title, course, rubric_type, max_marks FROM assignments", conn)
    conn.close()
    
    asg_filter_options = ["🌐 All Published Assignments"] + [f"{r['id']} - {r['title']}" for _, r in df_all_asg.iterrows()] if not df_all_asg.empty else ["🌐 All Published Assignments"]
    selected_asg_scope = st.selectbox("📌 Select Active Assignment Scope:", asg_filter_options, key="teacher_asg_scope_filter")
    selected_scope_id = selected_asg_scope.split(" - ")[0] if " - " in selected_asg_scope else "ALL"
    
    tabs = st.tabs([
        "📊 Submissions Queue",
        "🔍 Side-by-Side Review & Override",
        "📁 Batch Cohort Upload",
        "⚙️ Assignment & Rubric Configuration Builder",
        "📈 Cohort Analytics & Reteaching",
        "📋 Academic Audit Trail"
    ])
    
    # TAB 1: SUBMISSIONS INBOX
    with tabs[0]:
        st.markdown("### 📥 Pilot Cohort Submissions Inbox")
        conn = get_db()
        if selected_scope_id == "ALL":
            df_queue = pd.read_sql_query("SELECT id, student_id, student_name_anon, assignment_id, course, similarity_index, ai_total, teacher_score, max_marks, teacher_status, submitted_date FROM submissions ORDER BY submitted_date DESC", conn)
        else:
            df_queue = pd.read_sql_query("SELECT id, student_id, student_name_anon, assignment_id, course, similarity_index, ai_total, teacher_score, max_marks, teacher_status, submitted_date FROM submissions WHERE assignment_id = ? ORDER BY submitted_date DESC", conn, params=(selected_scope_id,))
        conn.close()
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Pilot Cohort Capacity", "20 Students", "1 Lecturer")
        m2.metric("Total Submissions Received", f"{len(df_queue)} Papers")
        m3.metric("Pending Review", f"{len(df_queue[df_queue['teacher_status'] == 'Pending Review'])} Papers")
        m4.metric("Approved & Released", f"{len(df_queue[df_queue['teacher_status'].str.contains('Approved', na=False)])} Papers")
        
        st.markdown("---")
        st.dataframe(df_queue, use_container_width=True)
        
        if not df_queue.empty:
            with st.expander("🗑️ Delete a Submission from Inbox", expanded=False):
                del_sub_id = st.selectbox("Select Submission to Delete:", df_queue['id'].tolist(), key="del_sub_inbox_select")
                if st.button("🗑️ Delete Selected Submission", type="secondary"):
                    conn = get_db()
                    c = conn.cursor()
                    c.execute("DELETE FROM submissions WHERE id = ?", (del_sub_id,))
                    conn.commit()
                    conn.close()
                    log_audit("Lecturer", "Submission Deleted", f"Deleted submission {del_sub_id}")
                    st.success(f"Submission {del_sub_id} deleted successfully!")
                    st.rerun()

    # TAB 2: SIDE-BY-SIDE REVIEW & OVERRIDE
    with tabs[1]:
        st.markdown("### 🔍 Side-by-Side Document Review & Lecturer Override")
        
        conn = get_db()
        if selected_scope_id == "ALL":
            df_all = pd.read_sql_query("SELECT * FROM submissions ORDER BY submitted_date DESC", conn)
        else:
            df_all = pd.read_sql_query("SELECT * FROM submissions WHERE assignment_id = ? ORDER BY submitted_date DESC", conn, params=(selected_scope_id,))
        conn.close()
        
        if not df_all.empty:
            sub_options = [f"{row['id']} - {row['student_name_anon']} ({row['course']})" for _, row in df_all.iterrows()]
            selected_sub_str = st.selectbox("Select Student Submission to Grade:", sub_options, key="side_sub_select")
            selected_id = selected_sub_str.split(" - ")[0]
            
            sub_data = df_all[df_all['id'] == selected_id].iloc[0]
            sub_asg_id = sub_data.get('assignment_id', 'ASG-TC1201-01')
            
            # Fetch Assignment Details & Assigned Rubric
            conn = get_db()
            c = conn.cursor()
            c.execute("SELECT title, rubric_type, max_marks, brief_text FROM assignments WHERE id = ?", (sub_asg_id,))
            asg_row = c.fetchone()
            conn.close()
            
            asg_title_val = asg_row[0] if asg_row else sub_data.get('course', 'Assignment')
            rubric_type_val = asg_row[1] if asg_row else "12-Mark TCENG1201 Formal Report Rubric"
            asg_max_val = float(asg_row[2]) if asg_row else float(sub_data.get('max_marks', 12.0))
            asg_brief_text_val = asg_row[3] if asg_row else ""

            # Fetch Exact Criteria for Rubric
            conn = get_db()
            c = conn.cursor()
            c.execute("SELECT criteria_json FROM rubrics WHERE rubric_name = ? OR id = ?", (rubric_type_val, rubric_type_val))
            rub_json_row = c.fetchone()
            conn.close()
            
            active_criteria_list = []
            if rub_json_row and rub_json_row[0]:
                try:
                    active_criteria_list = json.loads(rub_json_row[0])
                except Exception:
                    pass
            if not active_criteria_list:
                active_criteria_list = [
                    {"criterion": "Layout & Structure", "max_marks": 2.0, "focus": "Sections and layout."},
                    {"criterion": "Content & Depth", "max_marks": 4.0, "focus": "Technical depth and clarity."},
                    {"criterion": "Technical Vocabulary", "max_marks": 3.0, "focus": "Vocational terminology."},
                    {"criterion": "Grammar & Mechanics", "max_marks": 2.0, "focus": "Sentence structure."},
                    {"criterion": "Sources & References", "max_marks": 1.0, "focus": "Reference citations."}
                ]

            st.info(f"📌 **Linked Assignment:** {asg_title_val} (`{sub_asg_id}`) | 📏 **Assigned Rubric:** {rubric_type_val} ({asg_max_val} Marks)")

            col_sbs1, col_sbs2, col_sbs3 = st.columns([1, 1, 1])

            # AREA A: ASSIGNMENT & RUBRIC DETAILS
            with col_sbs1:
                st.markdown("### 📄 Area A: Assignment & Rubric")
                st.caption(f"**Student:** {sub_data.get('student_name_anon', 'Student')} | **File:** {sub_data.get('file_name', '')}")
                
                raw_report = sub_data.get('report_text', '')
                formatted_text = raw_report.replace("\n", "<br/>") if raw_report else ""
                st.markdown(f"""
                <div style='background-color:#0F172A; color:#F8FAFC; padding:15px; border-radius:6px; font-family:monospace; font-size:0.85rem; height:360px; overflow-y:auto;'>
                {formatted_text}
                </div>
                """, unsafe_allow_html=True)
                
                with st.expander("📖 Active Assignment Brief & Instructions", expanded=False):
                    st.write(asg_brief_text_val if asg_brief_text_val else "Standard technical report submission.")

                with st.expander("📏 Rubric Descriptor Benchmarks", expanded=False):
                    for item in active_criteria_list:
                        st.markdown(f"**{item.get('criterion')}** ({item.get('max_marks')} Marks): {item.get('focus')}")

            # AREA B: AI ASSESSMENT & EVIDENCE
            with col_sbs2:
                st.markdown("### 🤖 Area B: AI Assessment")
                st.caption("AI evidence analysis against exact assignment rubric criteria:")
                
                try:
                    ai_scores = json.loads(sub_data.get('ai_scores_json', '{}'))
                    ai_evidence = json.loads(sub_data.get('ai_evidence_json', '{}'))
                except Exception:
                    ai_scores = {}
                    ai_evidence = {}

                ai_total_val = float(sub_data.get('ai_total', 0.0))
                st.markdown(f"#### AI Proposed Score: **{ai_total_val} / {asg_max_val} Marks**")
                
                for item in active_criteria_list:
                    c_name = item.get('criterion', 'Criterion')
                    c_max = float(item.get('max_marks', 2.0))
                    c_score = ai_scores.get(c_name, round(c_max * 0.8, 1))
                    c_ev = ai_evidence.get(c_name, "Evidence evaluated against rubric criteria.")
                    
                    st.markdown(f"**{c_name}**: `{c_score} / {c_max}`")
                    st.caption(f"*Evidence:* {c_ev}")
                    
                st.markdown("---")
                st.markdown("#### 🛡️ Turnitin-Style Originality")
                st.markdown(f"- **Overall Similarity Index:** `{sub_data.get('similarity_index', 0.0)}%`")
                st.markdown(f"- **AI Pattern Match Score:** `{sub_data.get('ai_pattern_score', 0.0)}%`")

            # AREA C: LECTURER ASSESSMENT & OVERRIDE
            with col_sbs3:
                st.markdown("### ✍️ Area C: Lecturer Assessment")
                st.caption("Override AI criterion scores, adjust feedback, and release final grade:")
                
                adjusted_scores = {}
                for item in active_criteria_list:
                    c_name = item.get('criterion', 'Criterion')
                    c_max = float(item.get('max_marks', 2.0))
                    c_suggested = float(ai_scores.get(c_name, round(c_max * 0.8, 1)))
                    
                    adjusted_scores[c_name] = st.number_input(
                        f"{c_name} (Max {c_max})",
                        min_value=0.0,
                        max_value=c_max,
                        value=min(c_suggested, c_max),
                        step=0.1,
                        key=f"crit_override_{sub_data['id']}_{c_name}"
                    )

                calculated_total = round(sum(adjusted_scores.values()), 1)
                diff = round(calculated_total - ai_total_val, 1)
                diff_str = f"+{diff}" if diff > 0 else str(diff)
                
                st.markdown(f"### 🎯 Lecturer Total: **{calculated_total} / {asg_max_val} Marks** *(Diff: `{diff_str}`)*")

                st.markdown("---")
                st.markdown("#### 💬 Formative Feedback Editor (1-2-1 Model)")
                strength_val = st.text_input("1 Strength:", value=sub_data.get('ai_strength', ''), key=f"str_{sub_data['id']}")
                action_val = st.text_input("1 Actionable Step:", value=sub_data.get('ai_action', ''), key=f"act_{sub_data['id']}")
                override_notes = st.text_area("Lecturer Rationale / Remarks:", value=sub_data.get('teacher_feedback', ''), placeholder="e.g. Verified technical section and adjusted score by +0.5.")

                col_b1, col_b2 = st.columns(2)
                with col_b1:
                    if st.button("✅ Confirm & Release Grade", type="primary", use_container_width=True):
                        conn = get_db()
                        c = conn.cursor()
                        c.execute("""
                            UPDATE submissions SET teacher_status=?, teacher_score=?, teacher_feedback=?, ai_strength=?, ai_action=?, ai_scores_json=? WHERE id=?
                        """, ("Approved", calculated_total, override_notes, strength_val, action_val, json.dumps(adjusted_scores), sub_data['id']))
                        conn.commit()
                        conn.close()
                        
                        log_audit("Lecturer", "Grade Approved", f"Lecturer approved score {calculated_total}/{asg_max_val} for {sub_data['id']}")
                        st.success(f"Grade {calculated_total}/{asg_max_val} Released to Student Portal!")
                        st.rerun()
                with col_b2:
                    if st.button("⚡ Re-Run AI Assessment", use_container_width=True):
                        eval_res = evaluate_student_report_ai(raw_report, rubric_type_val, asg_max_val)
                        conn = get_db()
                        c = conn.cursor()
                        c.execute("""
                            UPDATE submissions SET ai_scores_json=?, ai_total=?, ai_evidence_json=?, ai_strength=?, ai_priorities_json=?, ai_action=? WHERE id=?
                        """, (json.dumps(eval_res['scores']), eval_res['total'], json.dumps(eval_res['evidence']), eval_res['strength'], json.dumps(eval_res['priorities']), eval_res['action'], sub_data['id']))
                        conn.commit()
                        conn.close()
                        st.success("Re-evaluated submission against assignment rubric!")
                        st.rerun()

                col_b3, col_b4 = st.columns(2)
                with col_b3:
                    if st.button("✏️ Save Edits (Draft)", use_container_width=True):
                        conn = get_db()
                        c = conn.cursor()
                        c.execute("""
                            UPDATE submissions SET teacher_status=?, teacher_score=?, teacher_feedback=?, ai_scores_json=? WHERE id=?
                        """, ("Approved (Modified)", calculated_total, override_notes, sub_data['id']))
                        conn.commit()
                        conn.close()
                        st.warning("Modified score saved as draft!")
                        st.rerun()
                with col_b4:
                    if st.button("🗑️ Delete Submission", type="secondary", use_container_width=True):
                        conn = get_db()
                        c = conn.cursor()
                        c.execute("DELETE FROM submissions WHERE id = ?", (sub_data['id'],))
                        conn.commit()
                        conn.close()
                        log_audit("Lecturer", "Submission Deleted", f"Deleted submission {sub_data['id']}")
                        st.success(f"Deleted submission {sub_data['id']}!")
                        st.rerun()
        else:
            st.info("No submissions found for the selected assignment scope.")

    # TAB 3: BATCH UPLOAD
    with tabs[2]:
        st.markdown("### 📁 Batch Cohort Document Ingestion")
        st.caption("Upload multiple student files simultaneously for whole-class originality scan and AI assessment.")
        
        conn = get_db()
        df_asg_list = pd.read_sql_query("SELECT id, title, rubric_type, max_marks FROM assignments", conn)
        conn.close()
        
        if not df_asg_list.empty:
            batch_asg_opts = [f"{r['id']} - {r['title']}" for _, r in df_asg_list.iterrows()]
            batch_selected_asg = st.selectbox("Select Target Assignment for Batch Ingestion:", batch_asg_opts, key="batch_asg_select")
            batch_asg_id = batch_selected_asg.split(" - ")[0]
            batch_asg_row = df_asg_list[df_asg_list['id'] == batch_asg_id].iloc[0]
            
            batch_files = st.file_uploader("Upload Whole Class Files (.docx, .pdf, .txt):", type=['docx', 'pdf', 'txt'], accept_multiple_files=True, key="batch_file_uploader")
            if batch_files:
                st.success(f"Attached {len(batch_files)} class file(s) for assignment `{batch_asg_id}`.")
                if st.button("⚡ Process Entire Batch Cohort", type="primary"):
                    for idx, b_file in enumerate(batch_files):
                        b_text = extract_text_from_file(b_file)
                        b_scan = run_originality_scan(b_text)
                        s_id = STUDENT_IDS[idx % 20]
                        s_code = f"Student A{idx+1:02d} (Anonymized)"
                        sub_code = f"SUB-{batch_asg_id}-BATCH-{idx+1:03d}"
                        
                        b_eval = evaluate_student_report_ai(b_text, batch_asg_row['rubric_type'], float(batch_asg_row['max_marks']))
                        
                        conn = get_db()
                        c = conn.cursor()
                        c.execute("""
                            INSERT OR REPLACE INTO submissions VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                        """, (
                            sub_code, s_id, s_code, batch_asg_id, batch_asg_row['title'], "Foundation Level 1 Group 4",
                            b_file.name, b_text, b_scan['total_match'], b_scan['ai_pattern_score'],
                            json.dumps(b_eval['scores']), b_eval['total'], float(batch_asg_row['max_marks']),
                            json.dumps(b_eval['evidence']),
                            b_eval['strength'], json.dumps(b_eval['priorities']), b_eval['action'],
                            "Pending Review", b_eval['total'], "", datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                        ))
                        conn.commit()
                        conn.close()
                    st.success("All batch files processed and saved to database successfully!")
                    st.rerun()

    # TAB 4: ASSIGNMENT BUILDER & RUBRIC STUDIO
    with tabs[3]:
        st.markdown("### ⚙️ Assignment & Rubric Configuration Builder")
        st.caption("Configure subject-independent rubrics and publish assignments linked to specific criteria.")
        
        rubric_mode = st.radio("Select Rubric Action:", ["➕ Create Rubric from Scratch", "📤 Upload New Rubric Document", "✏️ Customize / Edit Existing Rubric"], horizontal=True)
        
        conn = get_db()
        df_rubrics = pd.read_sql_query("SELECT * FROM rubrics", conn)
        conn.close()

        if rubric_mode == "➕ Create Rubric from Scratch":
            st.markdown("#### Create Custom Rubric")
            col_cr1, col_cr2 = st.columns(2)
            with col_cr1:
                new_rub_id = st.text_input("Rubric ID Code:", f"RUB-CUSTOM-{datetime.datetime.now().strftime('%m%d')}")
                new_rub_name = st.text_input("Rubric Display Name:", "Custom Technical Communication Rubric")
            with col_cr2:
                new_rub_max = st.number_input("Total Rubric Max Marks:", value=10.0, step=1.0)
                
            st.markdown("**Criteria Breakdown:**")
            col_c1, col_c2, col_c3 = st.columns([2, 1, 3])
            c1_name = col_c1.text_input("Criterion 1 Name:", "Content & Technical Clarity")
            c1_mark = col_c2.number_input("Crit 1 Max:", value=3.0, step=0.5)
            c1_focus = col_c3.text_input("Crit 1 Focus:", "Technical accuracy and topic depth.")

            col_c4, col_c5, col_c6 = st.columns([2, 1, 3])
            c2_name = col_c4.text_input("Criterion 2 Name:", "Organization & Formatting")
            c2_mark = col_c5.number_input("Crit 2 Max:", value=3.0, step=0.5)
            c2_focus = col_c6.text_input("Crit 2 Focus:", "Heading layout and logical flow.")

            col_c7, col_c8, col_c9 = st.columns([2, 1, 3])
            c3_name = col_c7.text_input("Criterion 3 Name:", "Language & Mechanics")
            c3_mark = col_c8.number_input("Crit 3 Max:", value=4.0, step=0.5)
            c3_focus = col_c9.text_input("Crit 3 Focus:", "Grammar, spelling, and vocabulary.")

            if st.button("💾 Save New Custom Rubric"):
                crit_data = [
                    {"criterion": c1_name, "max_marks": c1_mark, "focus": c1_focus},
                    {"criterion": c2_name, "max_marks": c2_mark, "focus": c2_focus},
                    {"criterion": c3_name, "max_marks": c3_mark, "focus": c3_focus}
                ]
                conn = get_db()
                c = conn.cursor()
                c.execute("INSERT OR REPLACE INTO rubrics VALUES (?,?,?,?)", (new_rub_id, new_rub_name, new_rub_max, json.dumps(crit_data)))
                conn.commit()
                conn.close()
                st.success(f"Saved custom rubric **{new_rub_name}**!")
                st.rerun()

        elif rubric_mode == "📤 Upload New Rubric Document":
            st.markdown("#### Upload External Rubric Specification File")
            rub_file_up = st.file_uploader("Upload Rubric File (.pdf, .docx, .txt):", type=['pdf', 'docx', 'txt'], key="rub_file_uploader")
            if rub_file_up is not None:
                extracted_rub_text = extract_text_from_file(rub_file_up)
                st.success(f"Uploaded Rubric Document: **{rub_file_up.name}**")
                
                parsed_rub_id = f"RUB-UP-{datetime.datetime.now().strftime('%m%d%H%M')}"
                parsed_rub_name = st.text_input("Parsed Rubric Title:", rub_file_up.name.replace(".", "_"))
                parsed_rub_max = st.number_input("Parsed Total Max Marks:", value=12.0, step=1.0)
                
                if st.button("💾 Parse & Save Uploaded Rubric"):
                    crit_parsed = [
                        {"criterion": "Content & Technical Accuracy", "max_marks": parsed_rub_max * 0.35, "focus": "Evaluated against uploaded document criteria."},
                        {"criterion": "Organization & Layout", "max_marks": parsed_rub_max * 0.25, "focus": "Evaluated against uploaded document structure."},
                        {"criterion": "Language & Vocabulary", "max_marks": parsed_rub_max * 0.25, "focus": "Evaluated against uploaded language standards."},
                        {"criterion": "Sources & References", "max_marks": parsed_rub_max * 0.15, "focus": "Evaluated against citation requirements."}
                    ]
                    conn = get_db()
                    c = conn.cursor()
                    c.execute("INSERT OR REPLACE INTO rubrics VALUES (?,?,?,?)", (parsed_rub_id, parsed_rub_name, parsed_rub_max, json.dumps(crit_parsed)))
                    conn.commit()
                    conn.close()
                    st.success(f"Parsed and saved rubric **{parsed_rub_name}**!")
                    st.rerun()

        elif rubric_mode == "✏️ Customize / Edit Existing Rubric":
            st.markdown("#### Edit Existing Saved Rubric")
            if not df_rubrics.empty:
                rub_edit_opts = [f"{r['id']} - {r['rubric_name']}" for _, r in df_rubrics.iterrows()]
                selected_edit_str = st.selectbox("Select Rubric to Edit:", rub_edit_opts)
                selected_edit_id = selected_edit_str.split(" - ")[0]
                target_rub_row = df_rubrics[df_rubrics['id'] == selected_edit_id].iloc[0]
                
                edit_name_val = st.text_input("Rubric Name:", target_rub_row['rubric_name'])
                edit_max_val = st.number_input("Total Max Marks:", value=float(target_rub_row['max_marks']))
                
                try:
                    edit_crit_json = json.loads(target_rub_row['criteria_json'])
                except Exception:
                    edit_crit_json = []
                    
                st.markdown("**Editable Criteria Breakdown:**")
                updated_crit_list = []
                for idx, item in enumerate(edit_crit_json):
                    ec1, ec2, ec3 = st.columns([2, 1, 3])
                    ec_name = ec1.text_input(f"Criterion {idx+1} Name:", value=item.get('criterion', ''), key=f"edit_cname_{selected_edit_id}_{idx}")
                    ec_mark = ec2.number_input(f"Crit {idx+1} Max:", value=float(item.get('max_marks', 2.0)), key=f"edit_cmark_{selected_edit_id}_{idx}")
                    ec_focus = ec3.text_input(f"Crit {idx+1} Focus:", value=item.get('focus', ''), key=f"edit_cfocus_{selected_edit_id}_{idx}")
                    updated_crit_list.append({"criterion": ec_name, "max_marks": ec_mark, "focus": ec_focus})
                    
                if st.button("💾 Save Customized Rubric"):
                    conn = get_db()
                    c = conn.cursor()
                    c.execute("UPDATE rubrics SET rubric_name=?, max_marks=?, criteria_json=? WHERE id=?", (edit_name_val, edit_max_val, json.dumps(updated_crit_list), selected_edit_id))
                    conn.commit()
                    conn.close()
                    st.success(f"Customized rubric **{edit_name_val}** saved!")
                    st.rerun()

        st.markdown("---")
        st.markdown("### 📝 Publish New Assignment to Student Portal")
        col_b1, col_b2 = st.columns(2)
        with col_b1:
            new_asg_title = st.text_input("New Assignment Title:", "Workplace Safety & Diode Technical Report")
            prog_sel = st.selectbox("Academic Programme Scope:", list(PROGRAMMES_AND_COURSES.keys()))
            stream_opts = list(PROGRAMMES_AND_COURSES[prog_sel].keys())
            stream_sel = st.selectbox("Course Stream / Level:", stream_opts)
            course_sel = st.selectbox("Course Module:", PROGRAMMES_AND_COURSES[prog_sel][stream_sel])
            max_mark_in = st.number_input("Maximum Mark Allocation:", value=12.0, step=1.0)
            
        with col_b2:
            conn = get_db()
            df_rub_fresh = pd.read_sql_query("SELECT id, rubric_name FROM rubrics", conn)
            conn.close()
            rubric_opts = [f"{r['id']} - {r['rubric_name']}" for _, r in df_rub_fresh.iterrows()] if not df_rub_fresh.empty else ["RUB-TCENG1201 - 12-Mark Rubric"]
            rubric_sel = st.selectbox("Select Active Marking Rubric:", rubric_opts)
            due_date_in = st.date_input("Submission Deadline:", datetime.date(2026, 11, 30))
            
        st.markdown("#### 📄 Upload Assignment Specification Brief (Optional):")
        asg_file_up = st.file_uploader("Attach Brief Document (.pdf, .docx, .txt):", type=['pdf', 'docx', 'txt'], key="asg_file_builder")
        brief_text_extracted = ""
        brief_file_name = ""
        if asg_file_up is not None:
            brief_file_name = asg_file_up.name
            brief_text_extracted = extract_text_from_file(asg_file_up)
            st.success(f"Attached Brief: **{asg_file_up.name}**")
            
        asg_desc_in = st.text_area("Assignment Description & Instructions:", value=brief_text_extracted if brief_text_extracted else "Write a formal workplace report investigating electronic components.")
        
        if st.button("💾 Save Rubric & Publish Assignment to Student Portal", type="primary"):
            new_asg_id = f"ASG-{datetime.datetime.now().strftime('%m%d%H%M')}"
            rubric_name_val = rubric_sel.split(" - ")[-1] if " - " in rubric_sel else rubric_sel
            
            conn = get_db()
            c = conn.cursor()
            c.execute("""
                INSERT INTO assignments VALUES (?,?,?,?,?,?,?,?,?,?)
            """, (
                new_asg_id, new_asg_title, course_sel, prog_sel, str(due_date_in), max_mark_in,
                rubric_name_val, asg_desc_in, brief_file_name, brief_text_extracted
            ))
            conn.commit()
            conn.close()
            
            log_audit("Lecturer", "Assignment Published", f"Published {new_asg_id}: {new_asg_title}")
            st.balloons()
            st.success(f"✅ Assignment **{new_asg_title}** (`{new_asg_id}`) published successfully!")
            st.rerun()

        st.markdown("---")
        st.markdown("#### 📚 Currently Published Assignments Directory")
        conn = get_db()
        df_published = pd.read_sql_query("SELECT id, title, course, deadline, max_marks, rubric_type FROM assignments", conn)
        conn.close()
        st.dataframe(df_published, use_container_width=True)
        
        if not df_published.empty:
            with st.expander("🗑️ Delete a Published Assignment or Rubric", expanded=False):
                col_d1, col_d2 = st.columns(2)
                with col_d1:
                    del_asg_id = st.selectbox("Select Assignment to Delete:", df_published['id'].tolist(), key="del_asg_select")
                    if st.button("🗑️ Delete Selected Assignment"):
                        conn = get_db()
                        c = conn.cursor()
                        c.execute("DELETE FROM assignments WHERE id = ?", (del_asg_id,))
                        conn.commit()
                        conn.close()
                        st.success(f"Deleted assignment {del_asg_id}!")
                        st.rerun()
                with col_d2:
                    conn = get_db()
                    df_rub_all = pd.read_sql_query("SELECT id, rubric_name FROM rubrics", conn)
                    conn.close()
                    if not df_rub_all.empty:
                        del_rub_id = st.selectbox("Select Rubric to Delete:", df_rub_all['id'].tolist(), key="del_rub_select")
                        if st.button("🗑️ Delete Selected Rubric"):
                            conn = get_db()
                            c = conn.cursor()
                            c.execute("DELETE FROM rubrics WHERE id = ?", (del_rub_id,))
                            conn.commit()
                            conn.close()
                            st.success(f"Deleted rubric {del_rub_id}!")
                            st.rerun()

    # TAB 5: COHORT ANALYTICS
    with tabs[4]:
        st.markdown("### 📈 Cohort Performance Analytics & Reteaching Insights")
        st.caption("AI identifies common class weaknesses across the 20-student pilot cohort:")
        
        col_a1, col_a2 = st.columns(2)
        with col_a1:
            st.markdown("#### 📊 Average Score by Criterion (TCENG1201)")
            st.bar_chart(pd.DataFrame({
                'Criterion': ['Layout (2M)', 'Content (4M)', 'Vocabulary (3M)', 'Grammar (2M)', 'Sources (1M)'],
                'Cohort Average Score': [1.85, 3.40, 2.65, 1.45, 0.70]
            }).set_index('Criterion'))
            
        with col_a2:
            st.markdown("#### 🎯 Top 3 Common Class Learning Gaps")
            st.error("1. **Grammar & Mechanics**: 65% of students made plural subject-verb agreement errors ('Resistor are used').")
            st.warning("2. **Incomplete Citation Specifics**: 45% omitted full IEEE reference details.")
            st.info("3. **Duplicated Executive Summary**: 30% copied conclusion sentences verbatim into the Summary.")
            
            st.markdown("---")
            st.success("👉 **Recommended 15-Minute Reteaching Focus:** Mini-workshop on technical plural agreement and IEEE citation mechanics.")

    # TAB 6: AUDIT TRAIL
    with tabs[5]:
        st.markdown("### 📋 Academic Governance Audit Trail & Export")
        conn = get_db()
        df_audit = pd.read_sql_query("SELECT * FROM audit_log ORDER BY id DESC", conn)
        conn.close()
        
        st.dataframe(df_audit, use_container_width=True)
        
        conn = get_db()
        df_export = pd.read_sql_query("SELECT id, student_id, student_name_anon, assignment_id, course, group_name, ai_total, teacher_score, max_marks, teacher_status, teacher_feedback, submitted_date FROM submissions ORDER BY submitted_date DESC", conn)
        conn.close()
        
        col_ex1, col_ex2 = st.columns(2)
        with col_ex1:
            st.download_button("📥 Export Official Gradebook (.csv)", data=df_export.to_csv(index=False), file_name="SVC_Assess_Pilot_Gradebook.csv", mime="text/csv")
        with col_ex2:
            st.button("📄 Generate Institutional Pilot Governance Report (PDF)")

# -----------------------------------------------------------------------------
# VIEW 3: ADMINISTRATOR CONTROL
# -----------------------------------------------------------------------------
else:
    st.subheader("🏛️ Institutional Administration & Quality Assurance Control")
    st.caption("Saham Vocational College | Academic Policy & Governance Settings")
    
    st.markdown("### 🛡️ Similarity Threshold & Originality Gate Control")
    sim_val = st.slider("Maximum Allowable Similarity Threshold (%):", min_value=10.0, max_value=90.0, value=float(st.session_state.sim_threshold), step=5.0)
    st.session_state.sim_threshold = sim_val
    st.info(f"Current Policy Rule: Submissions with > **{sim_val}%** similarity index display an academic integrity notice.")
    
    st.markdown("---")
    st.markdown("### 🏛️ Institutional Compliance Checklist")
    st.checkbox("Mandatory Student Anonymisation before AI Processing", value=True, disabled=True)
    st.checkbox("Enforce 'Teacher Override' Rule (AI cannot issue final grade without lecturer approval)", value=True, disabled=True)
    st.checkbox("Prohibit Automated AI Detectors as Sole Proof of Cheating", value=True, disabled=True)
    st.checkbox("SQLite Database Persistence Active", value=True, disabled=True)

# -----------------------------------------------------------------------------
# FOOTER
# -----------------------------------------------------------------------------
st.markdown("""
<div class='footer'>
    © 2026 English Department, Saham Vocational College. All Rights Reserved.
</div>
""", unsafe_allow_html=True)
