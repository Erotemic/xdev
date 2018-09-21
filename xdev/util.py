def bubbletext(text, font='cybermedium'):
    """
    Uses pyfiglet to create bubble text.

    Args:
        font (str): default=cybermedium, other fonts include: cybersmall and
            cyberlarge.

    References:
        http://www.figlet.org/

    Example:
        >>> bubble_text = bubbletext('TESTING BUBBLE TEXT', font='cybermedium')
        >>> print(bubble_text)
    """
    try:
        import pyfiglet
    except ImportError:
        print('Missing pyfiglet')
        return text
    else:
        bubble_text = pyfiglet.figlet_format(text, font=font)
        return bubble_text


def conj_phrase(list_, cond='or'):
    """
    Joins a list of words using English conjunction rules

    Args:
        list_ (list):  of strings
        cond (str): a conjunction (or, and, but)

    Returns:
        str: the joined cconjunction phrase

    References:
        http://en.wikipedia.org/wiki/Conjunction_(grammar)

    Example:
        >>> list_ = ['a', 'b', 'c']
        >>> result = conj_phrase(list_, 'or')
        >>> print(result)
        a, b, or c

    Example1:
        >>> list_ = ['a', 'b']
        >>> result = conj_phrase(list_, 'and')
        >>> print(result)
        a and b
    """
    if len(list_) == 0:
        return ''
    elif len(list_) == 1:
        return list_[0]
    elif len(list_) == 2:
        return ' '.join((list_[0], cond, list_[1]))
    else:
        condstr = ''.join((', ' + cond, ' '))
        return ', '.join((', '.join(list_[:-2]), condstr.join(list_[-2:])))


def take_column(list_, colx):
    """ iterator version of take_column """
    if isinstance(colx, list):
        # multi select
        return [[row[colx_] for colx_ in colx] for row in list_]
    else:
        return [row[colx] for row in list_]
