#!/usr/bin/env python
# coding: utf-8
import codecs
import sys
import requests
try:
	from bs4 import BeautifulSoup
except ImportError:
	print('Error: BeautifulSoup 4 is not installed.')

DEFAULT_INFILENAME = 'src.php'
DEFAULT_OUTFILENAME = 'result.txt'
SRC_URL = u'http://xn--eckq7fg8cygsa1a1je.xn--wiki-4i9hs14f.com/index.php?%E7%B7%8A%E6%80%A5%E4%BB%BB%E5%8B%99%E3%80%80%E3%81%8A%E8%BF%94%E3%81%97%E3%82%B9%E3%82%A4%E3%83%BC%E3%83%84%E5%A4%A7%E4%BD%9C%E6%88%A6/%E3%82%AB%E3%83%BC%E3%83%89%E3%82%81%E3%81%8F%E3%82%8A'

__doc__ = u"""Mass translates card flip cheat sheets for Flower Knight Girl.

The sheets are downloaded from a page in the Japanese wiki, specifically:
{0}
The output is written to a file and is intended for our English Wiki.

Purely to satiate non-Python savvy users, a "Press Enter to continue" is added
to this script.

Support is geared towards Python 3, so Python 2 may not work.
""".format(SRC_URL)

major_ver = sys.version_info.major
if major_ver < 3:
	# This is probably Python 2.
	# Make input behave like Python3; don't interpret the inputted text.
	input = raw_input

event_char = u'キヌサヤ'

# Normalize the text to be translated.
typo_fixes = [
# Turn full-width alphanumeric symbols into half-width alphanumeric symbols.
(u'　', ' '),
(u'（', '('),
(u'）', ')'),
(u'０', '0'),
(u'１', '1'),
(u'２', '2'),
(u'５', '5'),
(u'Ｇ', 'G'),
(u'ｇ', 'G'),
(u'×', 'x'),
(u'，', ''),
(u'、', ''),
# For gold
('1,000', '1000'),
('1,500', '1500'),
('2,000', '2000'),
('2,500', '2500'),
('4,500', '4500'),
('5,000', '5000'),
('10,000', '10000'),
('20,000', '20000'),
('25,000', '25000'),
('50,000', '50000'),
('g', 'G'),
# For gacha seeds
(u'中级', u'中級'), # typo
# For Manyus, Blums, and Fururus
(u'歳', u'才'),
(u'赤の', u'赤'),
(u'青の', u'青'),
(u'紫の', u'紫'),
(u'黄の', u'黄'),
(u'龍', u'竜'),
(u'ブルム', u'進化竜'),
(u'プルム', u'進化竜'),
# For Ampules
(u'命の', u'命'),
(u'攻の', u'攻'),
(u'守の', u'守'),
(u'防の', u'守'),
(u'守りの', u'守'),
# For equipment and forge spirits
(u'飾りの', u'飾'),
(u'飾り', u'飾'),
(u'首飾', u'首輪'),
(u'輪の', u'輪'),
(u'(銅)', u'銅'),
(u'(銀)', u'銀'),
(u'(金)', u'金'),
(u'オキタエール', u'オキタ'),
(u'キタエール', u'オキタ'),
(u'★2 ', u'2*'),
(u'★2', u'2*'),
(u'★3 ', u'3*'),
(u'★3', u'3*'),
(u'★4 ', u''),
(u'★4', u''),
(u'★5 ', u''),
(u'★5', u''),
# For gifts
(u'(小)', u'小'),
(u'(中)', u'中'),
(u'(大)', u'大'),
(u'ナズナ特製ケーキ', u'ナズナケーキ'),
(u'贈り物ランダム', u'贈り物'),
(u'「銅」', u'銅'),
(u'「銀」', u'銀'),
# Gacha seeds
(u'中級装備種', u'中級装備ガチャ種'),
(u'中級ガチャ種', u'中級装備ガチャ種'),
# Typo for "skill"
(u'枝花', u'技花'),
# Typo for "equipment"
(u'裝花', u'装花'),
# Chinese characters
(u'黃', u'黄'),
]

