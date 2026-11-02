FROM python:3.14-slim@sha256:930e1abba7c4e8f96ed93e8012c35d174d7732752731bbd5e8e757d7ec6f3966

COPY --from=ghcr.io/astral-sh/uv:0.10.10 /uv /usr/local/bin/uv

# Match the host user so files written to the mounted data folder stay editable.
ARG UID=1000
ARG GID=1000
RUN groupadd --gid "$GID" app \
    && useradd --uid "$UID" --gid "$GID" --create-home app \
    && mkdir /app \
    && chown app:app /app

USER app
WORKDIR /app

ENV UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

COPY --chown=app:app pyproject.toml uv.lock .python-version ./
RUN uv sync --frozen --no-install-project

COPY --chown=app:app api ./api
COPY --chown=app:app checkbox_detection ./checkbox_detection
COPY --chown=app:app frontend ./frontend

EXPOSE 8000

CMD ["uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8000"]
