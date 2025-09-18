class Pot:
    value: float
    players: list[str]


class GameState:
    index_to_action: int
    index_of_small_blind: int
    players: list[str]
    player_cards: list[str]
    held_money: list[float]
    bet_money: list[float]
    community_cards: list[str]
    pots: list[Pot]
    small_blind: float
    big_blind: float


# DO NOT CHANGE ABOVE CODE OR FUNCTION SIGNATURE ELSE YOUR CODE WILL NOT RUN!
# except... some libraries can be imported


def bet(state: GameState) -> int:
    return 0
