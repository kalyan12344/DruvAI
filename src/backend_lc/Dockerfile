#######################################################################
# Dockerfile – Druv backend (Flask / FastAPI / LangChain / Playwright)
#######################################################################

# ---- 1. Base image --------------------------------------------------
    FROM python:3.11-slim

    # Prevent Python stdout buffering (nice for Cloud Run logs)
    ENV PYTHONUNBUFFERED=1
    
    # ---- 2. Set working directory ---------------------------------------
    WORKDIR /app
    
    # ---- 3. Copy and install Python deps --------------------------------
    COPY requirements.txt .
    RUN pip install --no-cache-dir -r requirements.txt
    
    # ---- 4. Install system libs Playwright/Chromium needs ---------------
    RUN apt-get update && \
        apt-get install -y --no-install-recommends \
            wget gnupg libnss3 libatk1.0-0 libatk-bridge2.0-0 \
            libcups2 libdrm2 libgbm1 libxshmfence1 && \
        rm -rf /var/lib/apt/lists/*
    
    # ---- 5. Install Playwright browsers & deps --------------------------
    # RUN playwright install --with-deps
    
    # ---- 6. Copy application source code --------------------------------
    # (Build context is src/backend_lc/, so this brings in backend only.)
    COPY . .
    
    # ---- 7. Cloud Run expects the service to listen on $PORT ------------
    ENV PORT=8080
    EXPOSE 8080
    
    # ---- 8. Start Gunicorn with an async Uvicorn worker -----------------
    # Gunicorn will automatically listen on the $PORT variable.
    # The "-b" flag is not needed when deploying to Cloud Run.
    CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "server:app"]