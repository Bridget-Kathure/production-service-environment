FROM python:3.11-slim
WORKDIR /app
COPY app.py .
RUN pip install flask requests
ENV PYTHONUNBUFFERED=1
CMD ["python", "app.py"]
