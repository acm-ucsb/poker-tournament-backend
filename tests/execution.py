from src.util.models import Pot, GameState
from src.util.helpers import into_stdin_format

s = GameState(
    players=["danteam_id", "howdyteam_id"],
    players_cards=[["as", "2d"], ["ad, th"]],
    held_money=[100, 200],
    bet_money=[1, 2],
    community_cards=["5s", "9d", "td"],
    pots=[Pot(value=3, players=["danteam_id", "howdyteam_id"])],
    current_round="turn",
)

print(into_stdin_format(s))
