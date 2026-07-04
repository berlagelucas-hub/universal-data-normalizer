# -----------------------------------------------------------------------------
# Builder
# -----------------------------------------------------------------------------
FROM python:3.14-slim AS builder

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock README.md ./
COPY src ./src

RUN uv build


# -----------------------------------------------------------------------------
# Runtime
# -----------------------------------------------------------------------------
FROM python:3.14-slim

WORKDIR /app

COPY --from=builder /app/dist/*.whl .

RUN pip install --no-cache-dir *.whl && rm *.whl

CMD ["python", "-m", "python_service_template"]