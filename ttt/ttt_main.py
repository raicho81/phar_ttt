#!/usr/bin/python3
import json
import os
from threading import Thread, Semaphore
from multiprocessing import Pool, Manager
import sys
import logging

from dynaconf import settings
if len(sys.argv) > 1:
    settings.load_file(path=sys.argv[1])

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
        logger.info("pool_update_redis_to_db_run_threaded -> process started")
        postgres_conn_pool_threaded = ttt_train_data_postgres.ReallyThreadedPGConnectionPool(1, self.tp_conn_count , f"dbname={self.dbname} user={self.user} password={self.password} host={self.host} port={self.port}")
        training_data_shared_postgres = ttt_train_data_postgres.TTTTrainDataPostgres(self.board_size, postgres_conn_pool_threaded)
        logger.info("pool_update_redis_to_db_run_threaded -> starting {} thread(s)".format(len(thrs_data)))
        threads = [Thread(target=training_data_shared_postgres.update_from_redis, args=(msg_data.items(),)) for msg_data in thrs_data]
        [t.start() for t in threads]
        [t.join() for t in threads]
        logger.info("pool_update_redis_to_db_run_threaded -> process ended")
        return True

    def pool_main_run_train_cvsc(self):
        training_data_shared_redis = ttt_train_data_redis.TTTTrainDataRedis(self.board_size, settings.REDIS_HOST, settings.REDIS_PORT, settings.REDIS_PASS, settings.REDIS_DESKS_HSET_KEY,
                                                                            settings.REDIS_STATES_HSET_KEY_PREFIX, settings.REDIS_CONSUMER_GROUP_NAME, settings.REDIS_CONSUMER_NAME)
        m = TTTMain(training_data_shared_redis, self.inner_iterations, self.n_iter_info_skip, self.game_type, self.train, self.board_size, self.concurrency)
        m.run()
        return True

    def get_next_states_to_update_from_redis_stream(self, training_data_shared_redis, timeout=5):
        next_states_to_update = training_data_shared_redis.get_states_to_update_from_stream(timeout=timeout)
        if next_states_to_update == []:
            return None
        ret = {}
        for msg_id, message in next_states_to_update[0][1]:
            ret[msg_id] = json.loads(message["states_to_update"])
        return ret

    def run(self):
        training_data_shared_redis = ttt_train_data_redis.TTTTrainDataRedis(self.board_size, settings.REDIS_HOST, settings.REDIS_PORT, settings.REDIS_PASS, settings.REDIS_DESKS_HSET_KEY,
                                                                            settings.REDIS_STATES_HSET_KEY_PREFIX, settings.REDIS_CONSUMER_GROUP_NAME, settings.REDIS_CONSUMER_NAME)
        postgres_conn_pool_threaded = ttt_train_data_postgres.ReallyThreadedPGConnectionPool(1, self.tp_conn_count , f"dbname={self.dbname} user={self.user} password={self.password} host={self.host} port={self.port}")
        training_data_shared_postgres = ttt_train_data_postgres.TTTTrainDataPostgres(self.board_size, postgres_conn_pool_threaded)

        if self.game_type is ttt_game_type.TTTGameTypeCVsC and self.train:
            if settings.REDIS_MASTER and settings.REDIS_CLEAR_DATA_ON_START:
                training_data_shared_redis.clear()
            if not settings.REDIS_MASTER:
                with Pool(self.process_pool_size) as pool:
                    for run_n in range(self.iterations):
                        res = []
                        # self.pool_main_run_train_cvsc()
                        for _ in range(self.process_pool_size):
                            res.append(pool.apply_async(self.pool_main_run_train_cvsc))
                        for r in res:
                           r.wait()
                        
            if settings.REDIS_MASTER:
                with Pool(self.process_pool_size) as pool:
                    res = []
                    while True:
                        training_data_shared_redis.claim_pending_stream_messages(self.process_pool_size * self.concurrency)
                        for _ in range(self.process_pool_size - len(res)):
                            thrs_data = []
                            for n_thr in range(self.concurrency):
                                next_states_to_update = self.get_next_states_to_update_from_redis_stream(training_data_shared_redis)
                                if next_states_to_update is None:
                                    break
                                thrs_data.append(next_states_to_update)
                            if thrs_data != []:
                                # self.pool_update_redis_to_db_run_threaded(thrs_data,)
                                res.append(pool.apply_async(self.pool_update_redis_to_db_run_threaded, args=(thrs_data,)))
                        for r in res:
                            r.wait()
                            res.remove(r)
                            break
        else:
            if self.game_type is ttt_game_type.TTTGameTypeCVsC:
                ttm = TTTMain(training_data_shared_postgres, self.inner_iterations, self.n_iter_info_skip, self.game_type, self.train, self.board_size, self.concurrency)
                ttm.run()
            elif self.game_type is ttt_game_type.TTTGameTypeHVsC:
                    ttm = TTTMain(training_data_shared_postgres, self.inner_iterations, self.n_iter_info_skip, self.game_type, self.train, self.board_size, self.concurrency)
                    ttm.run()
            else:
                raise ValueError("Unknown game type!")


if __name__ == "__main__":
    game_type = ttt_game_type.game_type_factory(settings.GAME_TYPE)
    mppr = MainProcessPoolRunner(settings.PROCESS_POOL_SIZE, settings.ITERATIONS, settings.INNER_ITERATIONS, settings.TRAIN_ITERATIONS_INFO_SKIP,
                                 game_type, settings.TRAIN, settings.BOARD_SIZE, settings.THREADS_COUNT, settings.POSTGRES_DBNAME,
                                 settings.POSTGRES_USER, settings.POSTGRES_PASS, settings.POSTGRES_HOST, settings.POSTGRES_PORT,
                                 settings.POSTGRES_CONNECTION_POOLING_FACTOR)
    mppr.run()
