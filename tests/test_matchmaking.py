import sys
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

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


def test_assign_table():
    matchmaker = Matchmaking()

    matchmaker.players = [Player(str(i)) for i in range(50)]
    tables = matchmaker.assign_table()
    
    assert len(tables) == 7
    assert len([1 for table in tables if table.size == 7]) == 6 # 6 tables of 7
    assert len([1 for table in tables if table.size == 8]) == 1 # 1 table of 8
    print("Assignment Tests passed")

    # reassign tests

    reassign = matchmaker.determine_reassign()
    assert reassign[0] == False

    tables.sort(key= lambda table:table.size, reverse=True)
    tables[0].seating.append(Player("50"))
    matchmaker.update_players()

    reassign = matchmaker.determine_reassign()
    assert reassign[0] == True and reassign[1] == 2, "upper bound faulty"

    tables[0].seating = tables[0].seating[:8]
    matchmaker.update_players()
    temp = tables[1].seating[2]
    tables[1].seating[2].is_eliminated = True
    matchmaker.remove_eliminated_players()


    reassign = matchmaker.determine_reassign()
    assert reassign[0] == True and reassign[1] == 2, "lower bound faulty"

    tables[1].seating[2] = temp
    tables[0].remove_random_players(2)
    matchmaker.update_players()


    reassign = matchmaker.determine_reassign()
    assert reassign[0] == True and reassign[1] == 1, "lower num tables faulty"

    print("Determine Reassign Tests Passed")

def test_reassign_1():
    matchmaker = Matchmaking()
    matchmaker.players = [Player(str(i)) for i in range(50)]
    tables = matchmaker.assign_table()

    tables[0].remove_random_players(2)
    tables[2].remove_random_players(3)
    tables[3].remove_random_players(4)
    tables[4].remove_random_players(1)
    tables[1].remove_random_players(1)
    matchmaker.update_players()
    assert len(matchmaker.players) == 39

    reassign, type = matchmaker.determine_reassign()

    assert reassign == True and type == 1

    print("Initial test passed")



    # tables = matchmaker.reassign_table_1()
    # print("\n")
    # for i, table in enumerate(tables):
    #     print(f"{i}: ", end="")

    #     for player in table.seating:
    #         if player:
    #             print(f"--{player.id}--", end = " ")
    #         else:
    #             print("-N/A-", end = " ")

    #     print()

    tables = matchmaker.reassign_table_1()

    # for i, table in enumerate(tables):
    #     print(f"{i}: ", end="")

    #     for player in table.seating:
    #         if player:
    #             print(f"--{player.id}--", end = " ")
    #         else:
    #             print("-N/A-", end = " ")

    #     print()

    assert len(tables) == 5
    assert len([1 for table in tables if len(table.players) == 8]) == 4
    assert len([1 for table in tables if len(table.players) == 7]) == 1

    print("Test passed!")

    # print("\n\n")
    

    # tables = matchmaker.reassign_table_1()


test_reassign_1()

    
