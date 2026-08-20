# ---- Stage 1: Build the React Frontend ----
FROM node:22-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# ---- Stage 2: Build the Python Backend ----
FROM python:3.12-slim
WORKDIR /app

# Install system dependencies required by OpenCV and RapidOCR
RUN apt-get update && apt-get install -y libgl1 libglib2.0-0 && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code and model weights
COPY backend/ ./backend/
COPY models/ ./models/

# Copy the built React files from Stage 1
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Hugging Face Spaces uses port 7860 by default
ENV PORT=7860
EXPOSE 7860

# Run the Uvicorn server
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "7860"]