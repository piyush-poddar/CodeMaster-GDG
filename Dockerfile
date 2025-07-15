# ✅ Base image with Python 3.12
FROM python:3.12-slim

# ✅ Install system-level dependencies (git for GitPython)
RUN apt-get update && \
    apt-get install -y git && \
    apt-get clean

# ✅ Set working directory
WORKDIR /app

# ✅ Copy your code
COPY . .

# ✅ Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# ✅ Expose port for Streamlit
EXPOSE 8080

# ✅ Run Streamlit app on container start
CMD ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0"]
