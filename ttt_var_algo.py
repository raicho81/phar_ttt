import random


class VarAlgo:

    GAME_STATE_WIN_X = 1
    GAME_STATE_WIN_O = 2
    GAME_STATE_DRAW = 3
    GAME_STATE_UNFINISHED = 4

    @staticmethod
    def choose_next_move_random_idx(desk):
        possible_moves_indices = desk.get_possible_moves_indices()
        # choose the next random move
        next_move_idx = random.choice(possible_moves_indices)
        return next_move_idx

    @staticmethod
    def possible_moves_indices(state):
        possible_moves_indices = []
        for x in range(len(state)):
            for y in range(len(state)):
                if state[y][x] is None:
                    possible_moves_indices.append(x + y * len(state))
        return possible_moves_indices
    
    @staticmethod
    def choose_next_best_move_idx(state, train_data):
        # choose the next move by selecting the best possible move from the training data
        possible_moves = train_data.get_train_data().get(state, None)
        if possible_moves is None:
            train_data.add_train_state(state, VarAlgo.possible_moves_indices(state))
            possible_moves = train_data.get_train_data()[state]
        possible_moves_sorted_by_wins_rev = sorted(possible_moves, key=lambda m: m.n_wins, reverse=True)
        for move in possible_moves_sorted_by_wins_rev:
            if move.n_wins > move.n_looses:
                return move.move_idx
        possible_moves_sorted_by_draws = sorted(possible_moves, key=lambda m: m.n_draws, reverse=True)
        for move in possible_moves_sorted_by_draws:
            if move.n_draws > move.n_looses:
                return move.move_idx
        possible_moves_sorted_by_looses = sorted(possible_moves, key=lambda m: m.n_looses)
        return possible_moves_sorted_by_looses[0].move_idx

    @staticmethod
    def check_who_wins(square_mark):
        if square_mark =="x":
            return VarAlgo.GAME_STATE_WIN_X
        else:
            return VarAlgo.GAME_STATE_WIN_O

    @staticmethod
    def eval_game_state(desk):
        # check rows
        for row in desk.desk:
            win = False
            first_square = row[0]
            if first_square is None:
                break
            for square in row[1:]:
                if square is None:
                    win = False
                    break
                if square == first_square:
                    win = True
                else:
                    win = False
                    break
            if win:
                return VarAlgo.check_who_wins(first_square)

        # check columns
        for x in range(desk.size):
            win = False
            first_square = desk.desk[0][x]
            if first_square is None:
                break
            for y in range(1, desk.size):
                square = desk.desk[y][x]
                if square is None:
                    win = False
                    break
                if square == first_square:
                    win = True
                else:
                    win = False
                    break
            if win:
                return VarAlgo.check_who_wins(first_square)
        
        # check main diagonal
        win = False
        first_square = desk.desk[0][0]
        if first_square is not None:
            for x in range(1, desk.size):
                square = desk.desk[x][x]
                if square is None:
                    win = False
                    break
                if square == first_square:
                    win = True
                else:
                    win = False
                    break
            if win:
                return VarAlgo.check_who_wins(first_square)
        
        # check reverse diagonal
        first_square = desk.desk[0][desk.size - 1]
        if first_square is not None:
            win = False
            for y, x in zip(range(1, desk.size), range(desk.size - 2, -1 , -1)):
                square = desk.desk[y][x]
                if square is None:
                    win = False
                    break
                if square == first_square:
                    win = True
                else:
                    win = False
                    break
            if win:
                return VarAlgo.check_who_wins(first_square)

        possible_moves = desk.get_possible_moves_indices()
        if len(possible_moves) == 0:
            return VarAlgo.GAME_STATE_DRAW
        
        return VarAlgo.GAME_STATE_UNFINISHED
