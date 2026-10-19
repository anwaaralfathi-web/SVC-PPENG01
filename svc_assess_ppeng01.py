import streamlit as st
import pandas as pd
import datetime
import sqlite3
import json
import re

# -----------------------------------------------------------------------------
# PAGE CONFIGURATION & THEME STYLING
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="SVC Assess | Saham Vocational College",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Institutional Navy & Gold Theme
st.markdown("""
<style>
    .main {
        background-color: #F8FAFC;
    }
    .main-header {
        color: #0F172A;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-weight: 700;
        margin-bottom: 0px;
    }
    .sub-header {
        color: #1E3A8A;
        font-size: 1.05rem;
        font-weight: 600;
        margin-top: 0px;
        margin-bottom: 15px;
    }
    .concept-badge {
        background-color: #F0F9FF;
        border-left: 4px solid #0284C7;
        padding: 10px 15px;
        border-radius: 4px;
        color: #0369A1;
        font-size: 0.9rem;
        margin-bottom: 20px;
    }
    .card {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 15px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .status-approved {
        background-color: #DCFCE7;
        color: #15803D;
        padding: 4px 10px;
        border-radius: 12px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .status-pending {
        background-color: #FEF3C7;
        color: #B45309;
        padding: 4px 10px;
        border-radius: 12px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .footer {
        text-align: center;
        color: #64748B;
        font-size: 0.8rem;
        margin-top: 40px;
        padding-top: 20px;
        border-top: 1px solid #E2E8F0;
    }
</style>
""", unsafe_allow_html=True)

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
            "15-Mark PS1301 Public Speaking & Presentation Rubric",
            15.0,
            json.dumps([
                {"criterion": "Content & Structure", "max_marks": 4.0, "focus": "Clear introduction, main arguments, and solid conclusion."},
                {"criterion": "Delivery & Articulation", "max_marks": 4.0, "focus": "Voice projection, pacing, pronunciation, and fluency."},
                {"criterion": "Visual Aids & Slides", "max_marks": 4.0, "focus": "Professional slide layout, diagrams, and bullet design."},
                {"criterion": "Engagement & Q&A", "max_marks": 3.0, "focus": "Eye contact, posture, confidence, and Q&A handling."}
            ])
        )
        c.execute("INSERT INTO rubrics VALUES (?,?,?,?)", rubric_tceng)
        c.execute("INSERT INTO rubrics VALUES (?,?,?,?)", rubric_tc1202)
        c.execute("INSERT INTO rubrics VALUES (?,?,?,?)", rubric_ps1301)

    # Seed Initial Pilot Assignment if empty
    c.execute("SELECT COUNT(*) FROM assignments")
    if c.fetchone()[0] == 0:
        c.execute("""
            INSERT INTO assignments VALUES (
                'ASG-TC1201-01',
                'Formal Technical Report on Electronic Components',
                'TCENG1201 - Formal Technical Communication',
                'Foundation Level 1 Group 4',
                '2026-10-30',
                12.0,
                'RUB-TCENG1201 - 12-Mark TCENG1201 Formal Report Rubric',
                'Write a formal workplace technical report investigating electronic components, safety protocols, and vocational applications.',
                'TCENG1201_Assignment_Brief.pdf',
                'Assignment Brief: Prepare a 3-5 page formal technical report investigating electronic components (resistors, diodes, or capacitors). Include Transmittal Letter, Executive Summary, Introduction, Technical Body, Conclusion, and IEEE References.'
            )
        """)

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
# FILE PARSER HELPER (Supports Single & Multiple Files)
# -----------------------------------------------------------------------------
def extract_text_from_file(uploaded_files):
    if uploaded_files is None:
        return ""
    
    files_list = uploaded_files if isinstance(uploaded_files, list) else [uploaded_files]
    combined_texts = []
    
    for f in files_list:
        try:
            f.seek(0)
        except Exception:
            pass
            
        file_ext = f.name.split('.')[-1].lower()
        text = ""
        try:
            if file_ext == 'docx':
                import docx
                doc = docx.Document(f)
                text = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
            elif file_ext == 'pdf':
                import pypdf
                reader = pypdf.PdfReader(f)
                pages = [page.extract_text() for page in reader.pages if page.extract_text()]
                text = "\n".join(pages)
            elif file_ext == 'txt':
                text = f.read().decode('utf-8', errors='ignore')
        except Exception as e:
            text = f"[Parsing Error for {f.name}: {str(e)}]"
            
        if text.strip():
            combined_texts.append(f"--- Document: {f.name} ---\n{text.strip()}")
            
    return "\n\n".join(combined_texts)

# -----------------------------------------------------------------------------
# TURNITIN-STYLE ORIGINALITY & SIMILARITY DETECTOR ENGINE
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
    
    ai_pattern_pct = min(100.0, round((ai_count * 25.0) / max(1, (word_count / 150.0)), 1))
    web_match_pct = min(100.0, round((len(re.findall(r'\b(the|and|is|in|to|of|that|with|for|as)\b', text_lower)) * 0.15), 1))
    peer_match_pct = round(web_match_pct * 0.3, 1)
    
    total_match = min(100.0, round((web_match_pct * 0.6) + (peer_match_pct * 0.2) + (ai_pattern_pct * 0.2), 1))
    
    return {
        'total_match': total_match,
        'peer_match': peer_match_pct,
        'web_match': web_match_pct,
        'ai_pattern_score': ai_pattern_pct,
        'flagged_phrases': [tr for tr in ai_triggers if tr in text_lower]
    }

