import pickle


class TTTTrainDataMove:
    def __init__(self, move_idx, n_wins=0, n_draws=0, n_looses=0):
        self.move_idx = move_idx
        self.n_wins = n_wins
        self.n_draws = n_draws
        self.n_looses = n_looses


class TTTTrainData:

    def __init__(self, data_encoder, filename=None):
        self.filename = filename
        self.total_games_finished = 0
        self.train_data = {}
        self.enc = data_encoder
        if self.filename is not None:
            self.load()

    def save(self):
        print("Saving training data to: {}".format(self.filename))
        with open(self.filename, "wb+") as f:
            pickle.dump((self.total_games_finished, self.train_data), f)

    def load(self):
        print("Loading training data from: {}".format(self.filename))
        try:
            with open(self.filename, "rb") as f:
                self.total_games_finished, self.train_data = pickle.load(f)
        except FileNotFoundError as e:
            print(e)

    def has_state(self, state):
        return self.enc.encode(state) in self.train_data.keys()

    def add_train_state(self, state, possible_moves_indices):
        self.train_data[self.enc.encode(state)] = self.enc.encode([[move_idx, 0, 0, 0] for move_idx in sorted(possible_moves_indices)])

    def find_train_state_possible_move_by_idx(self, state, move_idx):
        state_possible_moves = self.enc.decode(self.train_data[self.enc.encode(state)])
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

    def get_train_state(self, state):
        state_possible_moves = self.train_data.get(self.enc.encode(state), None)
        if state_possible_moves is not None:
            return self.enc.decode(state_possible_moves)
        else:
            return None
