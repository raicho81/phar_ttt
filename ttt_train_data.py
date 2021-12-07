import pickle

from ttt_move import TTTMoveTrainData


class TTTTrainData:

    def __init__(self, filename=None):
        self.filename = filename
        self.total_games_finished = 0
        self.train_data = {}
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
        if state in self.train_data.keys():
            return True
        return False

    def add_train_state(self, state, possible_moves_indices):
        self.train_data[state] = [TTTMoveTrainData(move_idx) for move_idx in possible_moves_indices]

    def get_train_state_possible_moves(self, state):
        possible_moves = self.train_data.get(state, None)
        if possible_moves is None:
            raise ValueError("Train state {} not present in training data!".format(state))
        return possible_moves

    def find_train_state_possible_move_by_idx(self, state, move_idx):
        state_possible_moves = self.get_train_state_possible_moves(state)
        if state_possible_moves is not None:
            for move in state_possible_moves:
                if move.move_idx == move_idx:
                    return move
            raise IndexError("Unknown train state possoble move index!")

    def get_train_data(self):
        return self.train_data