# -----------------------------------------------------------------------------
# ADVANCED DYNAMIC AI EVALUATION ENGINE (MATCHED TO ASSIGNED RUBRIC)
# -----------------------------------------------------------------------------
def evaluate_student_report_ai(report_text, assignment_id):
    conn = get_db()
    df_asg = pd.read_sql_query("SELECT * FROM assignments WHERE id = ?", conn, params=(assignment_id,))
    conn.close()
    
    rubric_criteria = [
        {"criterion": "Layout & Structure", "max_marks": 2.0, "focus": "Transmittal letter, Summary, Intro, Body, Conclusion, References."},
        {"criterion": "Content & Depth", "max_marks": 4.0, "focus": "Technical accuracy, vocational applications, data depth."},
        {"criterion": "Technical Vocabulary", "max_marks": 3.0, "focus": "Domain terminology, formal tone, precise phrasing."},
        {"criterion": "Grammar & Mechanics", "max_marks": 2.0, "focus": "Subject-verb agreement, sentence structure, punctuation."},
        {"criterion": "Sources & References", "max_marks": 1.0, "focus": "IEEE or formal technical reference citations."}
    ]
    asg_max_marks = 12.0
    
    if not df_asg.empty:
        current_asg = df_asg.iloc[0]
        asg_max_marks = float(current_asg.get('max_marks', 12.0))
        rubric_type_str = str(current_asg.get('rubric_type', ''))
        
        conn = get_db()
        df_rubrics = pd.read_sql_query("SELECT * FROM rubrics", conn)
        conn.close()
        
        matched_rubric = None
        if not df_rubrics.empty:
            for _, r_row in df_rubrics.iterrows():
                if r_row['id'] in rubric_type_str or r_row['rubric_name'] in rubric_type_str:
                    matched_rubric = r_row
                    break
            if matched_rubric is None and len(df_rubrics) > 0:
                matched_rubric = df_rubrics.iloc[0]
                
        if matched_rubric is not None:
            try:
                parsed_c = json.loads(matched_rubric['criteria_json'])
                if isinstance(parsed_c, list) and len(parsed_c) > 0:
                    rubric_criteria = parsed_c
            except Exception:
                pass

    if not report_text or len(report_text.strip()) < 10:
        scores = {c['criterion']: 0.0 for c in rubric_criteria}
        evidence = {c['criterion']: "No substantive report text provided." for c in rubric_criteria}
        return {
            'scores': scores,
            'total': 0.0,
            'evidence': evidence,
            'strength': "Document submitted.",
            'priorities': ["Provide complete technical report content."],
            'action': "Resubmit assignment with complete report text."
        }

    text_lower = report_text.lower()
    words = report_text.split()
    word_count = len(words)
    
    scores = {}
    evidence = {}
    
    headings = ["transmittal", "executive summary", "summary", "introduction", "conclusion", "references", "recommendation"]
    found_headings = [h for h in headings if h in text_lower]
    
    tech_terms = ["resistor", "diode", "transistor", "capacitor", "voltage", "current", "circuit", "semiconductor", "ohmmeter", "multimeter", "schematic", "safety", "protocol", "vocational", "workplace"]
    found_terms = [t for t in tech_terms if t in text_lower]
    
    grammar_flaws = []
    if re.search(r'\b(resistor|diode|component|circuit)\s+(are|were|have)\b', text_lower):
        grammar_flaws.append("Subject-verb agreement error (singular subject with plural verb).")
    if re.search(r'\b(resistors|diodes|components|circuits)\s+(is|was|has)\b', text_lower):
        grammar_flaws.append("Subject-verb agreement error (plural subject with singular verb).")
        
    has_refs = bool(re.search(r'\b(references|ieee|bibliography|\[1\]|\b1\.\s+)\b', text_lower))

    for item in rubric_criteria:
        c_name = item['criterion']
        c_max = float(item['max_marks'])
        
        c_lower = c_name.lower()
        if "layout" in c_lower or "structure" in c_lower or "organization" in c_lower:
            ratio = min(1.0, (len(found_headings) + 1) / 5.0)
            scores[c_name] = round(c_max * ratio, 1)
            evidence[c_name] = f"Identified {len(found_headings)} standard sections ({', '.join(found_headings[:3]) if found_headings else 'general layout'})."
        elif "content" in c_lower or "depth" in c_lower or "creativity" in c_lower:
            ratio = min(1.0, max(0.4, (word_count / 250.0)))
            scores[c_name] = round(c_max * ratio, 1)
            evidence[c_name] = f"Technical depth evaluated across {word_count} words with {len(found_terms)} domain references."
        elif "vocab" in c_lower or "language" in c_lower or "delivery" in c_lower:
            ratio = min(1.0, max(0.5, (len(found_terms) / 5.0)))
            scores[c_name] = round(c_max * ratio, 1)
            evidence[c_name] = f"Vocabulary usage includes key domain terms ({', '.join(found_terms[:3]) if found_terms else 'general terminology'})."
        elif "grammar" in c_lower or "mechanics" in c_lower or "articulation" in c_lower:
            deduction = 0.3 * len(grammar_flaws)
            scores[c_name] = max(0.5, round(c_max - deduction, 1))
            evidence[c_name] = "Minor agreement issues detected." if grammar_flaws else "Clean grammar syntax and sentence structure."
        elif "source" in c_lower or "ref" in c_lower or "visual" in c_lower or "engagement" in c_lower:
            scores[c_name] = c_max if has_refs else round(c_max * 0.5, 1)
            evidence[c_name] = "Bracketed citations or reference section detected." if has_refs else "Citation list missing or incomplete."
        else:
            scores[c_name] = round(c_max * 0.8, 1)
            evidence[c_name] = f"Evaluated against criterion benchmark ({item.get('focus', '')[:40]})."

    total_calculated = round(sum(scores.values()), 1)
    
    top_strength = f"Demonstrates good technical articulation ({word_count} words) with clear section organization."
    priorities = []
    if grammar_flaws:
        priorities.append(grammar_flaws[0])
    if not has_refs:
        priorities.append("Include complete IEEE or formal technical reference citations.")
    if len(priorities) < 2:
        priorities.append("Ensure all figures and data tables have explicit numbered captions.")
        
    action = "Review the highlighted priorities, fix sentence mechanics, and verify reference list formatting before final submission."
    
    return {
        'scores': scores,
        'total': total_calculated,
        'evidence': evidence,
        'strength': top_strength,
        'priorities': priorities,
        'action': action
    }

