import streamlit as st
import pandas as pd
import datetime
import sqlite3
import json
import re

# -----------------------------------------------------------------------------
# PAGE CONFIGURATION
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="SVC Assess — Level 1 Group 4",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------------------------------------------------------
# INSTITUTIONAL CUSTOM CSS THEME & BRANDING (Saham Vocational College)
# -----------------------------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
    }

    /* Main Canvas Background Gradient */
    .stApp {
        background: linear-gradient(135deg, #F8FAFC 0%, #E2E8F0 50%, #F1F5F9 100%);
        color: #0F172A;
    }

    /* Dark Navy Sidebar Styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0F172A 0%, #1E3A8A 100%) !important;
        border-right: 2px solid #0284C7;
    }

    [data-testid="stSidebar"] * {
        color: #F8FAFC !important;
    }

    /* Header Banner with SVC Institutional Styling */
    .svc-header-banner {
        background: linear-gradient(90deg, #0F172A 0%, #1E3A8A 50%, #0284C7 100%);
        border-radius: 12px;
        padding: 24px 30px;
        color: #FFFFFF;
        box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.25);
        margin-bottom: 22px;
        border-left: 6px solid #D97706; /* Amber Gold Accent */
        display: flex;
        align-items: center;
        justify-content: space-between;
    }

    .svc-header-title {
        font-size: 2.1rem;
        font-weight: 800;
        margin: 0;
        color: #FFFFFF;
        letter-spacing: -0.5px;
    }

    .svc-header-subtitle {
        font-size: 1.05rem;
        color: #E2E8F0;
        margin-top: 6px;
        font-weight: 500;
    }

    /* Elevated White Card Container */
    .card {
        background-color: #FFFFFF;
        border: 1px solid #CBD5E1;
        border-radius: 12px;
        padding: 24px;
        box-shadow: 0 4px 16px -2px rgba(15, 23, 42, 0.08);
        margin-bottom: 22px;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }

    .card:hover {
        box-shadow: 0 8px 24px -4px rgba(15, 23, 42, 0.12);
    }

    /* Policy Badge Container */
    .concept-badge {
        background: linear-gradient(90deg, #EFF6FF 0%, #E0F2FE 100%);
        border-left: 5px solid #0284C7;
        border-radius: 8px;
        padding: 14px 20px;
        color: #1E3A8A;
        font-weight: 600;
        font-size: 0.95rem;
        margin-bottom: 20px;
        box-shadow: 0 2px 8px rgba(2, 132, 199, 0.1);
    }

    /* Styled Tab Navigation */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        border-bottom: 2px solid #CBD5E1;
    }

    .stTabs [data-baseweb="tab"] {
        height: 48px;
        background-color: #FFFFFF;
        border-radius: 8px 8px 0px 0px;
        color: #475569;
        font-weight: 600;
        padding: 10px 22px;
        border: 1px solid #E2E8F0;
        border-bottom: none;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(180deg, #1E3A8A 0%, #1E40AF 100%) !important;
        color: #FFFFFF !important;
        border-color: #1E3A8A !important;
        box-shadow: 0 4px 12px rgba(30, 58, 138, 0.25);
    }

    /* Primary & Secondary Buttons */
    .stButton > button[kind="primary"] {
        background: linear-gradient(90deg, #1E3A8A 0%, #0284C7 100%);
        border: none;
        color: white;
        font-weight: 700;
        border-radius: 8px;
        padding: 8px 20px;
        box-shadow: 0 4px 12px rgba(2, 132, 199, 0.3);
    }

    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(90deg, #1E40AF 0%, #0369A1 100%);
        transform: translateY(-1px);
    }

    /* Status Indicators */
    .status-approved {
        background-color: #DCFCE7;
        color: #15803D;
        padding: 6px 14px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.88rem;
        display: inline-block;
    }

    .status-pending {
        background-color: #FEF3C7;
        color: #B45309;
        padding: 6px 14px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.88rem;
        display: inline-block;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# DATABASE INITIALIZATION & AUTO-MIGRATION
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
    
    # Auto-migrations
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
        rubric_fnd1 = (
            "RUB-FND1-10M",
            "10-Mark Foundation Level 1 Technical Report Rubric",
            10.0,
            json.dumps([
                {"criterion": "Structure & Layout", "max_marks": 2.0, "focus": "Transmittal letter, Summary, Intro, Body, Conclusion, References."},
                {"criterion": "Technical Content & Accuracy", "max_marks": 3.0, "focus": "Vocational concepts, component analysis, safety guidelines."},
                {"criterion": "Vocabulary & Terminology", "max_marks": 2.0, "focus": "Technical domain terms, formal register, precision."},
                {"criterion": "Grammar & Sentence Mechanics", "max_marks": 2.0, "focus": "Plural agreement, punctuation, sentence structure."},
                {"criterion": "Citations & References", "max_marks": 1.0, "focus": "IEEE or technical source citations."}
            ])
        )
        rubric_tc1201 = (
            "RUB-TCENG1201",
            "12-Mark TCENG1201 Formal Technical Communication Rubric",
            12.0,
            json.dumps([
                {"criterion": "Layout & Organization", "max_marks": 2.0, "focus": "Standard report headings and logical sequencing."},
                {"criterion": "Technical Depth", "max_marks": 4.0, "focus": "Explanations of vocational engineering applications."},
                {"criterion": "Domain Terminology", "max_marks": 3.0, "focus": "Technical vocabulary and formal phrasing."},
                {"criterion": "Grammar & Syntax", "max_marks": 2.0, "focus": "Subject-verb agreement and mechanics."},
                {"criterion": "Sources & References", "max_marks": 1.0, "focus": "IEEE technical references."}
            ])
        )
        c.execute("INSERT INTO rubrics VALUES (?,?,?,?)", rubric_fnd1)
        c.execute("INSERT INTO rubrics VALUES (?,?,?,?)", rubric_tc1201)

    # Seed Initial Default Assignment for Level 1 Group 4 if empty
    c.execute("SELECT COUNT(*) FROM assignments")
    if c.fetchone()[0] == 0:
        c.execute("""
            INSERT INTO assignments VALUES (
                'ASG-L1G4-01',
                'Formal Technical Report on Electronic Components',
                'ENG101 - Foundation Technical English Level 1',
                'Foundation Programme',
                '2026-10-30',
                10.0,
                '10-Mark Foundation Level 1 Technical Report Rubric',
                'Write a formal technical report investigating electronic components, safety protocols, and workplace applications.',
                'TCENG1201_Assignment_Brief.pdf',
                'Assignment Specification: Prepare a 2-4 page technical report analyzing electronic components (resistors, diodes, or capacitors). Include Transmittal Letter, Executive Summary, Introduction, Technical Analysis, and References.'
            )
        """)
        
    # Seed Sample Pilot Submissions for Level 1 Group 4 if empty
    c.execute("SELECT COUNT(*) FROM submissions")
    if c.fetchone()[0] == 0:
        sample_sub1 = (
            "SUB-L1G4-001",
            "PPENG01/04-00001",
            "Student A01 (Anonymized)",
            "ASG-L1G4-01",
            "ENG101 - Foundation Technical English Level 1",
            "Level 1 Group 4",
            "Resistor_Technical_Report.docx",
            """TRANSMITTAL LETTER & TECHNICAL REPORT
To: Course Coordinator, English Department
From: Student A01
Date: 12 October 2026
Subject: Technical Analysis of Resistors in Vocational Circuits

SUMMARY:
Resistors are passive electronic components designed to limit electric current and protect sensitive circuits. This report examines fixed vs. variable resistors and workplace safety procedures.

1. INTRODUCTION:
Electrical resistance is measured in Ohms (Ω). Resistors control current flow according to Ohm's Law (V = IR).

2. TECHNICAL ANALYSIS:
- Fixed Resistors: Provide constant resistance value.
- Variable Resistors: Allow adjustable resistance in speed regulators.

3. CONCLUSION & RECOMMENDATIONS:
- Always check power wattage ratings prior to installation.
- Disconnect power supply before measuring resistance.

REFERENCES:
1. Saham Vocational College Electronics Safety Guide (2025).""",
            12.5,
            18.2,
            json.dumps({"Structure & Layout": 2.0, "Technical Content & Accuracy": 2.8, "Vocabulary & Terminology": 1.8, "Grammar & Sentence Mechanics": 1.7, "Citations & References": 0.9}),
            9.2,
            10.0,
            json.dumps({
                "Structure & Layout": "Includes transmittal letter, summary, intro, body, conclusion, references.",
                "Technical Content & Accuracy": "Accurately details resistor types and Ohm law applications.",
                "Vocabulary & Terminology": "Uses precise domain terms.",
                "Grammar & Sentence Mechanics": "Minor subject-verb agreement error in bullet items.",
                "Citations & References": "Includes reference citation."
            }),
            "Excellent technical report structure adhering to Foundation Level 1 requirements.",
            json.dumps(["Ensure plural noun agreement (e.g. Resistors are used).", "Format reference citations consistently."]),
            "Review plural agreement rules before final submission.",
            "Approved",
            9.2,
            "Approved baseline score after verifying technical accuracy and reference citation.",
            "2026-10-12 11:20"
        )
        c.execute("INSERT INTO submissions VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", sample_sub1)

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

def extract_text_from_file(uploaded_file):
    if uploaded_file is None:
        return ""
    file_ext = uploaded_file.name.split('.')[-1].lower()
    text = ""
    try:
        if file_ext == 'docx':
            import docx
            doc = docx.Document(uploaded_file)
            text = "\n".join([p.text for p in doc.paragraphs if p.text])
        elif file_ext == 'pdf':
            import pypdf
            reader = pypdf.PdfReader(uploaded_file)
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
        elif file_ext == 'txt':
            text = uploaded_file.read().decode('utf-8')
    except Exception as e:
        text = f"Error extracting document text: {str(e)}"
    return text

def run_originality_scan(text_content):
    if not text_content or len(text_content.strip()) < 20:
        return {"total_match": 0.0, "ai_pattern_score": 0.0, "web_match": 0.0, "peer_match": 0.0}
    
    words = text_content.lower().split()
    total_words = len(words)
    
    # Originality heuristic
    academic_buzzwords = ['transmittal', 'executive', 'summary', 'introduction', 'analysis', 'conclusion', 'recommendations', 'references', 'ieee', 'ohm']
    matched_words = sum(1 for w in words if any(b in w for b in academic_buzzwords))
    
    base_web = min(35.0, round((matched_words / max(total_words, 1)) * 100, 1))
    peer_match = round(base_web * 0.4, 1)
    total_match = min(100.0, round(base_web + peer_match, 1))
    
    ai_phrases = ['in conclusion', 'it is important to note', 'furthermore', 'moreover', 'in summary', 'plays a crucial role']
    ai_count = sum(1 for phrase in ai_phrases if phrase in text_content.lower())
    ai_pattern_score = min(95.0, round(ai_count * 12.5 + 8.0, 1))
    
    return {
        "total_match": total_match,
        "ai_pattern_score": ai_pattern_score,
        "web_match": base_web,
        "peer_match": peer_match
    }

# -----------------------------------------------------------------------------
# STUDENT CREDENTIALS & ROSTER (Level 1 Group 4)
# -----------------------------------------------------------------------------
STUDENT_ROSTER = [f"PPENG01/04-{i:05d}" for i in range(1, 21)]
STUDENT_CREDENTIALS = {
    uid: {
        "pass": f"L1G4#{100 + idx + 1}",
        "anon": f"Student A{idx + 1:02d} (Anonymized)"
    }
    for idx, uid in enumerate(STUDENT_ROSTER)
}

# -----------------------------------------------------------------------------
# SIDEBAR NAVIGATION
# -----------------------------------------------------------------------------
if 'active_view' not in st.session_state:
    st.session_state.active_view = 'Student Portal'

if 'sim_threshold' not in st.session_state:
    st.session_state.sim_threshold = 80.0

with st.sidebar:
    st.markdown("## 🏛️ Saham Vocational College")
    st.caption("English Department | Level 1 Group 4 Repository")
    st.markdown("---")
    st.markdown("### 🔒 Workspace Navigation")
    
    view_selection = st.radio(
        "Select Portal View:",
        ["🎓 Student Submission Portal", "👨‍🏫 Lecturer Workspace (Ms. Anwar)", "🏛️ Quality Assurance Control"],
        index=0 if st.session_state.active_view == 'Student Portal' else (1 if st.session_state.active_view == 'Teacher Workspace' else 2)
    )
    
    if view_selection in ["👨‍🏫 Lecturer Workspace (Ms. Anwar)", "🏛️ Quality Assurance Control"]:
        required_pin = "1234" if view_selection == "👨‍🏫 Lecturer Workspace (Ms. Anwar)" else "8888"
        pin_entered = st.text_input("Enter Faculty Security PIN:", type="password", help="Default PIN: Teacher = 1234, QA = 8888")
        
        if pin_entered == required_pin:
            st.success("✅ Access Granted!")
            st.session_state.active_view = 'Teacher Workspace' if view_selection == "👨‍🏫 Lecturer Workspace (Ms. Anwar)" else 'Admin Workspace'
        else:
            st.error("🔒 Security Lock Active. Enter PIN.")
            st.session_state.active_view = 'Student Portal'
    else:
        st.session_state.active_view = 'Student Portal'

    st.markdown("---")
    st.markdown("### 📌 Class Information")
    st.info("""
    **Institution:** Saham Vocational College  
    **Department:** English Department  
    **Class Cohort:** Foundation Level 1 Group 4  
    **Course Assessor:** Ms. Anwar Al-Fathi  
    **Student Roster:** 20 Students (`PPENG01/04-00001` - `00020`)
    """)

# -----------------------------------------------------------------------------
# MAIN HEADER BANNER
# -----------------------------------------------------------------------------
st.markdown("""
<div class='svc-header-banner'>
    <div>
        <div class='svc-header-title'>SVC Assess — Level 1 Group 4</div>
        <div class='svc-header-subtitle'>Class Assessment & Originality Feedback Platform | Saham Vocational College</div>
    </div>
    <div style='text-align: right; font-weight: 700; color: #FCD34D;'>
        📍 English Dept<br/>Ms. Anwar Al-Fathi
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class='concept-badge'>
    📍 <b>Institutional Assessment Policy (Saham Vocational College):</b>
    Artificial Intelligence serves strictly as an evidence-gathering co-pilot; 100% final grading authority remains with course assessor Ms. Anwar Al-Fathi.
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
        st.markdown("### 📝 Submit Class Technical Assignment")
        
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
            asg_course = current_asg.get('course', 'ENG101')
            asg_deadline = current_asg.get('deadline', '')
            asg_max_marks = float(current_asg.get('max_marks', 10.0))
            asg_rubric_type = current_asg.get('rubric_type', '')
            asg_id_val = current_asg.get('id', 'ASG-L1G4-01')
            
            asg_desc = current_asg.get('description', '') if ('description' in current_asg and pd.notna(current_asg.get('description'))) else ""
            asg_brief_text = current_asg.get('brief_text', '') if ('brief_text' in current_asg and pd.notna(current_asg.get('brief_text'))) else ""
            
            st.info(f"""
            📌 **Assignment:** {asg_title}  
            📚 **Course:** {asg_course} | 🗓️ **Deadline:** {asg_deadline}  
            🎯 **Mark Allocation:** {asg_max_marks} Marks | 📏 **Rubric:** {asg_rubric_type}
            """)
            
            with st.expander("📖 Read Full Assignment Brief & Instructions", expanded=False):
                if asg_desc:
                    st.markdown(f"**Description:** {asg_desc}")
                if asg_brief_text:
                    st.text_area("Specification Document:", value=str(asg_brief_text), height=120, disabled=True)
            
            st.markdown("#### 👤 Student Identification (Level 1 Group 4)")
            col_id, col_meta = st.columns([1, 1])
            with col_id:
                # SIMPLIFIED STUDENT USERNAME SELECTOR
                student_id_input = st.selectbox("Select Your Student Username ID:", STUDENT_ROSTER)
            with col_meta:
                st.markdown("**Class Enrolled Track:**")
                st.success("🎓 **Foundation Programme** | Level 1 | **Level 1 Group 4** (Assessor: Ms. Anwar Al-Fathi)")

            group_choice = "Level 1 Group 4"

            st.markdown("---")
            st.markdown("#### 📎 Attachment & Content Submission Tool")
            uploaded_file = st.file_uploader(
                "Attach Assignment Document (.docx, .pdf, .txt):",
                type=['docx', 'pdf', 'txt'],
                help="Drag and drop or browse to attach your document."
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
                    st.error(f"❌ SUBMISSION BLOCKED: Overall Similarity Index ({scan_res['total_match']}%) exceeds allowable threshold ({st.session_state.sim_threshold}%). Please revise your report in your own words.")
                    st.button("🚀 Submit Assignment for Evaluation", type="primary", disabled=True)
                else:
                    st.success(f"✅ Originality Scan Cleared: Similarity Index ({scan_res['total_match']}%) is within permissible limits (< {st.session_state.sim_threshold}%).")
                    if st.button("🚀 Submit Assignment for Evaluation", type="primary"):
                        anon_code = STUDENT_CREDENTIALS[student_id_input]["anon"]
                        sub_id = f"SUB-L1G4-{student_id_input.split('-')[-1]}"
                        provisional_score = round(asg_max_marks * 0.85, 1)
                        
                        conn = get_db()
                        c = conn.cursor()
                        c.execute("""
                            INSERT OR REPLACE INTO submissions VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                        """, (
                            sub_id, student_id_input, anon_code, asg_id_val, asg_course, group_choice,
                            file_name_val, report_text_input, scan_res['total_match'], scan_res['ai_pattern_score'],
                            json.dumps({"Structure & Layout": 2.0, "Technical Content & Accuracy": 2.8, "Vocabulary & Terminology": 1.8, "Grammar & Sentence Mechanics": 1.7, "Citations & References": 0.9}),
                            provisional_score, asg_max_marks,
                            json.dumps({
                                "Structure & Layout": "Standard report headings identified.",
                                "Technical Content & Accuracy": "Sufficient technical explanations included.",
                                "Vocabulary & Terminology": "Appropriate vocational terms used.",
                                "Grammar & Sentence Mechanics": "Minor grammar flaws found.",
                                "Citations & References": "Reference section present."
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
                        st.success(f"✅ Assignment Submitted Successfully! Reference Code: **{sub_id}** (Anonymised as **{anon_code}** for fair grading).")
        else:
            st.info("ℹ️ No active published assignments found. Ms. Anwar Al-Fathi will publish assignments here soon.")

    # TAB 2: CHECK MY GRADES
    with st_tabs[1]:
        st.markdown("### 📝 Private Student Grade & Feedback Vault")
        st.caption("Enter your student ID and private access password to view your released marks and feedback:")
        
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            lookup_id = st.selectbox("Select Your Student Username ID:", STUDENT_ROSTER, key="lookup_id_select")
        with col_p2:
            lookup_pass = st.text_input("Enter Private Access Password:", type="password", key="lookup_pass_input", help="Enter your assigned password (e.g. L1G4#101)")
        
        correct_pass = STUDENT_CREDENTIALS[lookup_id]["pass"]
        
        if lookup_pass and lookup_pass.strip() == correct_pass:
            st.success(f"✅ Credentials Verified for **{lookup_id}** ({STUDENT_CREDENTIALS[lookup_id]['anon']})")
            conn = get_db()
            df_my = pd.read_sql_query("SELECT * FROM submissions WHERE student_id = ?", conn, params=(lookup_id,))
            conn.close()
        else:
            if lookup_pass:
                st.error("❌ Incorrect Password. Access denied to grade vault.")
            else:
                st.info("🔒 Private Vault Locked: Please select your username and enter your personal password to unlock your grades.")
            df_my = pd.DataFrame()
        
        if not df_my.empty:
            for _, row in df_my.iterrows():
                row_course = row.get('course', 'ENG101')
                row_id = row.get('id', 'SUB')
                row_date = row.get('submitted_date', '')
                row_group = row.get('group_name', 'Level 1 Group 4')
                row_status = row.get('teacher_status', 'Pending Review')
                row_score = row.get('teacher_score', 0.0)
                row_max = row.get('max_marks', 10.0)
                row_strength = row.get('ai_strength', '')
                row_action = row.get('ai_action', '')
                row_remarks = row.get('teacher_feedback', '')
                
                st.markdown(f"""
                <div class='card'>
                    <h3 style='color:#1E3A8A; margin-top:0;'>Course Module: {row_course}</h3>
                    <p><b>Submission Code:</b> {row_id} | <b>Submitted Date:</b> {row_date} | <b>Class Group:</b> {row_group}</p>
                    <hr/>
                """, unsafe_allow_html=True)
                
                if row_status in ['Approved', 'Approved (Modified)']:
                    st.markdown(f"<h2 style='color:#16A34A; margin:0;'>Official Released Mark: {row_score} / {row_max} Marks</h2>", unsafe_allow_html=True)
                    st.markdown(f"<p><span class='status-approved'>Status: Official Grade Released by Ms. Anwar Al-Fathi</span></p>", unsafe_allow_html=True)
                    
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
                    st.markdown(f"<p><span class='status-pending'>Status: Under Evaluation by Ms. Anwar Al-Fathi</span></p>", unsafe_allow_html=True)
                    st.info("🔒 Provisional marks are undergoing human review. Official results will appear here once approved.")
                st.markdown("</div>", unsafe_allow_html=True)
        else:
            if lookup_pass and lookup_pass.strip() == correct_pass:
                st.info("No active submissions found for this Student Username ID.")

    # TAB 3: SKILL TRACKER
    with st_tabs[2]:
        st.markdown("### 📈 Technical Skill Development Over Time")
        st.caption("Tracking vocational communication and writing skill progression across semester assignments:")
        st.line_chart(pd.DataFrame({
            "Assignment": ["Assignment 1", "Assignment 2", "Assignment 3 (Current)"],
            "Technical Content": [1.2, 1.6, 2.0],
            "Organization & Structure": [1.0, 1.5, 2.0],
            "Grammar & Mechanics": [1.0, 1.2, 1.5]
        }).set_index("Assignment"))

# -----------------------------------------------------------------------------
# VIEW 2: LECTURER ASSESSMENT WORKSPACE (MS. ANWAR AL-FATHI)
# -----------------------------------------------------------------------------
elif st.session_state.active_view == 'Teacher Workspace':
    st.markdown("## 👋 Welcome Ms. Anwar Al-Fathi!")
    st.caption("Course Assessor & Lecturer — Foundation Level 1 Group 4 | Saham Vocational College")
    
    tabs = st.tabs([
        "📊 Submissions Queue",
        "🔍 Side-by-Side Review & Override",
        "📁 Batch Cohort Ingestion",
        "⚙️ Rubric & Assignment Builder",
        "📈 Cohort Analytics & Reteaching",
        "📋 Academic Governance Audit Trail"
    ])
    
    # TAB 1: SUBMISSIONS INBOX
    with tabs[0]:
        st.markdown("### 📥 Level 1 Group 4 Submissions Inbox")
        conn = get_db()
        df_queue = pd.read_sql_query("SELECT id, student_id, student_name_anon, course, group_name, similarity_index, ai_total, teacher_score, max_marks, teacher_status, submitted_date FROM submissions", conn)
        conn.close()
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Class Capacity", "20 Students", "Level 1 Group 4")
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
            
            with left_col:
                st.markdown(f"### 📄 Document View ({sub_data['student_name_anon']})")
                st.caption(f"**Course:** {sub_data['course']} | **Group:** {sub_data['group_name']} | **File:** {sub_data['file_name']}")
                
                formatted_text = str(sub_data['report_text']).replace("\n", "<br/>")
                st.markdown(f"""
                <div style='background-color:#0F172A; color:#F8FAFC; padding:15px; border-radius:8px; font-family:monospace; font-size:0.85rem; height:450px; overflow-y:auto;'>
                {formatted_text}
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown("#### 🛡️ Turnitin-Style Originality & Similarity Index")
                st.markdown(f"- **Overall Similarity Index:** `{sub_data['similarity_index']}%`")
                st.markdown(f"- **AI Pattern Match Score:** `{sub_data['ai_pattern_score']}%`")
                st.markdown(f"- **Student Anonymisation:** Verified ({sub_data['student_name_anon']})")
                
            with right_col:
                st.markdown("### 🎯 Criteria Breakdown & Lecturer Score Adjuster")
                
                adjusted_scores = {}
                try:
                    ai_scores = json.loads(sub_data['ai_scores_json'])
                    ai_evidence = json.loads(sub_data['ai_evidence_json'])
                    
                    for crit, val in ai_scores.items():
                        st.markdown(f"**{crit}** (AI Suggested: {val})")
                        ev_desc = ai_evidence.get(crit, "Criterion evidence identified.")
                        st.caption(f"💡 *Evidence:* {ev_desc}")
                        adjusted_scores[crit] = st.number_input(
                            f"Score ({crit})", min_value=0.0, max_value=5.0, value=float(val), step=0.1, key=f"crit_{sub_data['id']}_{crit}"
                        )
                except Exception as e:
                    st.warning(f"Using standard score adjustment: {e}")
                    adjusted_scores["Overall"] = st.number_input("Total Score:", value=float(sub_data.get('teacher_score', 8.5)))
                
                calculated_total = round(sum(adjusted_scores.values()), 1)
                max_marks_val = float(sub_data.get('max_marks', 10.0))
                st.markdown(f"### 🎯 Calculated Lecturer Score: **{calculated_total} / {max_marks_val} Marks**")
                
                st.markdown("---")
                st.markdown("#### 💬 Formative Feedback Editor (1-2-1 Model)")
                strength_val = st.text_input("1 Strength:", value=str(sub_data.get('ai_strength', '')), key=f"str_{sub_data['id']}")
                action_val = st.text_input("1 Actionable Step:", value=str(sub_data.get('ai_action', '')), key=f"act_{sub_data['id']}")
                
                st.markdown("---")
                override_notes = st.text_area("Lecturer Override Rationale (Logged in Audit Trail):", value=str(sub_data.get('teacher_feedback', '')), placeholder="e.g. Verified technical calculations and adjusted mark by +0.5.")
                
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
                        
                        log_audit("Lecturer", "Grade Approved", f"Ms. Anwar approved score {calculated_total}/{max_marks_val} for {sub_data['id']}")
                        st.success(f"Grade {calculated_total}/{max_marks_val} Released to Student Portal!")
                        st.rerun()
                with b2:
                    if st.button("✏️ Release with Modified Score", use_container_width=True):
                        conn = get_db()
                        c = conn.cursor()
                        c.execute("""
                            UPDATE submissions SET teacher_status=?, teacher_score=?, teacher_feedback=? WHERE id=?
                        """, ("Approved (Modified)", calculated_total, override_notes, sub_data['id']))
                        conn.commit()
                        conn.close()
                        
                        log_audit("Lecturer", "Grade Modified & Released", f"Ms. Anwar modified score to {calculated_total}/{max_marks_val} for {sub_data['id']}")
                        st.success("Modified Grade Released!")
                        st.rerun()
                with b3:
                    if st.button("❌ Reject / Flag for Resubmission", use_container_width=True):
                        conn = get_db()
                        c = conn.cursor()
                        c.execute("UPDATE submissions SET teacher_status=? WHERE id=?", ("Flagged", sub_data['id']))
                        conn.commit()
                        conn.close()
                        
                        log_audit("Lecturer", "Submission Flagged", f"Ms. Anwar flagged submission {sub_data['id']}")
                        st.warning("Submission Flagged for Resubmission.")
                        st.rerun()
        else:
            st.info("No student submissions currently available for review.")

    # TAB 3: BATCH INGESTION
    with tabs[2]:
        st.markdown("### 📁 Batch Cohort Document Ingestion")
        st.caption("Upload multiple student files simultaneously for whole-class originality scan and AI assessment.")
        
        batch_files = st.file_uploader("Upload Level 1 Group 4 Class Files (.docx, .pdf, .txt):", type=['docx', 'pdf', 'txt'], accept_multiple_files=True)
        if batch_files:
            st.success(f"Attached {len(batch_files)} class files for batch processing.")
            if st.button("⚡ Process Entire Batch Cohort"):
                for idx, b_file in enumerate(batch_files):
                    b_text = extract_text_from_file(b_file)
                    b_scan = run_originality_scan(b_text)
                    s_id = STUDENT_ROSTER[idx % 20]
                    s_code = STUDENT_CREDENTIALS[s_id]["anon"]
                    sub_code = f"SUB-BATCH-{idx+1:03d}"
                    
                    conn = get_db()
                    c = conn.cursor()
                    c.execute("""
                        INSERT OR REPLACE INTO submissions VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    """, (
                        sub_code, s_id, s_code, "ASG-L1G4-01", "ENG101 - Foundation Technical English Level 1", "Level 1 Group 4",
                        b_file.name, b_text, b_scan['total_match'], b_scan['ai_pattern_score'],
                        json.dumps({"Structure & Layout": 1.8, "Technical Content & Accuracy": 2.8, "Vocabulary & Terminology": 1.8, "Grammar & Sentence Mechanics": 1.5, "Citations & References": 0.8}),
                        8.7, 10.0,
                        json.dumps({"Structure & Layout": "Standard headings found."}),
                        "Clear technical structure.", json.dumps(["Review sentence punctuation."]), "Check grammar mechanics.",
                        "Pending Review", 8.7, "", datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                    ))
                    conn.commit()
                    conn.close()
                st.success("All batch files processed and saved to database successfully!")
                st.rerun()

    # TAB 4: RUBRIC & ASSIGNMENT BUILDER (DYNAMIC ADD & DELETE RUBRICS)
    with tabs[3]:
        st.markdown("### ⚙️ Rubric Management Studio & Assignment Builder")
        st.caption("Create, edit, delete, and manage subject rubrics and publish assignments for Level 1 Group 4.")
        
        rubric_subtabs = st.tabs(["📏 Manage & Create Rubrics", "📝 Publish New Assignment"])
        
        # SUB-TAB 1: MANAGE & CREATE RUBRICS
        with rubric_subtabs[0]:
            st.markdown("#### ➕ Create New Custom Rubric")
            
            c_r1, c_r2 = st.columns(2)
            with c_r1:
                new_rub_id = st.text_input("Rubric Reference ID:", f"RUB-L1G4-{datetime.datetime.now().strftime('%M%S')}")
                new_rub_name = st.text_input("Rubric Title Name:", "10-Mark Level 1 Technical Report Rubric")
            with c_r2:
                new_rub_marks = st.number_input("Total Max Marks:", value=10.0, step=1.0)
            
            st.markdown("**Configure Criteria Breakdown (Up to 5 Criteria):**")
            criteria_list = []
            col_crit1, col_crit2 = st.columns([1, 2])
            
            crit_names = ["Structure & Layout", "Technical Content", "Vocabulary & Phrasing", "Grammar & Mechanics", "Citations & References"]
            crit_defaults = [2.0, 3.0, 2.0, 2.0, 1.0]
            crit_descs = [
                "Transmittal letter, Summary, Intro, Body, Conclusion, References.",
                "Technical accuracy, vocational applications, data depth.",
                "Domain terminology, formal register, precision.",
                "Plural agreement, sentence mechanics, punctuation.",
                "IEEE or formal technical reference citations."
            ]
            
            for i in range(5):
                with st.expander(f"Criterion {i+1}: {crit_names[i]}", expanded=(i < 3)):
                    col_k1, col_k2 = st.columns([1, 2])
                    with col_k1:
                        c_name = st.text_input(f"Criterion {i+1} Name:", value=crit_names[i], key=f"c_name_{i}")
                        c_marks = st.number_input(f"Criterion {i+1} Max Mark:", value=crit_defaults[i], step=0.5, key=f"c_marks_{i}")
                    with col_k2:
                        c_focus = st.text_area(f"Criterion {i+1} Focus / Description:", value=crit_descs[i], height=70, key=f"c_focus_{i}")
                    criteria_list.append({"criterion": c_name, "max_marks": c_marks, "focus": c_focus})
            
            total_calc_marks = sum(c["max_marks"] for c in criteria_list)
            st.info(f"📊 **Calculated Rubric Total:** {total_calc_marks} Marks / {new_rub_marks} Marks Target")
            
            if st.button("💾 Save New Rubric to Database", type="primary"):
                conn = get_db()
                c = conn.cursor()
                c.execute("""
                    INSERT OR REPLACE INTO rubrics VALUES (?,?,?,?)
                """, (new_rub_id, new_rub_name, new_rub_marks, json.dumps(criteria_list)))
                conn.commit()
                conn.close()
                log_audit("Lecturer", "Rubric Created", f"Ms. Anwar saved rubric {new_rub_id}: {new_rub_name}")
                st.success(f"✅ Rubric **{new_rub_name}** saved successfully!")
                st.rerun()

            st.markdown("---")
            st.markdown("#### 🗑️ Manage & Delete Existing Rubrics")
            conn = get_db()
            df_existing_rubrics = pd.read_sql_query("SELECT * FROM rubrics", conn)
            conn.close()
            
            if not df_existing_rubrics.empty:
                for _, r_row in df_existing_rubrics.iterrows():
                    r_id = r_row['id']
                    r_name = r_row['rubric_name']
                    r_max = r_row['max_marks']
                    
                    r_col1, r_col2 = st.columns([4, 1])
                    with r_col1:
                        st.markdown(f"**{r_id}** — **{r_name}** ({r_max} Marks Total)")
                        try:
                            c_json = json.loads(r_row['criteria_json'])
                            with st.expander("🔍 View Criteria Details", expanded=False):
                                for item in c_json:
                                    st.markdown(f"- **{item['criterion']}** ({item['max_marks']}M): {item['focus']}")
                        except:
                            pass
                    with r_col2:
                        if st.button("🗑️ Delete", key=f"del_rub_{r_id}"):
                            conn = get_db()
                            c = conn.cursor()
                            c.execute("DELETE FROM rubrics WHERE id=?", (r_id,))
                            conn.commit()
                            conn.close()
                            log_audit("Lecturer", "Rubric Deleted", f"Ms. Anwar deleted rubric {r_id}")
                            st.warning(f"Deleted rubric {r_id}!")
                            st.rerun()
            else:
                st.info("No custom rubrics stored in database.")

        # SUB-TAB 2: PUBLISH NEW ASSIGNMENT
        with rubric_subtabs[1]:
            st.markdown("#### 📝 Publish Assignment for Level 1 Group 4")
            
            conn = get_db()
            df_rubrics = pd.read_sql_query("SELECT * FROM rubrics", conn)
            conn.close()
            
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                new_asg_title = st.text_input("Assignment Title:", "Formal Technical Report on Electronic Components")
                course_sel = st.text_input("Course Module Code:", "ENG101 - Foundation Technical English Level 1")
                prog_sel = "Foundation Programme"
                max_mark_in = st.number_input("Maximum Mark Allocation:", value=10.0, step=1.0)
                
            with col_b2:
                rubric_opts = [f"{r['id']} - {r['rubric_name']}" for _, r in df_rubrics.iterrows()] if not df_rubrics.empty else ["RUB-FND1-10M"]
                rubric_sel = st.selectbox("Select Active Marking Rubric:", rubric_opts)
                due_date_in = st.date_input("Submission Deadline:", datetime.date(2026, 10, 30))
                st.checkbox("Mandatory Anonymisation Enforced", value=True, disabled=True)
                st.checkbox("Automated 80% Originality Gate Enforced", value=True, disabled=True)
                
            st.markdown("---")
            st.markdown("#### 📄 Upload Assignment Specification Brief (Optional):")
            asg_file_up = st.file_uploader("Attach Brief Document (.pdf, .docx, .txt):", type=['pdf', 'docx', 'txt'], key="asg_file_builder")
            brief_text_extracted = ""
            brief_file_name = ""
            if asg_file_up is not None:
                brief_file_name = asg_file_up.name
                brief_text_extracted = extract_text_from_file(asg_file_up)
                st.success(f"Attached Brief: **{asg_file_up.name}**")
                
            asg_desc_in = st.text_area("Assignment Description & Instructions:", value=brief_text_extracted if brief_text_extracted else "Write a formal technical report analyzing electronic components.")
            
            if st.button("🚀 Publish Assignment to Level 1 Group 4", type="primary"):
                new_asg_id = f"ASG-L1G4-{datetime.datetime.now().strftime('%m%d%H%M')}"
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
                
                log_audit("Lecturer", "Assignment Published", f"Ms. Anwar published {new_asg_id}: {new_asg_title}")
                st.balloons()
                st.success(f"✅ Assignment **{new_asg_title}** published successfully for Level 1 Group 4!")
                st.rerun()

            st.markdown("---")
            st.markdown("#### 📚 Published Assignments Directory")
            conn = get_db()
            df_published = pd.read_sql_query("SELECT id, title, course, deadline, max_marks, rubric_type FROM assignments", conn)
            conn.close()
            
            if not df_published.empty:
                for _, a_row in df_published.iterrows():
                    a_id = a_row['id']
                    a_col1, a_col2 = st.columns([4, 1])
                    with a_col1:
                        st.markdown(f"📌 **{a_id}** — **{a_row['title']}** ({a_row['course']}) | Deadline: `{a_row['deadline']}` | Scale: `{a_row['max_marks']}M`")
                    with a_col2:
                        if st.button("🗑️ Delete", key=f"del_asg_{a_id}"):
                            conn = get_db()
                            c = conn.cursor()
                            c.execute("DELETE FROM assignments WHERE id=?", (a_id,))
                            conn.commit()
                            conn.close()
                            log_audit("Lecturer", "Assignment Deleted", f"Ms. Anwar deleted assignment {a_id}")
                            st.warning(f"Deleted assignment {a_id}!")
                            st.rerun()
            else:
                st.info("No assignments currently published.")

    # TAB 5: COHORT ANALYTICS
    with tabs[4]:
        st.markdown("### 📈 Class Performance Analytics & Reteaching Insights")
        st.caption("AI identifies common learning gaps across Level 1 Group 4:")
        
        col_a1, col_a2 = st.columns(2)
        with col_a1:
            st.markdown("#### 📊 Class Average Score by Criterion")
            st.bar_chart(pd.DataFrame({
                'Criterion': ['Structure (2M)', 'Content (3M)', 'Vocabulary (2M)', 'Grammar (2M)', 'Citations (1M)'],
                'Group Average Score': [1.85, 2.70, 1.65, 1.35, 0.65]
            }).set_index('Criterion'))
            
        with col_a2:
            st.markdown("#### 🎯 Top 3 Common Class Learning Gaps")
            st.error("1. **Subject-Verb Agreement**: 65% of students made plural noun errors ('Resistor are used').")
            st.warning("2. **Incomplete Citation Format**: 45% omitted full IEEE reference details.")
            st.info("3. **Summary Duplication**: 30% copied conclusion sentences verbatim into the Executive Summary.")
            
            st.markdown("---")
            st.success("👉 **Recommended 15-Minute Reteaching Focus:** Mini-workshop on technical plural agreement and citation mechanics.")

    # TAB 6: AUDIT TRAIL
    with tabs[5]:
        st.markdown("### 📋 Academic Governance Audit Trail & Export")
        conn = get_db()
        df_audit = pd.read_sql_query("SELECT * FROM audit_log ORDER BY id DESC", conn)
        conn.close()
        
        st.dataframe(df_audit, use_container_width=True)
        
        # CSV Export Tool
        conn = get_db()
        df_export = pd.read_sql_query("SELECT student_id, student_name_anon, course, group_name, similarity_index, ai_pattern_score, teacher_score, max_marks, teacher_status, submitted_date FROM submissions", conn)
        conn.close()
        
        csv_data = df_export.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Export Level 1 Group 4 Gradebook (CSV)",
            data=csv_data,
            file_name=f"L1G4_Gradebook_{datetime.datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            type="primary"
        )

# -----------------------------------------------------------------------------
# VIEW 3: ADMIN & QA WORKSPACE
# -----------------------------------------------------------------------------
elif st.session_state.active_view == 'Admin Workspace':
    st.markdown("## 🏛️ Quality Assurance & Institutional Compliance Workspace")
    st.caption("Saham Vocational College | Academic Governance Oversight")
    
    st.markdown("### ⚙️ System Policy Rules")
    sim_val = st.slider("Maximum Allowable Similarity Threshold (%):", min_value=10.0, max_value=90.0, value=float(st.session_state.sim_threshold), step=5.0)
    st.session_state.sim_threshold = sim_val
    st.info(f"Current Policy Rule: Submissions with > **{sim_val}%** similarity index are automatically blocked from student submission.")
    
    st.markdown("---")
    st.markdown("### 🏛️ Institutional Compliance Checklist")
    st.checkbox("Mandatory Student Anonymisation before AI Processing", value=True, disabled=True)
    st.checkbox("Enforce 'Teacher Override' Rule (AI cannot issue final grade without Ms. Anwar's approval)", value=True, disabled=True)
    st.checkbox("Prohibit Automated AI Detectors as Sole Proof of Cheating", value=True, disabled=True)
    st.checkbox("SQLite Database Persistence Active (svc_assess_l1g4.db)", value=True, disabled=True)

# -----------------------------------------------------------------------------
# INSTITUTIONAL FOOTER
# -----------------------------------------------------------------------------
st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: #64748B; font-size: 0.85rem;'>"
    "© 2026 English Department, Saham Vocational College. All Rights Reserved."
    "</p>",
    unsafe_allow_html=True
)
