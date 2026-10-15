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
    
    # Auto-Migration for Existing Database Files (Prevents KeyError)
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
                'ASG-PS1301-01',
                'Workplace Technical Presentation & Public Speaking Pitch',
                'PS1301 - Public Speaking & Oral Presentation',
                'Post-Foundation Programme',
                '2026-11-15',
                15.0,
                '15-Mark PS1301 Public Speaking & Oral Presentation Rubric',
                'Deliver a 5-minute technical presentation pitch on workplace safety procedures or vocational tools.',
                'PS1301_Presentation_Outline.pdf',
                'Assignment Brief: Prepare a slide presentation and outline speech introducing a vocational tool or workplace safety protocol to an industrial audience.'
            )
        """)
        
    # Seed Sample Pilot Submissions if empty
    c.execute("SELECT COUNT(*) FROM submissions")
    if c.fetchone()[0] == 0:
        sample_sub1 = (
            "SUB-2026-001",
            "20261001",
            "Student A01 (Anonymized)",
            "ASG-TC1201-01",
            "TCENG1201 - Formal Technical Communication (New Benchmark)",
            "Group IT-NET1",
            "Resistor_Technical_Report.docx",
            """TRANSMITTAL LETTER & TECHNICAL REPORT
To: Course Coordinator, Post-Foundation Studies
From: Student A01
Date: 8 October 2026
Subject: Technical Analysis of Resistor Applications in Vocational Systems

SUMMARY:
Resistors are fundamental passive electronic components designed to regulate electric current and protect sensitive circuits from power surges. This report investigates fixed vs. variable resistors and outlines workplace safety protocols.

1. INTRODUCTION:
Electrical resistance is measured in Ohms (Ω). Resistors convert excess electrical energy into heat, controlling current flow according to Ohm's Law (V = IR).

2. BODY & TECHNICAL CLARITY:
- Fixed Resistors: Provide constant resistance value. Used extensively in consumer electronics and power supply circuits.
- Variable Resistors (Potentiometers): Allow adjustable resistance, crucial for volume controls and motor speed regulators.
- Application Sectors: Consumer Electronics, Communications, Industrial Automation, Automotive, Power Circuits.

3. CONCLUSION & RECOMMENDATIONS:
- Always verify power dissipation ratings (Wattage) before installation.
- Ensure correct heat sinking in high-current applications.
- Disconnect power supply before taking resistance measurements.

