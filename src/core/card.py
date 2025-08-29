from random import randint
from pydantic import BaseModel, Field

SUIT = {
    1: "S",
    2: "H",
    3: "D",
    4: "C",
}

RANK = {
    13: "A",
    12: "K",
    11: "Q",
    10: "J",
    9: "10",
    8: "9",
    7: "8",
    6: "7",
    5: "6",
    4: "5",
    3: "4",
    2: "3",
    1: "2",
}

class Card(BaseModel):
    rank: int = Field(..., ge=1, le=13)
    suit: int = Field(..., ge=1, le=4)
    
class Deck():
    def __init__(self):
        self.reset()
    
    def reset(self) -> None:
        self.used_card: list[int] = [0] * 52
        
    def deal_card(self) -> Card:
        if sum(self.used_card) == 52:
            raise Exception("No more card left to deal")
        
        card = None
        while card == None or self.used_card[card] == 1:
            rank = randint(1, 13)
            suit = randint(1, 4)
            card = suit * 4 + rank
        
        self.used_card[card] = 1
            
        return Card(rank=card[0], suit=card[1])
    
    #TODO: test all of these functions
    # I ran all of these functions through gemini and it said they were correct


    """
    precondition: called from the deck object in the table class
    precondition: cards is a list of Card objects
    precondition: len(cards) == 7
    precondition: cards contains no duplicate cards
    precondition: cards contains only valid cards (1 <= rank <= 13, 1 <= suit <= 4)
    """

    # determine the strongest hand from a list of cards
    def hand_stength(self, cards: list[Card]) -> int:
        """
        check all strengths in order from strongest to weakest
        an integer representing the highest rank in each hand is returned
        return strength value + rank of highest card in the hand
        """
        
        # straight flush
        check = self._check_straight_flush(cards)
        if check != -1:
            return 800 + check # highest strength
        
        # four of a kind
        check = self._check_four_of_a_kind(cards)
        if check != -1:
            return 700 + check
        
        # full house
        check = self._check_full_house(cards)
        if check != -1:
            return 600 + check  
        
        # flush
        check = self._check_flush(cards)
        if check != -1:
            return 500 + check
        
        # straight
        check = self._check_straight(cards)
        if check != -1:
            return 400 + check
        
        # three of a kind
        check = self._check_three_of_a_kind(cards)
        if check != -1:
            return 300 + check
        
        # two pair
        check = self._check_two_pair(cards)
        if check != -1:
            return 200 + check
        
        # one pair
        check = self._check_one_pair(cards)
        if check != -1:
            return 100 + check  
        
        # high card
        check = self._check_high_card(cards)
        return check # lowest strength
        

    """
    private helper methods for hand strength
    call in order of strongest to weakest hand
    """

    def _check_straight_flush(self, cards: list[Card]) -> int:
        suits = {}
        for card in cards:
            if card.suit in suits:
                suits[card.suit] += 1
            else:
                suits[card.suit] = 1

        # check flush
        if all(v < 5 for v in suits.values()):
            return -1 # no flush found
        
        desired_suit = [suit for suit, v in suits.items() if v >= 5][0]
        cards_in_suit = [card for card in cards if card.suit == desired_suit]
        return self._check_straight(cards_in_suit)


    def _check_four_of_a_kind(self, cards: list[Card]) -> int:
        vals = {}
        for card in cards:
            if card.rank in vals:
                vals[card.rank] += 1
            else:
                vals[card.rank] = 1

        vals = sorted(vals.items(), key=lambda x: x[1], reverse=True)
        # if a 4 of a kind exists, it will be the first element
        if vals[0][1] == 4:
            return vals[0][0]
        return -1

    # return rank of highest card in the full house, -1 if no full house found
    def _check_full_house(self, cards: list[Card]) -> int:
        vals = {}
        for card in cards:
            if card.rank in vals:
                vals[card.rank] += 1
            else:
                vals[card.rank] = 1

        three_of_a_kind = -1
        pair = -1
        # sort descending by frequency
        vals = sorted(vals.items(), key=lambda x: x[1], reverse=True) 
        for rank, v in vals:
            # highest three of a kind
            if v >= 3 and three_of_a_kind == -1:
                three_of_a_kind = rank
            # next highest pair
            elif v >= 2 and pair == -1:
                pair = rank
            
            if three_of_a_kind != -1 and pair != -1:
                return three_of_a_kind
            
        return -1

    # return rank of highest card in the flush, -1 if no flush found
    def _check_flush(self, cards: list[Card]) -> int:
        suits = {}
        for card in cards:
            if card.suit in suits:
                suits[card.suit] += 1
            else:
                suits[card.suit] = 1

        # no flush found
        found = all(v < 5 for v in suits.values())
        if found: # all values < 5
            return -1
        
        #return highest card in the flush
        desired_suit = [suit for suit, v in suits.items() if v >= 5][0]
        max_rank = max([card.rank for card in cards if card.suit == desired_suit])
        return max_rank

    # return rank of highest card in the straight, -1 if no straight found
    def _check_straight(self, cards: list[Card]) -> int:
        vals = set()
        for card in cards:
            vals.add(card.rank)
        # ace can be high or lowe
        if 13 in vals:
            vals.add(0)
        vals = sorted(list(vals))
        # consecutive differences
        diffs = [vals[i+1] - vals[i] for i in range(len(vals)-1)]

        # lookf for 4 consecutive 1s in diffs
        # start from the end
        for i in reversed(range(len(diffs) - 3)):
            if diffs[i:i+4] == [1, 1, 1, 1]:
                return vals[i+4] # highest card in the straight
            
        return -1

    #return rank of the three, -1 if no three found
    def _check_three_of_a_kind(self, cards: list[Card]) -> int:
        vals = {}
        for card in cards:
            if card.rank in vals:
                vals[card.rank] += 1
            else:
                vals[card.rank] = 1

        #sort bu rank
        vals = sorted(vals.items(), key = lambda x: x[0], reverse=True)
        # highest three of a kind
        for rank, v in vals:
            if v == 3:
                return rank
            
        return -1

    # returns rank of highest pair, -1 if no pair found
    def _check_two_pair(self, cards: list[Card]) -> int:
        vals = {}
        for card in cards:
            if card.rank in vals:
                vals[card.rank] += 1
            else:
                vals[card.rank] = 1

        vals = sorted(vals.items(), key = lambda x: x[0], reverse=True)
        pairs = []
        for rank, v in vals:
            if v == 2:
                pairs.append(rank)
                if len(pairs) == 2:
                    return max(pairs)
            
        return -1 

    # only call this method if all previous methods return false
    def _check_one_pair(self, cards: list[Card]) -> int:
        vals = {}
        for card in cards:
            if card.rank in vals:
                vals[card.rank] += 1
            else:
                vals[card.rank] = 1
        # sort by rank
        vals = sorted(vals.items(), key = lambda x: x[0], reverse=True)
        # return highest pair
        for rank, v in vals:
            if v == 2:
                return rank
            
        return -1 # no pair found

    def _check_high_card(self, cards: list[Card]) -> int:
        return max([card.rank for card in cards])