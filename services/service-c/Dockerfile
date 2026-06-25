FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code
COPY services/service-c/app.py ./services/service-c/
COPY services/service-c/logger.py ./services/service-c/

# Expose port
EXPOSE 3003

# Run the service
CMD ["python", "services/service-c/app.py"]
