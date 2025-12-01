from fastapi import APIRouter

from .hosts import hosts_controller

app = APIRouter(prefix="/admin")
app.include_router(hosts_controller, tags=["[Admin] HyperV Hosts"])
