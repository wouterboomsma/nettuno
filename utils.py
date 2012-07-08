# utils.py --- Utility classes and functions
# Copyright (C) 2012 Sandro Bottaro, Christian Holzgraefe, Wouter Boomsma
#
# This file is part of Nettuno
#
# Nettuno is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Nettuno is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Nettuno.  If not, see <http://www.gnu.org/licenses/>.

import optparse

class SubOptions:
    '''Class for defining sub-options used for the command line parser'''

    def __init__(self, key_value_dict):
        '''Constructor. Initialized using a dictionary of (name, description) pairs'''
        self.dict = key_value_dict

    def __repr__(self):
        '''String representation'''
        output = "\n"
        for item in self.dict.items():
            output += "  %s: %s\n" % item
        return output


class HelpFormatterInnerOptions(optparse.IndentedHelpFormatter):
    '''Overrides default HelpFormatter for optparse command line parser
to provide nicer printing of inner options'''

    def format_option(self, option):
        # The help for each option consists of two parts:
        #   * the opt strings and metavars
        #     eg. ("-x", or "-fFILENAME, --file=FILENAME")
        #   * the user-supplied help string
        #     eg. ("turn on expert mode", "read data from FILENAME")
        #
        # If possible, we write both of these on the same line:
        #   -x      turn on expert mode
        #
        # But if the opt string list is too long, we put the help
        # string on a second line, indented to the same column it would
        # start in if it fit on the first line.
        #   -fFILENAME, --file=FILENAME
        #           read data from FILENAME
        import textwrap
        result = []
        opts = self.option_strings[option]
        opt_width = self.help_position - self.current_indent - 2
        if len(opts) > opt_width:
            opts = "%*s%s\n" % (self.current_indent, "", opts)
            indent_first = self.help_position
        else:                       # start help on same line as opts
            opts = "%*s%-*s  " % (self.current_indent, "", opt_width, opts)
            indent_first = 0
        result.append(opts)
        if option.help:
            help_text = self.expand_default(option)
            help_paragraphs = help_text.splitlines()
            first_paragraph = True
            for help_paragraph in help_paragraphs:
                help_lines = textwrap.wrap(help_paragraph, self.help_width)
                if len(help_lines) > 0:
                    if first_paragraph:
                        result.append("%*s%s\n" % (indent_first, "", help_lines[0]))
                    else:
                        result.append("%*s%s\n" % (self.help_position, "", help_lines[0]))
                    result.extend(["%*s%s\n" % (self.help_position, "", line)
                                   for line in help_lines[1:]])
                else:
                    result.append("\n")
                first_paragraph=False
        elif opts[-1] != "\n":
            result.append("\n")
        return "".join(result)


def vararg_callback(option, opt_str, value, parser):
    '''A callback for the option parser allowing a variable number of arguments.'''

    value = []

    for arg in parser.rargs:

        # stop on --foo like options
        if arg[:2] == "--" and len(arg) > 2:
            break

        # stop on -a, but not on -3 or -3.0
        if arg[:1] == "-" and len(arg) > 1 and not floatable(arg):
            break

        value.append(arg)
    del parser.rargs[:len(value)]

    parser.values.ensure_value(option.dest, []).append(value)
    

class CallbackHasMetaVarOption(optparse.Option):
    '''Overrides default optparse Option class, giving callbacks a metavar description'''
    ALWAYS_TYPED_ACTIONS = optparse.Option.ALWAYS_TYPED_ACTIONS + ('callback',)
