FROM python:3.12-slim AS build
FROM build
USER app
HEALTHCHECK CMD curl -fsS http://localhost/ || exit 1
