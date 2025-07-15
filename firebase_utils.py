import streamlit as st
import firebase_admin
from firebase_admin import credentials, auth, firestore
from datetime import datetime, timezone

# Initialize Firebase Admin
def init_firebase():
    if not firebase_admin._apps:
        firebase_admin.initialize_app()

DATABASE_ID = "codemaster-firestore"

# Verify ID token passed from frontend
def verify_token_and_store_user(id_token: str):
    try:
        decoded = auth.verify_id_token(id_token)
        st.session_state["user_email"] = decoded.get("email")
        st.session_state["user_uid"] = decoded.get("uid")
        return True, decoded.get("email")
    except Exception as e:
        return False, str(e)

def save_project_review(user_uid, project_name, feedback, source_type="upload"):
    """
    Save a project review for a given user into Firestore.

    Args:
        user_uid (str): Firebase Authentication UID of the logged-in user.
        project_name (str): Name of the project.
        feedback (str): AI feedback string.
        source_type (str): One of 'upload', 'paste', or 'github'.
    """
    try:
        db = firestore.client(database_id=DATABASE_ID)

        review_doc = {
            "project_name": project_name,
            "feedback": feedback,
            "source_type": source_type,
            "reviewed_at": datetime.now(timezone.utc).isoformat(),
        }

        # Add the document to the user's projects subcollection
        db.collection("users").document(user_uid).collection("projects").add(review_doc)
        st.success(f"✅ Project '{project_name}' review saved successfully!")

    except Exception as e:
        st.error(f"❌ Failed to save review: {str(e)}")

def get_user_projects(user_uid):
    """
    Fetch all projects for a given user from Firestore, sorted by most recent.

    Args:
        user_uid (str): The UID of the logged-in user.

    Returns:
        List[Dict]: A list of dictionaries with 'id' and 'project_name'.
    """
    try:
        db = firestore.client(database_id=DATABASE_ID)
        projects_ref = db.collection("users").document(user_uid).collection("projects")

        # Fetch all documents and convert to list
        docs = projects_ref.stream()

        # Extract and sort manually by reviewed_at timestamp
        projects = []
        for doc in docs:
            data = doc.to_dict()
            reviewed_at = data.get("reviewed_at")
            projects.append({
                "id": doc.id,
                "project_name": data.get("project_name", "Unnamed Project"),
                "reviewed_at": reviewed_at
            })

        # Sort by reviewed_at descending (most recent first)
        projects.sort(key=lambda x: x["reviewed_at"] or "", reverse=True)

        # Return only id and project_name (you can return full dict if needed)
        return [{"id": p["id"], "project_name": p["project_name"]} for p in projects]

    except Exception as e:
        print("Error fetching user projects:", e)
        return []
    
def get_last_three_reviews(user_uid):
    """
    Retrieve the latest 3 project reviews for a specific user UID from Firestore.
    """
    try:
        db = firestore.client(database_id=DATABASE_ID)
        projects_ref = db.collection(user_uid)  # collection name is user_uid (as per your structure)
        docs = projects_ref.stream()

        # Convert documents to list of dicts and sort by timestamp (desc)
        projects = []
        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            projects.append(data)

        # Sort by reviewed_at timestamp (most recent first)
        projects.sort(key=lambda x: x.get("reviewed_at", ""), reverse=True)

        # Return top 3
        return projects[:3]

    except Exception as e:
        print("Error fetching reviews:", e)
        return []
