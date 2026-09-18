FROM python:3.12-slim
RUN pip install --no-cache-dir uv
WORKDIR /app
COPY . .
RUN uv sync --frozen --package worker
CMD ["uv", "run", "--package", "worker", "python", "-m", "worker"]
