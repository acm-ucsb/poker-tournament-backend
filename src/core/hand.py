from functools import total_ordering

# mapped to 2-14 (ace := 14)
RANKS = ["a", "2", "3", "4", "5", "6", "7", "8", "9", "t", "j", "q", "k"]
# mapped to 0-3
SUITS = ["s", "d", "c", "h"]
FULL_DECK = [rank + suit for suit in SUITS for rank in RANKS]

HAND_TYPES = {
    "straight_flush": 8,
    "four_of_a_kind": 7,
    "full_house": 6,
    "flush": 5,
    "straight": 4,
    "three_of_a_kind": 3,
    "two_pair": 2,
    "pair": 1,
    "high_card": 0,
}


# class used within Hand only!
# ordering by ranks (eq not by suit, only rank)!
@total_ordering
class Card:
    comparison_err = TypeError("Card can only be compared with other Card instances.")

    def __init__(self, card_str: str):
        # mapped to 2-14 (ace := 14)
        self.rank: int = 14 if card_str[0] == "a" else RANKS.index(card_str[0])
        # mapped to 0-3
        self.suit: int = SUITS.index(card_str[1])

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Card):
            raise self.comparison_err
        return self.rank == other.rank

    def __gt__(self, other: object) -> bool:
        if not isinstance(other, Card):
            raise self.comparison_err
        return self.rank > other.rank

    def __str__(self) -> str:
        char1 = "a" if self.rank == 14 else RANKS[self.rank - 1]
        char2 = SUITS[self.suit]

        return char1 + char2


