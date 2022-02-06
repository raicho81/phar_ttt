import logging
import os
import json
import math
import sys
import redis
from pottery import RedisDict
from redis import RedisError

from dynaconf import settings
if len(sys.argv) > 1:
    settings.load_file(path=sys.argv[1])

from ttt_train_data_base import TTTTrainDataBase


logging.basicConfig(level = logging.INFO, filename = "TTTpid-{}.log".format(os.getpid()),
                    filemode = 'a+',
                    format='[%(asctime)s] pid: %(process)d - tid: %(thread)d - %(levelname)s - %(filename)s:%(lineno)s - %(funcName)s() - %(message)s')

logging.getLogger("pottery").setLevel("WARN")
logger = logging.getLogger(__name__)


class TTTTrainDataRedis(TTTTrainDataBase):
    def __init__(self, desk_size, host, port, password, redis_desks_hset_key, redis_states_hset_key_prefix, redis_stream_group, redis_stream_consumer_name):
        super().__init__()
        self.redis_desks_hset_key = redis_desks_hset_key
        self.redis_states_hset_key_prefix = redis_states_hset_key_prefix
        self.desk_size = desk_size
        self.redis_states_hset_key = "{}:size:{}".format(redis_states_hset_key_prefix, self.desk_size)
        self.redis_states_updates_zset_key = "{}:states_updates_zset".format(self.redis_states_hset_key)
        self.redis_states_updates_stream = "{}:stream".format(self.redis_states_hset_key)
        self.redis_states_updates_stream_group = redis_stream_group
        self.redis_stream_consumer_name = redis_stream_consumer_name
        self.redis_host = host
        self.redis_port = port
        self.__r = redis.Redis(host=host,
                                port=port,
                                password=password,
                                decode_responses=True)
        self.redis_desks_dict = RedisDict(redis=self.__r, key=self.redis_desks_hset_key)
        self.redis_states_dict = RedisDict(redis=self.__r, key=self.redis_states_hset_key)
        if settings.REDIS_MASTER:
            self.init_redis_stream_consumer_group()
            self.lastid = "0-0"
            self.check_backlog = True
        self.load()

    def claim_pending_stream_messages(self, count):
        try:
            claimed = self.__r.xautoclaim(self.redis_states_updates_stream, self.redis_states_updates_stream_group, self.redis_stream_consumer_name, 60*60*1000, 0, count, True)
            if claimed != []:
                logger.info("Claimed {} ID's to consumer: {}, stream: {}".format(claimed, self.redis_stream_consumer_name, self.redis_states_updates_stream))
        except RedisError as e:
            logger.exception(e)

    def init_redis_stream_consumer_group(self):
        try:
            groups = self.__r.xinfo_groups(self.redis_states_updates_stream)
            for gr in groups:
                if gr["name"] == self.redis_states_updates_stream_group:
                    return
        except RedisError as e:
            logger.exception(e)
        try:
            self.__r.xgroup_create(self.redis_states_updates_stream, self.redis_states_updates_stream_group, "0", True)
        except RedisError as e:
            logger.exception(e)

    def ack_stream_messages(self, msg_ids):
        try:
            self.__r.xack(self.redis_states_updates_stream, self.redis_states_updates_stream_group, *[str(msg_id) for msg_id in msg_ids])
        except RedisError as e:
            logger.exception(e)
            logger.info("stream, group, ID : {} {} {}".format(self.redis_states_updates_stream, self.redis_states_updates_stream_group, msg_ids))

    def publish_states_to_stream(self, states):
        if settings.REDIS_MASTER:
            raise RuntimeError("Only slaves can publish to Redis stream!")
        try:
            self.__r.xadd(self.redis_states_updates_stream, {"states_to_update": str(states)}, "*")
        except RedisError as e:
            logger.exception(e)

    def get_states_to_update_from_stream(self, timeout):
        stream_data = None
        if not settings.REDIS_MASTER:
            raise RuntimeError("Only master can read data from the Redis states updates stream!")
        try:
            if self.check_backlog:
                id = self.lastid
            else:
                id = '>'
            stream_data = self.__r.xreadgroup(self.redis_states_updates_stream_group, self.redis_stream_consumer_name, {self.redis_states_updates_stream: id}, 1, timeout*1000)
            if stream_data == [] or stream_data[0][1] == []:
                self.check_backlog = False
            else:
                (msg_id, msg) = stream_data[0][1][0]
                self.lastid = msg_id
        except RedisError as e:
            logger.exception(e)
        return stream_data

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
            self.__r.zrem(self.redis_states_updates_zset_key, *states)
            self.__r.hdel(self.redis_states_hset_key, *states)
            for lock in locks:
                lock.release()
        except redis.exceptions.LockNotOwnedError:
            pass
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
        logger.info("000 Redis connector loaded host: {} port: {} 000".format(self.redis_host, self.redis_port))
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
            if states_to_add != []:
                self.__r.hmset(self.redis_states_hset_key, {str(state): str(moves) for (state, moves) in zip(states_to_add, moves_to_add)})
                for state in states_to_add:
                    self.__r.zincrby(self.redis_states_updates_zset_key, str(1), state)
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
                for i in range(len(all_moves_to_update_decoded)):
                    try:
                        all_moves_to_update_decoded[i] = json.loads(all_moves_to_update_decoded[i])
                    except json.decoder.JSONDecodeError as jde:
                        logger.exception(jde)
                        logger.info("moves: {}".format(all_moves_to_update_decoded[i]))
                        logger.info("all_moves_to_update_decoded: {}".format(all_moves_to_update_decoded))
                        logger.info("other_moves_list: {}".format(other_moves_list))
                for moves_to_update_decoded, other_moves in zip(all_moves_to_update_decoded, other_moves_list):
                    if moves_to_update_decoded == 'None': # Error occured skip update for this moves as for some reason data in Redis is missing for them
                        moves_to_update_decoded = other_moves
                        continue
                    for i, this_move in enumerate(moves_to_update_decoded):
                        this_move[1] += other_moves[i][1]
                        this_move[2] += other_moves[i][2]
                        this_move[3] += other_moves[i][3]
            if all_moves_to_update_decoded != []:
                self.__r.hmset(self.redis_states_hset_key, {str(state): str(moves) for state, moves in zip(states, all_moves_to_update_decoded)})
                for state in states:
                    self.__r.zincrby(self.redis_states_updates_zset_key, str(1), state)
            for lock in locks:
                lock.release()
        except redis.exceptions.LockNotOwnedError as e:
            logger.exception(e)
        except redis.RedisError as re:
            logger.exception(re)
        except Exception as e:
            logger.exception(e)

    def get_train_state(self, state, raw=False):
        try:
            with self.__r.lock(self.redis_states_hset_key + ":__lock__:{}".format(state), timeout=5):
                return self.redis_states_dict.get(state if raw == True else self.int_none_tuple_hash(state), None)
        except redis.RedisError as re:
            logger.exception(re)

    def update_train_state(self, state, move):
        raise NotImplementedError()

    def get_train_data(self):
        return self.redis_states_dict

    def clear(self):
        self.redis_desks_dict.clear()
        self.redis_states_dict.clear()
        self.__r.delete(self.redis_states_updates_zset_key)

    def update(self, other):
        logger.info("Updating Intermediate data to Redis: 0% ...")
        s = len(other.get_train_data())
        vis = settings.REDIS_UPDATE_SKIP
        if vis == 0 :
            vis = 2
        count = 0
        states = []
        other_moves = []
        for state in other.get_train_data():
            other_moves.append(other.get_train_state(state, True))
            states.append(state)
            if len(states) >= settings.REDIS_KEYS_TO_UPDATE_AT_ONCE:
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
        while self.__r.zcount(self.redis_states_updates_zset_key, 2, math.inf) > 0:
            states_to_update_to_db = self.__r.zpopmax(self.redis_states_updates_zset_key, settings.REDIS_ZSET_EXTRACT_SIZE_FROM_SLAVE)
            states_to_update_to_db = [int(state) for (state , _) in states_to_update_to_db]
            self.publish_states_to_stream(str(states_to_update_to_db))
