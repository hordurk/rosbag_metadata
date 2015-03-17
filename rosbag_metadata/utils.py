# The MIT License (MIT)
#
# Copyright (c) 2015 Hordur K. Heidarsson
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import os
import sys

# http://code.activestate.com/recipes/577098/
def command_line_query(question, default=None, validate=None, style="compact"):
    """Ask the user a question using raw_input() and looking something
    like this ("compact" style, the default, `_` is the cursor):

        QUESTION [DEFAULT]: _
        ...validation...

    or this ("verbose" style):

        QUESTION
        Hit <Enter> to use the default, DEFAULT.
        > _
        ...validation...

    @param question {str} The question to ask.
    @param default {str} Optional. The default value if non is given.
    @param validate {str|function} is either a string naming a stock
        validator

            not-empty       Ensure the user's answer is not empty.
            yes-or-no       Ensure the user's answer is 'yes' or 'no'.
                            ('y', 'n' and any capitalization are
                            also accepted)
            int             Answer is an integer.

        or a callback function with this signature:
            validate(answer) -> normalized-answer
        It should raise `ValueError` to indicate an invalid answer.

        By default no validation is done.
    @param style {str} is a name for the interaction style, either "compact"
        (the default) or "verbose". See the examples above.
    @returns {str} The normalized answer.
    """
    if isinstance(validate, (str, unicode)):
        if validate == "not-empty":
            def validate_not_empty(answer):
                if not answer:
                    raise ValueError("You must enter some non-empty value.")
                return answer
            validate = validate_notempty
        elif validate == "yes-or-no":
            def validate_yes_or_no(answer):
                normalized = {"yes":"yes", "y":"yes", "ye":"yes",
                    "no":"no", "n":"no"}
                try:
                    return normalized[answer.lower()]
                except KeyError:
                    raise ValueError("Please enter 'yes' or 'no'.")
            validate = validate_yes_or_no
        elif validate == "int":
            def validate_int(answer):
                try:
                    int(answer)
                except ValueError:
                    raise ValueError("Please enter an integer.")
                else:
                    return answer
            validate = validate_int
        else:
            raise ValueError("unknown stock validator: '%s'" % validate)

    def indented(text, indent=' '*4):
        lines = text.splitlines(1)
        return indent + indent.join(lines)

    if style == "compact":
        prompt = question
        if default is not None:
            prompt += " [%s]" % (default or "<empty>")
        prompt += ": "
    elif style == "verbose":
        sys.stdout.write(question + '\n')
        if default:
            sys.stdout.write("Hit <Enter> to use the default, %r.\n" % default)
        elif default is not None:
            default_str = default and repr(default) or '<empty>'
            sys.stdout.write("Hit <Enter> to leave blank.\n")
        prompt = "> "
    else:
        raise ValueError("unknown query style: %r" % style)

    while True:
        if True:
            answer = raw_input(prompt)
        else:
            sys.stdout.write(prompt)
            sys.stdout.flush()
            answer = sys.stdout.readline()
        if not answer and default:
            answer = default
        if validate is not None:
            orig_answer = answer
            try:
                norm_answer = validate(answer)
            except ValueError, ex:
                sys.stdout.write(str(ex) + '\n')
                continue
        else:
            norm_answer = answer
        break
    return norm_answer

def query(question, default=None):
    return command_line_query(question, default=default)

# http://code.activestate.com/recipes/577058/
def query_yes_no(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the userself.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True, "no": False, "n": False}

    if default is None:
        prompt = " [y/n] "
    elif not valid.has_key(default):
        raise ValueError("invalid default answer: '%s'" % default)
    elif valid[default]:
        prompt = " [Y/n] "
    else:
        prompt = " [y/N] "

    while True:
        sys.stdout.write(question + prompt)
        choice = raw_input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' (or 'y' or 'n').\n")


def split_bagname(name):
    (path, rest) = os.path.split(name)
    m = re.match(r'(.*)_?(\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2})_?(\d+)?\.bag', rest)
    (prefix, date, seq) = m.groups()
    return (path, prefix, date, seq)

def make_bagname(path, prefix, date, seq=None):
    res = prefix+'_'+date
    if seq:
        res = res + '_' + seq
    res = res + '.bag'
    return os.path.join(path, res)
