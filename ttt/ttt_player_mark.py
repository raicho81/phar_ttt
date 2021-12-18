

class TTTPlayerMark:
    PLAYER_MARK_X = 0
    PLAYER_MARK_O = 1
    PLAYER_MARK_STRING = {PLAYER_MARK_X: 'x', PLAYER_MARK_O: 'o'}

    @staticmethod
    def get_code():
        raise NotImplementedError()

    @staticmethod
    def get_string(code):
        return TTTPlayerMark.PLAYER_MARK_STRING[code]


class TTTPlayerMarkX(TTTPlayerMark):
    @staticmethod
    def get_code():
        return TTTPlayerMark.PLAYER_MARK_X

    @staticmethod
    def get_string():
        return TTTPlayerMark.get_string(TTTPlayerMarkX.get_code())


class TTTPlayerMarkO(TTTPlayerMark):
    @staticmethod
    def get_code():
        return TTTPlayerMark.PLAYER_MARK_O

    @staticmethod
    def get_string():
        return TTTPlayerMark.get_string(TTTPlayerMarkO.get_code())