translations = [
(u'おまけシート', 'Bonus Sheet ', ''),
(u'シート', 'Sheet ', ''),
(u'フクシアの技花', "Fuchsia's Skill Flower", ''),
(u'フクシアの装花', "Fuchsia's Equipment Flower", ''),
(u'フクシア', 'Fuchsia', ''),
(u'シーマニアの技花', "Bolivian Sunset's Skill Flower", 'Seemannia_SkillFlower.png'),
(u'シーマニアの装花', "Bolivian Sunset's Equipment Flower", 'Seemannia_EquipFlower.png'),
(u'シーマニア', 'Bolivian Sunset', 'BolivianSunset_icon00.png'),
(u'メイゲツカエデの技花', "Fullmoon Maple's Skill Flower", 'AmurMaple_SkillFlower.png'),
(u'メイゲツカエデの装花', "Fullmoon Maple's Equipment Flower", 'AmurMaple_EquipmentFlower.png'),
(u'メイゲツカエデ', 'Fullmoon Maple', 'FullmoonMaple_icon00.png'),
(u'オリーブの技花', "Olive's Skill Flower", 'Olive_SkillFlower.png'),
(u'オリーブの装花', "Olive's Equipment Flower", 'Olive_EquipFlower.png'),
(u'オリーブ', 'Olive', 'Olive_icon00.png'),
(u'オリーブの技花', "Olive's Skill Flower", 'Olive_SkillFlower.png'),
(u'オリーブの装花', "Olive's Equipment Flower", 'Olive_EquipFlower.png'),
(u'モルチアナの技花', "Common Mallow's Skill Flower", 'CommonMallow_SkillFlower.png'),
(u'モルチアナの装花', "Common Mallow's Equipment Flower", 'CommonMallow_EquipFlower.png'),
(u'モルチアナ', 'Common Mallow', 'CommonMallow_icon00.png'),
(u'コマチソウの技花', "Sweet William Catchfly's Skill Flower", 'SweetWilliamCatchfly_SkillFlower.png'),
(u'コマチソウの装花', "Sweet William Catchfly's Equipment Flower", 'SweetWilliamCatchfly_EquipFlower.png'),
(u'コマチソウ', 'Sweet William Catchfly', 'SweetWilliamCatchfly_icon00.png'),
# Event 66
(u'エケベリアの技花', "Echeveria's Skill Flower", 'Echeveria_SkillFlower.png'),
(u'エケベリアの装花', "Echeveria's Equipment Flower", 'Echeveria_EquipFlower.png'),
(u'エケベリア', 'Echeveria', 'icon_128101.png'),
# Event 71
(u'メギの技花', "Japanese Barberry's Skill Flower", 'Japanese_Barberry_SkillFlower.png'),
(u'メギの装花', "Japanese Barberry's Equipment Flower", 'Japanese_Barberry_EquipFlower.png'),
# Event 77
(u'ビバーナムの技花', "Viburnum's Skill Flower", 'Viburnum_SkillFlower.png'),
(u'ビバーナムの装花', "Viburnum's Equipment Flower", 'Viburnum_EquipFlower.png'),
# Event 81
(u'キヌサヤの技花', "Snow Pea's Skill Flower", 'Snow_Pea_SkillFlower.png'),
(u'キヌサヤの装花', "Snow Pea's Equipment Flower", 'Snow_Pea_EquipFlower.png'),

(u'レイニーシーソー', 'Rainy Seesaw', ''),
(u'ﾚｲﾆｰｽﾌﾟﾘﾝｸﾞｻﾝﾎﾞﾝ', 'Rainy Spring Sanbon', ''),

# Event equipment
(u'てるてるぼうずの指輪', "Teru Teru Bouzu's Ring", ''),
(u'てるてるぼうずの首輪', "Teru Teru Bouzu's Necklace", ''),
(u'てるてるぼうずの耳飾り', "Teru Teru Bouzu's Earrings", ''),
(u'てるてるぼうずの腕輪', "Teru Teru Bouzu's Bracelet", ''),
(u'海賊の指輪', "Pirate's Ring", "pirate's-ring.png"),
(u'海賊の首輪', "Pirate's Necklace", "pirate's-necklace.png"),
(u'海賊の耳飾り', "Pirate's Earrings", "pirate's-earrings.png"),
(u'海賊の腕輪', "Pirate's Bracelet", "pirate's-bracelet.png"),
(u'実りの指輪', 'Harvest Ring', 'harvest_ring.png'),
(u'実りの首輪', 'Harvest Necklace', 'harvest_necklace.png'),
(u'実りの耳飾', 'Harvest Earrings', 'harvest_earrings.png'),
(u'実りの腕輪', 'Harvest Bracelet', 'harvest_bracelet.png'),
(u'童心の指輪', 'Childlike Innocence Ring', 'childlike innocence ring.png'),
(u'童心の首輪', 'Childlike Innocence Necklace', 'childlike innocence necklace.png'),
(u'童心の耳飾', 'Childlike Innocence Earrings', 'childlike innocence earrings.png'),
(u'童心の腕輪', 'Childlike Innocence Bracelet', 'childlike innocence bracelet.png'),
(u'蒼海の指輪', 'Blue Waters Ring', 'blue waters ring.png'),
(u'蒼海の首輪', 'Blue Waters Necklace', 'blue waters necklace.png'),
(u'蒼海の耳飾', 'Blue Waters Earrings', 'blue waters earrings.png'),
(u'蒼海の腕輪', 'Blue Waters Bracelet', 'blue waters bracelet.png'),
# Event 61
(u'栄光の指輪', 'Glory Ring', 'Glory ring.png'),
(u'栄光の首輪', 'Glory Necklace', 'Glory necklace.png'),
(u'栄光の耳飾', 'Glory Earrings', 'Glory earrings.png'),
(u'栄光の腕輪', 'Glory Bracelet', 'Glory bracelet.png'),
# Event 66
(u'飴細工の指輪', 'Shaped Candy Ring', 'Shaped candy ring.png'),
(u'飴細工の首輪', 'Shaped Candy Necklace', 'Shaped candy necklace.png'),
(u'飴細工の耳飾', 'Shaped Candy Earrings', 'Shaped candy earrings.png'),
(u'飴細工の腕輪', 'Shaped Candy Bracelet', 'Shaped candy bracelet.png'),
# Event 71
(u'指針の指輪', 'Compass Needle Ring', 'Compass needle ring.png'),
(u'指針の首輪', 'Compass Needle Necklace', 'Compass needle necklace.png'),
(u'指針の耳飾', 'Compass Needle Earrings', 'Compass needle earrings.png'),
(u'指針の腕輪', 'Compass Needle Bracelet', 'Compass needle bracelet.png'),
# Event 77
(u'雪玉モフモフの指輪', 'Fluffly Snowball Ring', 'Fluffy snowball ring.png'),
(u'雪玉モフモフの首輪', 'Fluffly Snowball Necklace', 'Fluffy snowball necklace.png'),
(u'雪玉モフモフの耳飾', 'Fluffly Snowball Earrings', 'Fluffy snowball earrings.png'),
(u'雪玉モフモフの腕輪', 'Fluffly Snowball Bracelet', 'Fluffy snowball bracelet.png'),
# Event 81
(u'白い日の指輪', 'White Day Ring', 'White day ring.png'),
(u'白い日の首輪', 'White Day Necklace', 'White day necklace.png'),
(u'白い日の耳飾', 'White Day Earrings', 'White day earrings.png'),
(u'白い日の腕輪', 'White Day Bracelet', 'White day bracelet.png'),

(u'？ゴールド', '? gold', 'gold.jpg'),
(u'1000ゴールド', '1,000 gold', 'gold1k.jpg'),
(u'5000ゴールド', '5,000 gold', 'gold5k.jpg'),
(u'10000ゴールド', '10,000 gold', 'gold10k.jpg'),
# Big amounts of gold go first.
('10000G', '10,000 gold', 'gold10k.jpg'),
('10000', '10,000 gold', 'gold10k.jpg'),
('20000G', '20,000 gold', 'gold-20k.jpg'),
('20000', '20,000 gold', 'gold-20k.jpg'),
('25000G', '25,000 gold', 'gold-25k.jpg'),
('25000', '25,000 gold', 'gold-25k.jpg'),
('50000G', '50,000 gold', 'gold50k.jpg'),
('50000', '50,000 gold', 'gold50k.jpg'),

('1000G', '1,000 gold', 'gold1k.jpg'),
('1500G', '1,500 gold', 'gold-1,500.jpg'),
('2000G', '2,000 gold', 'gold2k.png'),
('2000', '2,000 gold', 'gold2k.png'),
('2500G', '2,500 gold', 'gold-2,500.jpg'),
('2500', '2,500 gold', 'gold-2,500.jpg'),
('4500G', '4,500 gold', 'gold-4,500.jpg'),
('4500', '4,500 gold', 'gold-4,500.jpg'),
('5000G', '5,000 gold', 'gold5k.jpg'),
('5000', '5,000 gold', 'gold5k.jpg'),

# Small gold amounts go last.
('100G', '100 gold', 'gold100.jpg'),
('200G', '200 gold', 'gold200.jpg'),
('500G', '500 gold', 'gold500.jpg'),
(u'500ゴールド', '500 gold', 'gold500.jpg'),

(u'赤マニュ5才', '5 year old Red Manyu', 'small red manyu 5.jpg'),
(u'青マニュ5才', '5 year old Blue Manyu', 'small blue manyu 5.jpg'),
(u'紫マニュ5才', '5 year old Purple Manyu', 'small purple manyu 5.jpg'),
(u'黄マニュ5才', '5 year old Yellow Manyu', 'small yellow manyu 5.jpg'),
(u'赤マニュ20才', '20 year old Red Manyu', 'small red manyu 20.jpg'),
(u'青マニュ20才', '20 year old Blue Manyu', 'small blue manyu 20.jpg'),
(u'紫マニュ20才', '20 year old Purple Manyu', 'small purple manyu 20.jpg'),
(u'黄マニュ20才', '20 year old Yellow Manyu', 'small yellow manyu 20.jpg'),
(u'赤マニュ100才', '100 year old Red Manyu', 'small red manyu 100.jpg'),
(u'青マニュ100才', '100 year old Blue Manyu', 'small blue manyu 100.jpg'),
(u'紫マニュ100才', '100 year old Purple Manyu', 'small purple manyu 100.jpg'),
(u'黄マニュ100才', '100 year old Yellow Manyu', 'small yellow manyu 100.jpg'),

(u'赤進化竜20才', '20 year old Red Dragon', 'small red blum 20.jpg'),
(u'青進化竜20才', '20 year old Blue Dragon', 'small blue blum 20.jpg'),
(u'紫進化竜20才', '20 year old Purple Dragon', 'small purple blum 20.jpg'),
(u'黄進化竜20才', '20 year old Yellow Dragon', 'small yellow blum 20.jpg'),
(u'赤進化竜100才', '100 year old Red Dragon', 'small red blum 100.jpg'),
(u'青進化竜100才', '100 year old Blue Dragon', 'small blue blum 100.jpg'),
(u'紫進化竜100才', '100 year old Purple Dragon', 'small purple blum 100.jpg'),
(u'黄進化竜100才', '100 year old Yellow Dragon', 'small yellow blum 100.jpg'),

(u'ナズナケーキ', "Nazuna's Cake", '500405.png'),
(u'贈り物小', 'Gift (Small)', 'Random gift small.png'),
(u'贈り物中', 'Gift (Mid)', 'Random gift mid.png'),
(u'贈り物大', 'Gift (Big)', '500103.png'),
(u'贈り物', 'Gift', '500101.png'), # Lack of info
(u'特別功労賞銅', 'Special Services Award (Copper)', '500500.png'),
(u'特別功労賞銀', 'Special Services Award (Silver)', '500501.png'),

(u'マニュ20才ランダム', 'Random 20 year old Manyu', 'Kyouka_rei_20_year_red_random_icon.jpg'),
(u'マニュ20才', '20 year old Manyu', 'Kyouka_rei_20_year_red_random_icon.jpg'), # lack of info
(u'3*ランダム', 'Random 3 Star', '910000.png'),
(u'団長メダル', 'Leader Medal', 'danchou_medal.png'),

(u'耳飾オキタ銅', 'Earrings Forge Spirit (Copper)', 'small bronze earrings forge spirit.jpg'),
(u'首輪オキタ銅', 'Necklace Forge Spirit (Copper)', 'small bronze necklace forge spirit.jpg'),
(u'指輪オキタ銅', 'Ring Forge Spirit (Copper)', 'small bronze ring forge spirit.jpg'),
(u'腕輪オキタ銅', 'Bracelet Forge Spirit (Copper)', 'small bronze bracelet forge spirit.jpg'),

(u'耳飾オキタ銀', 'Earrings Forge Spirit (Silver)', 'small silver earrings forge spirit.jpg'),
(u'首輪オキタ銀', 'Necklace Forge Spirit (Silver)', 'small silver necklace forge spirit.jpg'),
(u'指輪オキタ銀', 'Ring Forge Spirit (Silver)', 'small silver ring forge spirit.jpg'),
(u'腕輪オキタ銀', 'Bracelet Forge Spirit (Silver)', 'small silver bracelet forge spirit.jpg'),

(u'耳飾オキタ金', 'Earrings Forge Spirit (Gold)', 'small gold earrings forge spirit.jpg'),
(u'首輪オキタ金', 'Necklace Forge Spirit (Gold)', 'small gold necklace forge spirit.jpg'),
(u'指輪オキタ金', 'Ring Forge Spirit (Gold)', 'small gold ring forge spirit.jpg'),
(u'腕輪オキタ金', 'Bracelet Forge Spirit (Gold)', 'small gold bracelet forge spirit.jpg'),
(u'専用装備オキタ金', 'Personal Equipment Forge Spirit (Gold)', 'small gold personal forge spirit.jpg'),

(u'中級装備ガチャ種x100', 'Mid Lv Equip Gacha Seeds x100', 'mid-equip-100.jpg'),
(u'中級装備ガチャ種x250', 'Mid Lv Equip Gacha Seeds x250', 'mid-equip-250.jpg'),
(u'中級装備ガチャ種x500', 'Mid Lv Equip Gacha Seeds x500', 'mid-equip-500.jpg'),
(u'中級装備ガチャ種x1,000', 'Mid Lv Equip Gacha Seeds x1,000', 'mid-equip-1k.jpg'),
(u'中級装備ガチャ種', 'Mid Lv Equip Gacha Seeds', 'Mid-equip-seed.jpg'),
(u'級装備種', 'Mid Lv Equip Gacha Seeds', 'Mid-equip-seed.jpg'), # typo
(u'装備ガチャ種', 'Mid Lv Equip Gacha Seeds', 'Mid-equip-seed.jpg'), # ambiguous
(u'ガチャ種x100', 'Gacha Seeds x100', 'gacha-100.jpg'),
(u'ガチャ種x250', 'Gacha Seeds x250', 'gacha-250.jpg'),
(u'ガチャ種x500', 'Gacha Seeds x500', 'gacha-500.jpg'),
(u'ガチャ種', 'Gacha Seeds', '000003.png'),
(u'絆水晶x10', 'Bond Crystals x10', 'Bond_crystal.png'),
(u'絆水晶', 'Bond Crystals', 'Bond_crystal.png'),

(u'命アンプルゥ', 'Ampule of Life', 'small life ampule.jpg'),
(u'攻アンプルゥ', 'Ampule of Attack', 'small attack ampule.jpg'),
(u'守アンプルゥ', 'Ampule of Protection', 'small defense ampule.jpg'),

(u'青フルル', 'Blue Fururu', 'Small blue fururu.jpg'),
(u'赤フルル', 'Red Fururu', 'Small red fururu.jpg'),
(u'紫フルル', 'Purple Fururu', 'Small purple fururu.jpg'),
(u'黄フルル', 'Yellow Fururu', 'Small yellow fururu.jpg'),
(u'プレミアムガチャチケット', 'Premium Gacha Ticket', 'Premium_gacha_ticket.png'),

(u'深い森の花びら', 'Petal of Deep Forest', 'Lily_wood_petal_icon.png'),
(u'常夏の花びら', 'Petal of Everlasting Summer', 'Banana_ocean_petal_icon.png'),
(u'知徳の花びら', 'Petal of Virtue and Knowledge', 'Blossom_hill_petal_icon.png'),
(u'風谷の花びら', 'Petal of Wind Valley', 'Bergamot_valley_petal_icon.png'),
(u'雪原の花びら', 'Petal of Snowfield', 'Winter_rose_petal_icon.png'),
]

