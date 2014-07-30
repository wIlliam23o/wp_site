from __future__ import print_function
from collections import OrderedDict, UserDict


def safe_dict_val(dict_, keyname_, default_value=None):
    """ safely retrieve a dict value
        if key is missing, just return default value like dict.get()
        allows for several accepted key names to be used.
        like:
            no_newlines = safe_dict_value(kwargs, ('nonewlines', 'no_newlines', 'no_newline'), None)
            # if any word in ('nonewlines', 'no_newlines', 'no_newline') is found as an argument
            # the first one found is returned.
    """

    if isinstance(keyname_, (list, tuple)):
        # a list of acceptable key names can be passed.
        # this will try them all.
        keynames = dict_.keys()
        for trykey in keyname_:
            if trykey in keynames:
                return dict_[trykey]
    else:
        default_value = dict_.get(keyname_, default_value)
    return default_value


class JSDict(UserDict):

    """ A dict that allows attribute access for keys, and will return a
        default value for keys that are missing (without creating the key).
        This hides errors that would otherwise be useful for
        dict-key and attribute access, but in this case we just want a
        value or None.

        t = JSDict({'name': {'first': 'cj', 'last': 'w'}}, default=None)
        t['name']['first'] == t.name.first
        t.missing_key == None
    """

    def __init__(self, data=None, default=None):
        if data is None:
            data = {}
        self.default = default
        self.data = self._convert_data(data)

    def _convert_data(self, start=None):
        if not start:
            return start

        converted = {}
        for key, val in start.items():
            if isinstance(val, dict):
                converted[key] = JSDict(val)
            else:
                converted[key] = val
        return converted

    def __getattr__(self, attr):
        try:
            val = super().__getattribute(attr)
        except AttributeError:
            return self.__getitem__(attr)
        return val

    def __getitem__(self, item):
        try:
            val = self.data[item]
        except KeyError:
            return self.default
        return val


