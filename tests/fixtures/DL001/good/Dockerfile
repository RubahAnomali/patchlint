FROM python:3.12-slim
COPY . /app
RUN useradd --create-home app
USER app
CMD ["python", "/app/main.py"]
