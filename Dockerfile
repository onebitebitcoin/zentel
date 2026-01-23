# ============================================
# Stage 1: Frontend Build
# ============================================
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

# Copy package files first for better caching
COPY frontend/package*.json ./

# Install dependencies
RUN npm ci --only=production=false

# Copy source code
COPY frontend/ ./

# Set production API URL for build
ENV VITE_API_URL=/api/v1

# Build frontend (generates static files in dist/)
RUN npm run build

# ============================================
# Stage 2: Backend Production
# ============================================
FROM python:3.11-slim AS production

WORKDIR /app

# Install system dependencies for Playwright Chromium
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    # Playwright Chromium dependencies
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libcairo2 \
    libatspi2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies one by one to reduce memory usage
RUN pip install --no-cache-dir fastapi==0.115.0 uvicorn==0.30.6
RUN pip install --no-cache-dir pydantic==2.9.2 pydantic-settings==2.5.2
RUN pip install --no-cache-dir sqlalchemy==2.0.35 psycopg2-binary==2.9.9
RUN pip install --no-cache-dir python-ulid==2.7.0
RUN pip install --no-cache-dir "python-jose[cryptography]==3.3.0"
RUN pip install --no-cache-dir "passlib[bcrypt]==1.7.4" "bcrypt>=4.0.0,<5.0.0"
RUN pip install --no-cache-dir "openai>=1.0.0"
RUN pip install --no-cache-dir sse-starlette==2.0.0
RUN pip install --no-cache-dir httpx==0.27.0 playwright==1.49.0

# Install Playwright Chromium browser
RUN playwright install chromium

# Copy backend source code
COPY backend/ ./backend/

# Copy frontend build output (static files)
COPY --from=frontend-builder /app/frontend/dist ./static/

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV ENVIRONMENT=production

# Expose port (Railway provides PORT env var)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Start server
# Railway injects PORT env var automatically
CMD ["sh", "-c", "cd backend && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
