import pytest
from external_sim.routes import router
from external_sim.store import InMemoryStore
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture()
def client():
    app = FastAPI()
    app.state.store = InMemoryStore()
    app.include_router(router)
    return TestClient(app)
