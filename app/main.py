from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.src.api.admin import app as admin_controller
from app.src.api.auth.controller import app as auth_controller
from app.src.api.clusters.controller import app as clusters_controller
from app.src.dependency import vault

vault.get_vault_client()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_controller, tags=["Auth"])
app.include_router(clusters_controller, tags=["Clusters"])
app.include_router(admin_controller)


# uvicorn app.main:app --host=0.0.0.0 --reload
