from fastapi import FastAPI

from budget_service.api.routes import router
from budget_service.infrastructure.db import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI(title="budget-service")
app.include_router(router)
