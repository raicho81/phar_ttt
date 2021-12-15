

class TTTPlayerType:
    PLAYER_TYPE_COMPUTER = 0
    PLAYER_TYPE_HUMAN = 1
    PLAYER_TYPE_STRING = {PLAYER_TYPE_COMPUTER: "Computer", PLAYER_TYPE_HUMAN: "Human"}

    def get_code(self):
        raise NotImplementedError()

    def get_string(self):
        return TTTPlayerType.PLAYER_TYPE_STRING[self.get_code()]


class TTTPlayerTypeHuman(TTTPlayerType):
    def get_code(self):
        return TTTPlayerType.PLAYER_TYPE_HUMAN


class TTTPlayerTypeComputer(TTTPlayerType):
    def get_code(self):
        return TTTPlayerType.PLAYER_TYPE_COMPUTER
