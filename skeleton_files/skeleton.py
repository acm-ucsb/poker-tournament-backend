# class Pot:
#     value: float
#     players: list[str]


# class GameState:
#     index_to_action: int
#     index_of_small_blind: int
#     players: list[str]
#     player_cards: list[str]
#     held_money: list[float]
#     bet_money: list[float]
#     community_cards: list[str]
#     pots: list[Pot]
#     small_blind: float
#     big_blind: float

# ======================= #
# ACTUAL BOT CODE HERE!!! #
# ======================= #
//%insert%//


def set_state_input(state: GameState):
    state.index_to_action = int(input())
    state.index_of_small_blind = int(input())
    state.players = input().split()
    state.player_cards = input().split()
    state.held_money = list(map(float, input().split()))
    state.bet_money = list(map(float, input().split()))
    state.community_cards = input().split()

    num_pots = int(input())
    state.pots = []
    for _ in range(num_pots):
        pot_input_list = input().split()
        p = Pot()
        p.value = float(pot_input_list[0])
        p.players = pot_input_list[1:]
        state.pots.append(p)

    state.small_blind = float(input())
    state.big_blind = float(input())


def main():
    state = GameState()

    set_state_input(state)

    print(bet(state))


if __name__ == "__main__":
    main()
