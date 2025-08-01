# input output

import pytorch
import tensorflow
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import sklearn


class GameState:
    hi: str


class Move:
    move: str


def main(params: GameState) -> Move:
    genius_move = Move()
    genius_move.move = "all in"

    return genius_move
