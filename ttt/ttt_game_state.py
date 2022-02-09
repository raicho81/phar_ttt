import requests



from django.http import JsonResponse


class TTTGameState:
    GAME_STATE_WIN = 0
    GAME_STATE_DRAW = 1
    GAME_STATE_UNFINISHED = 2

    @staticmethod
    def get_code():
        raise NotImplemented()


class TTTGameStateWin(TTTGameState):
    @staticmethod
    def get_code():
        return TTTGameState.GAME_STATE_WIN


class TTTGameStateDraw(TTTGameState):
    @staticmethod
    def get_code():
        return TTTGameState.GAME_STATE_DRAW


class TTTGameStateUnfinished(TTTGameState):
    @staticmethod
    def get_code():
        return TTTGameState.GAME_STATE_UNFINISHED