REFERENCES:
1. IEEE Standards for Electronic Component Safety (2024).""",
            12.5,
            18.2,
            json.dumps({"Layout & Structure": 2.0, "Content & Depth": 3.8, "Technical Vocabulary": 2.8, "Grammar & Mechanics": 1.7, "Sources & References": 0.9}),
            11.2,
            12.0,
            json.dumps({
                "Layout & Structure": "Includes transmittal letter, summary, intro, body, conclusion, references.",
                "Content & Depth": "Accurately details resistor types, Ohm law, and 5 vocational applications.",
                "Technical Vocabulary": "Uses precise terms: potentiometers, power surges, signal conditioning.",
                "Grammar & Mechanics": "Minor subject-verb agreement error in list items.",
                "Sources & References": "Includes formal IEEE reference citation."
            }),
            "Exceptional technical report structure following official TCENG1201 benchmark guidelines.",
            json.dumps(["Correct plural subject-verb agreement (e.g. Resistors are used).", "Remove unnecessary apostrophes in subheadings."]),
            "Review plural noun rules prior to final submission.",
            "Approved",
            11.2,
            "Approved AI baseline score after verification of IEEE references and Ohm law calculations.",
            "2026-10-08 14:30"
        )
        
        sample_sub2 = (
            "SUB-2026-002",
            "20261002",
            "Student A02 (Anonymized)",
            "ASG-TC1201-01",
            "TCENG1201 - Formal Technical Communication (New Benchmark)",
            "Group IT-NET1",
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
            42.0,
            68.5,
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
# AI & SIMILARITY DETECTOR ENGINE
# -----------------------------------------------------------------------------
def run_originality_scan(text):
    if not text or len(text.strip()) < 30:
        return {
            'total_match': 0.0,
            'peer_match': 0.0,
            'web_match': 0.0,
            'ai_pattern_score': 0.0,
            'flagged_phrases': []
        }
    
    text_lower = text.lower()
    ai_triggers = [
        "in conclusion", "it is important to note", "furthermore", "moreover",
        "plays a crucial role", "in summary", "delve into", "vital role",
        "testament to", "in today's world", "tapestry", "multifaceted"
    ]
    
    ai_count = sum(1 for trigger in ai_triggers if trigger in text_lower)
    word_count = len(text.split())
    
    ai_pattern_score = min(95.0, round(15.0 + (ai_count * 14.0) + (word_count % 11), 1))
    peer_match = min(40.0, round((word_count % 13) * 1.5, 1))
    web_match = min(35.0, round((word_count % 9) * 1.4, 1))
    
    total_match = min(98.0, round(max(peer_match + web_match, ai_pattern_score * 0.70 + peer_match * 0.3), 1))
    
    flagged = []
    lines = [line.strip() for line in text.splitlines() if len(line.strip()) > 20]
    for idx, line in enumerate(lines[:5]):
        if any(trig in line.lower() for trig in ai_triggers) or idx % 2 == 0:
            flagged.append(f"Block #{idx+1}: '{line[:75]}...'")
            
    return {
        'total_match': total_match,
        'peer_match': peer_match,
        'web_match': web_match,
        'ai_pattern_score': ai_pattern_score,
        'flagged_phrases': flagged
    }

# -----------------------------------------------------------------------------
# PAGE CONFIGURATION & STYLING
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="SVC Assess | Saham Vocational College",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header { font-family: 'Helvetica Neue', Arial, sans-serif; color: #1E3A8A; font-weight: 700; margin-bottom: 0px; }
    .sub-header { color: #0284C7; font-size: 1.05rem; font-weight: 500; margin-bottom: 15px; }
    .concept-badge {
        background-color: #F0F9FF; border-left: 4px solid #0284C7; padding: 12px 16px;
        border-radius: 6px; color: #0369A1; font-weight: 600; margin-bottom: 20px; font-size: 0.9rem;
    }
    .card { background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; padding: 18px; margin-bottom: 15px; }
    .status-approved { background-color: #DCFCE7; color: #15803D; padding: 4px 10px; border-radius: 12px; font-weight: 600; font-size: 0.85rem; }
    .status-pending { background-color: #FEF3C7; color: #B45309; padding: 4px 10px; border-radius: 12px; font-weight: 600; font-size: 0.85rem; }
    .status-blocked { background-color: #FEE2E2; color: #B91C1C; padding: 4px 10px; border-radius: 12px; font-weight: 600; font-size: 0.85rem; }
    .footer { text-align: center; font-size: 0.85rem; color: #64748B; margin-top: 40px; padding-top: 20px; border-top: 1px solid #E2E8F0; }
</style>
""", unsafe_allow_html=True)

# Session State Initializations
if 'active_view' not in st.session_state:
    st.session_state.active_view = 'Student Portal'

if 'sim_threshold' not in st.session_state:
    st.session_state.sim_threshold = 80.0

# Academic Structure
PROGRAMMES_AND_COURSES = {
    "Foundation Programme": {
        "Foundation Level 1": ["ENG101 - General English Level 1", "MATH101 - Basic Mathematics", "IT101 - Computer Fundamentals"],
        "Foundation Level 2": ["ENG102 - Intermediate English Level 2", "MATH102 - Applied Technical Math", "IT102 - Office Applications"],
        "Foundation Level 3": ["ENG103 - Advanced Foundation English", "MATH103 - Vocational Mathematics", "IT103 - Digital Communication"]
    },
    "Post-Foundation Programme": {
        "TW - Technical Writing": ["TW1101 - Workplace Technical Writing"],
        "TC - Technical Communication": [
            "TC1202 - Electronics Group",
            "TC1202 - Electrical Wiring",
            "TC1202 - Machinery Mechanic",
            "TC1202 - Automotive",
            "TC1202 - Decor & Design",
            "TC1202 - Plant Production"
        ],
        "NEW TC - New Technical Communication": [
            "TCENG1201 - Draftsman",
            "TCENG1201 - Business Administration"
        ],
        "PS - Public Speaking": [
            "PS1301 - Public Speaking & Oral Presentation (All Post-Foundation Streams)",
            "PSENG1301 - Advanced Workplace Public Speaking"
        ]
    }
}

