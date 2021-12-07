import sys

from ttt_play_base import TTTPlayBase
from ttt_var_algo import VarAlgo


class TTTPlayHVsC(TTTPlayBase):
    
    def __init__(self, desk_size, train_data_filename):
        super().__init__(desk_size=desk_size, train=False, train_data_filename=train_data_filename)

    def do_human_move(self, next_player):
        while True:
            text = input("HUMAN (PLAYER1 >>> {} <<<) enter your choice [1... {}] it must be a valid move. 'q' to quit now. Enter your choice > ".format(self.player1_mark, self.desk.size ** 2))
            if text == "q":
                sys.exit(0)
            try:
                next_move_idx = int(text)
            except ValueError as e:
                print(e)
                continue
            if next_move_idx < 1 or next_move_idx > (self.desk.size ** 2):
                print(), print("Invalid move (invalid square index?): {}".format(next_move_idx)), print()
                continue
            possible_moves_indices = self.desk.get_possible_moves_indices()
            if (next_move_idx - 1) not in possible_moves_indices:
                print(), print("Invalid move (square is already taken?): {}".format(next_move_idx)), print()
                continue
            self.save_move(next_move_idx - 1, self.next_player)
            state = self.desk.get_state()
            return state, next_move_idx
            
    def run(self):
        print(), print("Starting new game Human (PLAYER1 - {}) VS Computer (PLAYER2 - {})".format(self.player1_mark, self.player2_mark)), print()
        self.print_desk(), print()
        while True:
            if self.next_player == TTTPlayBase.PLAYER2:
                self.do_computer_move(self.next_player)
            else:
                self.do_human_move(self.next_player)
            print("{} moves".format(TTTPlayBase.PLAYER_2_STRING[self.next_player])), print()
            self.print_desk(), print()
            game_state = VarAlgo.eval_game_state(self.desk)
            self.next_player = TTTPlayBase.PLAYER2 if self.next_player == TTTPlayBase.PLAYER1 else TTTPlayBase.PLAYER1
            if game_state in (VarAlgo.GAME_STATE_WIN_X, VarAlgo.GAME_STATE_WIN_O, VarAlgo.GAME_STATE_DRAW):
                print("Game Over!")
                (game_state == VarAlgo.GAME_STATE_WIN_X or game_state == VarAlgo.GAME_STATE_WIN_O) and \
                    print("{} Wins!".format(self.PLAYER_2_STRING[self.game_state_win_2_player(game_state)]))
                game_state == VarAlgo.GAME_STATE_DRAW and \
                    print("Game is a draw!")
                return
