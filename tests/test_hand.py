from src.core.hand import Hand, HandType

straight_flush = Hand(["2h", "3h", "4h", "5h", "6h"])
ace_quads = Hand(["as", "ad", "ac", "ah", "td", "2h", "3h"])
full_house = Hand(["2h", "2d", "2c", "3h", "3c"])
flush = Hand(["ah", "2h", "3h", "4h", "6h"])
straight = Hand(["6c", "8h", "5h", "7d", "2c", "9s"])


flush_higher_kicker = Hand(["ah", "5h", "3h", "4h", "6h"])


def test_between_types():
    assert straight_flush > ace_quads
    assert ace_quads > full_house
    assert full_house > flush
    assert flush > straight


def test_within_type():
    assert flush_higher_kicker > flush


def test_hand_type():
    assert straight_flush.type == HandType.straight_flush
    assert ace_quads.type == HandType.four_of_a_kind
    assert flush.type == HandType.flush
