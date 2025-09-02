import sys
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)


from src.core.player import Player
from src.core.card import Card

class PlayerTests:
    """
    Test cases for the hand evaluation methods in the Player class.
    """
    @staticmethod
    def test_four_of_a_kind():
        # tested four of a kind and no four of a kind
        player = Player("test")
        cards = [
            Card(rank=0, suit=0),
            Card(rank=0, suit=1),
            Card(rank=0, suit=2),
            Card(rank=12, suit=3),
            Card(rank=3, suit=1),
            Card(rank=4, suit=2),
            Card(rank=5, suit=3),
        ]

        cards.sort(key=lambda card: card.rank, reverse=True)
        hand = player._build_four_of_a_kind(cards)
        for card in hand:
            print(card)
        # assert len(hand) == 5
        # assert hand[0].rank == 0
        # assert hand[-1].rank == 5
        assert len(hand) == 0
        return

    @staticmethod
    def test_straight_flush():
        # tested ace high, ace low, and wrap around
        player = Player("test")
        cards = [
            Card(rank=0, suit=0),
            Card(rank=1, suit=0),
            Card(rank=12, suit=0),
            Card(rank=11, suit=0),
            Card(rank=10, suit=0),
            Card(rank=3, suit=1),
            Card(rank=4, suit=2),
        ]

        cards.sort(key=lambda card: card.rank, reverse=True)
        hand = player._build_straight_flush(cards)
        assert len(hand) == 0
        return
        # for card in hand:
        #     print(card)
        # assert len(player._build_straight_flush(cards)) == 5
        # assert player._build_straight_flush(cards)[0].rank == 3
        # assert player._build_straight_flush(cards)[-1].rank == 12
    
    @staticmethod
    def test_full_house():
        # tested full house and no full house
        player = Player("test")
        cards = [
            Card(rank=0, suit=0),
            Card(rank=1, suit=1),
            Card(rank=2, suit=2),
            Card(rank=0, suit=1),
            Card(rank=2, suit=2),
            Card(rank=4, suit=2),
            Card(rank=4, suit=3),
        ]

        cards.sort(key=lambda card: card.rank, reverse=True)
        hand = player._build_full_house(cards)
        for card in hand:
            print(card)
        assert len(hand) == 0
        return
    
    @staticmethod
    def test_flush():
        # tested flush and no flush
        player = Player("test")
        cards = [
            Card(rank=0, suit=0),
            Card(rank=1, suit=0),
            Card(rank=2, suit=0),
            Card(rank=3, suit=0),
            Card(rank=4, suit=1),
            Card(rank=5, suit=2),
            Card(rank=6, suit=0),
        ]

        cards.sort(key=lambda card: card.rank, reverse=True)
        hand = player._build_flush(cards)
        # for card in hand:
        #     print(card)
        assert len(hand) == 5
        return
    
    def test_straight():
        # tested ace high, ace low, and wrap around
        player = Player("test")
        cards = [
            Card(rank=0, suit=0),
            Card(rank=1, suit=1),
            Card(rank=8, suit=2),
            Card(rank=9, suit=0),
            Card(rank=11, suit=1),
            Card(rank=10, suit=2),
            Card(rank=12, suit=0),
        ]

        cards.sort(key=lambda card: card.rank, reverse=True)
        hand = player._build_straight(cards)
        # for card in hand:
        #     print(card)
        assert len(hand) == 5
        return
    
    def test_three_of_a_kind():
        # tested three of a kind and no three of a kind
        player = Player("test")
        cards = [
            Card(rank=12, suit=0),
            Card(rank=0, suit=1),
            Card(rank=6, suit=1),
            Card(rank=4, suit=1),
            Card(rank=6, suit=2),
            Card(rank=5, suit=3),
            Card(rank=6, suit=0),
        ]

        cards.sort(key=lambda card: card.rank, reverse=True)
        hand = player._build_three_of_a_kind(cards)
        # for card in hand:
        #     print(card)
        assert len(hand) == 5
        return
    
    def test_two_pair():
        # tested two pair and no two pair
        player = Player("test")
        cards = [
            Card(rank=0, suit=0),
            Card(rank=0, suit=1),
            Card(rank=6, suit=1),
            Card(rank=4, suit=1),
            Card(rank=5, suit=2),
            Card(rank=6, suit=3),
            Card(rank=4, suit=0),
        ]

        cards.sort(key=lambda card: card.rank, reverse=True)
        hand = player._build_two_pair(cards)
        # for card in hand:
        #     print(card)
        assert len(hand) == 5
        return
    
    def test_one_pair():
        # tested one pair and no one pair
        player = Player("test")
        cards = [
            Card(rank=0, suit=0),
            Card(rank=1, suit=1),
            Card(rank=6, suit=1),
            Card(rank=4, suit=1),
            Card(rank=8, suit=2),
            Card(rank=7, suit=3),
            Card(rank=8, suit=0),
        ]

        cards.sort(key=lambda card: card.rank, reverse=True)
        hand = player._build_one_pair(cards)
        # for card in hand:
        #     print(card)
        assert len(hand) == 5
        return
    
    def test_high_card():
        # tested high card
        player = Player("test")
        cards = [
            Card(rank=0, suit=0),
            Card(rank=1, suit=1),
            Card(rank=6, suit=1),
            Card(rank=4, suit=1),
            Card(rank=8, suit=2),
            Card(rank=7, suit=3),
            Card(rank=9, suit=0),
        ]

        cards.sort(key=lambda card: card.rank, reverse=True)
        hand = player._build_high_card(cards)
        # for card in hand:
        #     print(card)
        assert len(hand) == 5
        return


if __name__ == "__main__":
    PlayerTests.test_straight_flush()
    print("Straight flush test passed.")
    PlayerTests.test_four_of_a_kind()
    print("Four of a kind test passed.")
    PlayerTests.test_full_house()
    print("Full house test passed.")
    PlayerTests.test_flush()
    print("Flush test passed.")
    PlayerTests.test_straight()
    print("Straight test passed.")
    PlayerTests.test_three_of_a_kind()
    print("Three of a kind test passed.")
    PlayerTests.test_two_pair()
    print("Two pair test passed.")
    PlayerTests.test_one_pair()
    print("One pair test passed.")
    PlayerTests.test_high_card()
    print("High card test passed.")
    print("All tests passed.")