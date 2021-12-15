
def game_type_factory(game_type_string):
    if game_type_string == "HVsC":
        return TTTGameTypeHVsC()
    if game_type_string == "CVsC":
        return TTTGameTypeCVsC()
    raise ValueError("Unknown Game Type!")


class TTTGameType:
    GAME_TYPE_HVsC = 0
    GAME_TYPE_CVsC = 1
    GAME_TYPE_STRING = {GAME_TYPE_HVsC: "Human Vs Computer", GAME_TYPE_CVsC: "Computer Vs Computer"}

    def get_code(self):
        raise NotImplementedError

    def get_string(self):
        return TTTGameType.GAME_TYPE_STRING[self.get_code()]


class TTTGameTypeHVsC(TTTGameType):
    def get_code(self):
        return TTTGameType.GAME_TYPE_HVsC


class TTTGameTypeCVsC(TTTGameType):
    def get_code(self):
        return TTTGameType.GAME_TYPE_CVsC
