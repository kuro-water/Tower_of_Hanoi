def hanoi(n, a, c, b):
    if n > 0:
        hanoi(n - 1, a, b, c)
        print(str(a) + "to" + str(c))
        hanoi(n - 1, b, c, a)
    return

n = 3
hanoi(n, 1, 3, 2)
