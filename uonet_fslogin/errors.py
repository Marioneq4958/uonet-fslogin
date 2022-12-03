class BaseException(Exception):
    pass


class IncorrectCredentialsException(BaseException):
    pass


class FailedRequestException(BaseException):
    pass


class NotRegisteredException(BaseException):
    pass


class NoPermissionsException(BaseException):
    pass


class InvalidLoginFormException(BaseException):
    pass
