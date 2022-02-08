from email.policy import default
import logging
import os, sys
import json

from dynaconf import settings
if len(sys.argv) > 1:
    settings.load_file(path=sys.argv[1])

from ttt_train_data_base import TTTTrainDataBase
import ttt_train_data_redis

logging.basicConfig(level = logging.INFO, filename = "TTTpid-{}.log".format(os.getpid()),
                    filemode = 'a+',
                    format='[%(asctime)s] pid: %(process)d - tid: %(thread)d - %(levelname)s - %(filename)s:%(lineno)s - %(funcName)s() - %(message)s')
logger = logging.getLogger(__name__)

from django import db
from django.db import transaction, DatabaseError
from db import models

class TTTTrainDataPostgres(TTTTrainDataBase):
    def __init__(self, desk_size):
        super().__init__()
        self.desk_size = desk_size
        db.connections.close_all()
        res, created = models.Desks.objects.get_or_create(size=desk_size, defaults={"size": desk_size, "total_games_played": 0})
        self.desk_db_id = res.id
        logger.info("111 Postgres Connector Loaded !!!")
        # self.load()

    @property
    def desk_id(self):
        return self.desk_db_id

    def total_games_finished(self):
        row = models.Desks.objects.get(id=self.desk_db_id)
        return row.total_games_played

    def save(self):
        print("TTTTrainDataPostgres:save")

    def load(self):
        res = models.Desks.objects.get(id=self.desk_db_id)      
        logger.info("DB contains Data for: {} total games palyed for training".format(res.total_games_played))
        count = models.States.objects.filter(desk_id=self.desk_db_id).count()
        logger.info("DB contains Data for: {} total states".format(count))

    def has_state(self, state):
        return models.States.objects.filter(state=state).exists()

    def find_train_state_possible_move_by_idx(self, state, move_idx):
        raise NotImplementedError()

    def inc_total_games_finished(self, count):
        try:
            with transaction.atomic():
                row = models.Desks.objects.get(id=self.desk_db_id)
                row.total_games_finished += count
                row.save()
        except DatabaseError as e:
            logger.exception(e)

    def update_train_states_moves(self, states_moves):
        try:
            with transaction.atomic():
                desk = models.Desks.objects.get(id=self.desk_db_id)
                bulk_update = []
                for state, moves in states_moves:
                    try:
                        res, created = models.States.objects.get_or_create(desk_id=desk, state=state, defaults={"moves": self.enc.encode(moves)})
                        if not created:
                            curr_moves_decoded = self.enc.decode(res.moves)
                            if curr_moves_decoded is not None:
                                for curr_move, move in zip(curr_moves_decoded, moves):
                                    if move[1] > 0 or move[2] > 0 or move[3] > 0:
                                        curr_move[1] += move[1]
                                        curr_move[2] += move[2]
                                        curr_move[3] += move[3]    
                                        res.moves = self.enc.encode(curr_moves_decoded)
                                        bulk_update.append(res)
                    except TypeError as e:
                        logger.exception(e)
                if bulk_update != []:
                    models.States.objects.bulk_update(bulk_update, ['moves'], batch_size=settings.POSTGRES_ADD_TRAIN_STATES_BATCH_SIZE)
        except DatabaseError as error:
            logger.exception(error)

    def get_train_state(self, state, raw=False):
        raise NotImplementedError()

    def update_train_state(self, state, move):
        raise NotImplementedError()

    def get_train_data(self):
        raise NotImplementedError()

    def cache_info(self):
        return "has_state.cache_info[hit_rate: {} %, hits: {}, misses: {}, currsize: {}, maxsize: {}]".format(
            self.has_state.cache_info().hits * 100 / (self.has_state.cache_info().hits + self.has_state.cache_info().misses),
            self.has_state.cache_info().hits,
            self.has_state.cache_info().misses,
            self.has_state.cache_info().currsize,
            self.has_state.cache_info().maxsize)

    def update(self, other):
        logger.info("Updating Intermediate data to DB: 0% ...")
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
                logger.info("Updating Intermediate data to DB is complete@{}%".format(int((count / s) * 100)))
        logger.info("Updating Intermediate data to DB Done.")
        self.inc_total_games_finished(other.total_games_finished)

    def update_from_redis(self, msg_data):
        training_data_shared_redis = ttt_train_data_redis.TTTTrainDataRedis(self.desk_size, settings.REDIS_HOST, settings.REDIS_PORT, settings.REDIS_PASS, settings.REDIS_DESKS_HSET_KEY,
                                                                            settings.REDIS_STATES_HSET_KEY_PREFIX, settings.REDIS_CONSUMER_GROUP_NAME, settings.REDIS_CONSUMER_NAME)
        for msg_id, states in msg_data:
            states_moves_to_upd = []
            s = len(states)
            vis = s // 10
            if vis == 0 :
                vis = 2
            logger.info("Updating Intermediate Redis data to DB: 0% ... (Redis data chunk size: {}, stream msg ID: {})".format(s, msg_id))
            count = 0
            for state in states:
                try:
                    moves = json.loads(training_data_shared_redis.get_train_state(state, raw=True))
                    states_moves_to_upd.append([state, moves])
                except TypeError as e:
                    logger.exception(e)
                if len(states_moves_to_upd) >= settings.POSTGRES_ADD_TRAIN_STATES_BATCH_SIZE or state == states[-1]:
                    self.update_train_states_moves(states_moves_to_upd)
                    count += len(states_moves_to_upd)
                    states_moves_to_upd = []
                    if count > 0 and count % vis == 0:
                        logger.info("Updating Intermediate Redis data to DB is complete@{}%.".format(int((count * 100 / s))))
            training_data_shared_redis.remove_states_from_cache(states)
            training_data_shared_redis.ack_stream_messages([msg_id])
            self.inc_total_games_finished(-self.total_games_finished())
            self.inc_total_games_finished(training_data_shared_redis.total_games_finished())
        logger.info("Updating Intermediate Redis data to DB Done.")