def translate_text(text):
	"""Translates a card on a sheet into a wikitable cell."""
	for typo in typo_fixes:
		text = text.replace(typo[0], typo[1])

	for trans in translations:
		jp_word, en_word, icon = trans
		if icon:
			if icon.startswith(u'small'):
				# Small icons don't need to be shrunk.
				# The filename will say "small" to show it's 50x50.
				full_icon = u'[[File:{0}|{1}]]'.format(
					icon, en_word)
			else:
				# Force the icon to be 50x50.
				full_icon = u'[[File:{0}|50px|{1}]]'.format(
					icon, en_word)
			text = text.replace(jp_word, full_icon)
		text = text.replace(jp_word, en_word)

	text = text.replace(event_char,
		'{{CImage|'+event_char+'|50px}}')

	return text

def get_sheet_table_as_nested_dict(soup):
	"""Parses a single table representing a Sheet in the soup.

	It must be the entire <table> tag.
	"""

	all_data = []
	# We need to save the row data from the very last sheet.
	# Therefore, row_data needs to exist outside of the loop.
	sheet_data = []
	for row in soup.find_all('tr'):
		if row.a:
			# This row is a stylish "gap" between sheets. We recognize it by
			# looking for the anchor specific to the next sheet.

			# Take all data seen up until now and save it as one "sheet".
			all_data.append(sheet_data)
			sheet_data = []
		else:
			# This is another row in a sheet.

			row_data = []
			# Note that th elements are those with gray backgrounds.
			# They store the Sheet name and the empty cells labeled with a dash.
			for data_cell in row.find_all(['td', 'th']):
				# The Sheet title should be the only cell with a rowspan.
				# Do not add it to our data.
				if not data_cell.get('rowspan'):
					row_data.append(translate_text(data_cell.text))
			sheet_data.append(row_data)
	# Append the very last rows of data. They consisted of another sheet, but
	# we wouldn't encounter a stylish "gap" to trigger the code in the loop
	# which would've otherwise closed off this last sheet.
	all_data.append(sheet_data)
	return all_data

