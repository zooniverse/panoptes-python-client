from __future__ import absolute_import, division, print_function
from builtins import range

import functools


ITERABLE_TYPES = (
    list,
    set,
    tuple,
)

MISSING_POSITIONAL_ERR = 'Required positional argument (pos 1) not found'

try:
    from numpy import ndarray
    ITERABLE_TYPES = ITERABLE_TYPES + (ndarray,)
except ImportError:
    pass


def isiterable(v):
    return isinstance(v, ITERABLE_TYPES)


def split(to_batch, batch_size):
    if type(to_batch) == set:
        to_batch = tuple(to_batch)
    for batch in [
        to_batch[i:i + batch_size]
        for i in range(0, len(to_batch), batch_size)
    ]:
        yield batch


def batchable(func=None, batch_size=100):
    @functools.wraps(func)
    def do_batch(*args, **kwargs):
        if len(args) <= 1:
            raise TypeError(MISSING_POSITIONAL_ERR)
        _batch_size = kwargs.pop('batch_size', batch_size)

        _self = args[0]
        to_batch = args[1]
        args = args[2:]
        if not isiterable(to_batch):
            to_batch = [to_batch]

        if isinstance(to_batch, set):
            to_batch = list(to_batch)

        for batch in split(to_batch, _batch_size):
            if _self is None:
                func(batch, *args, **kwargs)
            else:
                func(_self, batch, *args, **kwargs)

    # This avoids us having to call batchable wherever it's used, so we can
    # just write:
    #   @batchable
    #   def func(self, ...):
    #
    # Rather than:
    #   @batchable()
    #   def func(self, ...):
    #
    # While still allowing this:
    #   @batchable(batch_size=10)
    #   def func(self, ...):
    if func is None:
        return functools.partial(batchable, batch_size=batch_size)

    return do_batch
