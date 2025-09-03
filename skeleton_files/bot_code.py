class Pot:
    value: float
    players: list[str]


class GameState:
    players: list[str]
    player_cards: list[str]
    held_money: list[float]
    bet_money: list[float]
    community_cards: list[str]
    pots: list[Pot]
    current_round: str


# DO NOT CHANGE ABOVE CODE OR FUNCTION SIGNATURE ELSE YOUR CODE WILL NOT RUN!
# except... some libraries can be imported


def bet(state: GameState) -> int:
    return 0
