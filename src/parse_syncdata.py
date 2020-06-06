#!/usr/bin/python
# coding=utf-8
from common import *

__doc__ = """Parses the mastershyncData which holds FMs and maybe more.

Stores collective data for individual flower memories (FMs).

FM data is stored in a section of the masterData called masterSyncData.
Unlike other masterData sections, this section is layered like JSON.
It's not valid JSON though; they use single quotes instead of double quotes.
"""

# This is an example of the decoded masterSyncData after prettifying as JSON.
# Only two entries are kept at each deepest level.
# This is intended for inspection and unit testing.
sample_pretty_input = """
[
    {
        'dataType': 'master',
        'tableName': 'master_flower_memorys',
        'action': 'reset',
        'data': [
            {
                'id': 1,
                'itemId': 1000000,
                'name': '歌声は風に乗って',
                'readingName': 'うたごえはかぜにのって',
                'rarity': 6,
                'orderNum': 1,
                'growthType': 'normal',
                'initHitPoint': 135,
                'hitPointPerLevel': 90,
                'initAttack': 45,
                'attackPerLevel': 25,
                'initDefense': 36,
                'defensePerLevel': 10,
                'description': 'るるる　ららら\n箒のリズムに、歌声が乗る。\n小さく淡く、けれど確かな、希望の歌。\n面と向かって歌うのは、\nまだちょっとだけ恥ずかしいけど、\nいつか貴方にこの歌が、この歌の意味が届きますように。'
            },
            {
                'id': 2,
                'itemId': 1000001,
                'name': 'その足元にご用心？',
                'readingName': 'そのあしもとにごようじん',
                'rarity': 6,
                'orderNum': 2,
                'growthType': 'normal',
                'initHitPoint': 120,
                'hitPointPerLevel': 90,
                'initAttack': 66,
                'attackPerLevel': 25,
                'initDefense': 18,
                'defensePerLevel': 10,
                'description': 'いらっしゃいませ、美味しいよ☆\n煮てよし、焼いてよし、生はちょっと危険かも？\nキノコ祭りは大盛況、出張レストランも絶好調。\nそんな空気と美味しいキノコに浮き足立って、\nああ、彼女は忘れてしまっていたのです。\n不幸を引き寄せてしまう、哀しい己の体質を……。'
            },
            {
                'id': 3,
                'itemId': 1000002,
                'name': 'はにかみ屋の勇気',
                'readingName': 'はにかみやのゆうき',
                'rarity': 6,
                'orderNum': 3,
                'growthType': 'normal',
                'initHitPoint': 131,
                'hitPointPerLevel': 90,
                'initAttack': 42,
                'attackPerLevel': 25,
                'initDefense': 39,
                'defensePerLevel': 10,
                'description': 'あなたと二人、素敵なカフェへ。\n内気で弱気で、目も合わせられなかったりするけれど、\n前髪をちょっと避けたその先に、\nあなたの優しいまなざしが見えたから。\n今日はほんのちょっとだけ、\n大胆な事をしてみたいのです。'
            }
        ]
    },
    {
        'dataType': 'master',
        'tableName': 'master_flower_memory_over_limit_groups',
        'action': 'reset',
        'data': [
            {
                'id': 1,
                'flowerMemoryId': 1,
                'overLimitStep': 0,
                'memoryScore': 5
            },
            {
                'id': 2,
                'flowerMemoryId': 1,
                'overLimitStep': 1,
                'memoryScore': 5
            }
        ]
    },
    {
        'dataType': 'master',
        'tableName': 'master_flower_memory_raritys',
        'action': 'reset',
        'data': [
            {
                'id': 1,
                'rarity': 3,
                'maxOverLimitStep': 0,
                'saleGameMoney': 1,
                'synthesisGameMoneyPerLevel': 200,
                'expPerLevel': 0,
                'baseMaxLevel': 1,
                'releaselimitGameMoneyPerStep': 0
            },
            {
                'id': 2,
                'rarity': 4,
                'maxOverLimitStep': 4,
                'saleGameMoney': 2000,
                'synthesisGameMoneyPerLevel': 200,
                'expPerLevel': 1644,
                'baseMaxLevel': 10,
                'releaselimitGameMoneyPerStep': 20000
            }
        ]
    },
    {
        'dataType': 'master',
        'tableName': 'master_abilitys',
        'action': 'reset',
        'data': [
            {
                'id': 101,
                'name': '(自身)挑発+ダメージ軽減16%',
                'effectId': 2101,
                'description': '戦闘中、敵全員の攻撃対象を自身に引きつけ、敵から受けるダメージが16%減少する',
                'value1': 1600,
                'value2': 0,
                'value3': 100,
                'value4': 0
            },
            {
                'id': 102,
                'name': '(自身)挑発+ダメージ軽減17%',
                'effectId': 2101,
                'description': '戦闘中、敵全員の攻撃対象を自身に引きつけ、敵から受けるダメージが17%減少する',
                'value1': 1700,
                'value2': 0,
                'value3': 100,
                'value4': 0
            }
        ]
    },
    {
        'dataType': 'master',
        'tableName': 'master_flower_memorys_abilitys',
        'action': 'reset',
        'data': [
            {
                'id': 1,
                'flowerMemoryId': 1,
                'overLimitStep': 0,
                'abilityId': 102
            },
            {
                'id': 2,
                'flowerMemoryId': 1,
                'overLimitStep': 1,
                'abilityId': 102
            }
        ]
    },
    {
        'dataType': 'master',
        'tableName': 'master_flower_memory_materials',
        'action': 'reset',
        'data': [
            {
                'id': 1,
                'itemId': 1100001,
                'rarity': 1,
                'saleGameMoney': 100,
                'synthesisExperience': 795,
                'categoryId': 1,
                'description': 'フラワーメモリー強化合成専用、EXPが獲得できる'
            },
            {
                'id': 2,
                'itemId': 1100002,
                'rarity': 3,
                'saleGameMoney': 100,
                'synthesisExperience': 1590,
                'categoryId': 1,
                'description': 'フラワーメモリー強化合成専用、EXPが獲得できる'
            }
        ]
    },
    {
        'dataType': 'master',
        'tableName': 'master_flower_memory_growth_types',
        'action': 'reset',
        'data': [
            {
                'id': 1,
                'growthType': 'ex_late',
                'toLevel': 10,
                'coefficient': '0.8'
            },
            {
                'id': 2,
                'growthType': 'ex_late',
                'toLevel': 20,
                'coefficient': '0.9'
            }
        ]
    }
]
""".strip()

