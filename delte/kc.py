from math import floor

S = 32
LW = 32
ASC = 4

MR = 16
NR = 16
S_data = 8

for mr in range(1, MR + 1):
    row = []
    for nr in range(1, NR + 1):
        CAr = floor(ASC / (1 + (nr / mr)))
        Kc = floor((S * 1024 * CAr)/ (ASC * mr * S_data))
        # row.append(f"{Kc:4d}")  # floored int value, aligned width
        row.append(f"{CAr:4d}")  # floored int value, aligned width
    print(" ".join(row))