from copy import Error
import pickle
import os
import functools
import logging
from types import TracebackType

from dynaconf import settings
import psycopg2
import psycopg2.pool
import psycopg2.extras
import psycopg2.extensions

import ttt_dependency_injection
import ttt_data_encoder



logging.basicConfig(level = logging.INFO, filename = "TTTpid-{}.log".format(os.getpid()),
                    filemode = 'a+',
                    format='[%(asctime)s] pid: %(process)d - tid: %(thread)d - %(levelname)s - %(filename)s:%(lineno)s - %(funcName)s() - %(message)s')
logger = logging.getLogger(__name__)


class TTTTrainDataMove:
    def __init__(self, move_idx, n_wins=0, n_draws=0, n_looses=0):
        self.move_idx = move_idx
        self.n_wins = n_wins
        self.n_draws = n_draws
        self.n_looses = n_looses

    def __iadd__(self, other):
        if self.move_idx != other.move_id:
            raise ValueError("Move index values do not match!")
        self.n_wins += other.n_wins
        self.n_draws += other.n_draws
        self.n_looses += other.n_looses
        return self


    def __add__(self, other):
        if self.move_idx != other.move_id:
            raise ValueError("Move index values do not match!")
        new_obj = TTTTrainDataMove(
            self.move_idx,
            self.n_wins + other.n_wins,
            self.n_draws + other.n_draws,
            self.n_looses + other.n_looses
        )
        return new_obj

class TTTTrainDataBase:
    @ttt_dependency_injection.DependencyInjection.inject
    def __init__(self, filename=None, * , data_encoder=ttt_dependency_injection.Dependency(ttt_data_encoder.TTTDataEncoder)):
        self.filename = filename
        self.enc = data_encoder

    def possible_moves_indices(self, state):
        possible_moves_indices = []
        for x in range(len(state)):
            for y in range(len(state)):
                if state[y][x] is None:
                    possible_moves_indices.append(x + y * len(state))
        return possible_moves_indices

    def binary_search(self, state_possible_moves, low, high, x):
        if high >= low:
            mid = (high + low) // 2
            move = state_possible_moves[mid]
            if move[0] == x:
                return move
            elif move[0] > x:
                return self.binary_search(state_possible_moves, low, mid - 1, x)
            else:
                return self.binary_search(state_possible_moves, mid + 1, high, x)
        else:
            raise ValueError("Move index not found!")

    @functools.lru_cache(4096)
    def int_none_tuple_hash(self, t, hash_base=3):
        tuple_hash = 0
        power = 0
        for i in range(len(t)):
            for j in range(len(t[i])):
                update = (hash_base ** power) * (t[i][j] if t[i][j] is not None else 0)
                tuple_hash += update
                power += 1
        return tuple_hash

    @property
    def cache_info(self):
        return self.int_none_tuple_hash.cache_info()

    def save(self):
        pass

    def load(self):
        pass

    def get_total_games_finished(self):
        pass

    def has_state(self, state):
        pass

    def add_train_state(self, state, possible_moves_indices, raw=False):
        pass

    def find_train_state_possible_move_by_idx(self, state, move_idx):
        pass

    def inc_total_games_finished(self, count):
        pass

    def get_train_state(self, state, raw=False):
        pass

    def update_train_state(self, state, move):
        pass

    def get_train_data(self):
        pass

    def update(self, other):
        pass

    def clear(self):
        self.int_none_tuple_hash.cache_clear()


