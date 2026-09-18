FROM python:3.12-slim
RUN pip install --no-cache-dir uv
WORKDIR /app
COPY . .
RUN uv sync --frozen --package external-sim
EXPOSE 8002
CMD ["uv", "run", "--package", "external-sim", "uvicorn", "external_sim.main:app", \
     "--host", "0.0.0.0", "--port", "8002"]
