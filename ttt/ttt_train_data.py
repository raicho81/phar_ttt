import pickle
import logging

from ttt_train_data_base import TTTTrainDataBase

logger = logging.getLogger(__name__)


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
            print(state)
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
