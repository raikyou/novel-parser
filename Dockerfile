FROM python:3.9-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create volumes for novel files and data
VOLUME /app/docs
VOLUME /app/data

# Expose the API port
EXPOSE 5000

# Run the application
CMD ["python", "main.py", "--novel-dirs", "docs", "--db-path", "data/novels.db", "--port", "5000"]
