"""Word completion for GNU readline 2.0.

This requires the latest extension to the readline module. The completer
completes keywords, built-ins, globals, and file names in a selectable
namespace (which defaults to __main__); when completing NAME.NAME...,
it evaluates (!) the expression up to the last dot and completes its
attributes.

It's very cool to do "import sys" type "sys.", hit the
completion key (twice), and see the list of names defined by the
sys module!

Tip: to use the tab key as the completion key, call

    readline.parse_and_bind("tab: complete")

Notes:

- Exceptions raised by the completer function are *ignored* (and
generally cause the completion to fail).  This is a feature -- since
readline sets the tty device in raw (or cbreak) mode, printing a
traceback wouldn't work well without some complicated hoopla to save,
reset and restore the tty state.

- The evaluation of the NAME.NAME... form may cause arbitrary
application defined code to be executed if an object with a
__getattr__ hook is found.  Since it is the responsibility of the
application (or the user) to enable this feature, I consider this an
acceptable risk.  More complicated expressions (e.g. function calls or
indexing operations) are *not* evaluated.

- GNU readline is also used by the built-in functions input() and
raw_input(), and thus these also benefit/suffer from the completer
features.  Clearly an interactive application can benefit by
specifying its own completer function and using raw_input() for all
its input.

- When the original stdin is not a tty device, GNU readline is never
used, and this module (and the readline module) are silently inactive.

"""

import __builtin__
import __main__

__all__ = ["Completer"]

class Completer:
    def __init__(self, namespace = None):
        """Create a new completer for the command line.

        Completer([namespace]) -> completer instance.

        If unspecified, the default namespace where completions are performed
        is __main__ (technically, __main__.__dict__). Namespaces should be
        given as dictionaries.

        Completer instances should be used as the completion mechanism of
        readline via the set_completer() call:

        readline.set_completer(Completer(my_namespace).complete)
        """

        if namespace and not isinstance(namespace, dict):
            raise TypeError,'namespace must be a dictionary'

        # Don't bind to namespace quite yet, but flag whether the user wants a
        # specific namespace or to use __main__.__dict__. This will allow us
        # to bind to __main__.__dict__ at completion time, not now.
        if namespace is None:
            self.use_main_ns = 1
        else:
            self.use_main_ns = 0
            self.namespace = namespace

        # The cache of matches for a particular text fragment.
        self.matches = []

    def complete(self, text, state):
        """Return the next possible completion for 'text'.

        This is called successively with state == 0, 1, 2, ... until it
        returns None.  The completion should begin with 'text'.  Any text
        with a period (.) will match as an attribute.  Any text that begins
        with a single or double quote will match using file name expansion.

        """
        if self.use_main_ns:
            self.namespace = __main__.__dict__

        # For the first call with this set of text, compute all possible
        # matches and store them in a member variable.  Subsequent calls
        # will then iterate through this set of matches.
        if state == 0:
            if ('"' in text) or ("'" in text):
                self.matches = self.file_matches(text)
            elif "." in text:
                self.matches = self.attr_matches(text)
            else:
                self.matches = self.global_matches(text)
        if state < len(self.matches):
            return self.matches[state]
        else:
            return None

    def _callable_postfix(self, val, word):
        if hasattr(val, '__call__'):
            word = word + "("
        return word

    def global_matches(self, text):
        """Compute matches when text is a simple name.

        Return a list of all keywords, built-in functions and names currently
        defined in self.namespace that match.

        """
        import keyword
        matches = []
        n = len(text)
        for word in keyword.kwlist:
            if word[:n] == text:
                matches.append(word)
        for nspace in [__builtin__.__dict__, self.namespace]:
            for word, val in nspace.items():
                if word[:n] == text and word != "__builtins__":
                    matches.append(self._callable_postfix(val, word))
        return matches

    def attr_matches(self, text):
        """Compute matches when text contains a dot.

        Assuming the text is of the form NAME.NAME....[NAME], and is
        evaluatable in self.namespace, it will be evaluated and its attributes
        (as revealed by dir()) are used as possible completions.  (For class
        instances, class members are also considered.)

        WARNING: this can still invoke arbitrary C code, if an object
        with a __getattr__ hook is evaluated.

        """
        import re
        import types

        # Setup the regular expression for attributes
        m = re.match(r"(\w+(\.\w+)*)\.(\w*)", text)
        if not m:
            return []

        # Group 1 is the class name, group 3 is the attribute text
        expr, attr = m.group(1, 3)
        try:
            thisobject = eval(expr, self.namespace)
        except Exception:
            return []

        # get the content of the object, except __builtins__
        words = dir(thisobject)
        if "__builtins__" in words:
            words.remove("__builtins__")

        # If this type is a class instance, use the __class__ member to
        # get the dictionary of attributes
        if type(thisobject) == types.InstanceType:
            if hasattr(thisobject, '__class__'):
                words.append('__class__')
                words.extend(get_class_members(thisobject.__class__))
        elif type(thisobject) == types.ClassType:
            words.extend(get_class_members(thisobject))
        else:
            words.extend(dir(thisobject))

        # Build the full matching text from class.attribute matches
        matches = []
        n = len(attr)
        for word in words:
            if word[:n] == attr and hasattr(thisobject, word):
                val = getattr(thisobject, word)
                word = self._callable_postfix(val, "%s.%s" % (expr, word))
                matches.append(word)
        return matches

    def file_matches(self, text):
        """Compute matches when text is a file name.

        Expects a leading single or double quote character in the text.
        Will expand a leading ~ or ~user to a valid home directory.
        Will expand a leading $VAR to an environment variable name."""
        import glob
        import os

        # save the leading quote character so we can re-add it later
        quote = text[0]
        # strip the leading quote character
        path = text[1:]

        # expand a tilde (~) or a leading environment variable in the text
        path = os.path.expanduser( path )
        path = os.path.expandvars( path )

        # append the any match character to send to the glob routine
        path = path + "*"

        # use the glob module to get all of the matches
        rawMatches = glob.glob( path )

        # re-prefix the text with the quoting character and append the correct
        # terminating character depending on the type of match that was found.
        # Directories are terminated with '/' and files with an ending quote.
        matches = []
        for entry in rawMatches:
            if os.path.isdir( entry ):
                matches.append( quote + entry + os.sep )
            elif os.path.isfile( entry ):
                matches.append( quote + entry + quote )
            else:
                matches.append( quote + entry )
        return matches

def get_class_members(klass):
    ret = dir(klass)
    if hasattr(klass,'__bases__'):
        for base in klass.__bases__:
            ret = ret + get_class_members(base)
    return ret

try:
    import readline
except ImportError:
    pass
else:
    readline.set_completer(Completer().complete)
