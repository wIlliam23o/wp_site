""" Welborn Productions - Utilities - Decorators
    ..provides global decorators that can be used anywhere.
    -Christopher Welborn 2014
"""
import functools
import sys
import traceback


def log_errors(log=None):
    """ Decorator that automatically logs traceback info.
        Arguments:
            log  : A method that accepts a string as it's first argument.
                   If None is passed, print() will be used instead.
                   The idea is to use it like: @logcall(log=logger.error)
    """

    def wrapper(func):
        wrapsig = 'inner', 'ret = func(*args, **kwargs)'
        
        @functools.wraps(func)
        def inner(*args, **kwargs):
            try:
                ret = func(*args, **kwargs)
                return ret
            except Exception:
                typ, val, tb = sys.exc_info()
                tbinfo = traceback.extract_tb(tb)
                linefmt = ('Error in {fname}, {funcname}(), '
                           'line {num}: {txt}\n{typ}: {msg}')
                reporter = print if log is None else log.error
                for filename, lineno, funcname, txt in tbinfo:
                    if wrapsig == (funcname, txt):
                        # This wrapper doesnt count.
                        continue
                    # Build format() args from the tb info.
                    fmtargs = {
                        'fname': filename,
                        'funcname': funcname,
                        'num': lineno,
                        'txt': txt,
                        'typ': typ,
                        'msg': val,
                    }
                    # Report the error.
                    reporter(linefmt.format(**fmtargs))
                # Reraise the error, we're not silencing anything.
                raise
        return inner
    return wrapper
