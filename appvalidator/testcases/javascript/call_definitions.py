import math
import re

import traverser as js_traverser
import predefinedentities
import utils
from jstypes import *
from appvalidator.constants import BUGZILLA_BUG

# Function prototypes should implement the following:
#  wrapper : The JSWrapper instace that is being called
#  arguments : A list of argument nodes; untraversed
#  traverser : The current traverser object


# Global object function definitions:
def string_global(wrapper, arguments, traverser):
    if (not arguments or
        not arguments[0].get_literal_value()):
        return JSWrapper(JSObject(), traverser=traverser)
    value = utils.get_as_str(arguments[0].get_literal_value())
    return JSWrapper(value, traverser=traverser)


def array_global(wrapper, arguments, traverser):
    return JSWrapper(JSArray(arguments), traverser=traverser)


def number_global(wrapper, arguments, traverser):
    if not arguments:
        return JSWrapper(0, traverser=traverser)
    try:
        return JSWrapper(float(arguments[0].get_literal_value()), traverser=traverser)
    except (ValueError, TypeError):
        return utils.get_NaN(traverser)


def boolean_global(wrapper, arguments, traverser):
    if not arguments:
        return JSWrapper(False, traverser=traverser)
    return JSWrapper(bool(arguments[0].get_literal_value()),
                     traverser=traverser)


def python_wrap(func, args, nargs=False):
    """
    This is a helper function that wraps Python functions and exposes them to
    the JS engine. The first parameter should be the Python function to wrap.
    The second parameter should be a list of tuples. Each tuple should
    contain:

     1. The type of value to expect:
        - "string"
        - "num"
     2. A default value.
    """

    def _process_literal(type_, literal):
        if type_ == "string":
            return utils.get_as_str(literal)
        elif type_ == "num":
            return utils.get_as_num(literal)
        return literal

    def wrap(wrapper, arguments, traverser):
        params = []
        if not nargs:
            # Handle definite argument lists.
            for type_, def_value in args:
                if arguments:
                    parg = arguments[0]
                    arguments = arguments[1:]

                    passed_literal = parg.get_literal_value()
                    passed_literal = _process_literal(type_, passed_literal)
                    params.append(passed_literal)
                else:
                    params.append(def_value)
        else:
            # Handle dynamic argument lists.
            for arg in arguments:
                literal = arg.get_literal_value()
                params.append(_process_literal(args[0], literal))

        traverser._debug("Calling wrapped Python function with: (%s)" %
                             ", ".join(map(str, params)))
        try:
            output = func(*params)
        except:
            # If we cannot compute output, just return nothing.
            output = None

        return JSWrapper(output, traverser=traverser)

    return wrap


def math_log(wrapper, arguments, traverser):
    """Return a better value than the standard python log function."""
    if not arguments:
        return JSWrapper(0, traverser=traverser)

    arg = utils.get_as_num(arguments[0].get_literal_value())
    if arg == 0:
        return JSWrapper(float('-inf'), traverser=traverser)

    if arg < 0:
        return JSWrapper(traverser=traverser)

    arg = math.log(arg)
    return JSWrapper(arg, traverser=traverser)


def math_round(wrapper, arguments, traverser):
    """Return a better value than the standard python round function."""
    if not arguments:
        return JSWrapper(0, traverser=traverser)

    arg = utils.get_as_num(arguments[0].get_literal_value())
    # Prevent nasty infinity tracebacks.
    if abs(arg) == float("inf"):
        return arguments[0]

    # Python rounds away from zero, JS rounds "up".
    if arg < 0 and int(arg) != arg:
        arg += 0.0000000000000001
    arg = round(arg)
    return JSWrapper(arg, traverser=traverser)
