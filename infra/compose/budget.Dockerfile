FROM python:3.12-slim
RUN pip install --no-cache-dir uv
WORKDIR /app
COPY . .
RUN uv sync --frozen --package budget-service
EXPOSE 8001
CMD ["uv", "run", "--package", "budget-service", "uvicorn", "budget_service.main:app", \
     "--host", "0.0.0.0", "--port", "8001"]
