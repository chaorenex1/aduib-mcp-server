from controllers.common.base import BaseHttpException


class ApiNotCurrentlyAvailableError(BaseHttpException):
    def __init__(self):
        super().__init__(error_code=403, error_msg="api key is not currently available")

class ServiceError(BaseHttpException):
    def __init__(self, message: str = "service error"):
        super().__init__(error_code=500, error_msg=message)
class BadRequestError(BaseHttpException):
    def __init__(self, message: str = "bad request"):
        super().__init__(error_code=400, error_msg=message)
class UnauthorizedError(BaseHttpException):
    def __init__(self, message: str = "unauthorized"):
        super().__init__(error_code=401, error_msg=message)
class ForbiddenError(BaseHttpException):
    def __init__(self, message: str = "forbidden"):
        super().__init__(error_code=403, error_msg=message)


class InnerError(Exception):
    code: int
    message: str

    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message