import os
from google import genai
from github_clone_util import clone_repo, get_project_tree, get_all_code_files

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]

client = genai.Client(api_key=GEMINI_API_KEY)

# Prompt template
def get_code_review_prompt(code: str, guidelines: str = "") -> str:
    return f"""
    💻 **Student Code**:
    {code}

    ---
    📋 **Project Guidelines**:
    {guidelines if guidelines else "No specific guidelines provided."}

    ---

    You are a senior software engineering professor helping students with project submissions.

    Please review the following code as per general software engineering best practices and/or the provided guidelines.

    Give feedback in the following format:
    1. ✅ **Good Practices Used**
    2. ❌ **Issues, Bugs, or Bad Practices**
    3. 💡 **Suggestions for Improvement**
    4. 📈 **Time and Space Complexity (only if applicable and related to code)**

    If project guidelines are provided, strictly use them to make your suggestions more specific.
    Directly start with the feedback without any additional preamble.
    """

# 📄 Paste Mode (dicts with filename + content)
def get_code_feedback_from_texts(code_blocks: list[dict], guidelines: str = "") -> str:
    full_code = ""
    for block in code_blocks:
        if block["content"].strip():
            full_code += f"\n# FILE: {block['filename']}\n{block['content']}\n"

    prompt = get_code_review_prompt(full_code, guidelines)

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt
    )

    return response.text

# 📁 Upload Mode (uploaded files)
def get_code_feedback_from_files(files, guidelines: str = "") -> str:
    full_code = ""
    for f in files:
        try:
            content = f.read().decode("utf-8")
        except UnicodeDecodeError:
            content = f.read().decode("latin-1")
        full_code += f"\n# FILE: {f.name}\n{content}\n"

    prompt = get_code_review_prompt(full_code, guidelines)

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt
    )
    return response.text

def get_code_feedback_from_github_repo(repo_url: str, guidelines: str = "") -> str:
    try:
        # Step 1: Clone the repo into "temp_repo"
        repo_path = clone_repo(repo_url, clone_dir="temp_repo")

        # Step 2: Get tree view of project
        project_tree = get_project_tree(repo_path)

        # Step 3: Get all relevant code files
        code_blocks = get_all_code_files(repo_path)

        if not code_blocks:
            return "❌ No supported code files found in the repository."

        # Step 4: Build prompt content
        full_code = f"# 📁 Project Structure:\n{project_tree}\n\n"
        for block in code_blocks:
            full_code += f"\n# FILE: {block['filename']}\n{block['content']}\n"

        # Step 5: Gemini Prompt
        prompt = get_code_review_prompt(full_code, guidelines)

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        return response.text

    except Exception as e:
        return f"❌ Error while reviewing GitHub repo: {e}"
