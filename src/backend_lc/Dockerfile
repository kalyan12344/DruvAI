# ---- 1. Base image --------------------------------------------------
    FROM python:3.11-slim

    # Prevent Python stdout buffering (nice for Cloud Run logs)
    ENV PYTHONUNBUFFERED=1
    
    # ---- 2. Set working directory ---------------------------------------
    WORKDIR /app
    
    # ---- 3. Copy and install Python deps --------------------------------
    COPY requirements.txt .
    RUN pip install --no-cache-dir -r requirements.txt
    
    # ---- 4. Copy application source code --------------------------------
    COPY . .
    
    # ---- 5. Expose the port your app will listen on ---------------------
    EXPOSE 8080
    
    # ---- 6. Start Gunicorn with an async Uvicorn worker -----------------
    # Gunicorn will automatically listen on the $PORT variable provided by Cloud Run.
    CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "server:app"]