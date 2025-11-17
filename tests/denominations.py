def round_by_denominations(raise_size: int, denominations: list[int] | None = None):
    if denominations is None:
        denominations = [25, 100, 500, 1000]

    result = {}
    for denom in sorted(denominations, reverse=True):
        count = raise_size // denom
        if count > 0:
            result[denom] = count
            raise_size -= denom * count
    return result


print(round_by_denominations(7458))
