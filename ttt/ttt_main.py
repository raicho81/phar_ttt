#!/usr/bin/python3
import os
from threading import Thread
from multiprocessing import Pool

import logging
from dynaconf import settings
import psycopg2.pool

import ttt_play
import ttt_game_type
import ttt_train_data
import ttt_data_encoder
import ttt_dependency_injection

from threading import Semaphore

logging.basicConfig(level = logging.INFO, filename = "TTTpid-{}.log".format(os.getpid()),
                    filemode = 'a+',
                    format='[%(asctime)s] pid: %(process)d - tid: %(thread)d - %(levelname)s - %(filename)s:%(lineno)s - %(funcName)s() - %(message)s')
logger = logging.getLogger(__name__)


def init_dep_injection():
    # ttt_dependency_injection.DependencyInjection.add_dependency(TTTManager, singleton=True)
    if settings.ENCODE_TRAIN_DATA:
        ttt_dependency_injection.DependencyInjection.add_dependency(ttt_data_encoder.TTTDataEncoderMsgpack)
    else:
        ttt_dependency_injection.DependencyInjection.add_dependency(ttt_data_encoder.TTTDataEncoderNone)
    ttt_dependency_injection.DependencyInjection.add_dependency(ttt_train_data.TTTTrainData, default_args=(), default_kwargs={})


class ReallyThreadedPGConnectionPool(psycopg2.pool.ThreadedConnectionPool):
    def __init__(self, minconn, maxconn, *args, **kwargs):
        self._semaphore = Semaphore(maxconn)
        super().__init__(minconn, maxconn, *args, **kwargs)

    def getconn(self, *args, **kwargs):
        self._semaphore.acquire()
        return super().getconn(*args, **kwargs)

    def putconn(self, *args, **kwargs):
        super().putconn(*args, **kwargs)
        self._semaphore.release()


class TTTMain():
    def __init__(self, inner_iterations, n_iter_info_skip, game_type, train, board_size, concurrency, dbname, user, password, host, port):
        self.n_iter_info_skip = 
        self.train = train
        self.concurrency = concurrency
        self.board_size = board_size
        logger.info(f"Desk size: {settings.BOARD_SIZE}")
        logger.info(f"Game type: {settings.GAME_TYPE}")
        logger.info(f"Train: {settings.TRAIN}")
        tp_conn_count = self.concurrency // 2 or 1
        self.posgres_conn_pool_threaded = ReallyThreadedPGConnectionPool(1, tp_conn_count , f"dbname={dbname} user={user} password={password} host={host} port={port}")
        self.training_data_shared = [ttt_train_data.TTTTrainDataPostgres(self.board_size, self.posgres_conn_pool_threaded) for _ in range(self.concurrency)]
        self.inner_iterations = inner_iterations
        self.game_type = game_type

    def run(self):
        logger.debug("TTTMain::run()")
        game_type = self.game_type
        if game_type is ttt_game_type.TTTGameTypeCVsC and self.train:
            instances = [ttt_play.TTTPlay(self.board_size, self.training_data_shared[_], game_type, self.train, self.inner_iterations,
                                        self.n_iter_info_skip) for _ in range(self.concurrency)]
            threads = [Thread(target=play.run) for play in instances]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()
        else:
            instance = ttt_play.TTTPlay(self.board_size, self.training_data_shared[_], game_type, self.train, self.inner_iterations,
                                        self.n_iter_info_skip)
            instance.run()


class MainProcessPoolRunner:
    def __init__(self, process_pool_size, iterations, inner_iterations, n_iter_info_skip, game_type, train, board_size, threads_count,
                 dbname, user, password, host, port):
        self.process_pool_size = process_pool_size
        self.iterations = iterations
        self.inner_iterations = inner_iterations
        self.train = train
        self.board_size = board_size
        self.threads_count = threads_count
        self.dbname = dbname
        self.user = user
        self.password = password
        self.host = host
        self.port = port
        self.game_type = game_type
        self.n_iter_info_skip = n_iter_info_skip

    def pool_main_run(self):
        m = TTTMain(self.inner_iterations, self.n_iter_info_skip, self.game_type, self.train, self.board_size, self.threads_count, self.dbname, self.user, self.password, self.host, self.port)
        m.run()

    def run(self):
        if self.game_type is ttt_game_type.TTTGameTypeCVsC and self.train:
            for _ in range(self.iterations):
                with Pool(self.process_pool_size) as pool:
                    for _ in range(self.process_pool_size):
                        pool.apply_async(self.pool_main_run)
                    pool.close()
                    pool.join()
        else:
            if self.game_type is ttt_game_type.TTTGameTypeCVsC:
                for _ in range(self.iterations):
                    ttm = TTTMain(self.iterations, self.game_type, self.train, self.board_size, self.threads_count, self.dbname, self.user, self.password, self.host, self.port)
                    ttm.run()
            elif self.game_type is ttt_game_type.TTTGameTypeHVsC:
                    ttm = TTTMain(self.iterations, self.game_type, self.train, self.board_size, self.threads_count, self.dbname, self.user, self.password, self.host, self.port)
                    ttm.run()
            else:
                raise ValueError("Unknown game type!")


if __name__ == "__main__":
    init_dep_injection()
    game_type = ttt_game_type.game_type_factory(settings.GAME_TYPE)
    mppr = MainProcessPoolRunner(settings.PROCESS_POOL_SIZE, settings.ITERATIONS, settings.INNER_ITERATIONS, settings.TRAIN_ITERATIONS_INFO_SKIP,
                                 game_type, settings.TRAIN, settings.BOARD_SIZE, settings.THREADS_COUNT, settings.POSTGRES_DBNAME,
                                 settings.POSTGRES_USER, settings.POSTGRES_PASS, settings.POSTGRES_HOST, settings.POSTGRES_PORT)
    mppr.run()
