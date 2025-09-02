from src.core.table import Table
from src.core.player import Player
from src.core.card import Card

import pytest

def init_table() -> tuple[Table, list[Player]]:
    table = Table("1")
    players = [None] * 8
    players[0] = Player("0", 1000)
    players[2] = Player("2", 1000)
    players[3] = Player("3", 1000)
    players[6] = Player("6", 1000)
    players[7] = Player("7", 1000)
    
    table.seating = players
        
    table.players[0].chips = 0
    table.players[0].contribution = 300
    
    table.players[1].contribution = 500
    
    table.players[2].chips = 0
    table.players[2].contribution = 200
    
    table.players[3].contribution = 300
    table.players[3].has_folded = True
    
    table.pot = 1300
    
    return (table, players)

def test_blinds():
    table, _ = init_table()
    
    assert table.blinds == (2, 3)
    
    table.button = 6
    
    assert table.blinds == (7, 0)

def test_players():
    table, players = init_table()
    assert table.players == [player for player in players if player]
    assert table.players != players

def test_get_vacant():
    table, _ = init_table()
    
    assert table.get_vacant() == [1, 5, 4]
    
    table.button = 3
    
    assert table.get_vacant() == [5, 4, 1]

def test_payout():
    table, _ = init_table()
    
    assert table.payout_helper([table.players[2]]) == 800
    assert table.players[2].chips == 800
    assert table.pot == 500
    
    assert table.payout_helper([table.players[0], table.players[1]], 800) == 500
    assert table.players[0].chips == 150
    assert table.players[1].chips == 1350
    assert table.pot == 0
    
    table, _ = init_table()
    assert table.payout_helper([table.players[0], table.players[1]]) == 1300
    assert table.players[0].chips == 550
    assert table.players[1].chips == 1750
    assert table.pot == 0
    
    table, _ = init_table()
    assert table.payout_helper([table.players[0]]) == 1100
    assert table.payout_helper([table.players[1], table.players[2], table.players[3]], 1100) == 200
    assert table.players[0].chips == 1100
    assert table.players[1].chips == 1200
    assert table.players[2].chips == 0
    assert table.players[3].chips == 1000
    
    table, _ = init_table()
    table.players[0].contribution = 100
    table.players[1].contribution = 100
    table.players[2].contribution = 100
    table.players[3].contribution = 100
    table.pot = 400
    
    assert table.payout_helper([table.players[0], table.players[1], table.players[3]]) == 400
    assert table.players[0].chips == 133
    assert table.players[1].chips == 1134
    assert table.players[2].chips == 0
    assert table.players[3].chips == 1133