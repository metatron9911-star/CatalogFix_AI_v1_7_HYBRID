FROM python:3.12-slim
WORKDIR /app
COPY main.py command.json /app/
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
CMD ["python", "/app/main.py"]
