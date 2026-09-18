from fastapi import FastAPI

from external_sim.routes import router
from external_sim.store import InMemoryStore

app = FastAPI(title="external-sim")
app.state.store = InMemoryStore()
app.include_router(router)
