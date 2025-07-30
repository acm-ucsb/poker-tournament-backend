def main():
    file1 = open("func1.py", "r")
    file1_code = file1.read()
    file1.close()

    values = {"a": 2}
    exec(file1_code, globals(), values)
    exec(file1_code, globals(), values)
    print(values)
    


if __name__ == "__main__":
    main()
