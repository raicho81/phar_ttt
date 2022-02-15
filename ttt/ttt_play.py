import random
import sys
import itertools
import os
import logging

from dynaconf import settings
if len(sys.argv) > 1:
    settings.load_file(path=sys.argv[1])

import ttt_train_data
import ttt_desk
import ttt_player
import ttt_player_type
import ttt_player_mark
import ttt_game_state
import ttt_game_type


logging.basicConfig(level = logging.INFO, filename = "TTTpid-{}.log".format(os.getpid()),
                    filemode = 'a+',
                    format='[%(asctime)s] pid: %(process)d - tid: %(thread)d - %(levelname)s - %(filename)s:%(lineno)s - %(funcName)s() - %(message)s')
logger = logging.getLogger(__name__)


class TTTPlay():
    # @ttt_dependency_injection.DependencyInjection.inject
    def __init__(self, desk_size, training_data_shared, game_type, train=True, train_iterations=10000000, n_iter_info_skip=10000, game_uuid=None, player_id=None):
        self.game_type = game_type
        self.train = train
        self.train_iterations = train_iterations
        self.n_iter_info_skip = n_iter_info_skip
        self.train_data = ttt_train_data.TTTTrainData()
        self.training_data_shared = training_data_shared
        self.player_id = player_id
        self.game_uuid = game_uuid
        self.players = [ttt_player.TTTPlayer1(), ttt_player.TTTPlayer2()]
        self.player_types = self.init_player_types()
        self.player_mark = None
        if self.game_uuid is not None and self.player_id is not None:
            game = self.training_data_shared.load_game(self.game_uuid, self.player_id)
            if game != None:
                self.player_mark = game.player_mark
                self.player_code = game.player_code
                self.desk = ttt_desk.TTTDesk(size=desk_size, desk=self.enc.decode(game.desk))
                self.players[0].set_path(self.enc.decode(game.player1_path))
                self.players[1].set_path(self.enc.decode(game.player2_path))
                self.next_player = self.players[game.next_player - 1]
                if self.players[0].get_code() == game.player_code:
                    self.player_types = [ttt_player_type.TTTPlayerTypeHuman, ttt_player_type.TTTPlayerTypeComputer]
                    if self.player_marks[0].get_string() != self.player_mark:
                        m = self.marks[0]
                        self.marks[0] = self.marks[1]
                        self.marks[1] = m
                else:
                    if self.player_marks[1].get_string() != game.player_mark:
                        m = self.marks[0]
                        self.marks[0] = self.marks[1]
                        self.marks[1] = m

        else:
            self.desk = ttt_desk.TTTDesk(size=desk_size)
            self.marks = [ttt_player_mark.TTTPlayerMarkX, ttt_player_mark.TTTPlayerMarkO]
            self.player_code

    def init_player_types(self):
        if self.game_type is ttt_game_type.TTTGameTypeCVsC:
            player_types = [ttt_player_type.TTTPlayerTypeComputer] * 2
        else:
            player_types = [ttt_player_type.TTTPlayerTypeComputer, ttt_player_type.TTTPlayerTypeHuman]
        return player_types

    def init_players(self):
        random.shuffle(self.marks)
        if self.game_type is ttt_game_type.TTTGameTypeHVsC:
            random.shuffle(self.player_types)
        for player, mark, player_type in zip(self.players, self.marks, self.player_types):
            player.clear_path()
            player.set_mark(mark)
            player.set_type(player_type)

    def save_move(self, move_idx):
        self.desk.desk[move_idx // self.desk.size][move_idx % self.desk.size] = self.next_player

    def choose_next_move_random_idx(self):
        possible_moves_indices = self.desk.get_possible_moves_indices()
        if len(possible_moves_indices) == 1:
            return possible_moves_indices[0]
        else:
            return possible_moves_indices[random.randrange(0, len(possible_moves_indices))]

    def choose_next_best_move_idx(self):
        state = self.desk.get_state()
        _, possible_moves = self.training_data_shared.get_train_state(state)
        if possible_moves is None:
            possible_moves = [[move_idx, 0, 0, 0] for move_idx in sorted(self.desk.possible_moves_indices())]
            self.training_data_shared.add_train_state(self.training_data_shared.int_none_tuple_hash(state),
                                                      possible_moves
            )
        possible_moves_sorted_by_wins_rev = sorted(possible_moves, key=lambda m: m[1], reverse=True)
        for move in possible_moves_sorted_by_wins_rev:
            if move[1] > move[3]:
                return move[0]
        possible_moves_sorted_by_draws = sorted(possible_moves, key=lambda m: m[2], reverse=True)
        for move in possible_moves_sorted_by_draws:
            if move[2] > move[3]:
                return move[0]
        possible_moves_sorted_by_looses = sorted(possible_moves, key=lambda m: m[3])
        return possible_moves_sorted_by_looses[0][0]

    def choose_next_move_idx(self):
        if self.game_type is ttt_game_type.TTTGameTypeCVsC and self.train:
            next_move_idx = self.choose_next_move_random_idx()
        else:
            next_move_idx = self.choose_next_best_move_idx()
        return next_move_idx

    def do_computer_move(self):
        next_move_idx = self.choose_next_move_idx()
        if self.train:
            state = self.desk.get_state()
            has_state = self.train_data.has_state(state)
            if not has_state:
                # add state to training data if it is not there
                self.train_data.add_train_state(state, [[move_idx, 0, 0, 0] for move_idx in sorted(self.desk.possible_moves_indices())])
            self.next_player.add_path_node(ttt_player.TTTPlayerPathNode(state, next_move_idx))
        self.save_move(next_move_idx)

    def do_human_move(self, next_move_idx):
        state = self.desk.get_state()
        self.next_player.add_path_node(ttt_player.TTTPlayerPathNode(state, next_move_idx - 1))
        self.save_move(next_move_idx - 1)
    
    def do_human_move_cli(self):
        while True:
            text = input("Human ({} - {}) enter your choice [1... {}] it must be a valid move. 'q' to quit now. Enter your choice > ".format(
                self.next_player.get_string(), self.next_player.get_mark().get_string(), self.desk.size ** 2))
            if text == "q":
                sys.exit(0)
            try:
                next_move_idx = int(text)
            except ValueError as e:
                logger.exception(e)
                continue
            if next_move_idx < 1 or next_move_idx > (self.desk.size ** 2):
                print("Invalid move (invalid square index?): {}".format(next_move_idx))
                continue
            possible_moves_indices = self.desk.get_possible_moves_indices()
            if (next_move_idx - 1) not in possible_moves_indices:
                print("Invalid move (square is already taken?): {}".format(next_move_idx))
                continue
            self.do_human_move(next_move_idx)
            return

    def update_stats(self, game_state, win_player=None):
        self.train_data.inc_total_games_finished(1)
        if game_state is ttt_game_state.TTTGameStateDraw:
            for player in self.players:
                self.update_path_draw(player.get_path())
        if game_state is ttt_game_state.TTTGameStateWin:
            self.update_path_win(win_player.get_path())
            for player in self.players:
                if player is not win_player:
                    self.update_path_loose(player.get_path())

    def update_path_win(self, path):
        for state, move_idx in path:
            move = self.train_data.find_train_state_possible_move_by_idx(state, move_idx)
            move[1] += 1
            self.train_data.update_train_state(state, move)

    def update_path_draw(self, path):
        for state, move_idx in path:
            move = self.train_data.find_train_state_possible_move_by_idx(state, move_idx)
            move[2] += 1
            self.train_data.update_train_state(state, move)

    def update_path_loose(self, path):
        for state, move_idx in path:
            move = self.train_data.find_train_state_possible_move_by_idx(state, move_idx)
            move[3] += 1
            self.train_data.update_train_state(state, move)
    
    def init_game(self):
        # logger.info("TTTPlay re-seed the RNG")
        random.seed()
        self.desk.clear()
        self.init_players()

    def get_desk_state(self):
        return self.desk.get_state()

    def get_players(self):
        return (player for player in self.players)
    
    def get_next_player(self):
        return self.next_player

    def get_player_mark(self):
        return self.player_mark

    def get_player_code(self):
        return self.player_code

    def start_game(self):
        if self.game_type is not ttt_game_type.TTTGameTypeHVsC:
            raise ValueError("Game type must be: {}".format(ttt_game_type.TTTGameTypeHVsC.get_string()))
        self.init_game()
        self.next_player = self.players[0]
        self.player_mark = self.player_marks[0].get_string()
        self.player_code = self.players[0].get_code()        
        if self.players[0].get_type() is ttt_player_type.TTTPlayerTypeComputer:
            self.player_mark = self.player_marks[1].get_string()
            self.player_code = self.players[1].get_code()
            self.do_computer_move()
            self.next_player = self.players[1]
        self.training_data_shared.save_game(self.get_desk_state(), self.game_uuid, ttt_game_state.TTTGameStateUnfinished, self.player_id, self.player_code,
                                            self.player_mark, self.next_player.get_code(), self.players[0].get_path(), self.players[1].get_path())
        return ttt_game_state.TTTGameStateUnfinished.get_code()

    def make_move_stochastic(self, move_idx):
        self.do_human_move(move_idx)
        game_state, win_player = self.desk.eval_game_state()
        if game_state is ttt_game_state.TTTGameStateWin or game_state is ttt_game_state.TTTGameStateDraw:
            if self.train:
                self.update_stats(game_state, win_player)
        elif self.next_player is self.players[0]:
            self.next_player = self.players[1]
        else:
            self.next_player = self.players[0]
        if game_state == ttt_game_state.TTTGameStateUnfinished:
            self.do_computer_move()
            game_state, win_player = self.desk.eval_game_state()
            if game_state in[ttt_game_state.TTTGameStateWin, ttt_game_state.TTTGameStateDraw]:
                if self.train:
                    self.update_stats(game_state, win_player)
                    self.training_data_shared.update(self.train_data)                    
            elif self.next_player is self.players[0]:
                self.next_player = self.players[1]
            else:
                self.next_player = self.players[0]
        self.training_data_shared.save_game(self.get_desk_state(), self.game_uuid, game_state, self.player_id, self.player_code,
                                            self.player_mark, self.next_player.get_code(), self.players[0].get_path(), self.players[1].get_path())
        return game_state, win_player
        
    
    def play_game_cli(self):
        self.init_game()
        if self.game_type is ttt_game_type.TTTGameTypeHVsC or not self.train:
            print("Starting new game {}".format(self.game_type.get_string()))
            self.desk.print_desk()
        for self.next_player in itertools.cycle(self.players):
            if self.next_player.get_type() is ttt_player_type.TTTPlayerTypeComputer:
                self.do_computer_move()
            else:
                self.do_human_move_cli()
            if self.game_type is ttt_game_type.TTTGameTypeHVsC or not self.train:
                print("{} - {} moves".format(self.next_player.get_string(), self.next_player.get_type().get_string()))
                self.desk.print_desk()
            game_state, win_player = self.desk.eval_game_state()
            if game_state is ttt_game_state.TTTGameStateWin or game_state is ttt_game_state.TTTGameStateDraw:
                if self.game_type is ttt_game_type.TTTGameTypeHVsC or not self.train:
                    print("Game Over!")
                    if game_state is ttt_game_state.TTTGameStateWin:
                        print("{} Wins!".format(win_player.get_string()))
                    if game_state is ttt_game_state.TTTGameStateDraw:
                        print("Game is a draw!")
                if self.train:
                    self.update_stats(game_state, win_player)
                return

    def run(self):
        logger.info("TTTPlay started")
        self.train_data.clear()
        logger.info("Training Data Cleared!")
        if self.game_type is ttt_game_type.TTTGameTypeCVsC:
            n_iterations = 0
            while n_iterations < self.train_iterations:
                self.play_game_cli()
                n_iterations += 1
                self.train and n_iterations % self.n_iter_info_skip == 0 and (logger.info("Training iteration {} finished. More {} left".format(n_iterations, self.train_iterations - n_iterations)))
            logger.info("Done {} with {} iterations.".format("training" if self.train else "playing", self.train_iterations))
        if self.game_type is ttt_game_type.TTTGameTypeHVsC:
            self.play_game_cli()
        if self.train:
            self.training_data_shared.update(self.train_data)
            self.training_data_shared.load()
            logger.info("Total games played for training until now: {}".format(self.training_data_shared.total_games_finished()))
            logger.info("self.training_data.cache_info(): {}".format(self.train_data.cache_info))
        return True