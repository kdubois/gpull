import re
import sys
import os

# Text formatting functions
bold = lambda t: style_text(t, "bold")
red = lambda t: style_text(t, "red")
green = lambda t: style_text(t, "green")
yellow = lambda t: style_text(t, "yellow")
blue = lambda t: style_text(t, "blue")


def style_text(text, effect):
    """Give a text string a certain effect, such as boldness, or a color.
    :rtype : object
    """
    ansi = {  # ANSI escape codes to make terminal cli fancy
        "reset": "\x1b[0m",
        "bold": "\x1b[1m",
        "red": "\x1b[1m\x1b[31m",
        "green": "\x1b[1m\x1b[32m",
        "yellow": "\x1b[1m\x1b[33m",
        "blue": "\x1b[1m\x1b[34m",
    }

    try:  # pad text with effect, unless effect does not exist
        if os.name != 'nt':  # ansi formatting doesn't really work on windows
            return "{}{}{}".format(ansi[effect], text, ansi['reset'])
    except KeyError:
        return text


def out(indent, msg):
    """Print a message at a given indentation level.
    :rtype : object
    """
    width = 4  # amount to indent at each level
    if indent == 0:
        spacing = "\n"
    else:
        spacing = " " * width * indent
        msg = re.sub("\\n", "\\n "+spacing, msg)  # collapse multiple spaces into one
    sys.stdout.flush()
    print(spacing + msg)
    sys.stdout.flush()
