

class TTTPlayerType:
    PLAYER_TYPE_COMPUTER = 0
    PLAYER_TYPE_HUMAN = 1
    PLAYER_TYPE_STRING = {PLAYER_TYPE_COMPUTER: "Computer", PLAYER_TYPE_HUMAN: "Human"}

    @staticmethod
    def get_code():
        raise NotImplementedError()

    @staticmethod
    def get_string(code):
        return TTTPlayerType.PLAYER_TYPE_STRING[code]


class TTTPlayerTypeHuman(TTTPlayerType):
    @staticmethod
    def get_code(self):
        return TTTPlayerType.PLAYER_TYPE_HUMAN

    @staticmethod
    def get_string():
        return TTTPlayerType.get_string(TTTPlayerTypeHuman.get_code())


class TTTPlayerTypeComputer(TTTPlayerType):
    @staticmethod
    def get_code(self):
        return TTTPlayerType.PLAYER_TYPE_COMPUTER

    @staticmethod
    def get_string():
        return TTTPlayerType.get_string(TTTPlayerTypeComputer.get_code())
