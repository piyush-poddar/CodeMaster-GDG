import streamlit as st
from review_engine import (
    get_code_feedback_from_texts,
    get_code_feedback_from_files,
    get_code_feedback_from_github_repo,
)
from firebase_utils import (
    init_firebase,
    verify_token_and_store_user,
    get_user_projects,
    save_project_review,
    get_last_three_reviews
)

# Init Firebase
init_firebase()

# Constants
LOGIN_URL = "https://codemaster-login-yqv2aiqvmq-ew.a.run.app"
STREAMLIT_APP_URL = "https://codemaster-gdg-yqv2aiqvmq-ew.a.run.app"

st.set_page_config(page_title="AI Code Review Assistant", layout="centered")
st.title("💻 AI Code Review Assistant")

# --------------------------
# 🔐 Authentication
# --------------------------
if "user_email" not in st.session_state:
    st.subheader("🔐 Login Required")
    query_params = st.query_params
    token_param = query_params.get("token")

    if token_param:
        id_token_string = token_param[0] if isinstance(token_param, list) else token_param
        verified, result = verify_token_and_store_user(id_token_string)
        if verified:
            st.session_state.user_email = result
            st.success(f"✅ Logged in as {result}")
            st.query_params.clear()
            st.rerun()
        else:
            st.error(f"Login failed: {result}")
            st.query_params.clear()
            st.stop()
    else:
        login_redirect_url = f"{LOGIN_URL}?redirect={STREAMLIT_APP_URL}"
        st.markdown(f"""
            <a href="{login_redirect_url}" target="_self">
                <button style="font-size:16px;padding:10px 20px;background-color:#4285F4;color:white;border:none;border-radius:5px;cursor:pointer;">
                    Login with Google
                </button>
            </a>
        """, unsafe_allow_html=True)
        st.stop()

st.markdown(f"✅ Logged in as **{st.session_state['user_email']}**")
if st.button("Logout"):
    st.session_state.clear()
    st.rerun()

# --------------------------
# 🔄 Legacy code init
# --------------------------
def init_code_blocks():
    if "code_blocks" not in st.session_state:
        st.session_state.code_blocks = [{"filename": "main.py", "content": ""}]
    elif isinstance(st.session_state.code_blocks[0], str):
        st.session_state.code_blocks = [{"filename": f"file{i+1}.py", "content": c} for i, c in enumerate(st.session_state.code_blocks)]

init_code_blocks()

# --------------------------
# 🔍 Project History Check
# --------------------------
user_uid = st.session_state.get("user_uid")
user_projects = get_user_projects(user_uid)

if user_projects:
    st.subheader("📂 Select a Project You Reviewed Earlier")
    selected_project = st.selectbox("Choose from your previous projects:", user_projects, format_func=lambda x: x['project_name'])

    st.write("📝 Showing last 3 reviews:")
    reviews = get_last_three_reviews(user_uid)
    for r in reviews:
        st.markdown(f"**🔁 Reviewed At**: {r.get('reviewed_at', 'N/A')}")
        st.markdown(f"📄 **Feedback**:\n\n{r.get('feedback', 'No feedback found.')}")
        st.markdown("---")

    st.markdown("## 🔁 Re-review or Submit New Code for This Project")
    default_project_name = selected_project['project_name']
else:
    st.subheader("🆕 New User Detected — Let's Get Your First Review!")
    default_project_name = st.text_input("📝 Project Name", placeholder="e.g., Weather App", key="new_project_name")

# --------------------------
# 🔘 Mode Selection
# --------------------------
st.markdown("### 🚀 Choose Code Submission Method")
if "mode" not in st.session_state:
    st.session_state.mode = "upload"

cols = st.columns(3)
if cols[0].button("📁 Upload Files", type="primary" if st.session_state.mode == "upload" else "secondary"):
    st.session_state.mode = "upload"
    st.rerun()
if cols[1].button("✍️ Paste Code", type="primary" if st.session_state.mode == "paste" else "secondary"):
    st.session_state.mode = "paste"
    st.rerun()
if cols[2].button("🌐 GitHub Repo", type="primary" if st.session_state.mode == "github" else "secondary"):
    st.session_state.mode = "github"
    st.rerun()

# --------------------------
# 🧾 Input Forms
# --------------------------
uploaded_files, repo_url = None, None

if st.session_state.mode == "upload":
    uploaded_files = st.file_uploader("Upload your code files or zip", type=["py", "cpp", "java", "js", "txt", "zip"], accept_multiple_files=True)

elif st.session_state.mode == "paste":
    for i in range(len(st.session_state.code_blocks)):
        block = st.session_state.code_blocks[i]
        cols = st.columns([3, 1])
        block["filename"] = cols[0].text_input(f"Filename {i+1}", value=block["filename"], key=f"filename_{i}")
        if cols[1].button("❌ Delete", key=f"delete_{i}"):
            st.session_state.code_blocks.pop(i)
            st.rerun()
        block["content"] = st.text_area(f"Code: {block['filename']}", value=block["content"], height=200, key=f"code_{i}")
    if st.button("➕ Add Another Block"):
        st.session_state.code_blocks.append({"filename": f"file{len(st.session_state.code_blocks)+1}.py", "content": ""})

elif st.session_state.mode == "github":
    repo_url = st.text_input("Paste your GitHub repo URL", placeholder="https://github.com/username/repo")
    if repo_url and not repo_url.strip().startswith("https://github.com/"):
        st.warning("⚠️ Invalid GitHub URL")

# --------------------------
# 📋 Optional Guidelines
# --------------------------
st.subheader("📋 Paste Evaluation Criteria (Optional)")
guidelines_input = st.text_area("Paste rubric or grading guidelines", height=150)

# --------------------------
# 🔍 Review Button
# --------------------------
if st.button("🔍 Review My Code"):
    feedback = None
    source_type = st.session_state.mode

    if st.session_state.mode == "paste":
        all_code = [{"filename": b["filename"], "content": b["content"]} for b in st.session_state.code_blocks if b["content"].strip()]
        if not all_code:
            st.warning("⚠️ Paste at least one code block.")
        else:
            with st.spinner("Analyzing pasted code..."):
                feedback = get_code_feedback_from_texts(all_code, guidelines_input)

    elif st.session_state.mode == "upload":
        if not uploaded_files:
            st.warning("⚠️ Upload at least one file.")
        else:
            with st.spinner("Analyzing uploaded files..."):
                feedback = get_code_feedback_from_files(uploaded_files, guidelines_input)

    elif st.session_state.mode == "github":
        if not repo_url:
            st.warning("⚠️ Paste a GitHub URL.")
        else:
            with st.spinner("Analyzing GitHub repo..."):
                feedback = get_code_feedback_from_github_repo(repo_url.strip(), guidelines_input)

    if feedback:
        st.success("✅ Review Complete!")
        st.markdown("### 💬 AI Feedback")
        st.markdown(feedback)

        if default_project_name.strip():
            save_project_review(user_uid, default_project_name.strip(), feedback, source_type)
