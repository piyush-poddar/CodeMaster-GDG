import streamlit as st
import streamlit.components.v1 as components
from review_engine import (
    get_code_feedback_from_texts,
    get_code_feedback_from_files,
    get_code_feedback_from_github_repo,
)

from firebase_utils import init_firebase, verify_token_and_store_user

init_firebase()

LOGIN_URL = "https://codemaster-login-yqv2aiqvmq-ew.a.run.app"

if "user_email" not in st.session_state:
    st.subheader("🔐 Login Required")
    st.markdown("Please log in with your Google account to continue.")

    token_param = st.query_params.get("token")
    if token_param:
        verified, result = verify_token_and_store_user(token_param[0])
        if verified:
            st.success(f"✅ Logged in as {result}")
            st.experimental_set_query_params()  # Clear token
            st.rerun()
        else:
            st.error(f"Login failed: {result}")
            st.stop()
    else:
        redirect_url = "https://codemaster-gdg-yqv2aiqvmq-ew.a.run.app"
        login_redirect_url = f"{LOGIN_URL}?redirect={redirect_url}"

        st.markdown(f"""
            <a href="{login_redirect_url}">
                <button style="font-size:16px;padding:10px 20px;">Login with Google</button>
            </a>
        """, unsafe_allow_html=True)
        st.stop()
else:
    st.markdown(f"✅ Logged in as **{st.session_state['user_email']}**")

# ------------------------------
# 🧠 Fix legacy state (block = str)
# ------------------------------
def init_code_blocks():
    if "code_blocks" not in st.session_state:
        st.session_state.code_blocks = [{"filename": "main.py", "content": ""}]
    elif isinstance(st.session_state.code_blocks[0], str):
        st.session_state.code_blocks = [{"filename": f"file{i+1}.py", "content": c} for i, c in enumerate(st.session_state.code_blocks)]

init_code_blocks()

# ------------------------------
# 🌐 Page Setup
# ------------------------------
st.set_page_config(page_title="AI Code Review Assistant", page_icon="💻", layout="centered")
st.title("💻 AI Code Review Assistant")

st.markdown("""
Choose how you want to submit your code for review:
- 🗂️ **Upload your project files** (supports `.py`, `.cpp`, `.java`, `.zip`, etc.)
- ✍️ **Paste code manually**
- 🌐 **Import directly from a GitHub repository**
""")

# ------------------------------
# 🔘 Mode selection
# ------------------------------
if "mode" not in st.session_state:
    st.session_state.mode = "upload"

cols = st.columns(3)
if cols[0].button("📁 Upload Project Files", type="primary" if st.session_state.mode == "upload" else "secondary"):
    st.session_state.mode = "upload"
    st.rerun()
if cols[1].button("✍️ Paste Code", type="primary" if st.session_state.mode == "paste" else "secondary"):
    st.session_state.mode = "paste"
    st.rerun()
if cols[2].button("🌐 Import from GitHub", type="primary" if st.session_state.mode == "github" else "secondary"):
    st.session_state.mode = "github"
    st.rerun()

# ------------------------------
# 📁 Upload Mode
# ------------------------------
if st.session_state.mode == "upload":
    st.subheader("📁 Upload Code Files or Project Zip")
    uploaded_files = st.file_uploader(
        "Upload one or more code files or a `.zip` archive",
        type=["py", "cpp", "java", "js", "txt", "zip"],
        accept_multiple_files=True
    )

# ------------------------------
# ✍️ Paste Mode
# ------------------------------
elif st.session_state.mode == "paste":
    st.subheader("✍️ Paste Your Code (with File Names)")

    for i in range(len(st.session_state.code_blocks)):
        block = st.session_state.code_blocks[i]
        if isinstance(block, str):
            st.session_state.code_blocks[i] = {"filename": f"file{i+1}.py", "content": block}
            block = st.session_state.code_blocks[i]

        cols = st.columns([3, 1])
        block["filename"] = cols[0].text_input(f"Filename {i+1}", value=block["filename"], key=f"filename_{i}")

        if cols[1].button("❌ Delete", key=f"delete_{i}"):
            st.session_state.code_blocks.pop(i)
            st.rerun()

        block["content"] = st.text_area(
            f"Code: {block['filename']}",
            value=block["content"],
            height=200,
            key=f"code_{i}"
        )

    if st.button("➕ Add Another Code Block"):
        st.session_state.code_blocks.append({"filename": f"file{len(st.session_state.code_blocks)+1}.py", "content": ""})

# ------------------------------
# 🌐 GitHub Repo Mode
# ------------------------------
elif st.session_state.mode == "github":
    st.subheader("🌐 Import Code from GitHub Repository")

    repo_url = st.text_input("Paste your public GitHub repository URL", placeholder="https://github.com/username/project")
    if repo_url and not repo_url.strip().startswith("https://github.com/"):
        st.warning("Please enter a valid GitHub repository URL.")

# ------------------------------
# 📋 Guidelines
# ------------------------------
st.subheader("📋 Optional: Paste Project Guidelines")
guidelines_input = st.text_area("Paste your college's evaluation criteria (rubric)", height=200)

# ------------------------------
# 🔍 Review Button
# ------------------------------
if st.button("🔍 Review My Code"):
    if st.session_state.mode == "paste":
        all_code = [
            {"filename": block["filename"], "content": block["content"]}
            for block in st.session_state.code_blocks
            if block["content"].strip()
        ]
        if not all_code:
            st.warning("Please paste at least one code block.")
        else:
            with st.spinner("Analyzing pasted code..."):
                feedback = get_code_feedback_from_texts(all_code, guidelines_input)
                st.success("✅ Review complete!")
                st.markdown("### 📋 AI Feedback")
                st.markdown(feedback)

    elif st.session_state.mode == "upload":
        if not uploaded_files:
            st.warning("Please upload at least one file.")
        else:
            with st.spinner("Analyzing uploaded files..."):
                feedback = get_code_feedback_from_files(uploaded_files, guidelines_input)
                st.success("✅ Review complete!")
                st.markdown("### 📋 AI Feedback")
                st.markdown(feedback)

    elif st.session_state.mode == "github":
        if not repo_url.strip():
            st.warning("Please paste a GitHub repository URL.")
        else:
            with st.spinner("Cloning and reviewing repository..."):
                feedback = get_code_feedback_from_github_repo(repo_url.strip(), guidelines_input)
                st.success("✅ Review complete!")
                st.markdown("### 📋 AI Feedback")
                st.markdown(feedback)
