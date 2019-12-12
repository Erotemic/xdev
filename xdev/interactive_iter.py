import ubelt as ub
import numpy as np
from . import embeding
from . import util

__all__ = ['InteractiveIter']


INDEXABLE_TYPES = (list, tuple, np.ndarray)


class InteractiveIter(object):
    """
    Choose next value interactively

    iterable should be a list, not a generator. sorry

    """
    def __init__(iiter, iterable=None, enabled=True, startx=0,
                 default_action='next', custom_actions=[], wraparound=False,
                 display_item=False, verbose=True):
        r"""
        Args:
            iterable (None): (default = None)
            enabled (bool): (default = True)
            startx (int): (default = 0)
            default_action (str): (default = 'next')
            custom_actions (list): list of 4-tuple (name, actions, help, func) (default = [])
            wraparound (bool): (default = False)
            display_item (bool): (default = True)
            verbose (bool):  verbosity flag(default = True)

        Example:
            >>> # DISABLE_DOCTEST
            >>> from xdev.interactive_iter import *  # NOQA
            >>> iterable = [1, 2, 3]
            >>> enabled = True
            >>> startx = 0
            >>> default_action = 'next'
            >>> custom_actions = []
            >>> wraparound = False
            >>> display_item = True
            >>> verbose = True
            >>> iiter = InteractiveIter(iterable, enabled, startx, default_action, custom_actions, wraparound, display_item, verbose)
            >>> for _ in iiter:
            >>>     pass

        Example:
            >>> # DISABLE_DOCTEST
            >>> # Interactive matplotlib stuff
            >>> from xdev.interactive_iter import *  # NOQA
            >>> import kwimage
            >>> import kwplot
            >>> kwplot.autompl()
            >>> keys = list(kwimage.grab_test_image.keys())
            >>> iterable = [kwimage.grab_test_image(key) for key in keys]
            >>> iiter = InteractiveIter(iterable)
            >>> for img in iiter:
            >>>     kwplot.imshow(img)
            >>>     InteractiveIter.draw()
        """
        iiter.wraparound = wraparound
        iiter.enabled = enabled
        iiter.iterable = iterable

        for actiontup in custom_actions:
            if isinstance(custom_actions, tuple):
                pass
            else:
                pass

        iiter.custom_actions = util.take_column(custom_actions, [0, 1, 2])
        iiter.custom_funcs = util.take_column(custom_actions, 3)
        iiter.action_tuples = [
            # (name, list, help)
            ('next',   ['n'], 'move to the next index'),
            ('prev',   ['p'], 'move to the previous index'),
            ('reload', ['r'], 'stay at the same index'),
            ('index',  ['x', 'i', 'index'], 'move to that index'),
            ('set',    ['set'], 'set current index value'),
            ('ipy',    ['ipy', 'ipython', 'cmd'], 'start IPython'),
            ('quit',   ['q', 'exit', 'quit'], 'quit'),
        ] + iiter.custom_actions
        default_action_index = util.take_column(iiter.action_tuples, 0).index(default_action)
        iiter.action_tuples[default_action_index][1].append('')
        iiter.action_keys = {tup[0]: tup[1] for tup in iiter.action_tuples}
        iiter.index = startx
        iiter.display_item = display_item
        iiter.verbose = verbose

    @classmethod
    def eventloop(cls, custom_actions=[]):
        """
        For use outside of iteration wrapping. Makes an interactive event loop
        custom_actions should be specified in format
        [dispname, keys, desc, func]
        """
        iiter = cls([None], custom_actions=custom_actions, verbose=False)
        print('[IITER] Begining interactive main loop')
        for _ in iiter:
            pass
        return iiter

    def __iter__(iiter):
        global LIVE_INTERACTIVE_ITER
        LIVE_INTERACTIVE_ITER = iiter
        if not iiter.enabled:
            for item in ub.ProgIter(iiter.iterable, desc='nointeract: ', freq=1, adjust=False):
                yield item
            raise StopIteration()
        assert isinstance(iiter.iterable, INDEXABLE_TYPES), 'input is not iterable'
        iiter.num_items = len(iiter.iterable)
        if iiter.verbose:
            print('[IITER] Begin interactive iteration: %r items\n' % (iiter.num_items))
        if iiter.num_items == 0:
            raise StopIteration
        # TODO: replace with ub.ProgIter
        # mark_, end_ = util_progress.log_progress(length=iiter.num_items,
        #                                          lbl='interaction: ', freq=1)
        prog = ub.ProgIter(total=iiter.num_items, desc='interaction: ', freq=1,
                           show_times=True, verbose=2)

        prog.begin()
        prompt_on_start = False
        if prompt_on_start:
            ans = iiter.prompt()
            action = iiter.handle_ans(ans)
            REFRESH_ON_BAD_INPUT = False
            if not REFRESH_ON_BAD_INPUT:
                while action is False:
                    ans = iiter.prompt()
                    action = iiter.handle_ans(ans)
            if action == 'IPython':
                embeding.embed(n=1)

        while True:
            if iiter.verbose:
                print('')
            if iiter.wraparound:
                iiter.index = iiter.index % len(iiter.iterable)
            if iiter.index >= len(iiter.iterable):
                if iiter.verbose:
                    print('Got to end the end of the iterable')
                break

            # Hack to jump to a particular index
            # (TODO: update ProgIter to handle this)
            # offset = iiter.index - prog._iter_idx
            # prog._reset_internals()
            # prog.step(iiter.index + 1)

            item = iiter.iterable[iiter.index]
            if iiter.verbose:
                print('')
            yield item
            if iiter.verbose:
                print('')

            # prog._reset_internals()
            # offset = iiter.index - prog._iter_idx
            # prog.step(offset)
            prog._reset_internals()
            if iiter.index > 0:
                prog.step(iiter.index)
            else:
                prog.display_message()

            if iiter.verbose:
                print('')
                print('[IITER] current index=%r' % (iiter.index,))
                if iiter.display_item:
                    print('[IITER] current item=%r' % (item,))
            ans = iiter.prompt()
            action = iiter.handle_ans(ans)
            REFRESH_ON_BAD_INPUT = False
            if not REFRESH_ON_BAD_INPUT:
                while action is False:
                    ans = iiter.prompt()
                    action = iiter.handle_ans(ans)
            if action == 'IPython':
                embeding.embed(n=1)

        prog.end()
        print('Ended interactive iteration')
        LIVE_INTERACTIVE_ITER = None

    def handle_ans(iiter, ans_):
        """
        preforms an actionm based on a user answer
        """
        ans = ans_.strip(' ')
        def parse_str_value(ans):
            return ' '.join(ans.split(' ')[1:])
        def chack_if_answer_was(valid_keys):
            return any([ans == key or ans.startswith(key + ' ') for key in valid_keys])
        # Handle standard actions
        if ans in iiter.action_keys['quit']:
            raise StopIteration()
        elif ans in iiter.action_keys['prev']:
            iiter.index -= 1
        elif ans in iiter.action_keys['next']:
            iiter.index += 1
        elif ans in iiter.action_keys['reload']:
            iiter.index += 0
        elif chack_if_answer_was(iiter.action_keys['index']):
            try:
                iiter.index = int(parse_str_value(ans))
            except ValueError:
                print('Unknown ans=%r' % (ans,))
        elif chack_if_answer_was(iiter.action_keys['set']):
            try:
                iiter.iterable[iiter.index] = eval(parse_str_value(ans))
            except ValueError:
                print('Unknown ans=%r' % (ans,))
        elif ans in iiter.action_keys['ipy']:
            return 'IPython'
        else:
            # Custom interactions
            for func, tup in zip(iiter.custom_funcs, iiter.custom_actions):
                key = tup[0]
                if chack_if_answer_was(iiter.action_keys[key]):
                    value  = parse_str_value(ans)
                    # cal custom function
                    print('Calling custom action func')
                    import inspect
                    argspec = inspect.getfullargspec(func)
                    if len(argspec.args) == 3:
                        # Forgot why I had custom functions take args in the first place
                        func(iiter, key, value)
                    else:
                        func()
                    # Custom funcs dont cause iteration
                    return False
            print('Unknown ans=%r' % (ans,))
            return False
        return True

    def prompt(iiter):
        def _or_phrase(list_):
            return util.conj_phrase(list(map(repr, map(str, list_))), 'or')
        msg_list = ['enter %s to %s' % (_or_phrase(tup[1]), tup[2])
                    for tup in iiter.action_tuples]
        msg = ub.indent('\n'.join(msg_list), ' | * ')
        msg = ''.join([' +-----------', msg, '\n L-----------\n'])
        # TODO: timeout, help message
        print(msg)
        ans = iiter.wait_for_input()
        return ans

    def wait_for_input(iiter):
        ans = input().strip()
        return ans

    def __call__(iiter, iterable=None):
        iiter.iterable = iterable

    @classmethod
    def draw(iiter):
        """
        in the common case where InteractiveIter is used to view matplotlib
        figures, you will have to draw the figure manually. This is a helper
        for that task.
        """
        from matplotlib import pyplot as plt
        fig = plt.gcf()
        fig.canvas.draw()
