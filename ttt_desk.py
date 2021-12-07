

class TTTDesk:

    def __init__(self, size):
        self.size = size
        self.desk = None
        self.clear()

    def clear(self):
        self.desk = [
            [None] * self.size for _ in range(self.size)
        ]

    def get_possible_moves_indices(self):
        possible_moves_indices = []
        for x in range(self.size):
            for y in range(self.size):
                if self.desk[y][x] is None:
                    possible_moves_indices.append(x + y * self.size)
        return possible_moves_indices

    def get_state(self):
        return tuple(tuple(row) for row in self.desk)
