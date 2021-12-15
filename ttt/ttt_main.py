from dynaconf import settings

import ttt_play
import ttt_game_type


class TTTMain:
    
    def run(self):
        game_type = ttt_game_type.game_type_factory(settings.GAME_TYPE)
        play = ttt_play.TTTPlay(settings.BOARD_SIZE, game_type, settings.TRAINING_DATA_FILE, settings.TRAIN, train_iterations=settings.ITERATIONS, n_iter_info_skip=settings.TRAIN_ITERATIONS_INFO_SKIP,
                                encode_train_data=settings.ENCODE_TRAIN_DATA)
        play.run()


if __name__ == "__main__":
    main = TTTMain()
    main.run()
