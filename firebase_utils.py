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

def ensure_user_document(user_uid, email_id):
    db = firestore.client(database_id=DATABASE_ID)
    user_ref = db.collection("users").document(user_uid)
    user_ref.set({"email_id": email_id}, merge=True)

def create_project_if_not_exists(user_uid, project_name):
    db = firestore.client(database_id=DATABASE_ID)
    projects_ref = db.collection("users").document(user_uid).collection("projects")

    # Check if a project with the same name already exists
    existing = projects_ref.where("project_name", "==", project_name).get()
    if existing:
        return existing[0].id  # Return existing project_id

    # Else, create a new one
    doc_ref = projects_ref.document()
    doc_ref.set({
        "project_name": project_name
    })
    return doc_ref.id

def add_review_to_project(user_uid, project_id, feedback, source_type, guidelines=None):
    db = firestore.client(database_id=DATABASE_ID)
    review_doc = {
        "feedback": feedback,
        "source_type": source_type,
        "guidelines": guidelines,
        "reviewed_at": datetime.now(timezone.utc).isoformat()
    }
    reviews_ref = (
        db.collection("users")
          .document(user_uid)
          .collection("projects")
          .document(project_id)
          .collection("reviews")
    )
    reviews_ref.add(review_doc)

def get_user_projects(user_uid):
    """
    Fetch all projects for a given user from Firestore.

    Args:
        user_uid (str): The UID of the logged-in user.

    Returns:
        List[Dict]: A list of dictionaries with 'id' and 'project_name'.
    """
    try:
        db = firestore.client(database_id=DATABASE_ID)
        projects_ref = db.collection("users").document(user_uid).collection("projects")
        docs = projects_ref.stream()

        projects = []
        for doc in docs:
            data = doc.to_dict()
            projects.append({
                "id": doc.id,
                "project_name": data.get("project_name", "Unnamed Project")
            })

        return projects

    except Exception as e:
        print("Error fetching user projects:", e)
        return []

    
def get_last_three_reviews_for_project(user_uid: str, project_id: str):
    """
    Retrieve the latest 3 review entries for a specific project under a user's account.

    Args:
        user_uid (str): Firebase UID of the user.
        project_id (str): The ID of the project document.

    Returns:
        List[Dict]: List of last 3 review entries for the project.
    """
    try:
        db = firestore.client(database_id=DATABASE_ID)
        reviews_ref = db.collection("users").document(user_uid).collection("projects").document(project_id).collection("reviews")

        # Get the last 3 reviews ordered by reviewed_at descending
        docs = reviews_ref.order_by("reviewed_at", direction=firestore.Query.DESCENDING).limit(1).stream()

        reviews = []
        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            reviews.append(data)

        return reviews

    except Exception as e:
        print(f"Error fetching reviews for project {project_id}:", e)
        return []

if __name__ == "__main__":
    init_firebase()
    print("Firebase initialized.")
    reviews = get_last_three_reviews_for_project("vk506Oa7uuZHtBdAP91Cjt1egb12", "JgXNIDA5xxKRJoQy9Lrg")
    print("Last 3 reviews:", reviews)