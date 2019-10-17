from threading import Lock
from concurrent.futures import ThreadPoolExecutor

value = 0
lock = Lock()


def function(arg):
    global value
    for _ in range(arg):
        with lock:
            value += 1


def main():
    with ThreadPoolExecutor() as executor:
        for _ in range(5):
            executor.submit(function, 1000000)
    print("----------------------", value)


if __name__ == "__main__":
    main()