class TTTTrainData(TTTTrainDataBase):
    def __init__(self):
        super().__init__()
        self.total_games_finished = 0
        self.train_data = {}

    def get_total_games_finished(self):
       return self.total_games_finished

    def save(self):
        logger.info("Saving training data to: {}".format(self.filename))
        with open(self.filename, "wb") as f:
            pickle.dump((self.total_games_finished, self.train_data), f)

    def load(self):
        if self.filename is None:
            logger.info("No file with training data supplied.")
            return
        try:
            with open(self.filename, "rb") as f:
                logger.info("Loading data from {}".format(self.filename))
                self.total_games_finished, self.train_data = pickle.load(f)
                logger.info("Loaded training data from {} for {} training games. Training data dict contains {} diferent training states.".format(
                    self.filename, self.total_games_finished,
                    len(self.train_data)))
        except FileNotFoundError as e:
            logger.exception(e)

    def has_state(self, state):
        return self.int_none_tuple_hash(state) in self.train_data.keys()

    def add_train_state(self, state, possible_moves_indices, raw=False):
        self.train_data[self.int_none_tuple_hash(state) if not raw else state] = self.enc.encode(possible_moves_indices)

    def find_train_state_possible_move_by_idx(self, state, move_idx):
        state_possible_moves = self.get_train_state(state)
        if state_possible_moves is None:
            self.add_train_state(state,  [[move_idx, 0, 0, 0] for move_idx in sorted(self.possible_moves_indices(state))])
            state_possible_moves = self.get_train_state(state)
        return self.binary_search(state_possible_moves, 0, len(state_possible_moves) - 1, move_idx)

    def inc_total_games_finished(self, count):
        self.total_games_finished += count

    def get_train_state(self, state, raw=False):
        state_possible_moves = self.train_data.get(self.int_none_tuple_hash(state) if not raw else state, None)
        if state_possible_moves is not None:
            decoded_moves = self.enc.decode(state_possible_moves)
            return decoded_moves
        else:
            return None

    def update_train_state(self, state, move):
        pms = self.get_train_state(state)
        found_m = self.binary_search(pms, 0, len(pms) -1 , move[0])
        found_m[1] = move[1]
        found_m[2] = move[2]
        found_m[3] = move[3]

        self.train_data[self.int_none_tuple_hash(state)] = self.enc.encode(pms)

    def get_train_data(self):
        return self.train_data

    def update(self, other):
        self.inc_total_games_finished(other.total_games_finished)
        for state in other.get_train_data().keys():
            other_moves = other.get_train_state(state, True)
            this_moves = self.get_train_state(state, True)
            if this_moves is not None:
                for i, this_move in enumerate(this_moves):
                    this_move[1] += other_moves[i][1]
                    this_move[2] += other_moves[i][2]
                    this_move[3] += other_moves[i][3]
                self.train_data[state] = self.enc.encode(this_moves)
            else:
                self.add_train_state(state, other_moves, True)

    def clear(self):
        # super().clear()
        self.total_games_finished = 0
        self.train_data = {}

