from math import ceil, floor
from queue import PriorityQueue
import uuid

from src.core.table import Table
from src.core.player import Player

from dataclasses import dataclass, field
from typing import Any

from random import sample

@dataclass(order=True)
class PrioritizedItem:
    priority: int
    count: int
    item: Any=field(compare=False)

class Matchmaking:
    def __init__(self, players: list[Player] = []):
        self.tables: list[Table] = []
        self.players: list[Player] = players
        self.base_table_size = 6

        self.MIN_TABLE_SIZE = 5
        self.MAX_TABLE_SIZE = 8

        super().__init__()

    # TODO: finish this manual override request
    def _on_player_elimination(self, _=None) -> None:
        reassign, type = self.determine_reassign()
        if not reassign:
            return

        # TODO: Stop game

        # TODO: add a wait for all games to stop
        self.remove_eliminated_players()

        if type == 1:
            try:
                _ = self.reassign_table_1()
            except ValueError:
                # TODO: notify table rebalancing error
                # Ask for manual override
                self.reassign_table_manual()

            self.close_unused_tables() # doesn't matter for type 2 as no tables will be closed

            reassign, type = self.determine_reassign() # should never be (true, 1), can only be 
                                                       # (true, 2) or (false , 1)

        if type == 2:
            try:
                _ = self.reassign_tables_2()
            except ValueError:
                # TODO: notify table rebalancing error
                # Ask for manual override
                self.reassign_table_manual()

        # TODO: Resume game

    def add_players(self, players: list[Player]):
        self.players.extend(players)
    
    # Used for testing
    def update_players(self):
        players = []
        for table in self.tables:
            for player in table.seating:
                if player:
                    players.append(player)

        self.players = players

    def remove_eliminated_players(self) -> None:
        players = []

        for player in self.players:
            if player.is_eliminated:
                # write to db that player is eliminated
                # also need to remove player from any table they are in
                ...
                table = [table for table in self.tables if player in table.seating][0] # find table
                table.seating[table.seating.index(player)] = None # removed
            else:
                players.append(player)

        self.players = players

    def close_unused_tables(self) -> None:
        tables = []

        for table in self.tables:
            if table.size == 0:
                table.close()
            else:
                tables.append(table)

        self.tables = tables

    def determine_reassign(self) -> tuple[bool, int]:
        """
        Return: Type 1 reassign -> close a table
        Return: Type 2 reassign -> shift players around to make it more even
        Returns: true if table reassignment is needed, otherwise false
        """
        # no tables can't reassign
        if len(self.tables) == 0:
            return False

        min_table_size = self.tables[0].size
        max_table_size = self.tables[0].size

        for table in self.tables[1:]:
            min_table_size = min(min_table_size, table.size)
            max_table_size = max(max_table_size, table.size)

        # difference between any two tables is at most one
        # or one less table needed

        num_players = len(self.players)
        min_tables = ceil(num_players / self.MAX_TABLE_SIZE)
        max_tables = floor(num_players / self.MIN_TABLE_SIZE)

        # Choose the smallest number of tables that fulfill table size constrains and table size only differ by 1
        for num_tables in range(min_tables, max_tables + 1):
            base_size, extra = divmod(num_players, num_tables)
            # if theres some leftover and add one to each table is within the constraints 
            # or if there aren't any extras and within constraints
            if (
                extra > 0
                and self.MIN_TABLE_SIZE <= (base_size + 1) <= self.MAX_TABLE_SIZE
            ) or (self.MIN_TABLE_SIZE <= base_size <= self.MAX_TABLE_SIZE):
                break

        if num_tables == max_tables + 1:
            raise ValueError("Cannot distribute players within table size constraints.")
        
        if num_tables < len(self.tables):
            return (True, 1)
        if max_table_size - min_table_size > 1:
            return (True, 2)
        return (False, 1) # arbitrary

    def assign_table(self) -> list[Table]:
        """
        Raises:
            ValueError: when we can't assign players neatly in the table size constrains, use `assign_table_manual` after error is thrown.
        """
        num_players = len(self.players)

        min_tables = ceil(num_players / self.MAX_TABLE_SIZE)
        max_tables = floor(num_players / self.MIN_TABLE_SIZE)

        # Choose the smallest number of tables that fulfill table size constrains and table size only differ by 1
        for num_tables in range(min_tables, max_tables + 1):
            base_size, extra = divmod(num_players, num_tables)
            # if theres some leftover and add one to each table is within the constraints 
            # or if there aren't any extras and within constraints
            if (
                extra > 0
                and self.MIN_TABLE_SIZE <= (base_size + 1) <= self.MAX_TABLE_SIZE
            ) or (self.MIN_TABLE_SIZE <= base_size <= self.MAX_TABLE_SIZE):
                break

        if num_tables == max_tables + 1:
            raise ValueError("Cannot distribute players within table size constraints.")

        self.base_table_size = base_size
        self.tables = [Table(table_id=str(uuid.uuid1()), name=str(i)) for i in range(num_tables)] # initialize tables

        # round robin table assignments
        for i, player in enumerate(self.players):
            self.tables[i % num_tables].add_player(player)

        for table in self.tables:
            self._subscribe_to(table)

        return self.tables
    
    def _subscribe_to(self, table: Table) -> None:
        pass

    def assign_table_manual(self, tables: list[Table]) -> list[Table]:
        for table in tables:
            self._subscribe_to(table)
            self.tables.append(table)

        return self.tables

    """
    In the case where there's more tables open than necessary --> close the smallest ones
    and reassign those players to other tables based on seating priority
        -> players with higher priority in the closed tables get the higher priority seats in
            the other tables
    """
    def reassign_table_1(self) -> list[Table]:
        num_players = len(self.players)
        num_tables = len(self.tables)
        base_table_size, extras = divmod(num_players, num_tables)

        # TODO: test this algo
        if base_table_size < self.MIN_TABLE_SIZE:
            if ceil(num_players / (num_tables - 1)) > self.MAX_TABLE_SIZE:
                raise ValueError(
                    "Cannot redistribute players within table size constraints."
                )

        # new number of tables --> want the smallest number of new tables
        for new_num_tables in (range(1, num_tables)):
            if self.MAX_TABLE_SIZE >= ceil(num_players/new_num_tables) >= self.MIN_TABLE_SIZE:
                break

        # k is the number of tables to be removed
        k = num_tables - new_num_tables
        min_st = PriorityQueue()
        # want the k smallest tables
        for i, table in enumerate(self.tables):
            if i < k:
                min_st.put((-table.size, i))
                continue

            size_max, i_max = min_st.get()

            if -size_max > table.size:
                min_st.put((-table.size, i))

            else:
                min_st.put((size_max, i_max))

        # min_st should have all the tables that should close
        closing_tables_idx = [min_st.get()[1] for _ in range(k)]
        closing_tables = [
            table for i, table in enumerate(self.tables) if i in closing_tables_idx
        ] # the tables to be closed
        self.tables = [
            table
            for i, table in enumerate(self.tables)
            if i not in closing_tables_idx
        ] # the remaining tables
            
        pool = PriorityQueue() # max heap based off current seat position

        for i, table in zip(closing_tables_idx, closing_tables):
            size = self.MAX_TABLE_SIZE # max possible size of the table
            start = (table.big_blind + 1)%size if table.current_player else (table.button+3)%size
            
            priority = 0
            # add to heap based off of seat position
            for seat in range(start, start + size):
                priority += 1
                if table.seating[seat%size]:
                    pool.put(PrioritizedItem(priority=-priority, 
                                             count=i,
                                             item=table.seating[seat%size]))


        base_table_size, extras = divmod(num_players, new_num_tables)
        self.base_table_size = base_table_size

        seats = PriorityQueue()
        for i, table in enumerate(self.tables):
            size = self.MAX_TABLE_SIZE # max possible size of the table
            start = (table.big_blind + 1)%size if table.current_player else (table.button+3)%size

            needed = base_table_size - table.size
            priority = 9
            # only want just the right amount of seats per table to get the max table size to 
            # base_table_size
            for seat in range (start + 2*size - 1, start + size - 1, -1):
                if needed <= 0:
                    break
                priority -= 1
                if not table.seating[seat%size]:
                    seats.put(PrioritizedItem(priority=-priority, 
                                              count=i,
                                              item = [i, seat%size])) # in a max heap by seat priority
                    needed -= 1

        # assign players in pool to seats by priority
        while not (pool.qsize() == 0) and not (seats.qsize() == 0):
            player = pool.get()
            seat = seats.get()
            self.tables[seat.item[0]].seating[seat.item[1]] = player.item

        # for extra players
        if not (pool.qsize() == 0):
            for i, table in enumerate(self.tables):
                size = self.MAX_TABLE_SIZE # max possible size of the table
                start = (table.big_blind + 1)%size if table.current_player else (table.button+3)%size

                needed = 1 # need one more seat from each table
                priority = 9
                #want the highest priority seats
                for seat in range (start + 2*size - 1, start + size - 1, -1):
                    if needed <= 0:
                        break
                    priority -= 1
                    if not table.seating[seat%size]:

                        seats.put(PrioritizedItem(priority=-priority, count=i, item = [i, seat%size])) # in a max heap by seat priority
                        needed -= 1

            while not (pool.qsize() == 0):
                player = pool.get()
                seat = seats.get()
                self.tables[seat.item[0]].seating[seat.item[1]] = player.item

        return self.tables
    
    """
    In the case where there's too many or too little people in one or more tables
    --> randomly select players in tables where there's too many people
    --> move them to seats at empty tables with the highest priority
    """
    def reassign_tables_2(self):
        num_players = len(self.players)
        num_tables = len(self.tables)

        # want extra number of tables with players_per_table + 1
        players_per_table, extra = divmod(num_players, num_tables)
        self.base_table_size = players_per_table
        if (extra > 0 and players_per_table + 1 > self.MAX_TABLE_SIZE) or players_per_table < self.MIN_TABLE_SIZE:
            raise ValueError("Need more tables to fit seating restraints")
        
        pool = []
        for table in self.tables:
            if table.size > players_per_table:
                pool.extend(table.remove_random_players(table.size - players_per_table))
        for table in self.tables:
            if table.size < players_per_table:
                needed = players_per_table - table.size
                table.add_players(pool[:needed])
                pool = pool[needed:]

        if len(pool) != 0:
            population = range(len(self.tables)) # all tables will have the same number of people atp
            tables = sample(population, len(pool))

            for table, player in zip(tables, pool):
                self.tables[table].add_player(player)

        return self.tables


    # TODO
    def reassign_table_manual(self, /) -> list[Table]:
        pass
