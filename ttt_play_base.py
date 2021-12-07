import random

from abc import ABCMeta

from dynaconf import settings

import ttt_train_data
import ttt_desk
from ttt_var_algo import VarAlgo


class TTTPlayBase(metaclass=ABCMeta):
    
    PLAYER1 = 1
    PLAYER2 = 2
    PLAYER_TYPE_COMPUTER = 1
    PLAYER_TYPE_HUMAN = 2
    PLAYER_2_STRING = {PLAYER1: "PLAYER1", PLAYER2: "PLAYER2"}
    DEFAULT_DESK_SIZE = 3

    def __init__(self, desk_size=DEFAULT_DESK_SIZE, train_data_filename=None, train=True, train_iterations=10000000):
        self.train = train
        self.train_iterations = train_iterations
        self.next_player = random.choice((TTTPlayBase.PLAYER1, TTTPlayBase.PLAYER2))
        if self.next_player == TTTPlayBase.PLAYER1:
            self.player1_mark = "x"
            self.player2_mark = "o"
        else:
            self.player1_mark = "o"
            self.player2_mark = "x"
        self.train_data_filename = train_data_filename
        self.train_data = ttt_train_data.TTTTrainData(self.train_data_filename)
        self.desk = ttt_desk.TTTDesk(size=desk_size)

    def run(self):
        pass
    
    def mark_to_player(self, mark):
        if mark == self.player1_mark:
            return TTTPlayBase.PLAYER1
        else:
            return TTTPlayBase.PLAYER2

    def print_desk(self):
        print()
        for row in self.desk.get_state():
            print(" ".join([square if square is not None else "_" for square in row]))
        print()

    def save_move(self, move_idx, player):
        self.desk.desk[move_idx // self.desk.size][move_idx % self.desk.size] = self.player1_mark if player == TTTPlayBase.PLAYER1 else self.player2_mark

    def do_computer_move(self, player):
        if self.train:
            next_move_idx = VarAlgo.choose_next_move_random_idx(self.desk)
        else:
            next_move_idx = VarAlgo.choose_next_best_move_idx(self.desk.get_state(), self.train_data)
        state = self.desk.get_state()
        has_state = self.train_data.has_state(state)
        if not has_state:
            # add state to training data if it is not there
            self.train_data.add_train_state(state, self.desk.get_possible_moves_indices())
        self.save_move(next_move_idx, player)
        return state, next_move_idx
    
    def game_state_win_2_player(self, game_state):
        if game_state == VarAlgo.GAME_STATE_WIN_X:
            if self.player1_mark == "x":
                return TTTPlayBase.PLAYER1
            else:
                return TTTPlayBase.PLAYER2
        if game_state == VarAlgo.GAME_STATE_WIN_O:
            if self.player1_mark == "o":
                return TTTPlayBase.PLAYER1
            else:
                return TTTPlayBase.PLAYER2
        raise ValueError("Invalid winning game state value!")

    def update_stats(self, game_state, player_1_path, player_2_path):
        self.train_data.total_games_finished += 1
        if game_state == VarAlgo.GAME_STATE_DRAW:
            self.update_path_draw(player_1_path)
            self.update_path_draw(player_2_path)
            return
        if game_state in [VarAlgo.GAME_STATE_WIN_X, VarAlgo.GAME_STATE_WIN_O]:
            win_player = self.game_state_win_2_player(game_state)
            self.update_path_win(player_1_path if win_player == TTTPlayBase.PLAYER1 else player_2_path)
            self.update_path_loose(player_2_path if win_player == TTTPlayBase.PLAYER1 else player_1_path)

    def update_path_win(self, path):
        for state, move_idx in path:
            move = self.train_data.find_train_state_possible_move_by_idx(state, move_idx)
            move.n_wins += 1

    def update_path_draw(self, path):
        for state, move_idx in path:
            move = self.train_data.find_train_state_possible_move_by_idx(state, move_idx)
            move.n_draws += 1

    def update_path_loose(self, path):
        for state, move_idx in path:
            move = self.train_data.find_train_state_possible_move_by_idx(state, move_idx)
            move.n_looses += 1
