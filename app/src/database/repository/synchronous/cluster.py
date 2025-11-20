from app.src.database.models import Cluster

from . import BaseRepository


class ClusterRepository(BaseRepository[Cluster]):
    model = Cluster
