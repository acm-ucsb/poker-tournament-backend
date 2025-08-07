class Player:
    def __init__(self, player_id: str):
        self.id: str = player_id
        self.eliminated: bool = False