from math import ceil, floor
from queue import PriorityQueue

from .table import Table
from .player import Player
from .signaling import EventNotifier, SignalType

class Matchmaking(EventNotifier):
    def __init__(self):
        self.tables: list[Table] = []
        self.players: list[Player] = []
        self.base_table_size = 0
        
        self.MIN_TABLE_SIZE = 5
        self.MAX_TABLE_SIZE = 8
        
        super().__init__()
    
    # TODO: finish this manual override request
    def _on_player_elimination(self) -> None:
        if not self.determine_reassign():
            return
        
        # Stop game
        self.notify(SignalType.REQUEST_STOP_GAME.value)
        
        # TODO: add a wait for all games to stop
        
        self.remove_eliminated_players()
        
        try:
            self.reassign_table()
        except ValueError:
            self.notify(SignalType.TABLE_REASSIGNMENT_ERROR.value)
            # Ask for manual override
            self.reassign_table_manual()
        
        self.close_unused_tables()
        
        # Resume game
        self.notify(SignalType.REQUEST_RESUME_GAME.value)
        
    def signal_listener(self, signal: SignalType):
        if signal.value == SignalType.PLAYER_ELIMINATED.value:
            self._on_player_elimination()
    
    def remove_eliminated_players(self) -> None:
        players = []
        
        for player in self.players:
            if player.eliminated:
                # write to db that player is eliminated
                ...
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
        
    def determine_reassign(self) -> bool:
        """
        Returns: true if table reassignment is needed, otherwise false
        """
        if len(self.tables) == 0:
            return False
        
        min_table_size = self.tables[0]
        max_table_size = self.tables[0]
        
        for table in self.tables[1:]:
            min_table_size = min(min_table_size, table.size)
            max_table_size = max(max_table_size, table.size)
        
        return abs(max_table_size - self.base_table_size) > 1 or abs(min_table_size - self.base_table_size) > 1
    
    #TODO: test this
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
            
            if (extra < 0 and self.MIN_TABLE_SIZE <= (base_size + 1) <= self.MAX_TABLE_SIZE) or \
                (self.MIN_TABLE_SIZE <= base_size <=  self.MAX_TABLE_SIZE):
                break
            
        else:
            raise ValueError("Cannot distribute players within table size constraints.")
        
        self.base_table_size = base_size
        self.tables = [Table(str(i)) for i in range(num_tables)]
        
        for i, player in enumerate(self.players):
            self.tables[i % num_tables].add_player(player)
            
        for table in self.tables:
            table.subscribe(self.signal_listener)
        
        return self.tables
    
    def assign_table_manual(self, tables: list[Table]) -> list[Table]:
        for table in tables:
            table.subscribe(self.signal_listener)
            self.tables.append(table)
        
        return self.tables
    
    # TODO: test
    def reassign_table(self) -> list[Table]:
        num_players = len(self.players)
        num_tables = len(self.tables)
        base_table_size, extras = divmod(num_players, num_tables)
        
        # TODO: test this algo
        if base_table_size < self.MIN_TABLE_SIZE:
            if ceil(num_players / (num_tables - 1)) > self.MAX_TABLE_SIZE:
                raise ValueError("Cannot redistribute players within table size constraints.")
            
            for new_num_tables in reversed(range(1, num_tables)):
                if num_players // new_num_tables >= self.MIN_TABLE_SIZE:
                    break
            
            # k is the number of tables to be removed
            k = num_tables - new_num_tables
            min_st = PriorityQueue()
            
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
            closing_tables = [table for i, table in enumerate(self.tables) if i in closing_tables_idx]
            self.tables = [table for i, table in enumerate(self.tables) if i not in closing_tables_idx]
            pool = []
            
            for table in closing_tables:
                pool.extend(table.remove_all_players())
                table.close()
            
            base_table_size, extras = divmod(num_players, new_num_tables)
            
            # some tables might have more than base_table_size + 1
            for table in self.tables:
                if table.size > base_table_size + 1:
                    pool.extend(table.remove_random_players(table.size - base_table_size - 1))
            
            for i, table in enumerate(self.tables):
                needed = max(base_table_size - table.size, 0)
                table.add_players(pool[:needed])
                pool = pool[needed:]
            
            # does the assumption hold that pool.size <= self.tables.size
            i = 0
            for player in pool:
                if self.tables[i].size == base_table_size + 1:
                    continue
                
                self.tables[i].add_player(player)
                i += 1
            
        else:
            # TODO: test this algo
            target_sizes = [base_table_size + 1 if i < extras else base_table_size for i in range(num_tables)]
            diffs = [self.tables[i].size - target_sizes[i] for i in range(num_tables)]
            pool = []
            
            for table, diff in zip(self.tables, diffs):
                if diff > 0:
                    pool.extend(table.remove_random_players(diff))
            
            for table, diff in zip(self.tables, diffs):
                if diff < 0:
                    table.add_players(pool[:-diff])
                    pool = pool[-diff:]

        return self.tables
    
    # TODO
    def reassign_table_manual(self, /) -> list[Table]:
        pass