# CodeMaster-GDG

🔗 **Live App:** [https://codemaster-gdg-yqv2aiqvmq-ew.a.run.app](https://codemaster-gdg-yqv2aiqvmq-ew.a.run.app)


## 📌 Overview

The **CodeMaster** is a web-based tool built for students and developers to get instant, AI-generated feedback on their code. Whether you're preparing for academic project submissions or simply want to improve your code quality, this assistant can help you evaluate your work with detailed suggestions and improvements.


## 🧠 Key Features

- ✅ **Login with Google** for personalized experience
- 🔍 **AI-generated code reviews** using text, file upload, or GitHub URL
- 💾 **Save reviews** to your project history
- 📂 **Manage multiple projects** and access last reviews
- 🌐 **Fully deployed on Google Cloud Run** for global accessibility
- 📋 **Optional rubric input** to guide the review process


## 🧪 How it Works

1. **Authenticate** using Google OAuth
2. **Select an existing project** or **create a new one**
3. Submit your code using one of the methods:
   - Paste code
   - Upload files
   - GitHub repository URL
4. AI reviews your code and returns feedback
5. You can optionally **save the feedback** to your project history


## 🚀 Tech Stack

- **Frontend**: Streamlit
- **Backend AI**: Gemini API (Google Generative AI)
- **Database**: Firebase Firestore
- **Authentication**: Firebase Auth (Google OAuth)
- **Deployment**: Google Cloud Run


## 🧰 Google Technologies Used

- Firebase Authentication  
- Firebase Firestore  
- Google Generative AI (Gemini API)  
- Google Cloud Run  
- Google Cloud SDK  


## 📦 Folder Structure (Simplified)

```yaml
├── app.py # Main Streamlit frontend
├── firebase_utils.py # Firestore and auth integration
├── review_engine.py # LLM calling and feedback formatting
├── requirements.txt
└── README.md
```


## 🧑‍💻 Author

Developed with ❤️ by **Piyush Poddar**  
Computer Science & Engineering  
Jaypee Institute of Information Technology, Noida