class TTTTrainDataPostgres(TTTTrainDataBase):
    def __init__(self, desk_size, postgres_pool):
        super().__init__()
        self.postgres_pool = postgres_pool
        try:
            conn = self.get_conn_from_pg_pool()
            try:
                with conn.cursor() as c:
                    c.execute(
                                    """
                                        SELECT id
                                        FROM "Desks"
                                        WHERE size = %s
                                    """,
                                    (desk_size, )
                    )
                    rec = c.fetchone()
                    if rec is None:
                        c.execute(
                                    """
                                        INSERT INTO
                                            "Desks" (size)
                                        VALUES (%s)
                                        ON CONFLICT(size) DO NOTHING
                                        RETURNING id
                                    """,
                                    (desk_size, )
                        )
                        rec = c.fetchone()
                    self.desk_db_id = rec["id"]
                    if self.desk_db_id is None:
                        c.execute(
                                        """
                                            SELECT id
                                            FROM "Desks"
                                            WHERE size = %s
                                        """,
                                        (desk_size, )
                        )
                        rec = c.fetchone()
                        self.desk_db_id = rec["id"]
            finally:
                self.postgres_pool.putconn(conn)
        except psycopg2.DatabaseError as error:
            logger.exception(error)
        self.load()

    def get_conn_from_pg_pool(self):
        conn = self.postgres_pool.getconn()
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        conn.cursor_factory = psycopg2.extras.DictCursor
        return conn

    @property
    def desk_id(self):
        return self.desk_db_id

    def total_games_finished(self):
        try:
            try:
                conn = self.get_conn_from_pg_pool()
                with conn.cursor() as c:
                    c.execute(
                                    """
                                        SELECT total_games_played
                                        FROM "Desks"
                                        WHERE id=%s
                                    """,
                                    (self.desk_id, )
                )
                    row = c.fetchone()
            finally:
                self.postgres_pool.putconn(conn)
        except psycopg2.DatabaseError as error:
            logger.exception(error)
        return row["total_games_played"]

    def save(self):
        print("TTTTrainDataPostgres:save")

    def load(self):
        try:
            conn = self.get_conn_from_pg_pool()
            try:
                with conn.cursor() as c:
                    c.execute(
                                    """
                                        SELECT total_games_played
                                        FROM "Desks"
                                        WHERE id=%s
                                    """,
                                    (self.desk_id, )
                    )
                    res = c.fetchone()
                    logger.info("DB contains Data for: {} total games palyed for training".format(res["total_games_played"]))
                    c.execute(
                                        """
                                            SELECT count(*) FROM "States"
                                            WHERE desk_id=%s
                                        """,
                                        (self.desk_id, )
                    )
                    res = c.fetchone()
                    logger.info("DB contains Data for: {} total states".format(res[0]))
            finally:
                self.postgres_pool.putconn(conn)
        except psycopg2.DatabaseError as error:
            logger.exception(error)

    @functools.lru_cache(maxsize=10*10**6)
    def has_state(self, state):
        try:
            conn = self.get_conn_from_pg_pool()
            try:
                with conn.cursor() as c:
                    c.callproc("has_state", (self.desk_id, state))
                    res = c.fetchone()
                    return res[0]
            finally:
                self.postgres_pool.putconn(conn)
        except psycopg2.DatabaseError as error:
            logger.exception(error)

    def add_train_state(self, state, possible_moves):
        try:
            conn = self.get_conn_from_pg_pool()
            try:
                with conn.cursor() as c:
                    c.execute("CALL add_state_moves(%s, %s, %s)", (self.desk_id, state, psycopg2.Binary(self.enc.encode(possible_moves))))
            finally:
                self.postgres_pool.putconn(conn)
        except psycopg2.DatabaseError as error:
            logger.exception(error)

    def find_train_state_possible_move_by_idx(self, state, move_idx):
        raise NotImplementedError()

    def inc_total_games_finished(self, count):
        try:
            conn = self.get_conn_from_pg_pool()
            try:
                with conn.cursor() as c:
                    c.execute(
                                    """
                                        UPDATE "Desks"
                                        SET
                                            total_games_played = total_games_played + %s
                                        WHERE id = %s
                                    """,
                                    (count, self.desk_id)
                    )
            finally:
                self.postgres_pool.putconn(conn)
        except psycopg2.DatabaseError as error:
            logger.exception(error)


    def update_train_state_moves(self, state, moves):
        try:
            conn = self.get_conn_from_pg_pool()
            try:
                with conn.cursor() as c:
                    c.execute("CALL update_state_moves_v2(%s, %s, %s)", (self.desk_id, state, psycopg2.Binary(self.enc.encode(moves))))
            finally:
                self.postgres_pool.putconn(conn)
        except psycopg2.DatabaseError as error:
            logger.exception(error)

    def get_train_state(self, state, raw=False):
        try:
            conn = self.get_conn_from_pg_pool()
            try:
                with conn.cursor() as c:
                    c.callproc("get_desk_state_moves", (self.desk_id, state if raw == True else self.int_none_tuple_hash(state)))
                    rec = c.fetchone()
                    if rec is not None:
                        state_insert_id, moves_decoded = rec["state_insert_id"], self.enc.decode(rec["moves"])
                        return state_insert_id, moves_decoded
                    return None, None
            finally:
                self.postgres_pool.putconn(conn)
        except psycopg2.DatabaseError as error:
            logger.exception(error)
        except Error as error:
            logger.exception(error)

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
        for state in other.get_train_data().keys():
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
