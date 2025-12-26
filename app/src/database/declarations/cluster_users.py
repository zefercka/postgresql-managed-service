from enum import IntEnum


class ClusterUserStatusEnum(IntEnum):
    CREATING = 0
    EXISTING = 1
    DELETED = 2


CLUSTER_USER_STATUSES_DESCRIPTION = {
    ClusterUserStatusEnum.CREATING: "Создание пользователя",
    ClusterUserStatusEnum.EXISTING: "Пользователь существует",
    ClusterUserStatusEnum.DELETED: "Пользователь удалён",
}
