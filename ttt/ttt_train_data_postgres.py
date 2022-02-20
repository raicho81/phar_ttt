import logging
import os
import sys
import json

from dynaconf import settings
if len(sys.argv) > 1:
    settings.load_file(path=sys.argv[1])

import django.utils.timezone

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
        logger.info("PGC Postgres Connector Loaded PGC")
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
                row.total_games_played += count
                row.save()
        except DatabaseError as e:
            logger.exception(e)

    def update_train_states_moves(self, states_moves):
        try:
            with transaction.atomic():
                bulk_update = []
                for state, moves in states_moves:
                    try:
                        res, created = models.States.objects.get_or_create(desk_id=self.desk_db_id, state=state, defaults={"moves": self.enc.encode(moves)})
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
        st = models.States.objects.get(desk_id=self.desk_db_id, state=str(state) if raw else str(self.int_none_tuple_hash(state)))
        return st.id, self.enc.decode(st.moves)

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
            self.update_train_states_moves([[state, other_moves]])
            count += 1
            if count % vis == 0:
                logger.info("Updating Intermediate data to DB is complete@{}%".format(int((count / s) * 100)))
        logger.info("Updating Intermediate data to DB Done.")
        self.inc_total_games_finished(other.total_games_finished)
 
    def load_game(self, game_uuid, player_id):
        qs = models.Games.objects.filter(game_uuid=game_uuid, player_id=player_id)
        return qs[0] if len(qs) > 0 else None
    
    def save_game(self, desk, game_uuid, game_state, player_id, player_code, player_mark, next_player, player1_path, player2_path):
        models.Games.objects.update_or_create(game_uuid=game_uuid, desk=self.enc.encode(desk), game_state=game_state,
                                              player_id=player_id, player_code=player_code, next_player_code=next_player, player_mark=player_mark, modified=django.utils.timezone.now(),
                                              player1_path=self.enc.encode(player1_path), player2_path=self.enc.encode(player2_path))
    
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
            try:
                with transaction.atomic():           
                    self.inc_total_games_finished(-self.total_games_finished())
                    self.inc_total_games_finished(training_data_shared_redis.total_games_finished())
            except DatabaseError as e:
                logger.exception(e)
        logger.info("Updating Intermediate Redis data to DB Done.")
