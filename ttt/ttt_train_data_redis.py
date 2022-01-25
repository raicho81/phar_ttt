import logging
import os
import functools

import crc16
import redis
from pottery import RedisDict

from ttt_train_data_base import TTTTrainDataBase


logging.getLogger("pottery").setLevel("WARN")

logging.basicConfig(level = logging.INFO, filename = "TTTpid-{}.log".format(os.getpid()),
                    filemode = 'a+',
                    format='[%(asctime)s] pid: %(process)d - tid: %(thread)d - %(levelname)s - %(filename)s:%(lineno)s - %(funcName)s() - %(message)s')
logger = logging.getLogger(__name__)


class TTTTrainDataRedis(TTTTrainDataBase):
    def __init__(self, desk_size, host, port, password, redis_desks_hset_key, redis_states_hset_key_prefix):
        super().__init__()
        self.redis_desks_hset_key = redis_desks_hset_key
        self.redis_states_hset_key_prefix = redis_states_hset_key_prefix
        self.desk_size = desk_size
        self.redis_states_hset_key = "{}:size:{}".format(redis_states_hset_key_prefix, self.desk_size)
        try:
            self.__r = redis.Redis(host=host,
                                    port=port,
                                    password=password,
                                    decode_responses=True)
            self.redis_desks_dict = RedisDict(redis=self.__r, key=self.redis_desks_hset_key)
            self.redis_states_dict = RedisDict(redis=self.__r, key=self.redis_states_hset_key)
        except redis.RedisError as re:
            logger.exception(re)
        self.load()

    def hscan_states(self, count):
        try:
            cursor = 0
            while True:
                cursor, entries = self.__r.hscan(self.redis_states_hset_key, cursor, count=count)
                if cursor == 0:
                    break
                if entries != {}:
                    yield entries
        except redis.RedisError as re:
            logger.exception(re)

    def remove_state_from_cache(self, state):
        try:
            lock_key = self.redis_states_hset_key + ":__lock__:{}".format(state)
            with self.__r.lock(lock_key, timeout=1):
                self.redis_states_dict.pop(state)
        except redis.RedisError as re:
            logger.exception(re)

    def total_games_finished(self):
        try:
            with self.__r.lock(self.redis_desks_hset_key + ":__lock__:{}".format(self.desk_size), timeout=1):
                return self.redis_desks_dict[self.desk_size]
        except redis.RedisError as re:
            logger.exception(re)

    def save(self):
        raise NotImplementedError()

    def load(self):
        try:
            with self.__r.lock(self.redis_desks_hset_key + ":__lock__:{}".format(self.desk_size), timeout=1):
                games_finished = self.redis_desks_dict.get(self.desk_size, None)
            if games_finished is None:
                self.inc_total_games_finished(0)
            logger.info("Redis DB contains Data for: {} total games played for training".format(self.redis_desks_dict[self.desk_size]))
            logger.info("Redis DB contains Data for: {} total states".format(len(self.redis_states_dict)))
        except redis.RedisError as re:
            logger.exception(re)

    def has_state(self, state):
        try:
            with self.__r.lock(self.redis_states_hset_key + ":__lock__:{}".format(state), timeout=1):
                return state in self.redis_states_dict
        except redis.RedisError as re:
            logger.exception(re)

    def add_train_state(self, state, possible_moves):
        try:
            with self.__r.lock(self.redis_states_hset_key + ":__lock__:{}".format(state), timeout=1):
                if state not in self.redis_desks_dict:
                    self.redis_states_dict[state] = possible_moves
                    add = True
                else:
                    add = False
            if not add:
                self.update_train_state_moves(state, possible_moves)
        except redis.RedisError as re:
            logger.exception(re)

    def find_train_state_possible_move_by_idx(self, state, move_idx):
        raise NotImplementedError()

    def inc_total_games_finished(self, count):
        try:
            with self.__r.lock(self.redis_desks_hset_key + ":__lock__:{}".format(self.desk_size), timeout=1):
                current_total = self.redis_desks_dict.get(self.desk_size, None)
                if current_total is not None:
                    current_total = int(current_total) + count
                else:
                    current_total = count
                self.redis_desks_dict[self.desk_size] = current_total
        except redis.RedisError as re:
            logger.exception(re)


    def update_train_state_moves(self, state, other_moves):
        try:
            with self.__r.lock(self.redis_states_hset_key + ":__lock__:{}".format(state), timeout=1):
                moves_to_update_decoded = self.redis_states_dict[state]
                for i, this_move in enumerate(moves_to_update_decoded):
                    this_move[1] += other_moves[i][1]
                    this_move[2] += other_moves[i][2]
                    this_move[3] += other_moves[i][3]
                self.redis_states_dict[state] = moves_to_update_decoded
        except redis.RedisError as re:
            logger.exception(re)

    def get_train_state(self, state, raw=False):
        try:
            with self.__r.lock(self.redis_states_hset_key + ":__lock__:{}".format(state), timeout=1):
                return self.redis_states_dict[state if raw == True else self.int_none_tuple_hash(state)]
        except redis.RedisError as re:
            logger.exception(re)

    def update_train_state(self, state, move):
        raise NotImplementedError()

    def get_train_data(self):
        return self.redis_states_dict

    def clear(self):
        self.redis_desks_dict.clear()
        self.redis_states_dict.clear()

    def update(self, other):
        logger.info("Updating Intermediate data to Redis: 0% ...")
        s = len(other.get_train_data())
        vis = s // 10
        if vis == 0 :
            vis = 2
        count = 0
        for state in other.get_train_data():
            other_moves = other.get_train_state(state, True)
            if self.has_state(state):
                self.update_train_state_moves(state, other_moves)
            else:
                self.add_train_state(state, other_moves)
            count += 1
            if count % vis == 0:
                logger.info("Updating Intermediate data to Redis complete@{}%".format(int((count / s) * 100)))
        logger.info("Updating Intermediate data to Redis Done.")
        self.inc_total_games_finished(other.total_games_finished)

