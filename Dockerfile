FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create necessary directories
RUN mkdir -p /app/ai_debugger/{api,collector,correlator,reasoning,tests}

# Copy application code
COPY ai_debugger/ /app/ai_debugger/

# Create __init__.py files
RUN touch /app/ai_debugger/__init__.py \
    && touch /app/ai_debugger/api/__init__.py \
    && touch /app/ai_debugger/collector/__init__.py \
    && touch /app/ai_debugger/correlator/__init__.py \
    && touch /app/ai_debugger/reasoning/__init__.py \
    && touch /app/ai_debugger/tests/__init__.py

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "ai_debugger.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
