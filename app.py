import streamlit as st
import google.generativeai as genai
import json, os, time, datetime, socket
from PyPDF2 import PdfReader
from dotenv import load_dotenv

# ================= CONFIG =================
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
ADMIN_CODE = os.getenv("ADMIN_ACCESS_CODE")  # Stored in .env for safety
COOLDOWN_PERIOD = 60 * 60 * 24  # 24 hours
USAGE_FILE = "user_usage.json"

genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-2.5-flash")

st.set_page_config(page_title="AI Recruitment Agent", page_icon="💼", layout="centered")
st.title("💼 AI Recruitment Agent — The Hiring Brain")
st.caption("Built by Bhargav | Powered by Gemini 2.5 Flash 🧠")

# ============ LOAD OR CREATE USAGE FILE ============
if not os.path.exists(USAGE_FILE):
    with open(USAGE_FILE, "w") as f:
        json.dump({}, f)

with open(USAGE_FILE, "r") as f:
    usage_data = json.load(f)

# ============ GET USER IDENTIFIER ============
def get_user_id():
    try:
        # Use hostname or socket info to identify each user
        return socket.gethostbyname(socket.gethostname())
    except:
        return str(hash(os.getlogin()))

user_id = get_user_id()

# ============ SIDEBAR ADMIN ACCESS ============
st.sidebar.header("🔐 Admin Access (for Bhargav)")
access_code = st.sidebar.text_input("Enter Access Code:", type="password")
is_admin = access_code == ADMIN_CODE

# ============ TIME CHECK ============
current_time = time.time()

if not is_admin:
    if user_id in usage_data:
        last_used = usage_data[user_id]["last_used"]
        time_since = current_time - last_used
        if time_since < COOLDOWN_PERIOD:
            remaining = COOLDOWN_PERIOD - time_since
            hrs = int(remaining // 3600)
            mins = int((remaining % 3600) // 60)
            st.error(f"🚫 You already used this app. Try again after {hrs}h {mins}m.")
            st.info("💬 For unlimited use, contact admin at [aibhargav.site](https://aibhargav.site).")
            st.stop()

st.warning("⚠️ Each user can only use this app **once per 24 hours**. "
           "If you need extended access, contact admin at [aibhargav.site](https://aibhargav.site).")

# ============ HR INPUTS ============
st.subheader("🎯 Define HR Requirements")
role = st.text_input("Role Title (e.g., Data Scientist, Frontend Engineer)")
core_skills = st.text_area("Core Technical Skills (comma-separated)", placeholder="Python, Machine Learning, SQL")
soft_skills = st.text_area("Soft Skills (comma-separated)", placeholder="Communication, Teamwork, Problem Solving")
experience = st.selectbox("Experience Required", ["0-1 years", "1-3 years", "3-5 years", "5+ years"])

# ============ RESUME UPLOAD ============
st.subheader("📄 Upload Candidate Resume")
uploaded_file = st.file_uploader("Upload PDF or Text file", type=["pdf", "txt"])

resume_text = ""
if uploaded_file:
    if uploaded_file.name.endswith(".pdf"):
        reader = PdfReader(uploaded_file)
        for page in reader.pages:
            resume_text += page.extract_text() + "\n"
    else:
        resume_text = uploaded_file.read().decode("utf-8")

# ============ AI EVALUATION ============
if st.button("🧠 Analyze Candidate"):
    if not resume_text or not role:
        st.warning("⚠️ Please fill in both HR requirements and upload a resume.")
    else:
        with st.spinner("Analyzing candidate profile..."):
            # Step 1: HR requirement profile
            hr_profile = {
                "role": role,
                "core_skills": [s.strip() for s in core_skills.split(",") if s.strip()],
                "soft_skills": [s.strip() for s in soft_skills.split(",") if s.strip()],
                "experience_required": experience
            }

            # Step 2: Resume summarizer
            resume_prompt = f"""
            You are an expert HR analyst. Extract and summarize key candidate details:
            - Name (if found)
            - Total experience
            - Technical skills
            - Soft skills
            - Notable projects or achievements
            - Education
            Resume: {resume_text}
            Return summary as bullet points.
            """
            resume_analysis = model.generate_content(resume_prompt).text

            # Step 3: Fit evaluation
            match_prompt = f"""
            You are an AI recruitment evaluator.
            Compare the HR requirements and candidate profile below:

            HR Requirements: {json.dumps(hr_profile, indent=2)}
            Candidate Profile: {resume_analysis}

            Return a detailed evaluation including:
            - Skill Match %
            - Experience Match %
            - Missing Skills
            - Cultural Fit (High / Medium / Low)
            - Overall Fit Score %
            - Short reasoning (2-3 lines)
            """
            fit_eval = model.generate_content(match_prompt).text

            # Step 4: Final HR Advice
            advisor_prompt = f"""
            You are an AI HR advisor with emotional intelligence.
            Based on the evaluation below, provide the final hiring recommendation.

            {fit_eval}

            Return in markdown format:
            1. **Recommendation:** Hire / Consider / Reject  
            2. **Top Strengths**  
            3. **Weak Areas**  
            4. **Improvements for Candidate**  
            5. **Tone & Personality Analysis**
            """
            advisor_output = model.generate_content(advisor_prompt).text

            # Save usage data
            if not is_admin:
                usage_data[user_id] = {"last_used": current_time}
                with open(USAGE_FILE, "w") as f:
                    json.dump(usage_data, f)

        # ============ DISPLAY RESULTS ============
        st.success("✅ Recruitment evaluation complete!")

        st.subheader("📊 Candidate Summary")
        st.info(resume_analysis)

        st.subheader("⚖️ Evaluation Breakdown")
        st.write(fit_eval)

        st.subheader("💬 AI HR Recommendation")
        st.markdown(advisor_output)

        # ============ Show Next Available Time ============
        if not is_admin:
            next_time = datetime.datetime.fromtimestamp(current_time + COOLDOWN_PERIOD)
            st.info(f"⏰ You can use this app again after: {next_time.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            st.success("👑 Admin mode active — unlimited usage enabled!")

