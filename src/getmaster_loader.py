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

    def load_and_combine_getMasters(my, datafile_list=[]):
        """Finds all getMaster files and merges them into a dict."""
        if not datafile_list:
            datafile_list = my._get_default_inputs()

        master_json = OrderedDict()
        for infilename in datafile_list:
            latest_dict = my.parse_getMaster(infilename)
            if type(latest_dict) is str:
                # For backwards compatibility, plain text is loadable
                return latest_dict
            # Remove sections without data
            latest_dict = {k:v for k, v in latest_dict.items() if v}
            for key, val in latest_dict.items():
                if type(val) is list:
                    print('Key {0} is a list. Loading this is not supported.'.format(
                        key))
                    continue
                if key not in master_json:
                    master_json[key] = ''
                master_json[key] += val

        my.master_json = master_json
        return master_json
    
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
        
        json_dict = json.loads(raw_string, object_pairs_hook=OrderedDict)
        # Decoding done. Store the data in an understandable structure.
        master_json = OrderedDict()
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
