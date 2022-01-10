#!/usr/bin/python3
import os
from multiprocessing import Pool, Manager
from multiprocessing.managers import BaseManager

import logging 
from dynaconf import settings


import ttt_play
import ttt_game_type
import ttt_train_data
import ttt_data_encoder
import ttt_dependency_injection


logging.basicConfig(level = logging.INFO, filename = "TTTpid-{}.log".format(os.getpid()),
                    filemode = 'a+',
                    format='[%(asctime)s] pid: %(process)d - %(levelname)s - %(filename)s:%(lineno)s - %(funcName)s() - %(message)s')
logger = logging.getLogger(__name__)


class TTTManager(BaseManager):
    pass

def init_process_pool_manager():
    TTTManager.register('TTTTrainDataPostgres', ttt_train_data.TTTTrainDataPostgres)

def init_dep_injection():
    ttt_dependency_injection.DependencyInjection.add_dependency(TTTManager, singleton=True)
    if settings.ENCODE_TRAIN_DATA:
        ttt_dependency_injection.DependencyInjection.add_dependency(ttt_data_encoder.TTTDataEncoderMsgpack)
    else:
        ttt_dependency_injection.DependencyInjection.add_dependency(ttt_data_encoder.TTTDataEncoderNone)
    ttt_dependency_injection.DependencyInjection.add_dependency(ttt_train_data.TTTTrainData, default_args=(), default_kwargs={})


class TTTMain():
    @ttt_dependency_injection.DependencyInjection.inject
    def __init__(self, iterations, *, manager=ttt_dependency_injection.Dependency(BaseManager)):
        self.process_managers = [TTTManager() for _ in range(settings.PROCESS_POOL_SIZE if settings.PROCESS_POOL_SIZE !=0 else os.cpu_count())]
        [self.process_managers[i].start() for i in range(settings.PROCESS_POOL_SIZE if settings.PROCESS_POOL_SIZE !=0 else os.cpu_count())]
        logger.info("IPC manager started")
        logger.info(f"Desk size: {settings.BOARD_SIZE}")
        logger.info(f"Game type: {settings.GAME_TYPE}")
        logger.info(f"Train: {settings.TRAIN}")
        self.training_data_shared = [self.process_managers[_].TTTTrainDataPostgres(settings.BOARD_SIZE) for _ in range(settings.PROCESS_POOL_SIZE if settings.PROCESS_POOL_SIZE !=0 else os.cpu_count())]
        self.iterations = iterations

    def run(self):
        res = []
        game_type = ttt_game_type.game_type_factory(settings.GAME_TYPE)
        if game_type is ttt_game_type.TTTGameTypeCVsC and settings.TRAIN:
            instances = [ttt_play.TTTPlay(settings.BOARD_SIZE, self.training_data_shared[instance], game_type, settings.TRAIN, train_iterations=settings.INNER_ITERATIONS,
                                          n_iter_info_skip=settings.TRAIN_ITERATIONS_INFO_SKIP,) for instance in range(settings.PROCESS_POOL_SIZE if settings.PROCESS_POOL_SIZE!=0 else os.cpu_count())]
            for _ in range(self.iterations):
                with Pool(settings.PROCESS_POOL_SIZE if settings.PROCESS_POOL_SIZE !=0 else os.cpu_count()) as pool:
                    for instance in instances:
                            res = [pool.apply_async(instance.run)]
                    pool.close()
                    pool.join()
            # instance = ttt_play.TTTPlay(settings.BOARD_SIZE, self.training_data_shared[0], game_type, settings.TRAIN, train_iterations=settings.INNER_ITERATIONS,
            #                              n_iter_info_skip=settings.TRAIN_ITERATIONS_INFO_SKIP)
            # for _ in range(self.iterations):
            #     instance.run()
        else:
            instance = ttt_play.TTTPlay(settings.BOARD_SIZE, self.training_data_shared[0], game_type, settings.TRAIN, train_iterations=settings.INNER_ITERATIONS,
                                         n_iter_info_skip=settings.TRAIN_ITERATIONS_INFO_SKIP)
            instance.run()


if __name__ == "__main__":
    init_process_pool_manager()
    init_dep_injection()
    main = TTTMain(settings.ITERATIONS)
    main.run()
