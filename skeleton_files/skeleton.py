# class Pot:
#     value: int
#     players: list[str]


# class GameState:
#     index_to_action: int
#     index_of_small_blind: int
#     players: list[str]
#     player_cards: list[str]
#     held_money: list[int]
#     bet_money: list[int]
#     community_cards: list[str]
#     pots: list[Pot]
#     small_blind: int
#     big_blind: int

# ======================= #
# ACTUAL BOT CODE HERE!!! #
# ======================= #
//%insert%//


def set_state_input(state: GameState):
    state.index_to_action = int(input())
    state.index_of_small_blind = int(input())
    state.players = input().split()
    state.player_cards = input().split()
    state.held_money = list(map(int, input().split()))
    state.bet_money = list(map(int, input().split()))
    state.community_cards = input().split()

    num_pots = int(input())
    state.pots = []
    for _ in range(num_pots):
        pot_input_list = input().split()
        p = Pot()
        p.value = int(pot_input_list[0])
        p.players = pot_input_list[1:]
        state.pots.append(p)

    state.small_blind = int(input())
    state.big_blind = int(input())


def main():
    state = GameState()

    set_state_input(state)

    print(bet(state))


if __name__ == "__main__":
    main()
