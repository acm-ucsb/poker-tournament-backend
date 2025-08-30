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
        hand = self.hand + community_cards
        
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
        
        
        # TODO: (fix) make sure that the best_hand is sorted by eval types
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
        ranks = [0] * 13
        
        for card in cards:
            ranks[card.rank - 1] += 1
        
        best_rank = -1
        for rank, count in reversed(enumerate(ranks)):
            if count == 4:
                best_rank = rank
                break
            
        if best_rank == -1:
            return []
        
        best_hand = [card for card in cards if card.rank == best_rank]
        best_hand.extend(Player._build_high_card([card for card in cards if card.rank != best_rank]))[0]
        
        return best_hand
    
    # TODO: test
    @staticmethod
    def _build_full_house(cards: list[Card]) -> list[Card]:
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
        
        best_hand = [card for card in cards if card.suit == best_suit]
        best_hand.sort(key=lambda card: card.rank, reverse=True)
        
        return best_hand[:5]
    
    # TODO: test
    @staticmethod
    def _build_straight(cards: list[Card]) -> list[Card]:
        # 14 to account for the ace low
        ranks = [0] * 14
        for card in cards:
            ranks[card.rank + 1] += 1
            if card.rank == 12:
                ranks[0] += 1
        
        best_high = -1
        current_length = 0
        for rank, count in enumerate(ranks):
            if count != 0:
                current_length += 1
                
                if current_length >= 5:
                    best_high = rank
            else:
                current_length = 0
                
        if best_high == -1:
            return []
        
        cards_sorted = sorted(cards, key=lambda card: card.rank)
        
        # +1 to offset rank shifted due to low ace
        current_rank = best_high - 5 + 1
        best_hand = []
        
        if current_rank == 0:
            current_rank = 1
            best_hand.append(cards_sorted[-1])
            
        for card in cards_sorted:
            if len(best_hand) == 5:
                break
            
            if card.rank == current_rank:
                best_hand.append(card)
                current_rank += 1
        
        return best_hand
    
    #TODO: test
    @staticmethod
    def _build_three_of_a_kind(cards: list[Card]) -> list[Card]:
        ranks = [0] * 13
        for card in cards:
            ranks[card.rank] += 1
        
        best_rank = -1
        for rank, count in reversed(enumerate(ranks)):
            if count == 3:
                best_rank = rank
                
        if best_rank == -1:
            return []
                
        best_hand = [card for card in cards if card.rank == best_rank]
        best_hand.extend(Player._build_high_card([card for card in cards if card.rank != best_rank])[:2])
            
        return best_hand

    #TODO: test
    @staticmethod
    def _build_two_pair(cards: list[Card]) -> list[Card]:
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
        best_hand.extend(Player._build_high_card([card for card in cards if card.rank != best_rank_1 and card.rank != best_rank_2])[0])
            
        return best_hand
    
    #TODO: test
    @staticmethod
    def _build_one_pair(cards: list[Card]) -> list[Card]:
        ranks = [0] * 13
        for card in cards:
            ranks[card.rank] += 1
            
        best_rank = -1
        for rank, count in reversed(enumerate(ranks)):
            if count == 2:
                best_rank = rank
                break
            
        if best_rank == -1:
            return []
            
        best_hand = [card for card in cards if card.rank == best_rank]
        best_hand.extend(Player._build_high_card([card for card in cards if card.rank != best_rank])[:3])
        
        return best_hand
    
    #TODO: test
    @staticmethod
    def _build_high_card(cards: list[Card]) -> list[Card]:
        return sorted(cards, key=lambda card: card.rank, reverse=True)[:5]