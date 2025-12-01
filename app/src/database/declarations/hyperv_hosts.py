from enum import IntEnum


class HypervHostStatusEnum(IntEnum):
    ON_SERVICE = 0
    IN_USING = 1
    DISABLED = 2
    DELETED = 3


HYPERV_HOST_STATUSES_DESCRIPTION = {
    HypervHostStatusEnum.ON_SERVICE: "Сервер находиться на обслуживании",
    HypervHostStatusEnum.IN_USING: "Сервер работает",
    HypervHostStatusEnum.DISABLED: "Сервер отключён",
    HypervHostStatusEnum.DELETED: "Сервер удалён",
}
