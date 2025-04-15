FROM python:3.9-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create a non-root user to run the application
RUN useradd -m appuser
USER appuser

# Create a volume for novel files
VOLUME /app/docs

# Expose the API port
EXPOSE 5000

# Run the application
CMD ["python", "main.py", "--novel-dirs", "docs", "--port", "5000"]