def get_sheets_for_id(id_attr, soup, separated=False):
	"""Given an id attribute for an element in the soup, get its sheets.

	For example, id='Oli_01' looks for the tag whose id is that, then
	the table that directly follows it is parsed for sheets.

	Some of the formatting is odd for the Japanese Wiki. The unique tables
	have extra separators between the element with the id we want and the table
	we want. Set "separated" to True if this is a unique table.
	"""

	div_for_sheet = soup.find(id=id_attr).parent. \
		next_sibling.next_sibling
	if separated:
		div_for_sheet = div_for_sheet.next_sibling.next_sibling
	return get_sheet_table_as_nested_dict(div_for_sheet.table)

def parse_soup(soup):
	"""Takes a BeautifulSoup instance and removes all Sheets from it.

	Returns each set of sheets as a keys to a dict.
	"""

	sheets = {}
	sheets['Winter Cosmos'] = get_sheets_for_id('Win_01', soup)
	sheets["Flat Sea Holly"] = get_sheets_for_id('Ery_01', soup)
	sheets['Wheat'] = get_sheets_for_id('Kom_01', soup)
	sheets['Snow Pea'] = get_sheets_for_id('Kin_01', soup)
	sheets['Bonus'] = get_sheets_for_id('Extra_01', soup, False)
	return sheets