class PrintBlock(OrderedDict):

    """ Another dict() extension that allows you to
        build a block of text and print it out with some
        kind of aligned format.

        Initializing this with another dict() may put things
        out of order. However, passing in a list/tuple of key,value
        pairs seems to work.

        For the purposes of these examples and all help contained within this file
        I will be calling things by their names using dict terms like 'key' and 'value'.
        Example output (key + value):
            examplekey: value1
                        value2
             secondkey: value1
                        value2

        Example of basic usage:
            myfilename = "data.txt"
            myblockstring = (("warning: ", "this file is broken.", "don't use it."),
                             ("file: ", myfilename))
            myprintblock = PrintBlock(myblockstring)
            myprintblock.printblock()
            # prints:
            warning: this file is broken.
                     don't use it.
               file: data.txt

        Example of advanced usage:
            myblockstring = (("warning: ", "line1\nline2"),
                             ("tag2: ", ("line1\nline2", "line3")))
            myprintblock = PrintBlock(myblockstring)
            myprintblock.printblock()
            # prints:
            warning: line1
                     line2
               tag2: line1
                     line2
                     line3

        Adding stuff after initialization:
            # After the above 'advanced example' has been carried out:
            myprintblock['third tag: '] = ("some more", "stuff", "and lines")
            myprintblock.printblock()
            # prints:
              warning: line1
                       line2
                 tag2: line1
                       line2
                       line3
            third tag: some more
                       stuff
                       and lines
            # notice the original 'tags' have been shifted
            # to the right, to fit the new longer tag 'third tag'.

        Adding extra padding:
            myprintblock = PrintBlock((("info:", "extra spaces have been added."),
                                        ("tag2:", "this\nwill\work\nalso")))
            myprintblock.extra_spaces = 10
            myprintblock.printblock()
            # prints:
                      info:extra spaces have been added.
                      tag2:this
                           will
                           work
                           also
            # prints with 10 extra spaces in front of items.

        Newline characters:
            also note the use of '\n' characters.
            the newlines will be split and formatted,
            even inside the tuples (to one level deep, don't get crazy).
            like this:
            p = PrintBlock(("info:", ("my\nlines", "within\ntuple\nvalues"))).printblock()
            # prints:
            info:my
                 lines
                 within
                 tuple
                 values

            **  notice there is no space between 'info:' and the values.
                PrintBlock only prints what you tell it to. nothing else.

                if you want space you need to do something like:
                    p = PrintBlock(("info: ", "value1"))
                or using keyword arguments:
                    p = PrintBlock(("info", "value1", "value2"))
                    p.printblock(append_key=': ')
                        or:
                    p.printblock(prepend_val=': ')

        Extra Options:
            the iterblock() and printblock() functions have keyword arguments that allow more options
            in the formatting. see iterblock() for more detailed descriptions.
            the keyword arguments are:

                prepend_text : text to add before each line.
                prepend_key  : text to add before the key, after space-formatting.
                prepend_val  : text to add before the value, after space-formatting.
                append_key   : text to add after the key, before the value.
                append_text  : text to add after each line.
                extra_spaces : another way to set self.extra_spaces,
                               same thing as append_text=' ' * extra_spaces
                space_char   : char to use where the space character would
                               normally be used.
                               space_char="." would do:
                                   ...key1 : value1
                                   ..........value2
                                   .mykey2 : value1
                                   ..........value2

                newline_keys : adds a blank line after each key section.



    """
    class NoItemError(Exception):
        pass

    class NoValueError(Exception):
        pass

    def __init__(*args, **kwargs):
        OrderedDict.__init__(*args, **kwargs)
        self = args[0]
        self.extra_spaces = 0
        self.space_char = ' '
        self._maxlen = self._get_maxlen()

    def _get_maxlen(self):
        """ gets the longest key name, so we can align everything else to it.
        """
        if len(self) == 0:
            return self.extra_spaces

        return len(max(self.keys(), key=len)) + self.extra_spaces

    def _formatkey(self, k, **kwargs):
        """ formats the key name. applies the correct amount of self.space_char's
            and prepends/appends text where needed.
            keyword arguments:
                prepend_text   : text to add before the space-formatted keyname.
                prepend_insert : text to add before the keyname after space-formatting.
                append_text    : text to add after the space-formatted keyname.
                no_format      : ignore all space-formatting, only use prepend/append stuff.
                                 (True or False) [default: False]
        """

        prepend_text = safe_dict_val(kwargs, 'prepend_text', None)
        append_text = safe_dict_val(kwargs, 'append_text', None)
        prepend_insert = safe_dict_val(kwargs, 'prepend_insert', None)
        no_format = safe_dict_val(kwargs, 'no_format', False)
        pre_ = '' if prepend_text is None else prepend_text
        app_ = '' if append_text is None else append_text
        ins_ = '' if prepend_insert is None else prepend_insert
        # prepend insert affects space formatting, so do it first.
        k = ins_ + k + app_

        if no_format:
            formatted_ = ''
        else:
            formatted_ = (self.space_char * (self._maxlen - len(k)))
        return pre_ + formatted_ + k

    def _formatval(self, v, **kwargs):
        """ formats the value. applies the correct amount of self.space_char's
            and prepends/appends text where needed.
            keyword arguments:
                prepend_text   : text to add before space-formatted value.
                prepend_insert : text to add before the value after space-formatting.
                append_text    : text to add after space-formatted value.
                no_format      : ignore all space-formatting, only use prepend/append stuff.
                                 (True or False) [default: False]
        """

        prepend_text = safe_dict_val(kwargs, 'prepend_text', None)
        append_text = safe_dict_val(kwargs, 'append_text', None)
        prepend_insert = safe_dict_val(kwargs, 'prepend_insert', None)
        no_format = safe_dict_val(kwargs, 'no_format', False)
        pre_ = '' if prepend_text is None else prepend_text
        app_ = '' if append_text is None else append_text
        ins_ = '' if prepend_insert is None else prepend_insert
        # prepend insert affects space formatting, so do it first.
        v = ins_ + v

        if no_format:
            formatted_ = ''
        else:
            formatted_ = (self.space_char * (self._maxlen))
        return pre_ + formatted_ + v + app_

    def _fixvalues(self):
        """ parses all values, turns '\n' seperated strings into separate
            tuple items. Joins tuples and tuple-children into a single list
            of values to print per key.
            the printblock() function expects a certain format for printing
            the tracked dict, this just tries to make sure the dict is in
            the correct format. it hasn't failed me yet, if it were to fail
            it just means that the original format was WAY off the mark for
            "correct".
        """
        for key, val in self.items():
            fixedvals = []

            # strings are added, newlines are split
            if hasattr(val, 'encode'):
                if '\n' in val:
                    fixedvals = val.split('\n')
                else:
                    fixedvals = [val]
            # list/tuples are parsed one more level down.
            elif isinstance(val, (list, tuple)):
                # tuple/list children are parsed for \n's.
                for subval in val:
                    if hasattr(subval, 'encode'):
                        if '\n' in subval:
                            fixedvals += subval.split('\n')
                        else:
                            fixedvals.append(subval)
                    elif isinstance(subval, (list, tuple)):
                        fixedvals += list(subval)

            # update values
            self.update([(key, fixedvals)])

    def printblock(self, **kwargs):
        """ convenience function to print the block of text.
            keyword arguments:
                prepend_text : text to add before each line.
                prepend_key  : text to add before the key after space-formatting.
                append_key   : text to add after the key, before the value.
                prepend_val  : text to add before the value after space-formatting.
                append_text  : text to add after each line.
                extra_spaces : another way to set self.extra_spaces,
                               same thing as append_text=' ' * extra_spaces
                space_char   : char to use where the space character would
                               normally be used.
                               space_char="." would do:
                                   ...key1 : value1
                                   ..........value2
                                   .mykey2 : value1
                                   ..........value2

                newline_keys : adds a blank line after each key section.


            returns True, or raises Error if needed (see iterblock() for more detailed info).
        """

        # get keyword arguments, with safe default values, safe them in a dict.
        # ...this will be passed to iterblock()
        iterargs = {'prepend_text': safe_dict_val(kwargs, 'prepend_text', None),
                    'prepend_key': safe_dict_val(kwargs, 'prepend_key', None),
                    'append_key': safe_dict_val(kwargs, 'append_key', None),
                    'prepend_val': safe_dict_val(kwargs, 'prepend_val', None),
                    'append_text': safe_dict_val(kwargs, 'append_text', None),
                    'space_char': safe_dict_val(kwargs, 'space_char', None),
                    'extra_spaces': safe_dict_val(kwargs, 'extra_spaces', None),
                    'newline_keys': safe_dict_val(kwargs, ('newline_keys', 'newline_key'), False),
                    }

        if len(self) == 0:
            raise self.NoItemError("No items to print.")

        # cyle thru the block, preparing text where needed.
        for line_ in self.iterblock(**iterargs):
            print(line_)

    def iterblock(self, **kwargs):
        """ iterates through what would be printed with printblock().
            yields strings.
            keyword arguments:
                ** all examples shown have 'key1: ' and 'mykey: ' as keys.
                   notice the space after the keyname.
                   you must add your own ':' and space for keynames,
                   or pass append_key=': ' to regular key names like 'key1'.

            extra_spaces : adds a number extra space_char's to the beginning of each line.
                           same as append_text=(' ' * extra_spaces)
            space_char   : character to use where spaces would normally be used.
                           space_char = '.':
                               ..key1: value1
                               ........value2
                               .mykey: value1
            prepend_text : text to add before each line.
                           prepend_text = "--":
                               -- key1: value1
                               --       value2
                               --mykey: value1
            prepend_key  : text to add before each key.
                           prepend_key = "<":
                               <key1: value1
                                      value2
                              <mykey: value1
            prepend_val  : text to add before each value.
                           prepend_val = ">":
                                key1: >value1
                                      >value2
                               mykey: >value1
            append_text  : text to add after each line.
                           append_text = "!":
                                key1: value1!
                                      value2!
                               mykey: value1!
            append_key   : text to add after each key.
                           append_key = '!':
                                key1: !value1
                                       value2
                               mykey: !value1
            newline_keys : adds a blank line after each key section.
                           newline_keys = True:
                                key1: value1
                                      value2

                               mykey: value1
`       """
        if len(self) == 0:
            raise self.NoItemError("No items to iterate through.")

        # get keyword arguments, with safe default values
        prepend_text = safe_dict_val(kwargs, 'prepend_text', None)
        prepend_key = safe_dict_val(kwargs, 'prepend_key', None)
        prepend_val = safe_dict_val(kwargs, 'prepend_val', None)
        append_text = safe_dict_val(kwargs, 'append_text', None)
        append_key = safe_dict_val(kwargs, 'append_key', None)
        space_char = safe_dict_val(kwargs, 'space_char', None)
        extra_spaces = safe_dict_val(kwargs, 'extra_spaces', None)
        newline_keys = safe_dict_val(kwargs, ('newline_keys', 'newline_key'), False)

        # settings to use (if any were passed, we will use these from now on)
        if extra_spaces is not None:
            self.extra_spaces = extra_spaces
        if space_char is not None:
            self.space_char = space_char

        # update maxlen, extra_spaces may have been changed.
        # extra_spaces has changed.
        self._maxlen = self._get_maxlen()
        # prepending/appending stuff to the key messes up formatting, this will account for it.
        if prepend_key is not None:
            self._maxlen += len(prepend_key)
        if append_key is not None:
            self._maxlen += len(append_key)

        # make values compatible with this method
        # (we are overwriting values here)
        self._fixvalues()

        # iterate through keys
        for keyname, values in self.items():
            if not values:
                raise self.NoValueError("No values in: {}".format(keyname))

            # Yield first line (because the key and value should be in the same line)
            keyformat_args = {'prepend_text': prepend_text,
                              'prepend_insert': prepend_key,
                              'append_text': append_key}
            valformat_args = {'prepend_insert': prepend_val,
                              'append_text': append_text,
                              'no_format': True}
            yield (self._formatkey(keyname, **keyformat_args) + self._formatval(values[0], **valformat_args))

            # yield all children (without key)
            if len(values) > 1:
                for val in values[1:]:
                    # values was a single tuple/list of strings.
                    if hasattr(val, 'encode'):
                        valformat_args = {'append_text': append_text,
                                          'prepend_text': prepend_text,
                                          'prepend_insert': prepend_val}
                        yield (self._formatval(val, **valformat_args))
                    # values contained tuple/list children
                    elif isinstance(val, (list, tuple)):
                        for subval in val:
                            valformat_args = {'append_text': append_text,
                                              'prepend_text': prepend_text,
                                              'prepend_insert': prepend_val}
                            yield (self._formatval(subval, **valformat_args))

            # add a blank line after this key?
            if newline_keys:
                yield ''


def printx(s, endline='\n'):
    if not hasattr(s, 'encode'):
        s = str(s)

    print(s, end=endline)
    return s

if __name__ == "__main__":
    myblockstring = [["warning", "don't do this mang"],
                     ["also", ["dont", "do", "this", "either"]]
                     ]

    d = PrintBlock(myblockstring)
    format_args = {'append_text': '!',
                   'append_key': ': ',
                   'prepend_val': '..',
                   'newline_key': True}
    d.printblock(**format_args)
