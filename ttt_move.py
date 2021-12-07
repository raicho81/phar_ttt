

class TTTMoveTrainData:
    
    def __init__(self, move_idx, n_wins=0, n_draws=0, n_looses=0):
        self.n_wins = n_wins
        self.n_draws = n_draws
        self.n_looses = n_looses
        self.move_idx = move_idx
