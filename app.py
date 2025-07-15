import streamlit as st
from review_engine import (
    get_code_feedback_from_texts,
    get_code_feedback_from_files,
    get_code_feedback_from_github_repo,
)
from firebase_utils import (
    init_firebase,
    verify_token_and_store_user,
    ensure_user_document,
    get_user_projects,
    create_project_if_not_exists,
    add_review_to_project,
    get_last_three_reviews_for_project,
)

# Constants
LOGIN_URL = "https://codemaster-login-yqv2aiqvmq-ew.a.run.app"
STREAMLIT_APP_URL = "https://codemaster-gdg-yqv2aiqvmq-ew.a.run.app"

# Firebase Initialization
init_firebase()
st.set_page_config(page_title="AI Code Review Assistant", layout="centered")
st.title("💻 AI Code Review Assistant")

# -------------------------------
# 🔐 Authentication
# -------------------------------
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

user_uid = st.session_state.get("user_uid")
ensure_user_document(user_uid, st.session_state["user_email"])

# -------------------------------
# 🧠 Init Legacy State
# -------------------------------
def init_code_blocks():
    if "code_blocks" not in st.session_state:
        st.session_state.code_blocks = [{"filename": "main.py", "content": ""}]
    elif isinstance(st.session_state.code_blocks[0], str):
        st.session_state.code_blocks = [{"filename": f"file{i+1}.py", "content": c} for i, c in enumerate(st.session_state.code_blocks)]

init_code_blocks()

# -------------------------------
# 📂 Project Picker / New Project
# -------------------------------
user_projects = get_user_projects(user_uid)
selected_project = None
project_id = None

if user_projects:
    st.subheader("📁 Select an Existing Project")
    selected_project = st.selectbox(
        "Choose a project:",
        options=user_projects,
        format_func=lambda x: x["project_name"],
    )
    project_id = selected_project["id"]
    st.markdown("### 📝 Last 3 Reviews:")
    for review in get_last_three_reviews_for_project(user_uid, project_id):
        st.markdown(f"**🕒 Reviewed At**: {review.get('reviewed_at', '')}")
        st.markdown(f"**🔖 Source Type**: {review.get('source_type', '')}")
        st.markdown(f"**💬 Feedback**:\n\n{review.get('feedback', '')}")
        st.markdown("---")

    st.markdown("## 🔁 Re-review or Submit New Code")
    default_project_name = selected_project["project_name"]
else:
    st.subheader("🆕 New Project")
    default_project_name = st.text_input("Enter Project Name", key="new_project_name")

# -------------------------------
# 🔘 Mode Selection
# -------------------------------
st.markdown("### 🚀 Choose Submission Mode")

if "mode" not in st.session_state:
    st.session_state.mode = "upload"

cols = st.columns(3)
if cols[0].button("📁 Upload", type="primary" if st.session_state.mode == "upload" else "secondary"):
    st.session_state.mode = "upload"
    st.rerun()
if cols[1].button("✍️ Paste", type="primary" if st.session_state.mode == "paste" else "secondary"):
    st.session_state.mode = "paste"
    st.rerun()
if cols[2].button("🌐 GitHub", type="primary" if st.session_state.mode == "github" else "secondary"):
    st.session_state.mode = "github"
    st.rerun()

# -------------------------------
# 🧾 Input Code
# -------------------------------
uploaded_files, repo_url = None, None

if st.session_state.mode == "upload":
    uploaded_files = st.file_uploader("Upload your code", type=["py", "cpp", "java", "js", "txt", "zip"], accept_multiple_files=True)

elif st.session_state.mode == "paste":
    for i in range(len(st.session_state.code_blocks)):
        block = st.session_state.code_blocks[i]
        cols = st.columns([3, 1])
        block["filename"] = cols[0].text_input(f"Filename {i+1}", value=block["filename"], key=f"filename_{i}")
        if cols[1].button("❌ Delete", key=f"delete_{i}"):
            st.session_state.code_blocks.pop(i)
            st.rerun()
        block["content"] = st.text_area(f"Code: {block['filename']}", value=block["content"], height=200, key=f"code_{i}")
    if st.button("➕ Add Code Block"):
        st.session_state.code_blocks.append({"filename": f"file{len(st.session_state.code_blocks)+1}.py", "content": ""})

elif st.session_state.mode == "github":
    repo_url = st.text_input("GitHub repo URL", placeholder="https://github.com/username/repo")
    if repo_url and not repo_url.strip().startswith("https://github.com/"):
        st.warning("⚠️ Invalid GitHub URL")

# -------------------------------
# 📋 Optional Guidelines
# -------------------------------
st.subheader("📋 Paste Evaluation Criteria (Optional)")
guidelines_input = st.text_area("Paste rubric or grading guidelines", height=150)

# -------------------------------
# 🔍 Review Button
# -------------------------------
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
            pid = project_id or create_project_if_not_exists(user_uid, default_project_name.strip())
            add_review_to_project(user_uid, pid, feedback, source_type)
