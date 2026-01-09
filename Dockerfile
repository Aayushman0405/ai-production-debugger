# -----------------------------
# Base image
# -----------------------------
FROM python:3.11-slim

# -----------------------------
# Environment
# -----------------------------
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# -----------------------------
# System dependencies
# -----------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# -----------------------------
# Create non-root user
# -----------------------------
RUN useradd -m appuser
WORKDIR /app

# -----------------------------
# Install Python dependencies
# -----------------------------
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip cache purge

# -----------------------------
# Copy application code
# -----------------------------
COPY ai_debugger ./ai_debugger

# -----------------------------
# Permissions
# -----------------------------
RUN chown -R appuser:appuser /app
USER appuser

# -----------------------------
# Expose port
# -----------------------------
EXPOSE 8000

# -----------------------------
# Healthcheck
# -----------------------------
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s \
  CMD curl -f http://localhost:8000/health || exit 1

# -----------------------------
# Start API (MATCHES LOCAL RUN)
# -----------------------------
CMD ["python", "-m", "uvicorn", "ai_debugger.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
