
class BaseCode:
    CODE = -1

    @staticmethod
    def code_(cls):
        return eval(cls.__name__).CODE


class CodeStart(BaseCode):
    CODE = 0


class CodeGO(BaseCode):
    CODE = 1


class CodeMove(BaseCode):
    CODE = 2


class CodeRedraw(BaseCode):
    CODE = 3


class Message:
    def __init__(self, code=BaseCode, payload=None):
        self._code = code
        self._payload = payload
    
    @property
    def code(self):
        return self._code.code(self._code.__class__)
    
    @property
    def payload(self):
        return self._payload

print(BaseCode.code_(CodeStart))
print(BaseCode.code_(CodeGO))
print(BaseCode.code_(CodeMove))
print(BaseCode.code_(CodeRedraw))