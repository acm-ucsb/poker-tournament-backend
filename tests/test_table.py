from src.core.table import Table
from src.core.player import Player
from src.core.card import Card


def init_table() -> tuple[Table, list[Player | None]]:
    table = Table("1")
    seating: list[Player | None] = [None] * 8
    seating[0] = Player("0", 1000)
    seating[2] = Player("2", 1000)
    seating[3] = Player("3", 1000)
    seating[6] = Player("6", 1000)
    seating[7] = Player("7", 1000)

    table.seating = seating

    table.players[0].chips = 0
    table.players[0].contribution = 300

    table.players[1].contribution = 500

    table.players[2].chips = 0
    table.players[2].contribution = 200

    table.players[3].contribution = 300
    table.players[3].has_folded = True

    table.pot = 1300

    return (table, seating)


def test_blinds():
    table, _ = init_table()

    assert table.blinds == (2, 3)

    table.button = 6

    assert table.blinds == (7, 0)


def test_players():
    table, players = init_table()
    assert table.players == [player for player in players if player]
    assert table.players != players


def test_get_vacant():
    table, _ = init_table()

    assert table.get_vacant() == [1, 5, 4]

    table.button = 3

    assert table.get_vacant() == [5, 4, 1]


def test_payout():
    table, _ = init_table()

    assert table.payout_helper([table.players[2]]) == 800
    assert table.players[2].chips == 800
    assert table.pot == 500

    assert table.payout_helper([table.players[0], table.players[1]], 800) == 500
    assert table.players[0].chips == 150
    assert table.players[1].chips == 1350
    assert table.pot == 0

    table, _ = init_table()
    assert table.payout_helper([table.players[0], table.players[1]]) == 1300
    assert table.players[0].chips == 550
    assert table.players[1].chips == 1750
    assert table.pot == 0

    table, _ = init_table()
    assert table.payout_helper([table.players[0]]) == 1100
    assert (
        table.payout_helper(
            [table.players[1], table.players[2], table.players[3]], 1100
        )
        == 200
    )
    assert table.players[0].chips == 1100
    assert table.players[1].chips == 1200
    assert table.players[2].chips == 0
    assert table.players[3].chips == 1000

    table, _ = init_table()
    table.players[0].contribution = 100
    table.players[1].contribution = 100
    table.players[2].contribution = 100
    table.players[3].contribution = 100
    table.pot = 400

    assert (
        table.payout_helper([table.players[0], table.players[1], table.players[3]])
        == 400
    )
    assert table.players[0].chips == 133
    assert table.players[1].chips == 1134
    assert table.players[2].chips == 0
    assert table.players[3].chips == 1133


def test_step():
    table, players = init_table()

    table.button = 3

    """ sim tying hands """
    players[0].contribution = 50
    players[0].chips = 950
    players[2].has_folded = True
    players[3].contribution = 50
    players[3].chips = 950
    players[6].chips = 990
    players[6].has_folded = True
    players[6].contribution = 10
    players[7].chips = 970
    players[7].has_folded = True
    players[7].contribution = 30

    table.pot = 140

    players[0].hand = [Card(rank=12, suit=1), Card(rank=4, suit=1)]
    table.deck.used_card[25] = 1
    table.deck.used_card[17] = 1
    players[3].hand = [Card(rank=12, suit=0), Card(rank=4, suit=0)]
    table.deck.used_card[12] = 1
    table.deck.used_card[4] = 1

    table.community_cards = [
        Card(rank=12, suit=2),
        Card(rank=12, suit=3),
        Card(rank=4, suit=3),
    ]
    table.deck.used_card[38] = 1
    table.deck.used_card[51] = 1
    table.deck.used_card[43] = 1

    table.community_cards.extend([table.deck.deal_card() for _ in range(2)])
    table.community_cards.sort(key=lambda card: card.rank, reverse=True)

    rank1, cards1 = players[0].build_best_hand(table.community_cards)

    rank2, cards2 = players[3].build_best_hand(table.community_cards)

    # print(rank1, rank2)

    # for card1, card2 in zip(cards1, cards2):
    #     print(card1, card2)

    print(table)
    table.end_hand()
    # print(table)
    assert players[0].chips == 1020
    assert players[3].chips == 1020
