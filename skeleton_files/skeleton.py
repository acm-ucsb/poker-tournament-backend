# class Pot:
#     value: float
#     players: list[str]


# # cards are defined as 1st char: A(2-9)TJQK, 2nd char: SDCH
# # currently does not take into account side pots
# class GameState:
#     players: list[str]  # team_ids
#     player_cards: list[str]
#     held_money: list[float]
#     bet_money: list[float]  # per round, -1 for fold, 0 for check/hasn't bet yet
#     community_cards: list[str]
#     pots: list[Pot]
#     current_round: str  # preflop, flop, turn, river

# ======================= #
# ACTUAL BOT CODE HERE!!! #
# ======================= #
//%insert%//


def set_state_input(state: GameState):
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

    state.current_round = input()


def main():
    state = GameState()

    set_state_input(state)

    print(bet(state))


if __name__ == "__main__":
    main()
