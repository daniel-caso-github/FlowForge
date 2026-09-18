from fastapi import FastAPI

from budget_service.db import Base, engine
from budget_service.routes import router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="budget-service")
app.include_router(router)
