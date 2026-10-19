FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN useradd --create-home appuser
COPY --chown=appuser:appuser quality_tools ./quality_tools
USER appuser
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "quality_tools.api:app", "--host", "0.0.0.0", "--port", "8000"]
