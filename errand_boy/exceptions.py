class ErrandBoyBaseError(Exception):
    pass


class DisconnectedError(ErrandBoyBaseError):
    pass


class SessionClosedError(ErrandBoyBaseError):
    pass


class UnknownMethodError(ErrandBoyBaseError):
    pass
