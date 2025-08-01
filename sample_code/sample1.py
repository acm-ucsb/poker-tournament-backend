def fibon(n: int) -> int:
    if n <= 0:
        return 0
    elif n == 1:
        return 1
    return fibon(n - 1) + fibon(n - 2)


print("This is a test file.")
a = 5
b = 10
print(f"The sum of {a} and {b} is {a + b}.")


for i in range(10):
    print(f"Fibonacci of {i} is {fibon(i)}")

with open("file.txt", "w") as f:
    f.write("This is a test file for writing to a file.")
