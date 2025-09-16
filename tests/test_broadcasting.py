from src.core import broadcasting


def test_all():
    broadcasting.UpdateCode.TABLE_CLOSED == broadcasting.TableClosedPayload()
    broadcasting.PlayerJoinedPayload(player_id="124", seat=0)
    broadcasting.PlayerLeftPayload(player_id="3")
    broadcasting.ButtonMovedPayload(button_seat=0, small_blind_seat=3, big_blind_seat=5)
    broadcasting.PlayerActedPayload(player_id="243", action="CALL", amount=13)
    broadcasting.HandDealtPayload(player_id="135faw", cards=[])
    broadcasting.CCDealtPayload(cards=[])
    broadcasting.ShowdownPayload()
    broadcasting.PayoutPayload(payouts={"asdfe13": 134, "afe3": 4})
    broadcasting.BlindAmountUpdatePayload()
    broadcasting.PlayerEliminatedPayload(player_id="ae13r")
    broadcasting.NewHandPayload()
    broadcasting.GameMessagePayload(message="Hello World")
