import os
from multiprocessing import freeze_support, Pool, Manager
from multiprocessing.managers import BaseManager
import functools
import logging

from dynaconf import settings


import ttt_play
import ttt_game_type
import ttt_train_data
import ttt_data_encoder

# logging.basicConfig(level = logging.INFO, filename = "TTTpid-{}.log".format(os.getpid()), filemode = 'w', format='%(process)d - %(name)s - %(levelname)s - %(message)s')

class TTTManager(BaseManager):
    pass

TTTManager.register('TTTTrainData', ttt_train_data.TTTTrainData)

class TTTMain:

    def __init__(self, iterations):
        # self.training_data_shared = ttt_train_data.TTTTrainData(ttt_data_encoder.TTTDataEncoder, settings.TRAINING_DATA_FILE)
        self.process_manager = TTTManager()
        self.m = Manager()
        self.data_lock = self.m.Lock()
        self.process_manager.start()        
        self.training_data_shared = self.process_manager.TTTTrainData(ttt_data_encoder.TTTDataEncoder, settings.TRAINING_DATA_FILE)
        self.training_data_shared.load()
        self.process_pool = Pool(settings.PROCESS_POOL_SIZE if settings.PROCESS_POOL_SIZE !=0 else os.cpu_count())
        self.iterations = iterations

    def run(self):
        res = []
        game_type = ttt_game_type.game_type_factory(settings.GAME_TYPE)
        if game_type.get_code() == ttt_game_type.TTTGameTypeCVsC.get_code() and settings.TRAIN:
            instances = [ttt_play.TTTPlay(settings.BOARD_SIZE, game_type, self.training_data_shared, settings.TRAIN, train_iterations=settings.INNER_ITERATIONS, n_iter_info_skip=settings.TRAIN_ITERATIONS_INFO_SKIP,
                                    encode_train_data=settings.ENCODE_TRAIN_DATA) for instance in range(settings.PROCESS_POOL_SIZE if settings.PROCESS_POOL_SIZE!=0 else os.cpu_count())]
            for _ in range(self.iterations):
                for instance in instances:
                    f = functools.partial(instance.run, self.data_lock)
                    res.append(self.process_pool.apply_async(f))
            self.process_pool.close()
            self.process_pool.join()
        else:
            instance = ttt_play.TTTPlay(settings.BOARD_SIZE, game_type, self.training_data_shared, settings.TRAIN, train_iterations=settings.INNER_ITERATIONS,
                                         n_iter_info_skip=settings.TRAIN_ITERATIONS_INFO_SKIP, encode_train_data=settings.ENCODE_TRAIN_DATA)
            f = functools.partial(instance.run, self.data_lock)
            res.append(self.process_pool.apply_async(f))
            self.process_pool.close()
            self.process_pool.join()            
        if settings.TRAIN:
            self.training_data_shared.save()

if __name__ == "__main__":
    # freeze_support()
    main = TTTMain(settings.ITERATIONS)
    main.run()
