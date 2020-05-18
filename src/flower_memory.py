#!/usr/bin/python
# coding=utf-8
from __future__ import print_function
from common import *
from entry import *

__doc__ = """Stores collective data for individual flower memories (FMs).

FM data is stored in a section of the masterData called masterSyncData.
Unlike other masterData sections, this section is layered like JSON.
It's not valid JSON though; they use single quotes instead of double quotes.
"""

class FMParser(object):
    def __init__(self, list_of_dicts=[]):
        self.parse_and_store(list_of_dicts)

    def _debug_explain(self, something, called):
        to_say = '{0} has {1} entries of type {2}'.format(
            called, len(something), str(type(something)) )
        if type(something) is dict:
            to_say += ' with keys: ' + ', '.join(something.keys())
        print(to_say)

    def parse_and_store(self, list_of_dicts):
        """Parses the masterSyncData and saves the result as a class var."""
        self._debug_explain(list_of_dicts, 'list_of_dicts')
        for idx, inner_dict in enumerate(list_of_dicts):
            self._debug_explain(inner_dict, 'inner_dict #' + str(idx))
            break
