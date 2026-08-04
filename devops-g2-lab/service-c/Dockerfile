FROM python:3.11-slim
WORKDIR /app
COPY app.py .
RUN pip install flask
ENV PYTHONUNBUFFERED=1
CMD ["python", "app.py"]
