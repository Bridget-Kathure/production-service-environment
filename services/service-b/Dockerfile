FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code
COPY services/service-b/app.py ./services/service-b/
COPY services/service-b/logger.py ./services/service-b/

# Expose port
EXPOSE 3002

# Run the service
CMD ["python", "services/service-b/app.py"]
