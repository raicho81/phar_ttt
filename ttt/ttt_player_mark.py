

class TTTPlayerMark:
    PLAYER_MARK_X = 0
    PLAYER_MARK_O = 1
    PLAYER_MARK_STRING = {PLAYER_MARK_X: 'x', PLAYER_MARK_O: 'o'}

    def get_code(self):
        raise NotImplementedError()

    def get_string(self):
        return TTTPlayerMark.PLAYER_MARK_STRING[self.get_code()]


class TTTPlayerMarkX(TTTPlayerMark):
    def get_code(self):
        return super().PLAYER_MARK_X


class TTTPlayerMarkO(TTTPlayerMark):
    def get_code(self):
        return super().PLAYER_MARK_O
