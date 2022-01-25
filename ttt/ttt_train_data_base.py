import functools

import ttt_dependency_injection
import ttt_data_encoder


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
        # tuple_hash = hash(t)
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
