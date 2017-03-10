import functools


def batchable(func=None, batch_size=100):
    def do_batch(*args, **kwargs):
        _batch_size = kwargs.pop('batch_size', batch_size)
        if type(args[0]) in (list, set, tuple):
            _self = None
            to_batch = args[0]
            args = args[1:]
        else:
            _self = args[0]
            to_batch = args[1]
            args = args[2:]

        for _batch in [
            to_batch[i:i+_batch_size]
            for i in xrange(0, len(to_batch), _batch_size)
        ]:
            if _self is None:
                func(_batch, *args, **kwargs)
            else:
                func(_self, _batch, *args, **kwargs)

    if func is None:
        return functools.partial(batchable, batch_size=batch_size)
    return do_batch
