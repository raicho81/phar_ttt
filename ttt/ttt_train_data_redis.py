import logging
import os
import json

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

    def remove_states_from_cache(self, states):
        try:
            locks = []
            for state in states:
                lock_key = self.redis_states_hset_key + ":__lock__:{}".format(state)
                locks.append(self.__r.lock(lock_key, timeout=5))
                locks[-1].acquire()
            self.redis_states_dict.delete(self.redis_states_hset_key, states)
            for lock in locks:
                lock.release()
        except redis.RedisError as re:
            logger.exception(re)

    def total_games_finished(self):
        try:
            with self.__r.lock(self.redis_desks_hset_key + ":__lock__:{}".format(self.desk_size), timeout=5):
                return self.redis_desks_dict[self.desk_size]
        except redis.RedisError as re:
            logger.exception(re)

    def save(self):
        raise NotImplementedError()

    def load(self):
        try:
            with self.__r.lock(self.redis_desks_hset_key + ":__lock__:{}".format(self.desk_size), timeout=5):
                games_finished = self.redis_desks_dict.get(self.desk_size, None)
            if games_finished is None:
                self.inc_total_games_finished(0)
            logger.info("Redis DB contains Data for: {} total games played for training".format(self.redis_desks_dict[self.desk_size]))
            logger.info("Redis DB contains Data for: {} total states".format(len(self.redis_states_dict)))
        except redis.RedisError as re:
            logger.exception(re)

    def has_state(self, state):
        try:
            with self.__r.lock(self.redis_states_hset_key + ":__lock__:{}".format(state), timeout=5):
                return state in self.redis_states_dict
        except redis.RedisError as re:
            logger.exception(re)

    def add_train_states(self, states, possible_moves):
        try:
            locks = []
            states_to_add = []
            moves_to_add = []
            states_to_update = []
            moves_to_update = []
            for state in states:
                locks.append(self.__r.lock(self.redis_states_hset_key + ":__lock__:{}".format(state), timeout=5))
                locks[-1].acquire()
            for i, state in enumerate(states):
                if state not in self.redis_states_dict:
                    states_to_add.append(state)
                    moves_to_add.append(possible_moves[i])
                else:
                    states_to_update.append(state)
                    moves_to_update.append(possible_moves[i])
            if states_to_update != []:
                self.__r.hmset(self.redis_states_hset_key, {str(state): str(moves) for (state, moves) in zip(states_to_add, moves_to_add)})
            for lock in locks:
                lock.release()
            if states_to_update != []:
                self.update_train_state_moves(states_to_update, moves_to_update)
        except redis.RedisError as re:
            logger.exception(re)

    def find_train_state_possible_move_by_idx(self, state, move_idx):
        raise NotImplementedError()

    def inc_total_games_finished(self, count):
        try:
            with self.__r.lock(self.redis_desks_hset_key + ":__lock__:{}".format(self.desk_size), timeout=5):
                current_total = self.redis_desks_dict.get(self.desk_size, None)
                if current_total is not None:
                    current_total = int(current_total) + count
                else:
                    current_total = count
                self.redis_desks_dict[self.desk_size] = current_total
        except redis.RedisError as re:
            logger.exception(re)


    def update_train_state_moves(self, states, other_moves_list):
        try:
            locks = []
            for state in states:
                locks.append(self.__r.lock(self.redis_states_hset_key + ":__lock__:{}".format(state), timeout=5))
                locks[-1].acquire()
            all_moves_to_update_decoded = []
            for state in states:
                all_moves_to_update_decoded = self.__r.hmget(self.redis_states_hset_key, [str(state) for state in states])
                all_moves_to_update_decoded = [json.loads(moves) for moves in all_moves_to_update_decoded]
                for moves_to_update_decoded, other_moves in zip(all_moves_to_update_decoded, other_moves_list):
                    for i, this_move in enumerate(moves_to_update_decoded):
                        this_move[1] += other_moves[i][1]
                        this_move[2] += other_moves[i][2]
                        this_move[3] += other_moves[i][3]
            if all_moves_to_update_decoded != []:
                self.__r.hmset(self.redis_states_hset_key, {str(state): str(moves) for state, moves in zip(states, all_moves_to_update_decoded)})
            for lock in locks:
                lock.release()
        except redis.exceptions.LockNotOwnedError as e:
            logger.exception(e)
        except redis.RedisError as re:
            logger.exception(re)

    def get_train_state(self, state, raw=False):
        try:
            with self.__r.lock(self.redis_states_hset_key + ":__lock__:{}".format(state), timeout=5):
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
        vis = 5000
        if vis == 0 :
            vis = 2
        count = 0
        states = []
        other_moves = []
        for state in other.get_train_data():
            other_moves.append(other.get_train_state(state, True))
            states.append(state)
            if len(states) >= 20:
                self.add_train_states(states, other_moves)
                count += len(states)
                states = []
                other_moves = []
                if count % vis == 0:
                    logger.info("Updating Intermediate data to Redis complete@{}%".format(int((count / s) * 100)))
        if states != []:
            self.add_train_states(states, other_moves)
            count += len(states)
            if count % vis == 0:
                logger.info("Updating Intermediate data to Redis complete@{}%".format(int((count / s) * 100)))
        logger.info("Updating Intermediate data to Redis Done.")
        self.inc_total_games_finished(other.total_games_finished)

