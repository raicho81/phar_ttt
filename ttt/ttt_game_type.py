
def game_type_factory(game_type_string):
    if game_type_string == "HVsC":
        return TTTGameTypeHVsC
    if game_type_string == "CVsC":
        return TTTGameTypeCVsC
    raise ValueError("Unknown Game Type!")


class TTTGameType:
    GAME_TYPE_HVsC = 0
    GAME_TYPE_CVsC = 1
    GAME_TYPE_STRING = {GAME_TYPE_HVsC: "Human Vs Computer", GAME_TYPE_CVsC: "Computer Vs Computer"}

    @staticmethod
    def get_code():
        raise NotImplementedError

    @staticmethod
    def get_string(code):
        return TTTGameType.GAME_TYPE_STRING[code]


class TTTGameTypeHVsC(TTTGameType):
    def get_code(self):
        return TTTGameType.GAME_TYPE_HVsC

    @staticmethod
    def get_string(code):
        return TTTGameType.get_string(TTTGameTypeHVsC.get_code())


class TTTGameTypeCVsC(TTTGameType):
    def get_code(self):
        return TTTGameType.GAME_TYPE_CVsC

    @staticmethod
    def get_string(code):
        return TTTGameType.get_string(TTTGameTypeCVsC.get_code())