def output_to_file(text, filename=DEFAULT_OUTFILENAME):
	with codecs.open(filename, 'w', encoding='utf-8') as outfile:
		outfile.write(text)

def process_sheets_dict(all_sheets):
	"""Gets the sheets data as a full string ready to be printed."""
	text = u'''__NOTOC__
These are the card sheets for [[{title}]]. The set of cards sheets a player will have will be based on which of the four featured girls appears on card flipping screen. Bonus Sheets have the same pattern for all players. Mouse over icons to display their meaning. All data comes directly from the [{wiki} Japanese Wiki] with great gratitude.
{{| style="text-align: center"
|-
|{{{{CImage|{char1_jp}|center|link=#{char1_en}_Sheets}}}}
|{{{{CImage|{char2_jp}|center|link=#{char2_en}_Sheets}}}}
|{{{{CImage|{char3_jp}|center|link=#{char3_en}_Sheets}}}}
|{{{{CImage|{char4_jp}|center|link=#{char4_en}_Sheets}}}}
| rowspan="2"| [[#Bonus Sheets|Bonus Sheets]]
|-
|[[#{char1_en} Sheets|{char1_en}]]
|[[#{char2_en} Sheets|{char2_en}]]
|[[#{char3_en} Sheets|{char3_en}]]
|[[#{char4_en} Sheets|{char4_en}]]
|}}

'''.format(title=u'Fierce Fight! The Climactic Snowball Fight',
	wiki=SRC_URL,
	char1_jp=u'ウィンターコスモス', char1_en=u'Winter Cosmos',
	char2_jp=u'エリンジウム', char2_en=u"Flat Sea Holly",
	char3_jp=u'コムギ', char3_en=u'Wheat',
	char4_jp=u'キヌサヤ', char4_en=u'Snow Pea')
	display_order = ['Winter Cosmos', 'Flat Sea Holly',
		'Wheat', 'Snow Pea', 'Bonus']
	char_num = 0
	for sheet_owner in display_order:
		# Write the header for one character's sheets.
		text += '==={0} Sheets===\n'.format(sheet_owner)
		text += '{| class="wikitable"\n'
		text += '|+{0} Card Sheets\n'.format(sheet_owner)
		text += '|-\n'
		text += '|colspan="9"|\n'
		text += '|-\n'
		# Write each sheet.
		sheet_num = 1
		for char_sheets in all_sheets[sheet_owner]:
			text += '!rowspan="{0}" |Sheet {1}\n|'.format(len(char_sheets),
				sheet_num)
			first_loop = True
			for sheet in char_sheets:
				text += '' if first_loop else '\n|-\n'
				first_loop = False
				text += '| ' + ' || '.join([row for row in sheet])
			sheet_num += 1
			# Separate all sheets with a full-length table row.
			# Check that we aren't at the end of the sheets, because we
			# don't want this separator at the end of the table.
			if sheet_num <= len(all_sheets[sheet_owner]):
				text += '\n|-' \
						'\n!colspan="{0}" height=20|' \
						'\n|-\n'.format(8)
		# Close off the whole table of sheets.
		text += '\n|}'
		# Move on to the next character's sheet.
		char_num += 1
		if char_num < len(all_sheets):
			# All this does is put space between each character's sheets.
			# The if-statement checks that we aren't at the page's end.
			text += '\n\n'
	return text

