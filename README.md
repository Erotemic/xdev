# xdev
Miscellaneous interactive debugging tools for developers


Perhaps I should just use `ipdb` but I often just like to directly embed with IPython whenever I want:

```python
import xdev
xdev.embed()
```


Or wherever I want whenever there is an exception.

```python

import xdev
with xdev.embed_on_exception_context:
    some_code()

```

I don't feel like I need `ipdb`'s other features. 


I also like to 

```python
def func(a=1, b=2, c=3):
    """
    Example:
        >>> from this.module import *  # import contextual namespace
        >>> import xinspect
        >>> globals().update(xinspect.get_func_kwargs(func))  # populates globals with default kwarg value
        >>> print(a + b + c)
        6
    """
```

But I know these things are a little dirty. 

But these aren't production practises. These are development tricks and life
hacks to make working faster.


Also see `xinspect` for things like `autogen_imports`
