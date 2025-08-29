from src.core.matchmaking import Matchmaking
from src.core.player import Player

import pytest

@pytest.mark.skip
def write_state(matchmaker: Matchmaking, name: str):
    with open(name, "w") as f:
        f.write(f"player count: {len(matchmaker.players)}\n")
        for table in matchmaker.tables:
            f.write(f"table\nid: {table.id}\nsize: {table.size}\n")
            f.write(f"{[player.id for player in table.seating]}\n")

@pytest.mark.skip
def test_basic():
    matchmaker = Matchmaking()
    matchmaker.players = [Player(i) for i in range(42)]
    matchmaker.assign_table()

    write_state(matchmaker, "tests/output/matchmaking_assignment_basic.txt")

    matchmaker.tables[1].seating.pop().is_eliminated = True
    matchmaker.tables[1].seating.pop().is_eliminated = True
    matchmaker.remove_eliminated_players()
    matchmaker.reassign_table()

    write_state(matchmaker, "tests/output/matchmaking_reassignment_1_basic.txt")

    matchmaker.tables[1].seating.pop().is_eliminated = True
    matchmaker.tables[0].seating.pop().is_eliminated = True
    matchmaker.tables[0].seating.pop().is_eliminated = True
    matchmaker.tables[0].seating.pop().is_eliminated = True
    matchmaker.tables[0].seating.pop().is_eliminated = True
    matchmaker.tables[5].seating.pop().is_eliminated = True
    matchmaker.tables[5].seating.pop().is_eliminated = True
    matchmaker.remove_eliminated_players()
    matchmaker.reassign_table()

    write_state(matchmaker, "tests/output/matchmaking_reassignment_2_basic.txt")

    for _ in range(5):
        matchmaker.tables[2].seating.pop().is_eliminated = True
    matchmaker.remove_eliminated_players()
    matchmaker.reassign_table()

    write_state(matchmaker, "tests/output/matchmaking_reassignment_3_basic.txt")