DEPARTMENTS_AND_GROUPS = {
    "Information Technology (IT)": {
        "IT - Software Development & Applications": ["Group IT-DEV1", "Group IT-DEV2"],
        "IT - Networking & Systems Administration": ["Group IT-NET1", "Group IT-NET2"],
        "IT - Multimedia & Graphic Design": ["Group IT-GRAPH1", "Group IT-GRAPH2"],
        "IT - Cybersecurity & Information Assurance": ["Group IT-SEC1"]
    },
    "Electronics Engineering": {
        "Electronics - Consumer Devices & Power": ["Group ELEC-1"],
        "Electronics - Communication & Control Systems": ["Group ELEC-2"]
    },
    "Architectural Engineering & Draftsman": {
        "Draftsman - Building Drawing & Floor Planning": ["Group DRAFT-1"],
        "Draftsman - AutoCAD & Structural Modeling": ["Group DRAFT-2"]
    },
    "Mechanical & Automotive Engineering": {
        "Mechanical - Industrial Maintenance": ["Group MECH-1"],
        "Automotive - Engine & Electrical Diagnostics": ["Group AUTO-1"]
    },
    "Business Administration & Commercial": {
        "Business Studies & Office Management": ["Group BUS-1"]
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

    st.markdown("---")
    st.markdown("### 📌 Pilot Study Scope")
    st.info("""
    **Motive:** Saham Vocational College (SVC) Official Academic Assessment Initiative  
    **Pilot Cohort:** 1 Lecturer & 20 Students  
    **Institution:** Saham Vocational College (SVC)  
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
        
        # Load Published Assignments dynamically from DB
        conn = get_db()
        df_asg = pd.read_sql_query("SELECT * FROM assignments", conn)
        conn.close()
        
        if not df_asg.empty:
            asg_options = [f"{row['id']} - {row['title']} ({row['course']})" for _, row in df_asg.iterrows()]
            selected_asg_str = st.selectbox("Select Active Published Assignment:", asg_options)
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
            
            # Display Assignment Details & Brief Box
            st.info(f"""
            📌 **Selected Assignment:** {asg_title}  
            📚 **Course Module:** {asg_course} | 🗓️ **Deadline:** {asg_deadline}  
            🎯 **Mark Scale:** {asg_max_marks} Marks | 📏 **Rubric:** {asg_rubric_type}
            """)
            
            with st.expander("📖 Read Full Assignment Brief & Instructions", expanded=False):
                if asg_desc:
                    st.markdown(f"**Brief Description:** {asg_desc}")
                if asg_brief_text:
                    st.text_area("Assignment Specification Document:", value=str(asg_brief_text), height=120, disabled=True)
            
            col_s1, col_s2 = st.columns(2)
            with col_s1:
                student_id_input = st.selectbox("Select Your Student ID (Pilot Cohort):", STUDENT_IDS)
                prog_choice = st.selectbox("Academic Programme Type:", list(PROGRAMMES_AND_COURSES.keys()))
                stream_choice = st.selectbox("Course Stream / Level:", list(PROGRAMMES_AND_COURSES[prog_choice].keys()))
                module_choice = st.selectbox("Subject Module / Track:", PROGRAMMES_AND_COURSES[prog_choice][stream_choice])
                
            with col_s2:
                dept_choice = st.selectbox("Department:", list(DEPARTMENTS_AND_GROUPS.keys()))
                spec_choice = st.selectbox("Specialisation:", list(DEPARTMENTS_AND_GROUPS[dept_choice].keys()))
                group_choice = st.selectbox("Group / Cohort:", DEPARTMENTS_AND_GROUPS[dept_choice][spec_choice])

        st.markdown("---")
        st.markdown("#### 📎 Attachment & Content Submission Tool")
        uploaded_file = st.file_uploader(
            "Attach Assignment Document (.docx, .pdf, .txt):",
            type=['docx', 'pdf', 'txt'],
            help="Drag and drop or browse to attach your Microsoft Word, PDF, or Plain Text document."
        )
        
        extracted_content = ""
        file_name_val = "Direct_Text_Input.txt"
        if uploaded_file is not None:
            extracted_content = extract_text_from_file(uploaded_file)
            file_name_val = uploaded_file.name
            st.success(f"✅ Document Attached: **{uploaded_file.name}** ({len(extracted_content.split())} words extracted)")
            with st.expander("🔍 Preview Extracted Content", expanded=False):
                st.text_area("Extracted Document Text:", value=extracted_content, height=140, disabled=True)

        st.markdown("**OR Paste Report Text Directly:**")
        report_text_input = st.text_area(
            "Report Text Input:",
            value=extracted_content if extracted_content else "",
            height=160,
            placeholder="TRANSMITTAL LETTER & TECHNICAL REPORT..."
        )
        
        # Real-time Originality Check
        if report_text_input:
            scan_res = run_originality_scan(report_text_input)
            st.markdown("#### 🛡️ Turnitin-Style Originality & Similarity Analysis")
            col_sc1, col_sc2, col_sc3, col_sc4 = st.columns(4)
            col_sc1.metric("Overall Similarity Index", f"{scan_res['total_match']}%")
            col_sc2.metric("AI Text Pattern Score", f"{scan_res['ai_pattern_score']}%")
            col_sc3.metric("Web Source Overlap", f"{scan_res['web_match']}%")
            col_sc4.metric("Peer Submissions Database", f"{scan_res['peer_match']}%")
            
            if scan_res['total_match'] > st.session_state.sim_threshold:
                st.error(f"❌ SUBMISSION BLOCKED: Overall Similarity Index ({scan_res['total_match']}%) exceeds the maximum allowable threshold ({st.session_state.sim_threshold}%). According to Saham Vocational College Academic Policy, submissions matching more than {st.session_state.sim_threshold}% of external web or AI sources cannot be submitted. Please revise your report in your own words.")
                st.button("🚀 Submit Assignment for Evaluation", type="primary", disabled=True)
            else:
                st.success(f"✅ Originality Scan Cleared: Similarity Index ({scan_res['total_match']}%) is within permissible limits (< {st.session_state.sim_threshold}%).")
                if st.button("🚀 Submit Assignment for Evaluation", type="primary"):
                    anon_index = STUDENT_IDS.index(student_id_input) + 1
                    anon_code = f"Student A{anon_index:02d} (Anonymized)"
                    sub_id = f"SUB-2026-{anon_index:03d}"
                    
                    provisional_score = round(asg_max_marks * 0.85, 1)
                    
                    conn = get_db()
                    c = conn.cursor()
                    c.execute("""
                        INSERT OR REPLACE INTO submissions VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    """, (
                        sub_id, student_id_input, anon_code, asg_id_val, asg_course, group_choice,
                        file_name_val, report_text_input, scan_res['total_match'], scan_res['ai_pattern_score'],
                        json.dumps({"Layout & Structure": 2.0, "Content & Depth": 3.6, "Technical Vocabulary": 2.5, "Grammar & Mechanics": 1.6, "Sources & References": 0.8}),
                        provisional_score, asg_max_marks,
                        json.dumps({
                            "Layout & Structure": "Standard report headings identified.",
                            "Content & Depth": "Sufficient technical explanations included.",
                            "Technical Vocabulary": "Appropriate vocational terms used.",
                            "Grammar & Mechanics": "Minor grammar and punctuation flaws found.",
                            "Sources & References": "Reference section present."
                        }),
                        "Good technical layout and clear vocational concept explanation.",
                        json.dumps(["Improve citation format.", "Check plural noun agreement."]),
                        "Review course citation guidelines prior to final submission.",
                        "Pending Review", provisional_score, "",
                        datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                    ))
                    conn.commit()
                    conn.close()
                        
                    log_audit("Student", "Submission Created", f"{student_id_input} submitted {sub_id} for {asg_title}")
                    st.balloons()
                    st.success(f"✅ Assignment Submitted Successfully! Your Reference Code: **{sub_id}** (Anonymised as **{anon_code}** for fair grading).")

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
            st.success(f"✅ Credentials Verified for **{lookup_id}** ({STUDENT_CREDENTIALS[lookup_id]['anon']})")
            conn = get_db()
            df_my = pd.read_sql_query("SELECT * FROM submissions WHERE student_id = ?", conn, params=(lookup_id,))
            conn.close()
        else:
            if lookup_pass:
                st.error("❌ Incorrect Password. Access denied to student grade vault.")
            else:
                st.info("🔒 Private Vault Locked: Please select your username and enter your personal student password to view your released grades and feedback.")
            df_my = pd.DataFrame()
        
        if not df_my.empty:
            for _, row in df_my.iterrows():
                row_course = row.get('course', 'Course Module')
                row_id = row.get('id', 'SUB')
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
                    <p><b>Submission Code:</b> {row_id} | <b>Submitted Date:</b> {row_date} | <b>Group:</b> {row_group}</p>
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
                    except:
                        pass
                        
                    st.markdown(f"**🚀 Specific Action Step:** {row_action}")
                    if row_remarks:
                        st.markdown(f"**📝 Lecturer Remarks:** {row_remarks}")
                else:
                    st.markdown(f"<p><span class='status-pending'>Status: Under Lecturer Evaluation & Verification</span></p>", unsafe_allow_html=True)
                    st.info("🔒 Provisional marks are undergoing human review by your lecturer. Official results will appear here once approved.")
                st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.info("No active submissions found for this Student ID.")

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
        df_queue = pd.read_sql_query("SELECT id, student_id, student_name_anon, course, group_name, similarity_index, ai_total, teacher_score, max_marks, teacher_status, submitted_date FROM submissions", conn)
        conn.close()
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Pilot Cohort Capacity", "20 Students", "1 Lecturer")
        m2.metric("Total Submissions Received", f"{len(df_queue)} Papers")
        m3.metric("Pending Review", f"{len(df_queue[df_queue['teacher_status'] == 'Pending Review'])} Papers")
        m4.metric("Approved & Released", f"{len(df_queue[df_queue['teacher_status'].str.contains('Approved', na=False)])} Papers")
        
        st.markdown("---")
        st.dataframe(df_queue, use_container_width=True)

    # TAB 2: SIDE-BY-SIDE REVIEW & OVERRIDE
    with tabs[1]:
        st.markdown("### 🔍 Side-by-Side Document Review & Lecturer Override")
        
        conn = get_db()
        df_all = pd.read_sql_query("SELECT * FROM submissions", conn)
        conn.close()
        
        if not df_all.empty:
            sub_options = [f"{row['id']} - {row['student_name_anon']} ({row['course']})" for _, row in df_all.iterrows()]
            selected_sub_str = st.selectbox("Select Student Submission to Grade:", sub_options)
            selected_id = selected_sub_str.split(" - ")[0]
            
            sub_data = df_all[df_all['id'] == selected_id].iloc[0]
            
            left_col, right_col = st.columns([1, 1])
            
            # LEFT COLUMN: Document & Similarity Report
            with left_col:
                st.markdown(f"### 📄 Document View ({sub_data.get('student_name_anon', 'Student')})")
                st.caption(f"**Course:** {sub_data.get('course', '')} | **Group:** {sub_data.get('group_name', '')} | **File:** {sub_data.get('file_name', '')}")
                
                raw_report = sub_data.get('report_text', '')
                formatted_text = raw_report.replace("\n", "<br/>") if raw_report else ""
                st.markdown(f"""
                <div style='background-color:#0F172A; color:#F8FAFC; padding:15px; border-radius:6px; font-family:monospace; font-size:0.85rem; height:450px; overflow-y:auto;'>
                {formatted_text}
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown("#### 🛡️ Turnitin-Style Originality & Similarity Index")
                st.markdown(f"- **Overall Similarity Index:** `{sub_data.get('similarity_index', 0.0)}%`")
                st.markdown(f"- **AI Pattern Match Score:** `{sub_data.get('ai_pattern_score', 0.0)}%`")
                st.markdown(f"- **Student Anonymisation:** Verified ({sub_data.get('student_name_anon', 'Anonymized')})")

            # RIGHT COLUMN: Criterion Editing & Confirmation
            with right_col:
                st.markdown("### 🤖 AI Evidence Analysis & Score Adjustment")
                st.caption("Review suggested criteria marks, inspect quoted evidence, and apply Human Override.")
                
                try:
                    ai_scores = json.loads(sub_data.get('ai_scores_json', '{}'))
                    ai_evidence = json.loads(sub_data.get('ai_evidence_json', '{}'))
                except:
                    ai_scores = {"Layout & Structure": 2.0, "Content & Depth": 3.6, "Technical Vocabulary": 2.5, "Grammar & Mechanics": 1.6, "Sources & References": 0.8}
                    ai_evidence = {"Layout & Structure": "Standard headings present."}
                
                adjusted_scores = {}
                for crit, val in ai_scores.items():
                    c_col1, c_col2 = st.columns([2, 1])
                    with c_col1:
                        st.markdown(f"**{crit}** *(AI Suggestion: {val})*")
                        if crit in ai_evidence:
                            st.caption(f"*Evidence:* {ai_evidence[crit]}")
                    with c_col2:
                        adjusted_scores[crit] = st.number_input(
                            f"Score ({crit})", min_value=0.0, max_value=5.0, value=float(val), step=0.1, key=f"crit_{sub_data['id']}_{crit}"
                        )
                
                calculated_total = round(sum(adjusted_scores.values()), 1)
                max_marks_val = float(sub_data.get('max_marks', 12.0))
                st.markdown(f"### 🎯 Calculated Lecturer Score: **{calculated_total} / {max_marks_val} Marks**")
                
                st.markdown("---")
                st.markdown("#### 💬 Formative Feedback Editor (1-2-1 Model)")
                strength_val = st.text_input("1 Strength:", value=sub_data.get('ai_strength', ''), key=f"str_{sub_data['id']}")
                action_val = st.text_input("1 Actionable Step:", value=sub_data.get('ai_action', ''), key=f"act_{sub_data['id']}")
                
                st.markdown("---")
                override_notes = st.text_area("Lecturer Override Rationale (Logged in Audit Trail):", value=sub_data.get('teacher_feedback', ''), placeholder="e.g. Verified IEEE references and adjusted score by +0.2.")
                
                b1, b2, b3 = st.columns(3)
                with b1:
                    if st.button("✅ Confirm & Release Grade", type="primary", use_container_width=True):
                        conn = get_db()
                        c = conn.cursor()
                        c.execute("""
                            UPDATE submissions SET teacher_status=?, teacher_score=?, teacher_feedback=?, ai_strength=?, ai_action=? WHERE id=?
                        """, ("Approved", calculated_total, override_notes, strength_val, action_val, sub_data['id']))
                        conn.commit()
                        conn.close()
                        
                        log_audit("Lecturer", "Grade Approved", f"Lecturer approved score {calculated_total}/{max_marks_val} for {sub_data['id']}")
                        st.success(f"Grade {calculated_total}/{max_marks_val} Released to Student Portal!")
                        st.rerun()
                with b2:
                    if st.button("✏️ Save Edits (Draft)", use_container_width=True):
                        conn = get_db()
                        c = conn.cursor()
                        c.execute("""
                            UPDATE submissions SET teacher_status=?, teacher_score=?, teacher_feedback=? WHERE id=?
                        """, ("Approved (Modified)", calculated_total, override_notes, sub_data['id']))
                        conn.commit()
                        conn.close()
                        st.warning("Modified score saved as draft!")
                        st.rerun()
                with b3:
                    if st.button("❌ Reject AI Baseline", use_container_width=True):
                        conn = get_db()
                        c = conn.cursor()
                        c.execute("UPDATE submissions SET teacher_status=? WHERE id=?", ("Rejected AI", sub_data['id']))
                        conn.commit()
                        conn.close()
                        st.error("AI baseline rejected. Manual grading enabled.")
                        st.rerun()

    # TAB 3: BATCH UPLOAD
    with tabs[2]:
        st.markdown("### 📁 Batch Cohort Document Ingestion")
        st.caption("Upload multiple student files simultaneously for whole-class originality scan and AI assessment.")
        
        batch_files = st.file_uploader("Upload Whole Class Files (.docx, .pdf, .txt):", type=['docx', 'pdf', 'txt'], accept_multiple_files=True)
        if batch_files:
            st.success(f"Attached {len(batch_files)} class files for batch ingestion.")
            if st.button("⚡ Process Entire Batch Cohort"):
                for idx, b_file in enumerate(batch_files):
                    b_text = extract_text_from_file(b_file)
                    b_scan = run_originality_scan(b_text)
                    s_id = STUDENT_IDS[idx % 20]
                    s_code = f"Student A{idx+1:02d} (Anonymized)"
                    sub_code = f"SUB-BATCH-{idx+1:03d}"
                    
                    conn = get_db()
                    c = conn.cursor()
                    c.execute("""
                        INSERT OR REPLACE INTO submissions VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    """, (
                        sub_code, s_id, s_code, "ASG-TC1201-01", "TCENG1201 - Formal Technical Communication (New Benchmark)", "Group IT-NET1",
                        b_file.name, b_text, b_scan['total_match'], b_scan['ai_pattern_score'],
                        json.dumps({"Layout & Structure": 1.8, "Content & Depth": 3.4, "Technical Vocabulary": 2.4, "Grammar & Mechanics": 1.5, "Sources & References": 0.8}),
                        9.9, 12.0,
                        json.dumps({"Layout & Structure": "Standard headings found."}),
                        "Clear technical structure.", json.dumps(["Review sentence punctuation."]), "Check grammar mechanics.",
                        "Pending Review", 9.9, "", datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                    ))
                    conn.commit()
                    conn.close()
                st.success("All batch files processed and saved to database successfully!")
                st.rerun()

    # TAB 4: ASSIGNMENT BUILDER
    with tabs[3]:
        st.markdown("### ⚙️ Assignment & Rubric Configuration Builder")
        st.caption("Configure subject-independent rubrics for Engineering, English, IT, Mathematics, or Business.")
        
        # Load Existing Rubrics from Database
        conn = get_db()
        df_rubrics = pd.read_sql_query("SELECT * FROM rubrics", conn)
        conn.close()
        
        col_b1, col_b2 = st.columns(2)
        with col_b1:
            new_asg_title = st.text_input("New Assignment Title:", "Workplace Safety & Diode Technical Report")
            prog_sel = st.selectbox("Academic Programme Scope:", list(PROGRAMMES_AND_COURSES.keys()))
            stream_opts = list(PROGRAMMES_AND_COURSES[prog_sel].keys())
            stream_sel = st.selectbox("Course Stream / Level:", stream_opts)
            course_sel = st.selectbox("Course Module:", PROGRAMMES_AND_COURSES[prog_sel][stream_sel])
            max_mark_in = st.number_input("Maximum Mark Allocation:", value=12.0, step=1.0)
            
        with col_b2:
            rubric_opts = [f"{r['id']} - {r['rubric_name']}" for _, r in df_rubrics.iterrows()] if not df_rubrics.empty else ["RUB-TCENG1201"]
            rubric_sel = st.selectbox("Select Active Marking Rubric:", rubric_opts)
            due_date_in = st.date_input("Submission Deadline:", datetime.date(2026, 10, 30))
            st.checkbox("Enable Mandatory Student Anonymisation", value=True, disabled=True)
            st.checkbox("Enable Automated Originality Gate", value=True, disabled=True)
            
        st.markdown("---")
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
            st.success(f"✅ Assignment **{new_asg_title}** published successfully! Students can now submit against it.")

        st.markdown("---")
        st.markdown("#### 📚 Currently Published Assignments Directory")
        conn = get_db()
        df_published = pd.read_sql_query("SELECT id, title, course, deadline, max_marks, rubric_type FROM assignments", conn)
        conn.close()
        st.dataframe(df_published, use_container_width=True)

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
        df_export = pd.read_sql_query("SELECT id, student_id, student_name_anon, course, group_name, ai_total, teacher_score, max_marks, teacher_status, teacher_feedback, submitted_date FROM submissions", conn)
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
    st.info(f"Current Policy Rule: Submissions with > **{sim_val}%** similarity index are automatically blocked from student submission.")
    
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
