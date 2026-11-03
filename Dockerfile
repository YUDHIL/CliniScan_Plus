FROM python:3.11-slim

# Install system dependencies for OpenCV and PyTorch
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies (Using PyTorch CPU wheel to keep image lightweight and fast on Render)
COPY requirements.txt .
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY models/ ./models/
COPY src/ ./src/
COPY app/ ./app/
COPY data/ ./data/
COPY recommender/ ./recommender/
COPY doctor_2000_realnames.csv .
COPY run_backend.py .


# Environment defaults
ENV PORT=8000
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

# Start FastAPI server
CMD ["python", "run_backend.py"]
