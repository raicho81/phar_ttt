#!/usr/bin/python3
import copy
import json
import os
from threading import Thread
from multiprocessing import Pool

import logging
from dynaconf import settings

import ttt_play
import ttt_game_type
import ttt_train_data
import ttt_train_data_redis
import ttt_train_data_postgres
import ttt_data_encoder
import ttt_dependency_injection


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


class TTTMain():
    def __init__(self, training_data_shared, inner_iterations, n_iter_info_skip, game_type, train, board_size, concurrency):
        self.training_data_shared = training_data_shared
        self.n_iter_info_skip = n_iter_info_skip
        self.train = train
        self.concurrency = concurrency
        self.board_size = board_size
        self.game_type = game_type
        logger.info(f"Desk size: {self.board_size}")
        logger.info(f"Game type: {self.game_type.get_string()}")
        logger.info(f"Train: {self.train}")
        self.inner_iterations = inner_iterations
        self.instances = [ttt_play.TTTPlay(self.board_size, self.training_data_shared, game_type, self.train, self.inner_iterations,
                                    self.n_iter_info_skip) for _ in range(self.concurrency)]

    def run(self):
        logger.debug(f"TTTMain::run(), game_type: {self.game_type.get_string()}, train: {self.train}")
        game_type = self.game_type
        if game_type is ttt_game_type.TTTGameTypeCVsC and self.train:
            threads = [Thread(target=play.run) for play in self.instances]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()
        elif game_type is ttt_game_type.TTTGameTypeCVsC:
                self.instances[0].run()
        elif game_type is ttt_game_type.TTTGameTypeHVsC:
                self.instances[0].run()


class MainProcessPoolRunner:
    def __init__(self, process_pool_size, iterations, inner_iterations, n_iter_info_skip, game_type, train, board_size, threads_count,
                 dbname, user, password, host, port, conn_pool_factor):
        self.process_pool_size = process_pool_size
        self.iterations = iterations
        self.inner_iterations = inner_iterations
        self.train = train
        self.board_size = board_size
        self.concurrency = threads_count
        self.dbname = dbname
        self.user = user
        self.password = password
        self.host = host
        self.port = port
        self.game_type = game_type
        self.n_iter_info_skip = n_iter_info_skip
        self.conn_pool_factor = conn_pool_factor
        self.tp_conn_count = self.concurrency // self.conn_pool_factor or 1

    def pool_update_redis_to_db_run_threaded(self, thrs_data):
        postgres_conn_pool_threaded = ttt_train_data_postgres.ReallyThreadedPGConnectionPool(1, self.tp_conn_count , f"dbname={self.dbname} user={self.user} password={self.password} host={self.host} port={self.port}")
        training_data_shared_postgres = ttt_train_data_postgres.TTTTrainDataPostgres(self.board_size, postgres_conn_pool_threaded)
        threads = [Thread(target=training_data_shared_postgres.update_from_redis, args=(d,)) for d in thrs_data]
        [t.start() for t in threads]
        [t.join() for t in threads]
        training_data_shared_redis = ttt_train_data_redis.TTTTrainDataRedis(self.board_size, settings.REDIS_HOST, settings.REDIS_PORT, settings.REDIS_PASS,
                                                                    settings.REDIS_DESKS_HSET_KEY, settings.REDIS_STATES_HSET_KEY_PREFIX)
    def pool_main_run_train_cvsc(self):
        training_data_shared_redis = ttt_train_data_redis.TTTTrainDataRedis(self.board_size, settings.REDIS_HOST, settings.REDIS_PORT, settings.REDIS_PASS,
                                                                        settings.REDIS_DESKS_HSET_KEY, settings.REDIS_STATES_HSET_KEY_PREFIX)
        m = TTTMain(training_data_shared_redis, self.inner_iterations, self.n_iter_info_skip, self.game_type, self.train, self.board_size, self.concurrency)
        m.run()

    def run(self):
        training_data_shared_redis = ttt_train_data_redis.TTTTrainDataRedis(self.board_size, settings.REDIS_HOST, settings.REDIS_PORT, settings.REDIS_PASS, settings.REDIS_DESKS_HSET_KEY, settings.REDIS_STATES_HSET_KEY_PREFIX)
        postgres_conn_pool_threaded = ttt_train_data_postgres.ReallyThreadedPGConnectionPool(1, self.tp_conn_count , f"dbname={self.dbname} user={self.user} password={self.password} host={self.host} port={self.port}")
        training_data_shared_postgres = ttt_train_data_postgres.TTTTrainDataPostgres(self.board_size, postgres_conn_pool_threaded)
        if self.game_type is ttt_game_type.TTTGameTypeCVsC and self.train:
            if settings.MASTER and settings.CLEAR_REDIS_DATA_ON_START:
                training_data_shared_redis.clear()
            for run_n in range(self.iterations):
                # self.pool_main_run_train_cvsc() # For debug purposes
                if settings.SLAVE:
                    with Pool(self.process_pool_size) as pool:
                        for _ in range(self.process_pool_size):
                            pool.apply_async(self.pool_main_run_train_cvsc)
                        pool.close()
                        pool.join()
                if settings.MASTER:
                    scan_gen = training_data_shared_redis.hscan_states(count=settings.REDIS_HSCAN_SLICE_SIZE)
                    try:
                        next_slice = next(scan_gen)
                    except StopIteration:
                        next_slice = None
                    while next_slice:
                        with Pool(self.process_pool_size) as pool:
                            for _ in range(self.process_pool_size):
                                thrs_data = []
                                for n_thr in range(self.concurrency):
                                    d = {}
                                    for state, moves in next_slice.items():
                                        d[int(state)] = json.loads(moves)
                                    thrs_data.append(d)
                                    try:
                                        next_slice = next(scan_gen)
                                    except StopIteration:
                                        next_slice = None
                                        break
                                if thrs_data != []:
                                    pool.apply_async(self.pool_update_redis_to_db_run_threaded, args=(thrs_data,))
                                if next_slice is None:
                                    break
                            pool.close()
                            pool.join()
                    training_data_shared_postgres.inc_total_games_finished(-training_data_shared_postgres.total_games_finished())
                    training_data_shared_postgres.inc_total_games_finished(training_data_shared_redis.total_games_finished())
                    # training_data_shared_redis.clear()
        else:
            if self.game_type is ttt_game_type.TTTGameTypeCVsC:
                ttm = TTTMain(training_data_shared_postgres, self.iterations, self.inner_iterations, self.n_iter_info_skip, self.game_type, self.train, self.board_size, self.threads_count)
                ttm.run()
            elif self.game_type is ttt_game_type.TTTGameTypeHVsC:
                    ttm = TTTMain(training_data_shared_postgres, self.iterations, self.inner_iterations, self.n_iter_info_skip, self.game_type, self.train, self.board_size, self.threads_count)
                    ttm.run()
            else:
                raise ValueError("Unknown game type!")


if __name__ == "__main__":
    init_dep_injection()
    game_type = ttt_game_type.game_type_factory(settings.GAME_TYPE)
    mppr = MainProcessPoolRunner(settings.PROCESS_POOL_SIZE, settings.ITERATIONS, settings.INNER_ITERATIONS, settings.TRAIN_ITERATIONS_INFO_SKIP,
                                 game_type, settings.TRAIN, settings.BOARD_SIZE, settings.THREADS_COUNT, settings.POSTGRES_DBNAME,
                                 settings.POSTGRES_USER, settings.POSTGRES_PASS, settings.POSTGRES_HOST, settings.POSTGRES_PORT,
                                 settings.POSTGRES_CONNECTION_POOLING_FACTOR)
    mppr.run()
