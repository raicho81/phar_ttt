import logging
import ttt_game_state


logger = logging.getLogger(__name__)

class TTTDesk:
    def __init__(self, size):
        self.size = size
        self.desk = None
        self.clear()

    def clear(self):
        self.desk = [[None] * self.size for _ in range(self.size)]

    def get_possible_moves_indices(self):
        possible_moves_indices = []
        for x in range(self.size):
            for y in range(self.size):
                if self.desk[y][x] is None:
                    possible_moves_indices.append(x + y * self.size)
        return sorted(possible_moves_indices)

    def get_state(self):
        return tuple(tuple(player.get_code() if player is not None else None for player in row) for row in self.desk)

    def eval_game_state(self):
        # check rows
        for row in self.desk:
            win = False
            player = row[0]
            if player is None:
                continue
            for square in row[1:]:
                if square is not player:
                    win = False
                    break
                if square is player:
                    win = True
                else:
                    win = False
                    break
            if win:
                return ttt_game_state.TTTGameStateWin, player
        # check columns
        for x in range(self.size):
            win = False
            player = self.desk[0][x]
            if player is None:
                continue
            for y in range(1, self.size):
                square = self.desk[y][x]
                if square is not player:
                    win = False
                    break
                if square is player:
                    win = True
                else:
                    win = False
                    break
            if win:
                return ttt_game_state.TTTGameStateWin, player
        # check main diagonal
        win = False
        player = self.desk[0][0]
        if player is not None:
            for x in range(1, self.size):
                square = self.desk[x][x]
                if square is None:
                    win = False
                    break
                if square is player:
                    win = True
                else:
                    win = False
                    break
            if win:
                return ttt_game_state.TTTGameStateWin, player
        # check reverse diagonal
        player = self.desk[0][self.size - 1]
        if player is not None:
            win = False
            for y, x in zip(range(1, self.size), range(self.size - 2, -1 , -1)):
                square = self.desk[y][x]
                if square is None:
                    win = False
                    break
                if square is player:
                    win = True
                else:
                    win = False
                    break
            if win:
                return ttt_game_state.TTTGameStateWin, player
        possible_moves = self.get_possible_moves_indices()
        if len(possible_moves) == 0:
            return ttt_game_state.TTTGameStateDraw, None
        return ttt_game_state.TTTGameStateUnfinished, None

    def possible_moves_indices(self):
        possible_moves_indices = []
        state = self.get_state()
        for x in range(len(state)):
            for y in range(len(state)):
                if state[y][x] is None:
                    possible_moves_indices.append(x + y * len(state))
        return possible_moves_indices

    def print_desk(self):
        for row in self.desk:
            print(" ".join([player.get_mark().get_string() if player is not None else "_" for player in row]))
