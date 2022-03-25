import xdev


@xdev.profile
def slow_func():
    z = 0
    for i in range(10):
        for j in range(10):
            for k in range(10):
                z = (i + j * k) + z


@xdev.profile
def outer_func():

    @xdev.profile
    def inner_func1():
        a = 3
        a = a + 1
        return 1321

    @xdev.profile
    def inner_func2():
        c = 3
        return inner_func1() + 3 + c

    return inner_func2()


@xdev.profile
def main():
    slow_func()
    outer_func()


if __name__ == '__main__':
    """
    CommandLine:
        python ~/code/xdev/dev/manual_test_profile.py --profile
    """
    main()
