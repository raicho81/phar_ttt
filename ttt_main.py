from ttt_play_c_vs_c import TTTPlayCVsC
from ttt_play import  TTTPlayHVsC

from dynaconf import settings


class TTTMain:
    
    def run(self):
        if settings.GAME_TYPE == "CVsC":
            play = TTTPlayCVsC(settings.BOARD_SIZE, settings.TRAIN, settings.TRAINING_DATA_FILE, train_iterations=settings.ITERATIONS,
                               n_iter_info_skip=settings.TRAIN_ITERATIONS_INFO_SKIP)
        if settings.GAME_TYPE == "HVsC":
            play = TTTPlayHVsC(settings.BOARD_SIZE, settings.TRAINING_DATA_FILE)
        play.run()


if __name__ == "__main__":
    main = TTTMain()
    main.run()
