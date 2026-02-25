# Stage 1: Build the frontend
FROM node:20-slim as frontend-builder
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm install
COPY frontend/ . 
RUN npm run build

# Stage 2: Build the backend
FROM python:3.11-slim as backend-builder
WORKDIR /app

# Copy built frontend from the previous stage
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Install backend dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application code
COPY backend/ . 

# Expose the port the app runs on
EXPOSE 80

# Command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]
