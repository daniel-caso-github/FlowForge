from fastapi import FastAPI

from invoice_service.api.routes import router
from invoice_service.infrastructure.db import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI(title="invoice-service")
app.include_router(router)
