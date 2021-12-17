import pickle
import os

import logging
logging.basicConfig(level = logging.INFO, filename = "TTTpid-{}.log".format(os.getpid()), filemode = 'w', format='[%(asctime)s] pid: %(process)d - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TTTTrainDataMove:
    def __init__(self, move_idx, n_wins=0, n_draws=0, n_looses=0):
        self.move_idx = move_idx
        self.n_wins = n_wins
        self.n_draws = n_draws
        self.n_looses = n_looses

    def __add__(self, other):
        if self.move_idx != other.move_id:
            raise ValueError("Move index values do not match!")
        self.n_wins += other.n_wins
        self.n_draws += other.n_draws
        self.n_looses += other.n_looses

class TTTTrainData:

    def __init__(self, data_encoder, filename=None):
        self.filename = filename
        self.total_games_finished = 0
        self.train_data = {}
        self.enc = data_encoder

    def get_total_games_finished(self):
        return self.total_games_finished

    def save(self):
        logging.info("Saving training data to: {}".format(self.filename))
        with open(self.filename, "wb") as f:
            pickle.dump((self.total_games_finished, self.train_data), f)

    def load(self):
        try:
            with open(self.filename, "rb") as f:
                logger.info("Loading data from {}".format(self.filename))
                self.total_games_finished, self.train_data = pickle.load(f)
        except FileNotFoundError as e:
            logging.info(e)

    def has_state(self, state):
        return self.enc.encode(state) in self.train_data.keys()

    def add_train_state(self, state, possible_moves_indices, raw=False):
        self.train_data[self.enc.encode(state) if not raw else state] = self.enc.encode(possible_moves_indices)

    def possible_moves_indices(self, state):
        possible_moves_indices = []
        for x in range(len(state)):
            for y in range(len(state)):
                if state[y][x] is None:
                    possible_moves_indices.append(x + y * len(state))
        return possible_moves_indices

    def find_train_state_possible_move_by_idx(self, state, move_idx):
        tmp_state = self.get_train_state(self.enc.encode(state))
        if tmp_state is None:
            self.add_train_state(state,  [[move_idx, 0, 0, 0] for move_idx in sorted(self.possible_moves_indices(state))])
            tmp_state = self.train_data[self.enc.encode(state)]
        state_possible_moves = self.enc.decode(tmp_state)
        return self.binary_search(state_possible_moves, 0, len(state_possible_moves) - 1, move_idx)

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

    def inc_total_games_finished(self, count):
        self.total_games_finished += count

    def get_train_state(self, state, raw=False):
        state_possible_moves = self.train_data.get(self.enc.encode(state) if not raw else state, None)
        if state_possible_moves is not None:
            return self.enc.decode(state_possible_moves)
        else:
            return None

    def update_train_state(self, state, move):
        pms = self.get_train_state(state)
        for i, m in enumerate(pms):
            if m[0] == move[0]:
                pms[i] = move
                self.train_data[self.enc.encode(state)] = self.enc.encode(pms)
                break
            
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
        self.total_games_finished = 0
        self.train_data = {}
