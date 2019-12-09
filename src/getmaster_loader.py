#!/usr/bin/python3
# coding: utf-8
import zlib
import json
from base64 import standard_b64encode
from datetime import date
from collections import OrderedDict
from os.path import join as path_join

INPUT_FOLDER = 'inputs'
OUTPUT_FOLDER = 'outputs'
MASTERDATA_INPUT = [
    'getSPMaster2.csv',
    'getSPMaster3.csv',
    'getSPMaster4.csv',
    'getSPMaster6.csv',
    'getSPMaster7.csv',
]
MASTERDATA_INPUT = [path_join(INPUT_FOLDER, fname) for fname in MASTERDATA_INPUT]

class MasterDataLoader(object):
    """Loads all getMaster files and merges them into one data source."""

    def __init__(my):
        my.master_json = my.load_and_combine_getMasters()
    
    def load_and_combine_getMasters(my, b64convert=False,
            datafile_list=MASTERDATA_INPUT):
        """Finds all getMaster files and merges them into a dict."""
        master_json = OrderedDict()
        if type(datafile_list) is list:
            for infilename in datafile_list:
                latest_dict = my.parse_getMaster(infilename)
                for key, val in latest_dict.items():
                    master_json[key] = val
        else:
            try:
                print(datafile_list)
                # parse it as standlone file
                #my.parse_getMaster(datafile_list)
            except:
                print('Could not load {0} as zlib-compressed data.'.format(
                    datafile_list))
        return master_json
    
    def parse_getMaster(my, infilename, b64convert=False):
        """Loads and interprets one getMaster file."""
        with open(infilename, 'rb') as infile:
            raw_string = zlib.decompress(infile.read()).decode('utf-8')
        json_dict  = json.loads(raw_string, object_pairs_hook=OrderedDict)

        master_json = OrderedDict()
        for key, content in json_dict.items():
            if type(content) is str:
                if b64convert:
                    content = standard_b64encode(content.encode(
                        'utf-8')).decode('utf-8')
                master_json[key] = content
        return master_json

    def output_getMaster_json(my, fname=''):
        master_json = my.load_and_combine_getMasters()
        if not fname:
            fname = path_join(OUTPUT_FOLDER, 'bigjson')
        with open(fname, 'w', encoding='utf-8') as outfile:
            json.dump(master_json, outfile, indent=4, sort_keys=True,
                ensure_ascii=False)
        return master_json

    def output_getMaster_recompiled(my, fname=''):
        master_json = my.load_and_combine_getMasters(True)
        if not fname:
            fname = path_join(OUTPUT_FOLDER, 'getMaster_test')
        with open('getMaster_test', 'w', encoding='utf-8') as outfile:
            json.dump(master_json, outfile)
        
        recompiled_data = zlib.compress(json.dumps(master_json).encode('utf-8'))
        my._output_file(recompiled_data, 'getMaster', 'wb')
        return recompiled_data

    def output_getMaster_plaintext(my, fname=''):
        master_json = my.load_and_combine_getMasters()
        master_texts = 'TimeStamp:{0}\n\n'.format(
            date.today().strftime('%d-%m-%Y') ) + \
            '\n'.join( ['{0}\n\n{1}'.format(key, value) \
            for key, value in master_json.items()] )
        if not fname:
            fname = path_join(OUTPUT_FOLDER, 'getMaster.txt')
        my._output_file(master_texts, 'getMaster.txt', 'w')
        return master_texts

    def _output_file(my, data, outfilename, open_mode='wb'):
        encode = None
        if 'b' in open_mode and type(data) is str:
            data = data.encode('utf-8')
        else:
            encode = 'utf-8'

        with open(outfilename, open_mode, encoding=encode) as outfile:
            outfile.write(data)
        print('Wrote the output to {0}.'.format(outfile))

if __name__ == '__main__':
    print('Running...')
    md = MasterDataLoader()
    md.output_getMaster_plaintext()
    print('Done')
