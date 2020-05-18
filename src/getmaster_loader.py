#!/usr/bin/python3
# coding: utf-8
import zlib
import json
from datetime import date
from collections import OrderedDict
from os import scandir, makedirs
from os.path import isfile, dirname, normpath, exists, abspath, join as path_join

__doc__ = """Handles the initial loading of any getMaster files.

getmaster_loader is for decoding the data.
parse_master is for interpreting and organizing the data.
getmaster_outputter is for outputting the organized data for the Wikia.

If there are multiple files to load, their data is blindly combined.

This class handles loading, but not parsing the data. The intention is
that any parsers should expect the same data format no matter how
the data was saved.

Simplistic data output is provided by this class.
"""

INPUT_FOLDER = 'inputs'
OUTPUT_FOLDER = 'outputs'

class MasterDataLoader(object):
    """Loads all getMaster files and merges them into one data source."""

    def __init__(my):
        my.compat_mode = False
        my.master_json = None
        my.master_text = ''

        loaded = my.load_and_combine_getMasters()
        if type(loaded) is str:
            # For backwards compatibility, allow saving plain text
            my.master_text = loaded
            my.compat_mode = True
        else:
            my.master_json = loaded

    def _get_default_inputs(self):
        if not exists(INPUT_FOLDER):
            raise FileNotFoundError('Please put the getMaster files into ' + \
                abspath(INPUT_FOLDER))
        return [fil for fil in scandir(INPUT_FOLDER) if fil.is_file()]

    def _append_dict_entry(self, the_dict, key, to_append):
        if key not in the_dict:
            if type(to_append) is str:
                the_dict[key] = ''
            else:
                the_dict[key] = []
        the_dict[key] += to_append

    def load_and_combine_getMasters(self, datafile_list=[]):
        """Finds all getMaster files and merges them into a dict."""
        if not datafile_list:
            datafile_list = self._get_default_inputs()

        master_json = {}
        for infilename in datafile_list:
            latest_dict = self.parse_getMaster(infilename)
            if type(latest_dict) is str:
                # For backwards compatibility, plain text is loadable
                return latest_dict
            # Remove sections without data
            for key, val in self._recursive_build_tree(latest_dict).items():
                self._append_dict_entry(master_json, key, val)
            # print('master_json is size ' + str(len(master_json)))
        self.master_json = master_json
        return master_json

    # This static vars and hidden fn are for debugging FM parsing
    first_fm_output = True
    listed = set()
    def __debug_say_append(self, tosay):
        if tosay not in self.listed:
            # print('Appending key ' + tosay)
            self.listed.add(tosay)

    first_fm_output = True
    def __debug_output_fm_decodes(self, val):
        fname = path_join(OUTPUT_FOLDER, 'masterSyncDataDecoded.json')
        # By default, we are APPENDING new data to the existing file
        open_mode = 'a'
        if self.first_fm_output:
            self.first_fm_output = False
            # Overwrite the old file with new contents
            open_mode = 'w'
        self._output_file(str(val), fname, open_mode)

    def _parse_master_sync_list(self, val):
        """Parses the split-up list of dicts that compose masterSyncData.

        masterSyncData holds the FM data.
        I don't know if I will be using this fn in the future.
        """

        # For debugging, output the whole thing to a file
        self.__debug_output_fm_decodes(val)

        # Remove empty entries
        val = [i for i in val if i]
        sub_merged = {}

        # The rest of this function is unused
        """
        for inner_dict_or_list in val:
            inner_tree = self._recursive_build_tree(inner_dict_or_list)
            # Merge inner_tree into sub_merged
            for inner_key, inner_val in inner_tree.items():
                self.__debug_say_append(inner_key)
                self._append_dict_entry(
                    sub_merged, inner_key, inner_val)
        # "val" is now reformated to be a dict
        """

        return sub_merged

    def _recursive_build_tree(self, my_dict):
        """Parses the whole tree of data stored in a master data file."""
        merged = {}
        assert type(my_dict) in (dict, OrderedDict), \
            'Data type of param is wrong: ' + str(type(my_dict))
        # Remove empty entries
        my_dict = {k:v for k, v in my_dict.items() if v}
        for key, val in my_dict.items():
            if type(val) is list:
                # We could assign "val" to the fn output.
                # Currently, I'm not using this fn for anything
                self._parse_master_sync_list(val)
            # Merge sub_merged into merged
            self._append_dict_entry(merged, key, val)
            # print('merged is size ' + str(len(merged)))
        return merged

    def parse_getMaster(my, pathlike):
        """Loads and interprets one getMaster file.
        
        Expects zlib compressed JSON as the file contents.
        However, plain text is supported as for backwards compatibility.

        Returns json if the the file was json, or text if it was plain text.
        """
        
        with open(pathlike, 'rb') as infile:
            raw_string = infile.read()
        
        # Decode the data.
        try:
            print('Loading {0} as zlib'.format(pathlike.name))
            raw_string = zlib.decompress(raw_string)
        except zlib.error:
            print('Failed, so loading {0} as utf-8 encoded text'.format(
                pathlike.name))
        
        raw_string = raw_string.decode('utf-8')
        pre_decoded = type(raw_string) is str and raw_string.startswith('TimeStamp')
        if pre_decoded:
            print('This text file is the final, decoded master data. Deprecated!')
            return raw_string
        
        json_dict = json.loads(raw_string)
        # Decoding done. Store the data in an understandable structure.
        master_json = {}
        for key, content in json_dict.items():
            master_json[key] = content
        return master_json

    def output_getMaster_json(my, fname=''):
        if my.compat_mode:
            output_getMaster_plaintext(fname)
            return

        if not fname:
            fname = path_join(OUTPUT_FOLDER, 'bigjson')
        with open(fname, 'w', encoding='utf-8') as outfile:
            json.dump(my.master_json, outfile, indent=4, sort_keys=True,
                ensure_ascii=False)

    # TODO: This method acts very differently from the rest. Refactor it.
    def output_getMaster_recompiled(my, fname=''):
        if my.compat_mode:
            output_getMaster_plaintext(fname)
            return

        temp_json = OrderedDict()
        for key, content in my.master_json.items():
            temp_json[key] = standard_b64encode(
                content.encode('utf-8')).decode('utf-8')
        if not fname:
            fname = path_join(OUTPUT_FOLDER, 'getMaster_test')
        with open('getMaster_test', 'w', encoding='utf-8') as outfile:
            json.dump(temp_json, outfile)
        
        # Output a second time for whatever reason...
        # TODO: Is this even necessary?
        recompiled_data = zlib.compress(json.dumps(temp_json).encode('utf-8'))
        fname = path_join(OUTPUT_FOLDER, 'getMaster')
        my._output_file(recompiled_data, fname, 'wb')
        return recompiled_data

    def output_getMaster_plaintext(my, fname=''):
        master_texts = ''
        if my.compat_mode:
            print('WARNING: Outputting in compatibility mode')
            master_texts = my.master_text
        else:
            master_texts = 'TimeStamp:{0}\n\n'.format(
                date.today().strftime('%d-%m-%Y') ) + \
                '\n'.join( ['{0}\n\n{1}'.format(key, value) \
                for key, value in my.master_json.items()] )

        if not fname:
            fname = path_join(OUTPUT_FOLDER, 'getMaster.txt')
        my._output_file(master_texts, fname, 'w')
        return master_texts

    def _output_file(my, data, outfilename, open_mode='wb'):
        encode = None
        if 'b' in open_mode and type(data) is str:
            data = data.encode('utf-8')
        else:
            encode = 'utf-8'

        makedirs(dirname(outfilename), exist_ok=True)
        with open(outfilename, open_mode, encoding=encode) as outfile:
            outfile.write(data)
        print('Wrote the output to {0}'.format(outfilename))

if __name__ == '__main__':
    print('Running...')
    md = MasterDataLoader()
    md.output_getMaster_plaintext()
    print('Done')
