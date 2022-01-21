import logging
import os
import functools
from threading import Semaphore

import psycopg2
import psycopg2.pool
import psycopg2.extras
import psycopg2.extensions

from ttt_train_data_base import TTTTrainDataBase


logging.basicConfig(level = logging.INFO, filename = "TTTpid-{}.log".format(os.getpid()),
                    filemode = 'a+',
                    format='[%(asctime)s] pid: %(process)d - tid: %(thread)d - %(levelname)s - %(filename)s:%(lineno)s - %(funcName)s() - %(message)s')
logger = logging.getLogger(__name__)


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
        except Exception as error:
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

    def update_from_redis(self, d):
        logger.info("Updating Intermediate Redis data to DB: 0% ...")
        s = len(d)
        vis = s // 10
        if vis == 0 :
            vis = 2
        count = 0
        for state in d:
            other_moves = d[state]
            if self.has_state(state):
                self.update_train_state_moves(state, other_moves)
            else:
                self.add_train_state(state, other_moves)
            count += 1
            if count % vis == 0:
                logger.info("Updating Intermediate Redis data to DB is complete@{}%".format(int((count / s) * 100)))
        logger.info("Updating Intermediate Redis data to DB Done.")