def get_sheets_page(url=SRC_URL, infilename=u'', outfilename=None, quiet=True):
	"""Gets the full Wikia page for card sheets.

	@param: url: String. Where in the Japanese Wikia to scrape data from.
	@param infilename: String. If empty, uses the url for reading data.
		If assigned, ignores the url and instead parses the input file.
	@param outfilename: String or None. If it's a string, the output goes
		to the file with that name and the page's text is returned.
		If None, the page's text is returned only.
	@param quiet: Boolean. If True, suppresses diagnostic messages.
	@returns: The full page text for the 
	"""

	full_text = u''

	if infilename:
		# We are given a source file. Read it as input.
		print('Reading the file data.')
		with open(infilename, 'r', encoding='utf-8', errors='ignore') as infile:
			full_text = infile.read()
		if major_ver == 2:
			full_text.encode('utf-8')
	else:
		# We are given a source URL. Download the web page as input.
		if not quiet:
			print('Retrieving the webpage content.')
		response = requests.get(url)
		full_text = response.content
	if not quiet:
		print('Parsing the data.')
	soup = BeautifulSoup(full_text, 'html.parser')
	sheets = parse_soup(soup)
	printable_tables = process_sheets_dict(sheets)
	if outfilename:
		output_to_file(printable_tables)
		if not quiet:
			print('Parsing completed. Please see ' + outfilename)
	return printable_tables

if __name__ == '__main__':
	get_sheets_page(outfilename=DEFAULT_OUTFILENAME, quiet=False)
	input('Press Enter to end the script.')
