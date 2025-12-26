from enum import IntEnum


class BackupStatusEnum(IntEnum):
    CREATING = 0
    COMPLETED = 1
    FAILED = 2
    DELETING = 3
    DELETED = 4


class BackupTypeEnum(IntEnum):
    MANUAL = 0
    SCHEDULED = 1


BACKUP_STATUSES_DESCRIPTION = {
    BackupStatusEnum.CREATING: "Создание бекапа",
    BackupStatusEnum.COMPLETED: "Бекап успешно создан",
    BackupStatusEnum.FAILED: "При создании бекапа произошла ошибка",
    BackupStatusEnum.DELETING: "Бекап удаляется",
    BackupStatusEnum.DELETED: "Бекап удалён",
}

BACKUP_TYPES_DESCRIPTION = {
    BackupTypeEnum.MANUAL: "Ручной бекап",
    BackupTypeEnum.SCHEDULED: "Автоматический бекап по расписанию",
}
