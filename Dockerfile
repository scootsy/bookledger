FROM node:22-alpine AS frontend
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app
COPY backend/pyproject.toml ./backend/
RUN pip install --no-cache-dir -e ./backend

COPY backend/ ./backend/
COPY --from=frontend /build/build ./backend/bookledger/static

COPY backend/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8787
ENV BOOKLEDGER_CONFIG_DIR=/config
VOLUME ["/config"]

ENTRYPOINT ["/entrypoint.sh"]
