import collections


TTTPlayerPathNode = collections.namedtuple("TTTPlayerPathNode", ["state", "move"])

class TTTPlayer:
    PLAYER1 = 1
    PLAYER2 = 2
    PLAYER_STRING = {PLAYER1: "Player 1", PLAYER2: "Player 2"}

    def __init__(self, player_type=None, mark=None):
        self.player_type = player_type
        self.mark = mark
        self.path = []

    def get_code(self):
        raise NotImplementedError

    def get_string(self):
        return TTTPlayer.PLAYER_STRING[self.get_code()]

    def get_mark(self):
        return self.mark

    def get_type(self):
        return self.player_type

    def set_mark(self, mark):
        self.mark = mark

    def set_type(self, player_type):
        self.player_type = player_type

    def add_path_node(self, node):
        self.path.append(node)

    def get_path(self):
        return self.path

    def clear_path(self):
        self.path = []


class TTTPlayer1(TTTPlayer):
    def __init__(self, player_type=None, mark=None):
        super().__init__(player_type=player_type, mark=mark)

    def get_code(self):
        return TTTPlayer.PLAYER1


class TTTPlayer2(TTTPlayer):
    def __init__(self, player_type=None, mark=None):
        super().__init__(player_type=player_type, mark=mark)

    def get_code(self):
        return TTTPlayer.PLAYER2
