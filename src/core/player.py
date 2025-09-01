from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field
from src.core.card import Card, RANK, SUIT

class ActionType(Enum):
    FOLD = 0
    CHECK = 1
    CALL = 2
    BET = 3
    RAISE = 4

class Action(BaseModel):
    action: ActionType
    amount: Optional[int] = None
    
class PlayerData(BaseModel):
    player_id: str = Field(serialization_alias="player-id")
    hand: list[str]
    chips: int
    has_folded: bool = Field(serialization_alias="has-folded")
    is_all_in: bool = Field(serialization_alias="is-all-in")
    pot_contribution: int = Field(serialization_alias="pot-contribution")

class Player:
    def __init__(self, player_id: str, starting_chips: int = 0):
        self.id: str = player_id
        self.chips: int = starting_chips
        
        self.hand: list[Card] = []
        
        self.is_eliminated: bool = False
        self.has_folded: bool = False
        
        self.contribution: int = 0
    
    @property
    def is_all_in(self):
        return self.chips == 0

    @property
    def data(self) -> PlayerData:
        return PlayerData(
            player_id=self.id,
            hand=[RANK[card.rank] + SUIT[card.suit] for card in self.hand],
            chips=self.chips,
            has_folded=self.has_folded,
            is_all_in=self.is_all_in,
            pot_contribution=self.contribution,
        )
    
    def new_hand(self):
        self.hand = []
        self.is_all_in = False
        self.has_folded = False
        self.contribution = 0
        
    def act(self) -> Action:
        ...
        
    def force_bet(self, amount: int) -> int:
        """Force player to bet `amount`, if not possible player goes all in.
        Returns: Amount player actually contributed.
        """
        if amount >= self.chips:
            contribution = self.chips
            self.chips = 0
            self.contribution += contribution
            return contribution
        
        self.chips -= amount
        self.contribution += amount
        return amount
    
    def build_best_hand(self, community_cards: list[Card]) -> tuple[int, list[Card]]:
        build_order = [
            self._build_straight_flush,
            self._build_four_of_a_kind,
            self._build_full_house,
            self._build_flush,
            self._build_straight,
            self._build_three_of_a_kind,
            self._build_two_pair,
            self._build_one_pair,
            self._build_high_card,
        ]
        
        hand = self.hand + community_cards
        hand.sort(key=lambda card: card.rank, reverse=True)
        
        for idx, build in enumerate(build_order):
            best_hand = build(hand)
            if len(best_hand) == 5:
                hand_rank = len(build_order) - idx
                return (hand_rank, best_hand)
    
    #TODO: test
    @staticmethod
    def _build_straight_flush(cards: list[Card]) -> list[Card]:
        suits = [0] * 4
        for card in cards:
            suits[card.suit] += 1
            
        best_suit = -1
        for suit, count in enumerate(suits):
            if count >= 5:
                best_suit = suit
                break
            
        if best_suit == -1:
            return []
        
        return Player._build_straight([card for card in cards if card.suit == best_suit])
    
    #TODO: test
    @staticmethod
    def _build_four_of_a_kind(cards: list[Card]) -> list[Card]:
        """Precondition: cards are sorted using rank descending."""
        current_hand = [cards[0]]
        for card in cards[1:]:
            if card.rank == current_hand[0].rank:
                current_hand.append(card)
            else:
                current_hand = []
            
            if len(current_hand) == 4:
                break
        
        if len(current_hand) < 4:
            return []
        
        return current_hand + [card for card in cards if card.rank != current_hand[0].rank][:1]
    
    # TODO: test
    @staticmethod
    def _build_full_house(cards: list[Card]) -> list[Card]:
        """Precondition: cards are sorted using rank descending."""
        # TODO: fix to be more efficient
        ranks = [0] * 13
        for card in cards:
            ranks[card.rank - 1] += 1

        three_of_a_kind_rank = -1
        pair_rank = -1
        for rank, count in reversed(enumerate(ranks)):
            if count >= 3 and three_of_a_kind_rank == -1:
                three_of_a_kind_rank = rank
            elif pair_rank >= 2 and pair_rank == -1:
                pair_rank = rank
        
        if three_of_a_kind_rank != -1 and pair_rank != -1:
            return []
        
        return [card for card in cards if card.rank == three_of_a_kind_rank][:3] + [card for card in cards if card.rank == pair_rank][:2]
    
    # TODO: test
    @staticmethod
    def _build_flush(cards: list[Card]) -> list[Card]:
        """Precondition: cards are sorted using rank descending."""
        suits = [0] * 4
        
        for card in cards:
            suits[card.suit] += 1

        best_suit = -1
        for suit, count in enumerate(suits):
            if count >= 5:
                best_suit = suit
                break
            
        if best_suit == -1:
            return []
        
        best_hand = [card for card in cards if card.suit == best_suit][:5]
        
        return best_hand
    
    # TODO: test
    @staticmethod
    def _build_straight(cards: list[Card]) -> list[Card]:
        """Precondition: cards are sorted using rank descending."""
        hand = [cards[0]]
        
        for card in cards[1:]:
            if hand[-1].rank - 1 == card.rank:
                hand.append(card)
            else:
                hand = []
            
            if len(hand) == 5:
                break
        
        # check for ace low
        if len(hand) == 4 and hand[-1].rank == 0 and cards[0].rank == 12:
            hand.insert(0, cards[0])
        
        if len(hand) < 5:
            return []
        
        return hand
    
    #TODO: test
    @staticmethod
    def _build_three_of_a_kind(cards: list[Card]) -> list[Card]:
        """Precondition: cards are sorted using rank descending."""
        hand = [cards[0]]
        for card in cards[1:]:
            if card.rank == hand[0].rank:
                hand.append(card)
            else:
                hand = []
            
            if len(hand) == 3:
                break
        
        if len(hand) < 3:
            return []
        
        return hand + [card for card in cards if card.rank != hand[0].rank][:2]

    #TODO: test
    @staticmethod
    def _build_two_pair(cards: list[Card]) -> list[Card]:
        """Precondition: cards are sorted using rank descending."""
        ranks = [0] * 13
        for card in cards:
            ranks[card.rank] += 1
        
        best_rank_1, best_rank_2 = -1, -1
        for rank, count in reversed(enumerate(ranks)):
            if count == 2:
                if best_rank_1 == -1:
                    best_rank_1 = rank
                elif best_rank_2 == -1:
                    best_rank_2 = rank
                else:
                    break
                
        if best_rank_1 == -1 or best_rank_2 == -1:
            return []
        
        best_hand = [card for card in cards if card.rank == best_rank_1 or card.rank == best_rank_2]
        best_hand.append([card for card in cards if card.rank != best_rank_1 and card.rank != best_rank_2][0])
            
        return best_hand
    
    #TODO: test
    @staticmethod
    def _build_one_pair(cards: list[Card]) -> list[Card]:
        """Precondition: cards are sorted using rank descending."""
        hand = [cards[0]]
        for card in cards[1:]:
            if card.rank == hand[0].rank:
                hand.append(card)
            else:
                hand = []
            
            if len(hand) == 2:
                break
        
        if len(hand) < 2:
            return []
        
        return hand + [card for card in cards if card.rank != hand[0].rank][:3]
    
    #TODO: test
    @staticmethod
    def _build_high_card(cards: list[Card]) -> list[Card]:
        """Precondition: cards are sorted using rank descending."""
        return cards[:5]