class SyncDataParser(object):
    def __init__(self, list_of_dicts=[]):
        self.synced = self.parse(list_of_dicts)

    def _debug_explain(self, something, called):
        to_say = '{0} has {1} entries of type {2}'.format(
            called, len(something), str(type(something)) )
        if type(something) is dict:
            to_say += ' with keys: ' + ', '.join(something.keys())
        print(to_say)

    def parse(self, list_of_dicts):
        out_all_tables = {}
        """Parses the masterSyncData and saves the result as a class var."""
        # self._debug_explain(list_of_dicts, 'list_of_dicts')
        for in_inner_dict in list_of_dicts:
            # Note: We only expect a table named "master_flower_memorys"
            in_table_name = in_inner_dict['tableName']
            out_this_table = {}
            if in_table_name in out_all_tables:
                out_this_table = out_all_tables[in_table_name]
            else:
                out_all_tables[in_table_name] = out_this_table 

            # self._debug_explain(in_inner_dict, 'in_inner_dict #' + str(idx))
            # Although there may be multiple keys, we only care about "data"
            # self._debug_explain(in_inner_dict['data'][0],
            #     'in_inner_dict[\'data\'][0] is ' + \
            #     str(in_inner_dict['data'][0]))
            in_deepest_list_of_dicts = in_inner_dict['data']
            # There should be a ton of list entries here. All are dicts
            for in_data_dict in in_deepest_list_of_dicts:
                # self._debug_explain(in_data_dict, 'in_data_dict is ' + \
                #     str(in_data_dict))
                # These are the data entries we need to save

                # Chances are, this is the ID of an FM
                in_item_id = in_data_dict['id']

                # Init this table if necessary
                # It might be like out_all_tables['master_flower_memorys']['3']
                out_id_to_data = {}
                if in_item_id in out_this_table:
                    out_id_to_data = out_this_table[in_item_id]
                else:
                    out_this_table[in_item_id] = out_id_to_data

                # in_data_dict is an example of a DEEPEST internal entry
                for key, val in in_data_dict.items():
                    out_id_to_data[key] = val
        return out_all_tables
