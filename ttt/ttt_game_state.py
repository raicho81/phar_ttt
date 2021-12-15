

class TTTGameState:

    GAME_STATE_WIN = 0
    GAME_STATE_DRAW = 1
    GAME_STATE_UNFINISHED = 2

    def get_code():
        raise NotImplemented()


class TTTGameStateWin(TTTGameState):
    def get_code():
        return TTTGameState.GAME_STATE_WIN


class TTTGameStateDraw(TTTGameState):
    def get_code():
        return TTTGameState.GAME_STATE_DRAW


class TTTGameStateUnfinished(TTTGameState):
    def get_code():
        return TTTGameState.GAME_STATE_UNFINISHED