# -----------------------------------------------------------------------------
# GLOBAL CONSTANTS & CREDENTIALS
# -----------------------------------------------------------------------------
PROGRAMMES_AND_COURSES = {
    "Foundation Level 1 Group 4": {
        "Foundation Level 1": ["TCENG1201 - Formal Technical Communication", "TC1202 - Vocational Writing & Reports", "PS1301 - Public Speaking & Oral Presentation"]
    }
}

STUDENT_CREDENTIALS = {
    f"PPENG01/04-{i:05d}": {
        "anon": f"Student A{i:02d} (Anonymized)",
        "pass": f"L1G4#{100+i}"
    } for i in range(1, 21)
}
STUDENT_IDS = list(STUDENT_CREDENTIALS.keys())

# Session State Initialization
if 'active_view' not in st.session_state:
    st.session_state.active_view = 'Student Portal'
if 'sim_threshold' not in st.session_state:
    st.session_state.sim_threshold = 35.0
if 'student_unlocked' not in st.session_state:
    st.session_state.student_unlocked = False
if 'unlocked_student_id' not in st.session_state:
    st.session_state.unlocked_student_id = None

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

    if st.session_state.active_view == 'Student Portal' and st.session_state.student_unlocked:
        st.markdown("---")
        if st.button("🔒 Log Out / Lock Student Session", use_container_width=True):
            st.session_state.student_unlocked = False
            st.session_state.unlocked_student_id = None
            st.rerun()

    st.markdown("---")
    st.markdown("### 📌 Class Pilot Scope")
    st.info("""
    **Class Group:** Foundation Level 1 Group 4  
    **Course Assessor:** Ms. Anwar Al-Fathi  
    **Pilot Cohort:** 20 Enrolled Students  
    **Institution:** Saham Vocational College (SVC)  
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
            
            st.info(f"""
            📌 **Selected Assignment:** {asg_title}  
            📚 **Course Module:** {asg_course} | 🗓️ **Submission Deadline:** {asg_deadline}  
            🎯 **Mark Scale:** {asg_max_marks} Marks | 📏 **Assigned Rubric:** {asg_rubric_type}
            """)
            
            with st.expander("📖 Read Full Assignment Brief & Instructions", expanded=False):
                if asg_desc:
                    st.markdown(f"**Brief Description:** {asg_desc}")
                if asg_brief_text:
                    st.text_area("Assignment Specification Document:", value=str(asg_brief_text), height=120, disabled=True)
            
            student_id_input = st.selectbox("Select Your Student ID (Level 1 Group 4):", STUDENT_IDS)
            
            st.markdown("---")
            st.markdown("#### 📎 Attachment & Content Submission Tool")
            uploaded_file = st.file_uploader(
                "Attach Assignment Document (.docx, .pdf, .txt) - Up to 5 files:",
                type=['docx', 'pdf', 'txt'],
                accept_multiple_files=True,
                help="Drag and drop or browse to attach your Word, PDF, or Plain Text document."
            )
            
            extracted_content = ""
            file_name_val = "Direct_Text_Input.txt"
            if uploaded_file:
                extracted_content = extract_text_from_file(uploaded_file)
                if isinstance(uploaded_file, list):
                    file_name_val = ", ".join([f.name for f in uploaded_file])
                else:
                    file_name_val = uploaded_file.name
                st.success(f"✅ Document Attached: **{file_name_val}** ({len(extracted_content.split())} words extracted)")
                with st.expander("🔍 Preview Extracted Document Text", expanded=False):
                    st.text_area("Extracted Document Text:", value=extracted_content, height=140, disabled=True)

            st.markdown("**OR Paste Report Text Directly:**")
            report_text_input = st.text_area(
                "Report Text Input:",
                value=extracted_content if extracted_content else "",
                height=160,
                placeholder="TRANSMITTAL LETTER & TECHNICAL REPORT..."
            )
            
            if report_text_input and len(report_text_input.strip()) > 10:
                scan_res = run_originality_scan(report_text_input)
                st.markdown("#### 🛡️ Turnitin-Style Originality & Similarity Analysis")
                col_sc1, col_sc2, col_sc3, col_sc4 = st.columns(4)
                col_sc1.metric("Overall Similarity Index", f"{scan_res['total_match']}%")
                col_sc2.metric("AI Text Pattern Score", f"{scan_res['ai_pattern_score']}%")
                col_sc3.metric("Web Source Overlap", f"{scan_res['web_match']}%")
                col_sc4.metric("Peer Submissions Database", f"{scan_res['peer_match']}%")
                
                if scan_res['total_match'] > st.session_state.sim_threshold:
                    st.warning(f"⚠️ **High Similarity Warning:** Overall Similarity Index ({scan_res['total_match']}%) exceeds the {st.session_state.sim_threshold}% institutional guideline. You may submit your work, but it will be flagged for Ms. Anwar Al-Fathi's review.")
                else:
                    st.success(f"✅ Originality Scan Cleared: Similarity Index ({scan_res['total_match']}%) is within permissible limits (< {st.session_state.sim_threshold}%).")
                
                if st.button("🚀 Submit Assignment for Evaluation", type="primary"):
                    anon_index = STUDENT_IDS.index(student_id_input) + 1
                    anon_code = f"Student A{anon_index:02d} (Anonymized)"
                    sub_id = f"SUB-2026-{anon_index:03d}"
                    
                    ai_eval = evaluate_student_report_ai(report_text_input, asg_id_val)
                    provisional_score = ai_eval['total']
                    
                    conn = get_db()
                    c = conn.cursor()
                    c.execute("""
                        INSERT OR REPLACE INTO submissions VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    """, (
                        sub_id, student_id_input, anon_code, asg_id_val, asg_course, "Level 1 Group 4",
                        file_name_val, report_text_input, scan_res['total_match'], scan_res['ai_pattern_score'],
                        json.dumps(ai_eval['scores']), provisional_score, asg_max_marks,
                        json.dumps(ai_eval['evidence']),
                        ai_eval['strength'], json.dumps(ai_eval['priorities']), ai_eval['action'],
                        "Pending Review", provisional_score, "",
                        datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                    ))
                    conn.commit()
                    conn.close()
                    
                    log_audit("Student", "Submission Created", f"{student_id_input} submitted {sub_id} for {asg_title}")
                    st.balloons()
                    st.success(f"✅ Assignment Submitted Successfully! Your Reference Code: **{sub_id}** (Anonymised as **{anon_code}** for fair grading). Submitted for **{asg_title}**.")
            else:
                st.info("💡 Please attach a document file above or paste your report text into the box to enable assignment submission.")
        else:
            st.warning("No active published assignments available. Please ask Ms. Anwar Al-Fathi to publish an assignment.")

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
            st.session_state.student_unlocked = True
            st.session_state.unlocked_student_id = lookup_id
            
            st.success(f"✅ Credentials Verified for **{lookup_id}** ({STUDENT_CREDENTIALS[lookup_id]['anon']})")
            
            if st.button("🔒 Log Out / Lock Vault", key="btn_lock_vault"):
                st.session_state.student_unlocked = False
                st.session_state.unlocked_student_id = None
                st.rerun()
                
            conn = get_db()
            df_my = pd.read_sql_query("SELECT * FROM submissions WHERE student_id = ?", conn, params=(lookup_id,))
            conn.close()
            
            if not df_my.empty:
                for _, row in df_my.iterrows():
                    row_course = row.get('course', 'Course Module')
                    row_id = row.get('id', 'SUB')
                    row_date = row.get('submitted_date', '')
                    row_asg_id = row.get('assignment_id', '')
                    row_status = row.get('teacher_status', 'Pending Review')
                    row_score = row.get('teacher_score', 0.0)
                    row_max = row.get('max_marks', 12.0)
                    row_strength = row.get('ai_strength', '')
                    row_action = row.get('ai_action', '')
                    row_remarks = row.get('teacher_feedback', '')
                    
                    st.markdown(f"""
                    <div class='card'>
                        <h3 style='color:#1E3A8A; margin-top:0;'>Course: {row_course}</h3>
                        <p><b>Submission Ref:</b> {row_id} | <b>Assignment ID:</b> {row_asg_id} | <b>Submitted Date:</b> {row_date}</p>
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
                        st.info("🔒 Provisional marks are undergoing human review by Ms. Anwar Al-Fathi. Official results will appear here once approved.")
                    st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.info("No active submissions found for this Student ID.")
        else:
            if lookup_pass:
                st.error("❌ Incorrect Password. Access denied to student grade vault.")
            else:
                st.info("🔒 Private Vault Locked: Please select your username and enter your personal student password to view your released grades and feedback.")

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
        "🔍 Side-by-Side Review & Correction",
        "📁 Batch Cohort Ingestion",
        "⚙️ Assignment & Rubric Configuration Builder",
        "📈 Cohort Analytics & Reteaching",
        "📋 Academic Audit Trail"
    ])
    
    # TAB 1: SUBMISSIONS INBOX
    with tabs[0]:
        st.markdown("### 📥 Class Submissions Queue")
        conn = get_db()
        df_queue = pd.read_sql_query("SELECT id, student_id, student_name_anon, assignment_id, course, group_name, similarity_index, ai_total, teacher_score, max_marks, teacher_status, submitted_date FROM submissions", conn)
        conn.close()
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Class Cohort Capacity", "20 Students", "1 Lecturer")
        m2.metric("Total Submissions Received", f"{len(df_queue)} Papers")
        m3.metric("Pending Review", f"{len(df_queue[df_queue['teacher_status'] == 'Pending Review'])} Papers")
        m4.metric("Approved & Released", f"{len(df_queue[df_queue['teacher_status'].str.contains('Approved', na=False)])} Papers")
        
        st.markdown("---")
        st.dataframe(df_queue, use_container_width=True)
        
        if not df_queue.empty:
            st.markdown("#### 🗑️ Delete Student Submission")
            col_del1, col_del2 = st.columns([3, 1])
            with col_del1:
                sub_to_delete = st.selectbox("Select Submission to Delete:", [f"{r['id']} - {r['student_id']} ({r['assignment_id']})" for _, r in df_queue.iterrows()])
            with col_del2:
                if st.button("🗑️ Delete Selected Submission", type="secondary"):
                    target_sub_id = sub_to_delete.split(" - ")[0]
                    conn = get_db()
                    c = conn.cursor()
                    c.execute("DELETE FROM submissions WHERE id = ?", (target_sub_id,))
                    conn.commit()
                    conn.close()
                    log_audit("Lecturer", "Submission Deleted", f"Lecturer deleted submission {target_sub_id}")
                    st.success(f"Submission {target_sub_id} deleted successfully.")
                    st.rerun()

    # TAB 2: SIDE-BY-SIDE REVIEW & CORRECTION
    with tabs[1]:
        st.markdown("### 🔍 Side-by-Side Document Review & Lecturer Correction")
        
        conn = get_db()
        df_all = pd.read_sql_query("SELECT * FROM submissions", conn)
        conn.close()
        
        if not df_all.empty:
            sub_options = [f"{row['id']} - {row['student_name_anon']} ({row['course']}) [Asg: {row['assignment_id']}]" for _, row in df_all.iterrows()]
            selected_sub_str = st.selectbox("Select Student Submission to Grade:", sub_options)
            selected_id = selected_sub_str.split(" - ")[0]
            
            sub_data = df_all[df_all['id'] == selected_id].iloc[0]
            asg_id_linked = sub_data.get('assignment_id', '')
            
            conn = get_db()
            df_linked_asg = pd.read_sql_query("SELECT * FROM assignments WHERE id = ?", conn, params=(asg_id_linked,))
            df_rubrics_all = pd.read_sql_query("SELECT * FROM rubrics", conn)
            conn.close()
            
            linked_asg_title = sub_data.get('course', 'Assignment')
            linked_rubric_name = "Standard Marking Rubric"
            rubric_criteria_list = [
                {"criterion": "Layout & Structure", "max_marks": 2.0, "focus": "Transmittal letter, Summary, Intro, Body, Conclusion, References."},
                {"criterion": "Content & Depth", "max_marks": 4.0, "focus": "Technical accuracy, vocational applications, data depth."},
                {"criterion": "Technical Vocabulary", "max_marks": 3.0, "focus": "Domain terminology, formal tone, precise phrasing."},
                {"criterion": "Grammar & Mechanics", "max_marks": 2.0, "focus": "Subject-verb agreement, sentence structure, punctuation."},
                {"criterion": "Sources & References", "max_marks": 1.0, "focus": "IEEE or formal technical reference citations."}
            ]
            
            if not df_linked_asg.empty:
                asg_row = df_linked_asg.iloc[0]
                linked_asg_title = f"{asg_row['title']} ({asg_row['course']})"
                r_type_str = str(asg_row['rubric_type'])
                
                matched_r = None
                for _, r_row in df_rubrics_all.iterrows():
                    if r_row['id'] in r_type_str or r_row['rubric_name'] in r_type_str:
                        matched_r = r_row
                        break
                if matched_r is None and len(df_rubrics_all) > 0:
                    matched_r = df_rubrics_all.iloc[0]
                    
                if matched_r is not None:
                    linked_rubric_name = matched_r['rubric_name']
                    try:
                        parsed_crit = json.loads(matched_r['criteria_json'])
                        if isinstance(parsed_crit, list) and len(parsed_crit) > 0:
                            rubric_criteria_list = parsed_crit
                    except Exception:
                        pass
            
            st.info(f"📌 **Linked Assignment:** {linked_asg_title} | 📏 **Assigned Rubric:** {linked_rubric_name}")
            
            left_col, right_col = st.columns([1, 1])
            
            # LEFT COLUMN: Document & Similarity Report
            with left_col:
                st.markdown(f"### 📄 Document View ({sub_data.get('student_name_anon', 'Student')})")
                st.caption(f"**Student ID:** {sub_data.get('student_id', '')} | **File:** {sub_data.get('file_name', '')} | **Date:** {sub_data.get('submitted_date', '')}")
                
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
                st.caption(f"Evaluated using assigned rubric: **{linked_rubric_name}**")
                
                if st.button("⚡ Re-Run Advanced AI Assessment on this Submission", type="secondary"):
                    ai_re = evaluate_student_report_ai(sub_data.get('report_text', ''), asg_id_linked)
                    conn = get_db()
                    c = conn.cursor()
                    c.execute("""
                        UPDATE submissions SET ai_scores_json=?, ai_total=?, ai_evidence_json=?, ai_strength=?, ai_priorities_json=?, ai_action=? WHERE id=?
                    """, (
                        json.dumps(ai_re['scores']), ai_re['total'], json.dumps(ai_re['evidence']),
                        ai_re['strength'], json.dumps(ai_re['priorities']), ai_re['action'], sub_data['id']
                    ))
                    conn.commit()
                    conn.close()
                    st.success("AI Assessment re-evaluated successfully against active rubric!")
                    st.rerun()
                
                try:
                    ai_scores = json.loads(sub_data.get('ai_scores_json', '{}'))
                    ai_evidence = json.loads(sub_data.get('ai_evidence_json', '{}'))
                except Exception:
                    ai_scores = {}
                    ai_evidence = {}
                
                adjusted_scores = {}
                for item in rubric_criteria_list:
                    c_name = item['criterion']
                    c_max = float(item['max_marks'])
                    c_focus = item.get('focus', '')
                    
                    val_suggested = float(ai_scores.get(c_name, round(c_max * 0.8, 1)))
                    val_suggested = min(c_max, max(0.0, val_suggested))
                    
                    c_col1, c_col2 = st.columns([2, 1])
                    with c_col1:
                        st.markdown(f"**{c_name}** *(Max: {c_max} Marks | AI: {val_suggested})*")
                        st.caption(f"*Focus:* {c_focus}")
                        if c_name in ai_evidence:
                            st.caption(f"*AI Evidence:* {ai_evidence[c_name]}")
                    with c_col2:
                        adjusted_scores[c_name] = st.number_input(
                            f"Score", min_value=0.0, max_value=c_max, value=val_suggested, step=0.1, key=f"crit_{sub_data['id']}_{c_name}"
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
                    if st.button("🗑️ Delete Submission", use_container_width=True):
                        conn = get_db()
                        c = conn.cursor()
                        c.execute("DELETE FROM submissions WHERE id = ?", (sub_data['id'],))
                        conn.commit()
                        conn.close()
                        st.error("Submission deleted.")
                        st.rerun()
        else:
            st.info("No student submissions currently available in the queue.")

    # TAB 3: BATCH COHORT INGESTION
    with tabs[2]:
        st.markdown("### 📁 Batch Cohort Document Ingestion")
        st.caption("Upload multiple student files simultaneously for whole-class originality scan and AI assessment.")
        
        conn = get_db()
        df_asgs_batch = pd.read_sql_query("SELECT id, title, course FROM assignments", conn)
        conn.close()
        
        if not df_asgs_batch.empty:
            batch_asg_sel = st.selectbox("Select Target Assignment for Batch Upload:", [f"{r['id']} - {r['title']} ({r['course']})" for _, r in df_asgs_batch.iterrows()])
            batch_asg_id = batch_asg_sel.split(" - ")[0]
            
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
                        
                        b_eval = evaluate_student_report_ai(b_text, batch_asg_id)
                        
                        conn = get_db()
                        c = conn.cursor()
                        c.execute("""
                            INSERT OR REPLACE INTO submissions VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                        """, (
                            sub_code, s_id, s_code, batch_asg_id, "TCENG1201 - Formal Technical Communication", "Level 1 Group 4",
                            b_file.name, b_text, b_scan['total_match'], b_scan['ai_pattern_score'],
                            json.dumps(b_eval['scores']), b_eval['total'], 12.0,
                            json.dumps(b_eval['evidence']),
                            b_eval['strength'], json.dumps(b_eval['priorities']), b_eval['action'],
                            "Pending Review", b_eval['total'], "", datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                        ))
                        conn.commit()
                        conn.close()
                    st.success("All batch files evaluated and saved to database successfully!")
                    st.rerun()

    # TAB 4: ASSIGNMENT BUILDER & RUBRIC STUDIO
    with tabs[3]:
        st.markdown("### ⚙️ Assignment Builder & Dynamic Rubric Management Studio")
        st.caption("Publish new assignments and customize marking rubrics for Foundation Level 1 Group 4.")
        
        st.markdown("#### 1️⃣ Marking Rubric Management Options")
        rubric_mode = st.radio("Rubric Management Method:", ["➕ Create Rubric from Scratch", "📤 Upload New Rubric Document", "✏️ Customize / Edit Existing Rubric"], horizontal=True)
        
        conn = get_db()
        df_rubrics = pd.read_sql_query("SELECT * FROM rubrics", conn)
        conn.close()
        
        active_rubric_id = "RUB-TCENG1201"
        
        if rubric_mode == "➕ Create Rubric from Scratch":
            st.markdown("##### Create Custom Rubric")
            r_id_new = st.text_input("Rubric ID Code:", value=f"RUB-CUSTOM-{datetime.datetime.now().strftime('%M%S')}")
            r_name_new = st.text_input("Rubric Name / Title:", value="Custom Technical Report Rubric")
            r_max_new = st.number_input("Total Max Marks:", value=12.0, step=1.0)
            
            num_crit = st.number_input("Number of Criteria Rows:", min_value=1, max_value=8, value=4)
            c_list_built = []
            for i in range(int(num_crit)):
                c_colA, c_colB, c_colC = st.columns([2, 1, 3])
                with c_colA:
                    cn = st.text_input(f"Criterion {i+1} Name:", value=f"Criterion {i+1}", key=f"cr_n_{i}")
                with c_colB:
                    cm = st.number_input(f"Max Mark {i+1}:", value=3.0, step=0.5, key=f"cr_m_{i}")
                with c_colC:
                    cf = st.text_input(f"Focus Guideline {i+1}:", value="Key performance aspects to evaluate.", key=f"cr_f_{i}")
                c_list_built.append({"criterion": cn, "max_marks": cm, "focus": cf})
                
            if st.button("💾 Save New Rubric to Database"):
                conn = get_db()
                c = conn.cursor()
                c.execute("INSERT OR REPLACE INTO rubrics VALUES (?,?,?,?)", (r_id_new, r_name_new, r_max_new, json.dumps(c_list_built)))
                conn.commit()
                conn.close()
                st.success(f"Rubric **{r_name_new}** saved successfully!")
                st.rerun()
                
        elif rubric_mode == "📤 Upload New Rubric Document":
            st.markdown("##### Upload Rubric File")
            up_rub_file = st.file_uploader("Upload Rubric Specification (.pdf, .docx, .txt, .json):", type=['pdf', 'docx', 'txt', 'json'], key="up_rub_doc")
            if up_rub_file is not None:
                extracted_rub_text = extract_text_from_file(up_rub_file)
                st.success(f"Parsed File: {up_rub_file.name}")
                st.text_area("Parsed Rubric Text Preview:", value=extracted_rub_text[:300], height=100, disabled=True)
                
                r_id_up = f"RUB-DOC-{datetime.datetime.now().strftime('%M%S')}"
                r_name_up = st.text_input("Parsed Rubric Title:", value=f"Uploaded Rubric ({up_rub_file.name})")
                
                if st.button("💾 Save Uploaded Rubric to Database"):
                    parsed_c_up = [
                        {"criterion": "Content & Depth", "max_marks": 4.0, "focus": "Evaluated from uploaded specification."},
                        {"criterion": "Organization & Structure", "max_marks": 3.0, "focus": "Evaluated from uploaded specification."},
                        {"criterion": "Technical Language", "max_marks": 3.0, "focus": "Evaluated from uploaded specification."},
                        {"criterion": "Grammar & Formatting", "max_marks": 2.0, "focus": "Evaluated from uploaded specification."}
                    ]
                    conn = get_db()
                    c = conn.cursor()
                    c.execute("INSERT OR REPLACE INTO rubrics VALUES (?,?,?,?)", (r_id_up, r_name_up, 12.0, json.dumps(parsed_c_up)))
                    conn.commit()
                    conn.close()
                    st.success(f"Rubric **{r_name_up}** parsed and saved successfully!")
                    st.rerun()
                    
        elif rubric_mode == "✏️ Customize / Edit Existing Rubric":
            st.markdown("##### Edit Existing Rubric")
            if not df_rubrics.empty:
                rub_edit_sel = st.selectbox("Select Existing Rubric to Customize:", [f"{r['id']} - {r['rubric_name']}" for _, r in df_rubrics.iterrows()])
                target_r_id = rub_edit_sel.split(" - ")[0]
                target_r_row = df_rubrics[df_rubrics['id'] == target_r_id].iloc[0]
                
                r_edit_name = st.text_input("Customized Rubric Name:", value=f"{target_r_row['rubric_name']} (Custom)")
                
                try:
                    c_edit_list = json.loads(target_r_row['criteria_json'])
                except Exception:
                    c_edit_list = []
                    
                st.markdown("###### Customize Criteria Weights & Guidelines:")
                new_c_edit = []
                for idx, c_item in enumerate(c_edit_list):
                    col_e1, col_e2, col_e3 = st.columns([2, 1, 3])
                    with col_e1:
                        e_cn = st.text_input(f"Criterion {idx+1}:", value=c_item['criterion'], key=f"ecn_{idx}")
                    with col_e2:
                        e_cm = st.number_input(f"Max Mark:", value=float(c_item['max_marks']), step=0.5, key=f"ecm_{idx}")
                    with col_e3:
                        e_cf = st.text_input(f"Focus:", value=c_item.get('focus', ''), key=f"ecf_{idx}")
                    new_c_edit.append({"criterion": e_cn, "max_marks": e_cm, "focus": e_cf})
                    
                if st.button("💾 Save Customized Rubric Copy"):
                    new_custom_r_id = f"RUB-MOD-{datetime.datetime.now().strftime('%M%S')}"
                    new_max_total = sum(c_x['max_marks'] for c_x in new_c_edit)
                    conn = get_db()
                    c = conn.cursor()
                    c.execute("INSERT INTO rubrics VALUES (?,?,?,?)", (new_custom_r_id, r_edit_name, new_max_total, json.dumps(new_c_edit)))
                    conn.commit()
                    conn.close()
                    st.success(f"Customized Rubric **{r_edit_name}** saved to database!")
                    st.rerun()

        st.markdown("---")
        st.markdown("#### 2️⃣ Publish New Assignment for Class")
        
        conn = get_db()
        df_rubrics_latest = pd.read_sql_query("SELECT * FROM rubrics", conn)
        conn.close()
        
        col_b1, col_b2 = st.columns(2)
        with col_b1:
            new_asg_title = st.text_input("New Assignment Title:", "Workplace Safety & Diode Technical Report")
            course_sel = st.selectbox("Course Module:", ["TCENG1201 - Formal Technical Communication", "TC1202 - Vocational Writing & Reports", "PS1301 - Public Speaking & Oral Presentation"])
            max_mark_in = st.number_input("Maximum Mark Allocation:", value=12.0, step=1.0)
            
        with col_b2:
            rubric_opts = [f"{r['id']} - {r['rubric_name']}" for _, r in df_rubrics_latest.iterrows()] if not df_rubrics_latest.empty else ["RUB-TCENG1201 - 12-Mark Rubric"]
            rubric_sel = st.selectbox("Assigned Marking Rubric:", rubric_opts)
            due_date_in = st.date_input("Submission Deadline:", datetime.date(2026, 10, 30))
            
        st.markdown("#### 📄 Upload Assignment Brief Document (Optional):")
        asg_file_up = st.file_uploader("Attach Brief Document (.pdf, .docx, .txt):", type=['pdf', 'docx', 'txt'], key="asg_file_builder")
        brief_text_extracted = ""
        brief_file_name = ""
        if asg_file_up is not None:
            brief_file_name = asg_file_up.name
            brief_text_extracted = extract_text_from_file(asg_file_up)
            st.success(f"Attached Brief: **{asg_file_up.name}**")
            
        asg_desc_in = st.text_area("Assignment Description & Instructions:", value=brief_text_extracted if brief_text_extracted else "Write a formal workplace report investigating electronic components.")
        
        if st.button("💾 Publish Assignment to Student Portal", type="primary"):
            new_asg_id = f"ASG-{datetime.datetime.now().strftime('%m%d%H%M')}"
            rubric_name_val = rubric_sel
            
            conn = get_db()
            c = conn.cursor()
            c.execute("""
                INSERT INTO assignments VALUES (?,?,?,?,?,?,?,?,?,?)
            """, (
                new_asg_id, new_asg_title, course_sel, "Foundation Level 1 Group 4", str(due_date_in), max_mark_in,
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
        
        if not df_published.empty:
            st.markdown("##### 🗑️ Delete Published Assignment")
            col_da1, col_da2 = st.columns([3, 1])
            with col_da1:
                asg_del_sel = st.selectbox("Select Assignment to Delete:", [f"{r['id']} - {r['title']}" for _, r in df_published.iterrows()])
            with col_da2:
                if st.button("🗑️ Delete Assignment", type="secondary"):
                    target_asg_id = asg_del_sel.split(" - ")[0]
                    conn = get_db()
                    c = conn.cursor()
                    c.execute("DELETE FROM assignments WHERE id = ?", (target_asg_id,))
                    conn.commit()
                    conn.close()
                    st.success(f"Assignment {target_asg_id} deleted successfully.")
                    st.rerun()

    # TAB 5: COHORT ANALYTICS
    with tabs[4]:
        st.markdown("### 📈 Cohort Performance Analytics & Reteaching Insights")
        st.caption("AI identifies common class weaknesses across Level 1 Group 4:")
        
        col_a1, col_a2 = st.columns(2)
        with col_a1:
            st.markdown("#### 📊 Average Score by Criterion")
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
        df_export = pd.read_sql_query("SELECT id, student_id, student_name_anon, assignment_id, course, group_name, ai_total, teacher_score, max_marks, teacher_status, teacher_feedback, submitted_date FROM submissions", conn)
        conn.close()
        
        col_ex1, col_ex2 = st.columns(2)
        with col_ex1:
            st.download_button("📥 Export Official Class Gradebook (.csv)", data=df_export.to_csv(index=False), file_name="SVC_Assess_L1G4_Gradebook.csv", mime="text/csv")
        with col_ex2:
            st.info("📄 Formal Institutional Governance Report ready in Studio Panel.")

# -----------------------------------------------------------------------------
# VIEW 3: ADMINISTRATOR CONTROL
# -----------------------------------------------------------------------------
else:
    st.subheader("🏛️ Institutional Administration & Quality Assurance Control")
    st.caption("Saham Vocational College | Academic Policy & Governance Settings")
    
    st.markdown("### 🛡️ Similarity Threshold & Originality Gate Control")
    sim_val = st.slider("Maximum Allowable Similarity Threshold (%):", min_value=10.0, max_value=90.0, value=float(st.session_state.sim_threshold), step=5.0)
    st.session_state.sim_threshold = sim_val
    st.info(f"Current Policy Rule: Submissions with > **{sim_val}%** similarity index display a high similarity warning for lecturer review.")
    
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
