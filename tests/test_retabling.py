import sys
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from src.core.table import Table
from src.core.tournament import Tournament

import pytest

#@pytest.fixture
def sample_states():
    state1 = {
        "players": [
                "1", "2", "3", "4", "", "", "7", "8"
        ],
        "bet_money": [
            0, 0, 0, 0, -2, -2, 0, 0
        ],
        "big_blind": 10,
        "held_money": [
            1, 2, 3, 4, -2, -2, 7, 8
        ],
        "small_blind": 5,
        "players_cards": [
            [], [], [], [], [], [], [], []
        ],
        "community_cards": [],
        "index_to_action": 6,
        "index_of_small_blind": 6
    }

    state2 = {
        "players": [
            "9", "10", "", "11", "", "12", "13", "14"
        ],
        "bet_money": [
            0, 0, -2, 0, -2, 0, 0, 0
        ],
        "big_blind": 10,
        "held_money": [
            9, 10, -2, 11, -2, 12, 13, 14
        ],
        "small_blind": 5,
        "players_cards": [
            [], [], [], [], [], [], [], []
        ],
        "community_cards": [],
        "index_to_action": 0,
        "index_of_small_blind": 0
    }

    state3 = {
        "players": [
            "", "19", "15", "", "16", "17", "20", "18"
        ],
        "bet_money": [
            0, 0, -2, 0, -2, 0, 0, 0
        ],
        "big_blind": 10,
        "held_money": [
            9, 10, -2, 11, -2, 12, 13, 14
        ],
        "small_blind": 5,
        "players_cards": [
            [], [], [], [], [], [], [], []
        ],
        "community_cards": [],
        "index_to_action": 6,
        "index_of_small_blind": 6
    }

    state4 = {
        "players": [
            "", "19", "15", "", "16", "17", "20", "18"
        ],
        "bet_money": [
            -2, 0, 0, -2, 0, 0, 0, 0
        ],
        "big_blind": 10,
        "held_money": [
            -2, 19, 15, -2, 16, 17, 20, 18
        ],
        "small_blind": 5,
        "players_cards": [
            [], [], [], [], [], [], [], []
        ],
        "community_cards": [],
        "index_to_action": 2,
        "index_of_small_blind": 2
    }

    return {
        "7ad9ab3b-9245-434b-9013-67b702fa661f": state1, 
        "9d804ae3-7807-4d46-b2d6-83ef280f9bc6": state2, 
        "ca4390ab-4219-4ab4-9357-e18a8c91fbf5": state3, 
        "da29ab38-98a5-4b08-b08f-01733fe93307": state4
        }

def test_close(sample_states):
    t = Tournament()
    t.tables = {
        "7ad9ab3b-9245-434b-9013-67b702fa661f": Table("7ad9ab3b-9245-434b-9013-67b702fa661f"), 
        "ca4390ab-4219-4ab4-9357-e18a8c91fbf5": Table("ca4390ab-4219-4ab4-9357-e18a8c91fbf5"), 
        "da29ab38-98a5-4b08-b08f-01733fe93307": Table("da29ab38-98a5-4b08-b08f-01733fe93307")
    }

    # one table should get deleted
    t.reassign()

test_close(sample_states())




        
        

