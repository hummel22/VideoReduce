FROM node:20 AS frontend-builder

WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm install

COPY frontend .
ARG ADMIN_DASHBOARD_TOKEN=dashboard-service-token
ENV VITE_ADMIN_API_TOKEN=${ADMIN_DASHBOARD_TOKEN}
RUN npm run build

FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r backend/requirements.txt

COPY backend ./backend
COPY --from=frontend-builder /app/frontend/dist ./backend/app/static/frontend
COPY setup_backend.sh ./setup_backend.sh
RUN chmod +x ./setup_backend.sh

ENV VIDEOR_ADMIN_USERNAME=admin \
    VIDEOR_ADMIN_PASSWORD=changeme \
    VIDEOR_JWT_SECRET_KEY=change-me \
    VIDEOR_DASHBOARD_USERNAME=dashboard \
    VIDEOR_DASHBOARD_TOKEN=dashboard-service-token

EXPOSE 8000

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
