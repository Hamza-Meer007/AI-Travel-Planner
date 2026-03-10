# ── Base image ────────────────────────────────────────────────────────────────
# Python 3.10-slim keeps the image small and satisfies onnxruntime==1.13.1
# which only supports up to Python 3.10.
FROM python:3.10-slim

# ── System dependencies ────────────────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

# ── Non-root user (Hugging Face Spaces requires uid 1000) ─────────────────────
RUN useradd -m -u 1000 user
USER user

ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# ── Working directory ──────────────────────────────────────────────────────────
WORKDIR /home/user/app

# ── Install Python dependencies ───────────────────────────────────────────────
# Copy requirements first so Docker can cache this layer.
COPY --chown=user:user requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ── Copy application source ────────────────────────────────────────────────────
COPY --chown=user:user . .

# ── Port ───────────────────────────────────────────────────────────────────────
# Hugging Face Spaces proxies ALL traffic on port 7860.
# Your app MUST listen on this port — not 8000.
EXPOSE 7860

# ── Start FastAPI server ───────────────────────────────────────────────────────
CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "7860"]
