#!/usr/bin/python3
# coding: utf-8
import zlib
import json
from base64 import standard_b64encode
from datetime import date
from collections import OrderedDict
MASTERDATA_INPUT = ['getSPMaster2.csv','getSPMaster3.csv','getSPMaster4.csv','getSPMaster6.csv','getSPMaster7.csv']

class MasterData(object):
    def __init__(my, datafile_list=MASTERDATA_INPUT):
        my.datafile_list = datafile_list
        my.masterJSON  = OrderedDict()
        my.masterTexts = "TimeStamp:{0}\n".format(date.today().strftime("%d-%m-%Y"))
        my.b64Convert  = False
    
    def load_getMaster(my):
            if type(my.datafile_list) is list:
                for infilename in my.datafile_list:
                    my.parse_getMaster(infilename)
            elif my.datafile_list.endswith(".txt"):
                    print(my.datafile_list)
                    #my.parse_getMaster_plaintext(infilename)
            else:
                try:
                    print(my.datafile_list)
                    #my.parse_getMaster(my.datafile_list) # try to parse it as standlone file
                except:
                    print('Could not load {0} as zlib-compressed data.'.format(infilename))
    
    def parse_getMaster(my, infilename):
        with open(infilename, 'rb') as infile:
            raw_string = zlib.decompress(infile.read()).decode("utf-8")
            json_list  = json.loads(raw_string, object_pairs_hook=OrderedDict)

            for key in json_list:
                content = json_list[key]
                if not key in my.masterJSON: 
                    my.masterJSON.update({key:None})
                if type(content) is str:
                    if my.b64Convert:
                            content = standard_b64encode(content.encode("utf-8")).decode("utf-8")
                    my.masterJSON[key] = content
        
    def print_getMaster_json(my):
        my.load_getMaster()
        with open("bigjson", 'w', encoding='UTF-8') as outfile:
            json.dump(my.masterJSON, outfile, indent=4, sort_keys=True, ensure_ascii=False)

    def recompile_getMaster(my):
        my.b64Convert = True
        my.load_getMaster()
        
        with open("getMaster_test", 'w', encoding='UTF-8') as outfile:
            json.dump(my.masterJSON, outfile)
        
        recompiled_data = zlib.compress(json.dumps(my.masterJSON).encode("utf-8"))
        output_file(recompiled_data,'getMaster','wb')
        my.b64Convert = False
        
    def print_getMaster_plaintext(my):
        my.load_getMaster()
        for key in my.masterJSON:
            my.masterTexts += '\n{0}\n\n{1}'.format(key, my.masterJSON[key])
        output_file(my.masterTexts,'getMaster.txt','w')

def output_file(data, outfilename, open_mode='wb'):
    if open_mode.find('b') > -1:
        encode = None
        if type(data) is str:
            data = data.encode('UTF-8')
    else:
        encode='UTF-8'
    
    with open(outfilename, open_mode, encoding=encode) as outfile:
        outfile.write(data)

if __name__ == '__main__':
    MasterData = MasterData()
    MasterData.print_getMaster_plaintext()
