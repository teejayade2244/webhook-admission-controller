FROM python:3.13-alpine	

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apk add --no-cache gcc musl-dev linux-headers

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY webhook.py .

# Create directory for TLS certificates
RUN mkdir -p /etc/webhook/certs

# Create non-root user for security
RUN adduser -S -G nobody appuser && \
    chown -R appuser:nobody /app /etc/webhook/certs
USER appuser

# Expose the webhook port
EXPOSE 8443

# Run the application
CMD ["python", "webhook.py"]