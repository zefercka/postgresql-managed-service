from enum import IntEnum


class ClusterStatusEnum(IntEnum):
    CREATING = 0
    RUNNING = 1
    FAILED = 2
    STOPPED = 3
    DELETING = 4
    DELETED = 5
    STARTING = 6


CLUSTER_STATUSES_DESCRIPTION = {
    ClusterStatusEnum.CREATING: "Создание кластера",
    ClusterStatusEnum.RUNNING: "Кластер работает",
    ClusterStatusEnum.FAILED: "При создании кластера произошла ошибка и он был остановлен. Попробуйте пересоздать его",
    ClusterStatusEnum.STOPPED: "Кластер остановлен",
    ClusterStatusEnum.DELETING: "Кластер удаляется",
    ClusterStatusEnum.DELETED: "Кластер удалён",
    ClusterStatusEnum.STARTING: "Кластер запускается",
}