# ordering by best hands!
@total_ordering
class Hand:
    comparison_err = TypeError("Hand can only be compared with other Hand instances.")

    # generating all pairs, all triples, all quads
    # rank occurences detailed in __init__
    @staticmethod
    def all_n_of_a_kind(n: int, cards: list[Card], rank_occurences: list[int]):
        pairs_trips_quads: list[list[Card]] = []

        # all of a kind produces the highest rank as the first
        for rank, count in reversed(list(enumerate(rank_occurences[2:]))):
            if count == n:
                pairs_trips_quads.append(
                    list(filter(lambda card: card.rank == rank, cards))
                )
        return pairs_trips_quads

    # =============================================================== #
    # THE FOLLOWING FUNCTIONS GENERATE CARDS FOR SPECIFIED HAND TYPES #
    # --------------------------------------------------------------- #
    # - will generate a list of best 5 cards for the hand             #
    # - cards: must be in sorted desc order (greatest first Ace -> 2) #
    # - return -> more important hand deciding cards first, kickers   #
    #   - eg: full_house -> [*(3 of a kind), *(pair)]                 #
    #   - eg: pair -> [*(pair), kicker1, kicker2, kicker3]            #
    # - returns None if not possible                                  #
    # =============================================================== #

    @staticmethod
    def four_of_a_kind(cards: list[Card], rank_occurences: list[int]):
        quads = Hand.all_n_of_a_kind(4, cards, rank_occurences)
        if len(quads) == 0:
            return None

        final_hand = quads[0]

        for card in cards:
            if len(final_hand) >= 5:
                break
            if card not in final_hand:
                final_hand.append(card)

        return final_hand

    @staticmethod
    def full_house(cards: list[Card], rank_occurences: list[int]):
        trips = Hand.all_n_of_a_kind(3, cards, rank_occurences)
        if len(trips) == 0:
            return None
        pairs = Hand.all_n_of_a_kind(2, cards, rank_occurences)
        if len(pairs) == 0:
            return None
        return trips[0] + pairs[0]

    # <10 cards, several flushes can exist otherwise.
    @staticmethod
    def flush(cards: list[Card], only_five_greatest=True):
        suit_counter = [0, 0, 0, 0]
        flush_suit = -1
        for card in cards:
            suit_counter[card.suit] += 1

        for i, count in enumerate(suit_counter):
            if count >= 5:
                flush_suit = i
                break
        else:
            return None

        hand_cards = []
        for i, card in enumerate(cards):
            if only_five_greatest and len(hand_cards) == 5:
                break
            if card.suit == flush_suit:
                hand_cards.append(card)
        return hand_cards

    @staticmethod
    def straight(cards: list[Card]):
        def are_consecutive_cards(li: list[Card], start: int, span: int) -> bool:
            if start + span > len(li) or len(li) < 2 or span < 2:
                return False

            # can be either asc or desc
            direction = 1 if li[start] < li[start + 1] else -1
            # check each two , start, end = start + span - 1
            for i, card in enumerate(li[start : start + span - 1]):
                if card.rank + direction != li[i + 1].rank:
                    return False

            return True

        # remove all duplicate rank cards. technically arbitrary.
        unique_cards = sorted(list(set(cards)), reverse=True)
        if len(unique_cards) < 5:
            return None

        for i, card in enumerate(unique_cards):
            # ace exception
            if card.rank == 5 and unique_cards[0] == 14:
                if are_consecutive_cards(unique_cards, i, 4):
                    return unique_cards[0:1] + unique_cards[i : i + 4]

            # consecutive check
            if are_consecutive_cards(unique_cards, i, 5):
                return unique_cards[i : i + 5]

        return None

    @staticmethod
    def three_of_a_kind(cards: list[Card], rank_occurences: list[int]):
        quads = Hand.all_n_of_a_kind(4, cards, rank_occurences)
        trips = Hand.all_n_of_a_kind(3, cards, rank_occurences)

        flattened_trips: list[Card] = []
        if len(quads) > 0:
            for group in quads:
                flattened_trips += quads[0][:3]
        if len(trips) > 0:
            for group in trips:
                flattened_trips += group

        # do any trips even exist?
        if len(flattened_trips) == 0:
            return None

        flattened_trips.sort(reverse=True)
        final_hand = flattened_trips[:3]

        for card in cards:
            if len(final_hand) >= 5:
                break
            if card not in final_hand:
                final_hand.append(card)

        return final_hand

    @staticmethod
    def two_pair(cards: list[Card], rank_occurences: list[int]):
        quads = Hand.all_n_of_a_kind(4, cards, rank_occurences)
        trips = Hand.all_n_of_a_kind(3, cards, rank_occurences)
        pairs = Hand.all_n_of_a_kind(2, cards, rank_occurences)

        flattened_pairs: list[Card] = []
        if len(quads) > 0:
            for group in quads:
                flattened_pairs += group[:2]
                flattened_pairs += group[2:]
        if len(trips) > 0:
            for group in trips:
                flattened_pairs += group[:2]
        if len(pairs) > 0:
            for group in pairs:
                flattened_pairs += group

        # do any pairs even exist?
        if len(flattened_pairs) == 0:
            return None

        flattened_pairs.sort(reverse=True)
        final_hand = flattened_pairs[:4]

        for card in cards:
            if len(final_hand) >= 5:
                break
            if card not in final_hand:
                final_hand.append(card)

        return final_hand

    @staticmethod
    def pair(cards: list[Card], rank_occurences: list[int]):
        quads = Hand.all_n_of_a_kind(4, cards, rank_occurences)
        trips = Hand.all_n_of_a_kind(3, cards, rank_occurences)
        pairs = Hand.all_n_of_a_kind(2, cards, rank_occurences)

        flattened_pairs: list[Card] = []
        if len(quads) > 0:
            for group in quads:
                flattened_pairs += group[:2]
                flattened_pairs += group[2:]
        if len(trips) > 0:
            for group in trips:
                flattened_pairs += group[:2]
        if len(pairs) > 0:
            for group in pairs:
                flattened_pairs += group

        # do any pairs even exist?
        if len(flattened_pairs) == 0:
            return None

        flattened_pairs.sort(reverse=True)
        final_hand = flattened_pairs[:2]

        final_hand = []
        for card in cards:
            if len(final_hand) >= 5:
                break
            if card not in final_hand:
                final_hand.append(card)

        return final_hand

    # cards must be >= 5. will determine best hand.
    def __init__(self, card_strs: list[str]):
        # Card list with HIGHER RANK cards first!!!
        cards = sorted(list(map(Card, card_strs)), reverse=True)

        # for straight flush and flush calculation
        all_flush = Hand.flush(cards, only_five_greatest=False)

        # for pairs, trips, quads
        # ranks as indexes from 2-14 (0 and 1 are ignored)
        rank_occurences = [0] * 15
        for card in cards:
            rank_occurences[card.rank] += 1

        straight_flush = Hand.straight(all_flush) if all_flush is not None else None
        if straight_flush is not None:
            self.cards = straight_flush
            self.type = "straight flush"
            return

        four_of_a_kind = Hand.four_of_a_kind(cards, rank_occurences)
        if four_of_a_kind is not None:
            self.cards = four_of_a_kind
            self.type = "four of a kind"
            return

        full_house = Hand.full_house(cards, rank_occurences)
        if full_house is not None:
            self.cards = full_house
            self.type = "full_house"
            return

        flush = all_flush[:5] if all_flush is not None else None
        if flush is not None:
            self.cards = flush
            self.type = "flush"
            return

        straight = Hand.straight(cards)
        if straight is not None:
            self.cards = straight
            self.type = "straight"
            return

        three_of_a_kind = Hand.three_of_a_kind(cards, rank_occurences)
        if three_of_a_kind is not None:
            self.cards = three_of_a_kind
            self.type = "three_of_a_kind"
            return

        two_pair = Hand.two_pair(cards, rank_occurences)
        if two_pair is not None:
            self.cards = two_pair
            self.type = "two_pair"
            return

        pair = Hand.pair(cards, rank_occurences)
        if pair is not None:
            self.cards = pair
            self.type = "pair"
            return

        high_card = cards[:5]
        self.cards = high_card
        self.type = "high_card"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Hand):
            raise self.comparison_err

        return self.cards == other.cards

    def __gt__(self, other: object) -> bool:
        if not isinstance(other, Hand):
            raise self.comparison_err

        # True if type is greater
        if HAND_TYPES[self.type] > HAND_TYPES[other.type]:
            return True

        # lexicographical comparison!!!
        # works because most important cards (higher rank) will be order in the right way
        # suit will not affect, Card __eq__ is only based on rank
        if HAND_TYPES[self.type] == HAND_TYPES[other.type]:
            return self.cards > other.cards

        return False
