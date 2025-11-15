import math
import random

max_size = 8
teams = random.sample(range(1, 99), 30)

print(teams, "\n")

num_groups = math.ceil(len(teams) / max_size)
print(f"num_groups: {num_groups}")
chunk_len = len(teams) // num_groups
rem = len(teams) % num_groups

for i in range(num_groups):
    idx = i * chunk_len + (i if i < rem else rem)
    table_sublist = teams[idx : idx + chunk_len + (1 if i < rem else 0)]
    print(table_sublist, len(table_sublist))
