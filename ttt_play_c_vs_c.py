from ttt_play_base import TTTPlayBase, settings
from ttt_var_algo import VarAlgo


class TTTPlayCVsC(TTTPlayBase):
    
    def __init__(self, desk_size, train, train_data_filename, train_iterations=10000000, n_iter_info_skip=100):
        self.n_iter_info_skip = n_iter_info_skip
        super().__init__(desk_size=desk_size, train=train, train_data_filename=train_data_filename, train_iterations=train_iterations)

    def run(self):
        player_1_path = []
        player_2_path = []
        n_iterations = 0
        while n_iterations < self.train_iterations:
            self.train or (print(), print("Starting new game Computer VS Computer"))
            while True:
                path_node = self.do_computer_move(self.next_player)
                if not self.train:
                    print("{} moves".format(TTTPlayBase.PLAYER_2_STRING[self.next_player]))
                    self.print_desk()
                    print()
                if self.next_player == TTTPlayBase.PLAYER1:
                    player_1_path.append(path_node)
                else:
                    player_2_path.append(path_node)
                game_state = VarAlgo.eval_game_state(self.desk)
                self.next_player = TTTPlayBase.PLAYER2 if self.next_player == TTTPlayBase.PLAYER1 else TTTPlayBase.PLAYER1
                if game_state in (VarAlgo.GAME_STATE_WIN_X, VarAlgo.GAME_STATE_WIN_O, VarAlgo.GAME_STATE_DRAW):
                    
                    if self.train:
                        self.update_stats(game_state, player_1_path, player_2_path)
                    else:
                        print("Game Over!")
                        (game_state == VarAlgo.GAME_STATE_WIN_X or game_state == VarAlgo.GAME_STATE_WIN_O) and \
                            print("{} Wins!".format(self.PLAYER_2_STRING[self.game_state_win_2_player(game_state)]))
                        game_state == VarAlgo.GAME_STATE_DRAW and \
                            print("Game is a draw!")
                    self.desk.clear()
                    player_1_path = []
                    player_2_path = []
                    break
            n_iterations += 1
            self.train and n_iterations % self.n_iter_info_skip == 0 and (print("Training iteration {} finished. More {} to go :D".format(n_iterations, self.train_iterations - n_iterations)))
        print("Done {} with {} iterations.".format("training" if self.train else "playing Computer VS Computer ", self.train_iterations))
        self.train_data.save()
