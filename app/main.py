from app.config import settings
from app.src.api.auth.controller import app as auth_controller
from app.src.api.clusters.controller import app as clusters_controller
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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


# uvicorn app.main:app --host=0.0.0.0 --reload
