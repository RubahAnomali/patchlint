FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
HEALTHCHECK --interval=30s --timeout=3s \
    CMD curl -fsS http://localhost:8000/health || exit 1
EXPOSE 8000
CMD ["python", "-m", "app"]
