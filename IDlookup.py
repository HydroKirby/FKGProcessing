#!/usr/bin/python3
# coding=utf-8
from __future__ import print_function
import os, sys, math, re, random, zlib, hashlib

if sys.version_info.major >= 3:
	# The script is being run under Python 3.
	from urllib.request import urlopen
elif sys.version_info.major < 3:
	# The script is being run under Python 2.
	from urllib2 import urlopen
	# Make some changes so that the code looks and acts like Python 3.
	# Use the codecs library for files.
	import codecs
	open = codecs.open
	range = xrange
	input = raw_input

__doc__ = """Checks the getMaster Data to generate the template data"""

DEFAULT_INFILENAME = 'getMaster_latest.txt'
DEFAULT_OUTFILENAME = 'result.txt'
DEFAULT_ASSETPATH = 'asset'

# Download state flags.
(DL_OK, # The download succeeded.
DL_FAIL, # The download failed.
DL_QUIT) = range(3) # The user forcefully stopped the download.

# Character image types.
(IMG_ICON,
IMG_STAND) = range(2)

# Specify the Flower Knight ID and their English name (which is not available in getMaster)
findID = [158101]
english_nameList = ["Aizoon Stonecrop"]
CmdPrint = True
ImgDownload = False

attribList = {
	'1':'Slash',
	'2':'Blunt',
	'3':'Pierce',
	'4':'Magic'
	}

nationList = {
	'1':'Winter Rose',
	'2':'Banana Ocean',
	'3':'Blossom Hill',
	'4':'Bergamot Valley',
	'5':'Lily Wood',
	'7':'Lotus Lake'
	}

giftList = {
	'1':'Gem',
	'2':'Teddy Bear',
	'3':'Cake',
	'4':'Book'
	}

# Maps a rarity to its maxmimum levels per evolution tier.
maxLevel = {
	'2':['50','60'],
	'3':['50','60'],
	'4':['50','60'],
	'5':['60','70','80'],
	'6':['60','70','80'],
}

def split_and_check_count(data_entry_csv, expected_count):
	"""Splits a line of CSV and verifies the number of entries is correct.

	data_entry_csv is a string of CSV data.
	expected_count is an int saying how many entries to expect.

	Returns a tuple: (entries, success, actual_count) such that "entries" is
		all of the CSV data turned into a list of strings, "success" says
		whether or not the expected_count was the number of actual CSV entries,
		and "actual_count" is the actual number of CSV entries.
	The returned "entries" is guaranteed to be the same size as expected_count.
	If the actual count = the expected count,
		the CSV are returned along with success = True.
	If the actual count < the expected count,
		the available CSV are returned and the parts that were unavailable
		become empty strings. success = False.
	If the actual count > the expected count,
		as many CSV as can fit into "entries" will be returned. succss = False.

	Returns (entries, success, actual_count)
	"""

	data_entry_csv = data_entry_csv.rstrip()
	entries = data_entry_csv.split(',')
	if data_entry_csv.endswith(','):
		# The last data entry is empty and unnecessary.
		entries = entries[:-1]

	actual_count = len(entries)
	if actual_count < expected_count:
		# Add empty strings to fill in the blanks.
		entries += ['' for i in range(expected_count - actual_count)]
	elif actual_count > expected_count:
		# Crop off the excess entries.
		entries = entries[:expected_count]

	return (entries, expected_count == actual_count, actual_count)

def remove_quotes(text):
	"""Removes double-quotes around strings."""
	if text.startswith('"') and text.endswith('"'):
		return text[1:-1]
	return text

def add_quotes(text):
	"""Puts double-quotes around strings."""
	if text.startswith('"') and text.endswith('"'):
		return text
	return '"' + text + '"'

def get_float(val):
	"""Checks if a value is a floating point number or not."""
	try:
		return float(val)
	except ValueError:
		return None

class FlowerKnight(object):
	"""Class for storing all of a flower knight's info.

	It does not store info for other variants.
	"""
	# These constants correspond to the "stats" dict.
	(HP,
	ATK,
	DEF) = range(3)
	# These are the evolution tiers the character is capable of.
	(NO_BLOOM,
	BLOOMABLE,
	BLOOM_POWERS_ONLY) = range(3)

	def __init__(my, entries):
		"""Constructor.

		@param entries: A list of 2~3 CharacterEntry instances.
			They must be the pre-evolved, evolved, and bloomed forms.
		"""

		# Organize the entries given to the ctor based on evolution tier.
		pre_evo_entry = evo_entry = bloom_entry = None
		if len(entries) < 1:
			print("Error: Can't find the requested flower knight.")
			return
		for entry in entries:
			tier = entry.getval('evolutionTier')
			if tier == '1':
				pre_evo_entry = entry
			elif tier == '2':
				evo_entry = entry
			else:
				bloom_entry = entry

		# Store info which should be the same across all evolution tiers of the character.
		my.spd = pre_evo_entry.getval('lvlOneSpd')
		my.fullName = pre_evo_entry.getval('fullName')
		my.rarity = pre_evo_entry.getval('rarity')
		my.skill = pre_evo_entry.getval('skill1ID')
		my.family = pre_evo_entry.getval('family')
		my.type = pre_evo_entry.getval('type')
		my.nation = pre_evo_entry.getval('nation')
		my.gift = pre_evo_entry.getval('gift')
		my.charID1 = pre_evo_entry.getval('charID1')

		# Store all stats in lists ordered as such: HP, Atk, Def.
		my.tiers = {'preEvo':{}, 'evo':{}, 'bloom':{}}
		my.tiers['preEvo']['id'] = pre_evo_entry.getval('id0')
		my.tiers['preEvo']['lvlCap'] = maxLevel[my.rarity][0]
		my.tiers['preEvo']['abilities'] = [pre_evo_entry.getval('ability1ID'), pre_evo_entry.getval('ability2ID')]
		my.tiers['preEvo']['lvlOne'] = [pre_evo_entry.getval('lvlOneHP'), pre_evo_entry.getval('lvlOneAtk'), pre_evo_entry.getval('lvlOneDef')]
		my.tiers['preEvo']['lvlMax'] = [pre_evo_entry.getval('lvlMaxHP'), pre_evo_entry.getval('lvlMaxAtk'), pre_evo_entry.getval('lvlMaxDef')]
		my.tiers['preEvo']['aff1'] = [pre_evo_entry.getval('aff1MultHP'), pre_evo_entry.getval('aff1MultAtk'), pre_evo_entry.getval('aff1MultDef')]
		my.tiers['preEvo']['aff2'] = [pre_evo_entry.getval('aff2MultHP'), pre_evo_entry.getval('aff2MultAtk'), pre_evo_entry.getval('aff2MultDef')]
		my.tiers['evo']['id'] = evo_entry.getval('id0')
		my.tiers['evo']['lvlCap'] = maxLevel[my.rarity][1]
		my.tiers['evo']['abilities'] = [evo_entry.getval('ability1ID'), evo_entry.getval('ability2ID')]
		my.tiers['evo']['lvlOne'] = [evo_entry.getval('lvlOneHP'), evo_entry.getval('lvlOneAtk'), evo_entry.getval('lvlOneDef')]
		my.tiers['evo']['lvlMax'] = [evo_entry.getval('lvlMaxHP'), evo_entry.getval('lvlMaxAtk'), evo_entry.getval('lvlMaxDef')]
		my.tiers['evo']['aff1'] = [evo_entry.getval('aff1MultHP'), evo_entry.getval('aff1MultAtk'), evo_entry.getval('aff1MultDef')]
		my.tiers['evo']['aff2'] = [evo_entry.getval('aff2MultHP'), evo_entry.getval('aff2MultAtk'), evo_entry.getval('aff2MultDef')]
		my.bloomability = FlowerKnight.NO_BLOOM
		my.tiers['bloom']['id'] = ''
		my.tiers['preEvo']['lvlCap'] = '0'
		my.tiers['bloom']['abilities'] = ['', '']
		my.tiers['bloom']['lvlOne'] = []
		my.tiers['bloom']['lvlMax'] = []
		my.tiers['bloom']['aff1'] = []
		my.tiers['bloom']['aff2'] = []
		if bloom_entry:
			if bloom_entry.getval('isBloomedPowersOnly') == "1":
				my.bloomability = FlowerKnight.BLOOM_POWERS_ONLY
			else:
				my.bloomability = FlowerKnight.BLOOMABLE
			my.tiers['bloom']['id'] = bloom_entry.getval('id0')
			my.tiers['bloom']['lvlCap'] = maxLevel[my.rarity][2]
			my.tiers['bloom']['abilities'] = [bloom_entry.getval('ability1ID'), bloom_entry.getval('ability2ID')]
			my.tiers['bloom']['lvlOne'] = [bloom_entry.getval('lvlOneHP'), bloom_entry.getval('lvlOneAtk'), bloom_entry.getval('lvlOneDef')]
			my.tiers['bloom']['lvlMax'] = [bloom_entry.getval('lvlMaxHP'), bloom_entry.getval('lvlMaxAtk'), bloom_entry.getval('lvlMaxDef')]
			my.tiers['bloom']['aff1'] = [bloom_entry.getval('aff1MultHP'), bloom_entry.getval('aff1MultAtk'), bloom_entry.getval('aff1MultDef')]
			my.tiers['bloom']['aff2'] = [bloom_entry.getval('aff2MultHP'), bloom_entry.getval('aff2MultAtk'), bloom_entry.getval('aff2MultDef')]

class BaseEntry(object):
	"""Base class for deriving Entry classes.

	Important note: The CSV entries are stored such that
	numerical values are strings, and
	string values are strings enclosed in double-quotes.
	"""

	INVALID_ENTRY_TYPE = 'invalid'
	# For a given entry type (eg. "character", "skill"), this stores a list of
	# indices for my.values pointing to the values that are strings instead of
	# numbers. It is used to track which entries to enclose in double-quotes.
	_string_valued_indices = {}
	# If we encounter an invalid number of CSV entries, warn the user and set
	# the corresponding entry type to True. Only state the warning once.
	_WARN_WRONG_SIZE = {}

	def __init__(my, data_entry_csv, entry_type=INVALID_ENTRY_TYPE, entries=[]):
		"""Ctor. To be overrridden and called by child classes."""
		if not len(entries) or entry_type == BaseEntry.INVALID_ENTRY_TYPE:
			raise Exception('Error: Trying to instantiate the base Entry class instead of a child class.')

		# Turn the CSV into a list.
		values, success, actual_count = split_and_check_count(
			data_entry_csv, len(entries))
		if entry_type not in BaseEntry. _WARN_WRONG_SIZE:
			BaseEntry._WARN_WRONG_SIZE[entry_type] = False
		if not success and not BaseEntry._WARN_WRONG_SIZE:
			print('Warning: There are {0} values in a/an {1} entry instead of {2}.'.format(
				actual_count, entry_type, len(entries)))
			print('The format of getMaster may have changed.')
			# Don't state the warning again.
			BaseEntry._WARN_WRONG_SIZE[entry_type] = True

		# Store the values. We can access it with integer indices, or
		# indirectly using my._named_values. The latter is done through
		# the class instance's getval() function.
		my.values = values
		my.enclose_string_values(entry_type)

		# Store a list of names to relate to the values.
		# This should be created in the child class.
		my._named_values = {}

	def enclose_string_values(my, entry_type=INVALID_ENTRY_TYPE):
		"""Surrounds all string CSV entries in double-quotes.

		This only needs to be called once per entry.
		The first call for a given entry will be slower than the rest.
		"""

		if entry_type == BaseEntry.INVALID_ENTRY_TYPE:
			raise Exception('Error: Trying to call a method from the base ' \
				'Entry class instead of a child class.')

		if entry_type not in my._string_valued_indices:
			# This is the first time assigning double-quotes to strings for
			# CSV entries of this type of Entry. Make a list of all values
			# that are strings instead of numbers.

			# Implementation note: Check for equivalance to None instead of
			# duck-typing and checking for not(value). get_float can return
			# 0 or 0.0 for valid numbers, but None for non-numbers.
			my._string_valued_indices[entry_type] = \
				[i for i in range(len(my.values)) if get_float(my.values[i]) is None]

		for value_index in my._string_valued_indices[entry_type]:
			my.values[value_index] = add_quotes(my.values[value_index])

	def getval(my, value_name):
		"""Returns a stored value by its name.

		This is the base class' implementation. Do not call this.
		"""

		raise Exception('Error: Calling a base class method (getval). ' \
			'Did you forget to implement it in the child class?')

	def getval_by_index(my, value_index):
		"""Returns a stored value by its index in the CSV."""
		if value_index >= 0 and value_index < len(my.values):
			return my.values[value_index]

	def getlua(my):
		"""Returns the stored data as a Lua list.

		This is the base class' implementation.
		It only provides a boilerplate for the kind of code you would make.
		From a child class, pass the named entries dict for nicer output.
		"""

		if my._named_values:
			# Relate the named entries to their value.
			# This relies on how Python maintains order in dicts.
			# Example output: {name="Bob", type="cat", hairs=5},
			return '{' + u', '.join([u'{0}={1}'.format(k, my.values[v]) for k, v in my._named_values.items()]) + '},'
		# There's no dict of named entries-to-indices.
		# Just output all of the values separated by commas.
		# Example output: {"Bob", "cat", 5},
		return '{' + u', '.join([v for v in my.values]) + '},'

class CharacterEntry(BaseEntry):
	"""Stores one line of data from the masterCharacter section."""
	__NAMED_ENTRIES = [
		'id0',
		'id1',
		'family',
		'nation',
		'charID1',
		'baseName0',
		'baseName1',
		'rarity',
		'type',
		'gift',
		'ability1ID',
		'ability2ID',
		'skill1ID',
		'skill2ID',
		'unknown00',
		'lvlOneHP',
		'lvlMaxHP',
		'lvlOneAtk',
		'lvlMaxAtk',
		'lvlOneDef',
		'lvlMaxDef',
		'lvlOneSpd',
		'lvlOneSpd',
		'ampuleBonusHP',
		'ampuleBonusAtk',
		'ampuleBonusDef',
		'goldSellValue',
		'sortCategory', # Unverified
		'evolutionKeyValue', # Unverified
		'isNotPreEvo',
		'isFlowerKnight1',
		'aff1MultHP',
		'aff1MultAtk',
		'aff1MultDef',
		'charID2',
		'evolutionTier',
		'isFlowerKnight2',
		'unknown01',
		'aff2MultHP',
		'aff2MultAtk',
		'aff2MultDef',
		'unknown02',
		'unknown03',
		'unknown04',
		'unknown05',
		'fullName',
		'isBloomedPowersOnly',
		'variant',
		'reading',
		'date0',
		'date1',
		'unknown06',
		'gameVersionWhenAdded',]

	def __init__(my, data_entry_csv):
		super(CharacterEntry, my).__init__(data_entry_csv, 'character',
			my.__NAMED_ENTRIES)
		if not my._named_values:
			# Create a dict that gives descriptive names to indices in the CSV.
			# As an example of what this does, it could set
			# my._named_values['id'] = 0
			my._named_values = dict(zip(my.__NAMED_ENTRIES,
				range(len(CharacterEntry.__NAMED_ENTRIES))))

	def getval(my, value_name):
		"""Returns a stored value by its name."""
		return my.values[my._named_values[value_name]]

	def getlua(my, named_values={}):
		"""Returns the stored data as a Lua list."""
		return super(CharacterEntry, my).getlua()

	def getlua_name_to_id(my):
		return u'[{0}] = {1},'.format(my.getval('fullName'), my.getval('id0'))

	def getlua_id_to_name(my):
		return u'[{0}] = {1},'.format(my.getval('id0'), my.getval('fullName'))

class SkillEntry(BaseEntry):
	"""Stores one line of data from the masterCharacter section."""
	__NAMED_ENTRIES = [
		'uniqueID',
		'nameJapanese',
		'typeID',
		'val0',
		'val1',
		'val2',
		'descJapanese',
		'triggerRateLv1',
		'triggerRateLvUp',
		'unknown00',
		'date00',
		'date01',
		'unknown01',]

	def __init__(my, data_entry_csv):
		super(SkillEntry, my).__init__(data_entry_csv, 'skill',
			my.__NAMED_ENTRIES)
		if not my._named_values:
			# Create a dict that gives descriptive names to indices in the CSV.
			# As an example of what this does, it could set
			# my._named_values['id'] = 0
			my._named_values = dict(zip(my.__NAMED_ENTRIES,
				range(len(SkillEntry.__NAMED_ENTRIES))))

	def getval(my, value_name):
		"""Returns a stored value by its name."""
		return my.values[my._named_values[value_name]]

	def getlua(my):
		return u'[{0}] = '.format(my.getval('uniqueID')) + \
			super(SkillEntry, my).getlua()

class AbilityEntry(BaseEntry):
	"""Stores one line of data from the ability section.

	In the master data, this section is named masterCharacterLeaderSkill.
	"""
	__NAMED_ENTRIES = [
		'uniqueID',
		'shortDescJapanese', # Used for synthesis mats.
		'ability1ID',
		'ability1Val0',
		'ability1Val1',
		'ability1Val2',
		'ability2ID',
		'ability2Val0',
		'ability2Val1',
		'ability2Val2',
		'descJapanese',
		'date00',
		'date01',
		'unknown00',]

	def __init__(my, data_entry_csv):
		super(AbilityEntry, my).__init__(data_entry_csv, 'ability',
			my.__NAMED_ENTRIES)
		if not my._named_values:
			# Create a dict that gives descriptive names to indices in the CSV.
			# As an example of what this does, it could set
			# my._named_values['id'] = 0
			my._named_values = dict(zip(my.__NAMED_ENTRIES,
				range(len(AbilityEntry.__NAMED_ENTRIES))))

	def getval(my, value_name):
		"""Returns a stored value by its name."""
		return my.values[my._named_values[value_name]]

	def getlua(my):
		return u'[{0}] = '.format(my.getval('uniqueID')) + \
			super(AbilityEntry, my).getlua()

class EquipmentEntry(BaseEntry):
	__NAMED_ENTRIES = [
		# TODO: Fill out this list with names of variables.
		]

	def __init__(my):
		raise Exception('Error: EquipmentEntry is not implemented yet!')

		super(EquipmentEntry, my).__init__(data_entry_csv, 'equipment',
			my.__NAMED_ENTRIES)
		if not my._named_values:
			# Create a dict that gives descriptive names to indices in the CSV.
			# As an example of what this does, it could set
			# my._named_values['id'] = 0
			my._named_values = dict(zip(my.__NAMED_ENTRIES,
				range(len(EquipmentEntry.__NAMED_ENTRIES))))

	def getval(my, value_name):
		"""Returns a stored value by its name."""
		return my.values[my._named_values[value_name]]

	def getlua(my):
		return u'[{0}] = '.format(my.getval('uniqueID')) + \
			super(EquipmentEntry, my).getlua()

class MasterData(object):
	"""Handles various info from the master data."""
	def __init__(my, infilename=''):
		my.masterTexts = {}
		my.characters = {}
		my.pre_evo_chars = {}
		my.skills = {}
		my.abilities = {}
		my.equipment_entries = []
		if infilename: my.load_getMaster(infilename)

	def _extract_section(my, section, rawdata):
		"""Gets all text from one section of the master data."""
		return rawdata.partition(section + '\n')[2][1:].partition('master')[0].strip().split('\n')

	def _parse_character_entries(my):
		"""Creates a list of character entries from masterCharacter."""
		character_entries = [CharacterEntry(entry) for entry in my.masterTexts['masterCharacter']]
		my.characters = {c.getval('id0'):c for c in character_entries}
		my.pre_evo_chars = {c.getval('id0'):c for c in character_entries if
			c.getval('isFlowerKnight1') == '1' and c.getval('evolutionTier') == '1'}

	def _parse_skill_entries(my):
		"""Creates a list of skill entries from masterCharacterSkill."""
		skill_entries = [SkillEntry(entry) for entry in my.masterTexts['masterSkill']]
		my.skills = {s.getval('uniqueID'):s for s in skill_entries}

	def _parse_ability_entries(my):
		"""Creates a list of ability entries from masterCharacterLeaderSkill."""
		ability_entries = [AbilityEntry(entry) for entry in my.masterTexts['masterAbility']]
		# Remove abilities related to Strengthening Synthesis.
		ability_entries = [entry for entry in ability_entries if
			u'合成' not in entry.getval('shortDescJapanese') and
			u'合成' not in entry.getval('descJapanese')]
		my.abilities = {a.getval('uniqueID'):a for a in ability_entries}
		
	def _parse_equipment_entries(my):
		"""Creates a list of equipment entries from masterCharacterEquipment."""
		my.equipment_entries = [entry.split(',')[:-1] for entry in my.masterTexts['masterEquipment']]

	def load_getMaster(my, infilename):
		"""Loads and parses getMaster.

		This function is called automatically if the constructor is given
		getMaster's filename in advance.
		"""

		# Open the master database
		with open(infilename, 'r', encoding='utf8') as infile:
			api_data = infile.read()
		
		# Extract relevant data from master database
		my.masterTexts['masterCharacter'] = my._extract_section('masterCharacter', api_data)
		my.masterTexts['masterSkill'] = my._extract_section('masterCharacterSkill', api_data)
		my.masterTexts['masterAbility'] = my._extract_section('masterCharacterLeaderSkill', api_data)
		my.masterTexts['masterPlantFamily'] = my._extract_section('masterCharacterCategory', api_data)
		my.masterTexts['masterFlowerBook'] = my._extract_section('masterCharacterBook', api_data)
		my.masterTexts['masterEquipment'] = my._extract_section('masterCharacterEquipment', api_data)
		
		#Parse character and equipment entries
		my._parse_character_entries()
		my._parse_skill_entries()
		my._parse_ability_entries()
		my._parse_equipment_entries()

	def get_skill_list_page(my):
		"""Outputs the table of skill IDs and their related skill info."""
		# Write the page header.
		module_name = 'Module:SkillList'
		def getid(entry):
			return int(entry.getval('uniqueID'))
		output = u'\n'.join([
			'-- Relates skill IDs with their accompanying data.',
			'-- This page is auto-generated.\n',
			'local p = {',

			# Write the page body.
			'\t' +  u'\n\t'.join([entry.getlua() for entry in
				sorted(my.skills.values(), key=getid)]),

			# Write the page footer.
			'}\n',
			'return p',
			])
		return output

	def get_ability_list_page(my):
		"""Outputs the table of ability IDs and their related ability info."""
		# Write the page header.
		module_name = 'Module:AbilityList'
		def getid(entry):
			return int(entry.getval('uniqueID'))
		output = u'\n'.join([
			'-- Relates ability IDs with their accompanying data.',
			'-- This page is auto-generated.\n',
			'local p = {',

			# Write the page body.
			'\t' + u'\n\t'.join([entry.getlua() for entry in
				sorted(my.abilities.values(), key=getid)]),

			# Write the page footer.
			'}\n',
			'return p',
			])
		return output

	def get_char_list_page(my):
		"""Outputs the table of char names and their related ID."""
		# Write the page header.
		module_name = 'Module:CharacterList'
		def getname(entry):
			return entry.getval('fullName')
		def getid(entry):
			return int(entry.getval('id0'))
		output = '\n'.join([
			'-- Relates character names to their IDs.',
			'-- This page is auto-generated.\n',
			'local p = {}\n',
			'p.namesToIDs = {',

			# Write the page body.
			'\t' + u'\n\t'.join([entry.getlua_name_to_id() for entry in
				sorted(my.pre_evo_chars.values(), key=getname)]),
			'}\n',
			'p.idsToNames = {',
			'\t' + u'\n\t'.join([entry.getlua_id_to_name() for entry in
				sorted(my.pre_evo_chars.values(), key=getid)]),

			# Write the page footer.
			'}\n',
			'return p',
			])
		return output

	def get_char_entries(my, char_name_or_id):
		"""Finds all entries relevant to a character ID or full name."""
		char_id = ''
		fullName = ''
		# Check if char_name_id is an integer or a stringly-typed integer.
		if type(char_name_or_id) is int or char_name_or_id.isdigit():
			# char_name_or_id was the character's ID.
			# Find the one entry for this character.
			char_id = str(char_name_or_id)
			if char_id in my.characters:
				fullName = my.characters[char_id].getval('fullName')
			else:
				print('Warning: No character by that ID exists.')
				return []

		# Either we found the full name based on the ID or it was passed in.
		fullName = add_quotes(fullName or char_name_or_id)
		# Search for all evolution tiers for the character.
		def same_name(entry):
			return entry.getval('fullName') == fullName
		entries = list(filter(same_name, my.characters.values()))
		if len(entries) < 2 or len(entries) > 3:
			print('Warning: No character by that name has 2~3 evolution stages.')
			return []
		return entries

	def get_char_module(my, char_name_or_id):
		"""Outputs a single character's module."""
		entries = my.get_char_entries(char_name_or_id)
		if not entries:
			return ''
		text = ''

	def get_char_template(my, char_name_or_id, english_name=''):
		"""Outputs a single character's template text to a file."""
		char_entries = my.get_char_entries(char_name_or_id)
		knight = FlowerKnight(char_entries)
		skill = my.skills[knight.skill]
		# Ability 1 is used by pre-evo and evo tiers.
		ability1 = my.abilities[knight.tiers['preEvo']['abilities'][0]]
		# Ability 2 is used by evo and bloom tiers.
		ability2 = my.abilities[knight.tiers['evo']['abilities'][1]]
		# Abilities 3 and 4 replace abilities 1 and 2 after blooming.
		ability3 = my.abilities[knight.tiers['bloom']['abilities'][0]]
		ability4 = my.abilities[knight.tiers['bloom']['abilities'][1]]
		
		#Lookup character equip
		dataEquipBase = dataEquipEvolved = []
		
		for line in my.equipment_entries:
			if line and line[21].partition('|')[0] == knight.charID1:
				mystery_number = int(line[2])
				if mystery_number >= 360000 and mystery_number < 380000:
					dataEquipBase.append(line)
				elif mystery_number >= 380000:
					dataEquipEvolved.append(line)
					personal_equip = True
		
		#Lookup flower family
		for line in my.masterTexts['masterPlantFamily']:
			if line.startswith(knight.family):
				family = line.split(",")
				break
		
		#Lookup flower meaning
		for line in my.masterTexts['masterFlowerBook']:
			if line.startswith(knight.charID1):
				meaning = line.split(",")
				break
		
		#Modifies English name to conform to IconName rule.
		icon_name = english_name.replace(' ','').replace('(','_').replace(')','')
		
		#Assembles the template data via repeated join and concatenations.
		template_text = ''.join(["{{CharacterStat\n|fkgID = ", knight.tiers['preEvo']['id'],
			"\n|type = ", attribList[knight.type],
			"\n|name = ", english_name,
			"\n|JP = ", knight.fullName,
			"\n|BasicCharImg = [[File:", icon_name, "_00.png|thumb|315x315px|center]]",
			"\n|EvoCharImg = [[File:", icon_name, "_01.png|thumb|315x315px|center]]",])
		if knight.bloomability == FlowerKnight.BLOOMABLE:
			template_text += "\n|BloomCharImg = [[File:" + icon_name + "_02.png|thumb|315x315px|center]]"
		template_text = ''.join([template_text,
			"\n|rarity = ", rarityStar(knight.rarity),
			"\n|IconName = ", icon_name,])
		if personal_equip:
			template_text += "\n|BasicEquipName = \n|BasicEquipJP = " + dataEquipBase[0][1]
			template_text += "\n|EvoEquipName = \n|EvoEquipJP = " + dataEquipEvolved[0][1]
		else:
			template_text += "\n|BasicEquipName = \n|BasicEquipJP = \n|EvoEquipName = \n|EvoEquipJP = "
		template_text = ''.join([template_text,
			"\n|likes = ", giftList[knight.gift],
			"\n|breed = ", family[1],
			"\n|nation = ", nationList[knight.nation],
			"\n|BasiclvlMax = ", knight.tiers['preEvo']['lvlCap'],
			"\n|BasicHPheartBonus = ", affectionCalc(knight.tiers['preEvo']['aff1'][0],0),
			"\n|BasicHPlv1 = ", knight.tiers['preEvo']['lvlOne'][0],
			"\n|BasicHPlv60 = ", knight.tiers['preEvo']['lvlMax'][0],
			"\n|BasicATKheartBonus = ", affectionCalc(knight.tiers['preEvo']['aff1'][1],0),
			"\n|BasicATKlv1 = ", knight.tiers['preEvo']['lvlOne'][1],
			"\n|BasicATKlv60 = ", knight.tiers['preEvo']['lvlMax'][1],
			"\n|BasicDEFheartBonus = ", affectionCalc(knight.tiers['preEvo']['aff1'][2],0),
			"\n|BasicDEFlv1 = ", knight.tiers['preEvo']['lvlOne'][2],
			"\n|BasicDEFlv60 = ", knight.tiers['preEvo']['lvlMax'][2],
			"\n|MVSpeed = ", knight.spd,
			"\n|EvolvlMax = ", knight.tiers['evo']['lvlCap'],
			"\n|EvoHPbloomBonus = ", affectionCalc(knight.tiers['evo']['aff1'][0], knight.tiers['evo']['aff2'][0]),
			"\n|EvoHPlv1 = ", knight.tiers['evo']['lvlOne'][0],
			"\n|EvoHPlv60 = ", knight.tiers['evo']['lvlMax'][0],
			"\n|EvoATKbloomBonus = ", affectionCalc(knight.tiers['evo']['aff1'][1], knight.tiers['evo']['aff2'][1]),
			"\n|EvoATKlv1 = ", knight.tiers['evo']['lvlOne'][1],
			"\n|EvoATKlv60 = ", knight.tiers['evo']['lvlMax'][1],
			"\n|EvoDEFbloomBonus = ", affectionCalc(knight.tiers['evo']['aff1'][2], knight.tiers['evo']['aff2'][2]),
			"\n|EvoDEFlv1 = ", knight.tiers['evo']['lvlOne'][2],
			"\n|EvoDEFlv60 = ", knight.tiers['evo']['lvlMax'][2]])
		if knight.bloomability != FlowerKnight.NO_BLOOM:
			template_text = ''.join([template_text,
				"\n|BloomlvlMax = ", knight.tiers['bloom']['lvlCap'],
				"\n|BloomHPheartBonus = ", affectionCalc(knight.tiers['evo']['aff1'][0], knight.tiers['bloom']['aff2'][0]),
				"\n|BloomHPlv1 = ", knight.tiers['bloom']['lvlOne'][0],
				"\n|BloomHPlv60 = ", knight.tiers['bloom']['lvlMax'][0],
				"\n|BloomATKheartBonus = ", affectionCalc(knight.tiers['evo']['aff1'][1], knight.tiers['bloom']['aff2'][1]),
				"\n|BloomATKlv1 = ", knight.tiers['bloom']['lvlOne'][1],
				"\n|BloomATKlv60 = ", knight.tiers['bloom']['lvlMax'][1],
				"\n|BloomDEFheartBonus = ", affectionCalc(knight.tiers['evo']['aff1'][2], knight.tiers['bloom']['aff2'][2]),
				"\n|BloomDEFlv1 = ", knight.tiers['bloom']['lvlOne'][2],
				"\n|BloomDEFlv60 = ", knight.tiers['bloom']['lvlMax'][2]])
		else:
			template_text += "\n|BloomHPheartBonus = \n|BloomHPlv1 = \n|BloomHPlv60 = \n|BloomATKheartBonus = \n|BloomATKlv1 = \n|BloomATKlv60 = \n|BloomDEFheartBonus = \n|BloomDEFlv1 = \n|BloomDEFlv60 = "
		if personal_equip:
			template_text = ''.join([template_text,
				"\n|BasicEquipATKLv1 = ", dataEquipBase[0][4],
				"\n|BasicEquipDEFLv1 = ", dataEquipBase[0][5],
				"\n|BasicEquipATKLvMax = ", dataEquipBase[0][7],
				"\n|BasicEquipDEFLvMax = ", dataEquipBase[0][8],
				"\n|EvoEquipATKLv1 = ", dataEquipEvolved[0][4],
				"\n|EvoEquipDEFLv1 = ", dataEquipEvolved[0][5],
				"\n|EvoEquipATKLvMax = ", dataEquipEvolved[0][7],
				"\n|EvoEquipDEFLvMax = ", dataEquipEvolved[0][8]])
		else:
			template_text += "\n|BasicEquipATKLv1 = \n|BasicEquipDEFLv1 = \n|BasicEquipATKLvMax = \n|BasicEquipDEFLvMax = \n|EvoEquipATKLv1 = \n|EvoEquipDEFLv1 = \n|EvoEquipATKLvMax = \n|EvoEquipDEFLvMax = "
		template_text = ''.join([template_text,
			"\n|SkillName = ",
			"\n|SkillNameJP = ", skill.getval('nameJapanese'),
			"\n|SkillLv1Trigger = ",skill.getval('triggerRateLv1'),
			"\n|SkillLv5Trigger = ",skillLv5Calc(skill.getval('triggerRateLv1'),skill.getval('triggerRateLvUp'),skill.getval('unknown00')),
			"\n|SkillDescription = ", skill.getval('descJapanese'),
			"\n|Passive1Description = ", ability1.getval('descJapanese'),
			"\n|Passive2Description = ", ability2.getval('descJapanese'),])
		if knight.bloomability != FlowerKnight.NO_BLOOM:
			template_text = ''.join([template_text,
				"\n|Passive3Description = ", ability3.getval('descJapanese'),
				"\n|Passive4Description = ", ability4.getval('descJapanese')])
		else:
			template_text += "\n|Passive3Description = \n|Passive4Description = "
		template_text += "\n|EvoEquipAbilityDescription = "
		if personal_equip:
			template_text += dataEquipEvolved[0][25].partition('※')[0]
		template_text = ''.join([template_text,
			"\n|ScientificName = ",
			"\n|CommonName = ",
			"\n|languageoftheflowers = ", meaning[5],
			"\n|RomajiName = ",
			"\n|NutakuName = ",
			"\n}}",])
		
		if CmdPrint: print(template_text)
		#rare_text()
		return template_text

def rarityStar(n):
	return u"★" * int(n)

def affectionCalc(Heart, Blossom):
	return str(math.floor((float(Heart) + float(Blossom)) * 1.2))
	
def skillLv5Calc(InitSkill,LevelSkill,SkillUpMultiplier):

	Skill     = int(InitSkill)
	SkillPlus = int(LevelSkill)
	SkillExp  = int(math.floor(float(SkillUpMultiplier) * 4))
	Skill5    = Skill + (SkillPlus * SkillExp)

	return str(Skill5)

def rare_text():
	RNG1 = random.randrange(0,9)
	RNG2 = random.randrange(0,9)
	
	if (RNG1 == RNG2): print("\n\n" + u"団長様、たまには私のことも構ってくださいね？")

def output_template(text, outfilename=DEFAULT_OUTFILENAME, append=True):
	has_data = append and os.path.exists(outfilename) and os.path.getsize(outfilename) > 0
	open_mode = 'a' if append else 'w'
	with open(outfilename, open_mode, encoding='UTF8') as outfile:
		if has_data:
			# Put spacing between the old and new text.
			outfile.write('\n\n')
		else:
			print("Creating new file: " + outfilename)
		outfile.write(text)
	
def downloadImageFunction(inputID,IconName,Bloom,EquipImgID,PowerOnly):
	
	#Create directory path if non-existant.
	if not os.path.exists(DEFAULT_ASSETPATH): os.makedirs(DEFAULT_ASSETPATH)

	dl_state = DL_OK
	
	if (Bloom and (PowerOnly == "0")):
		#download bloomed images only
		if dl_state == DL_OK: dl_state = downloadCharaImage(inputID,IconName,IMG_ICON,2)
		if dl_state == DL_OK: dl_state = downloadCharaImage(inputID,IconName,IMG_STAND,2)
	else:
		#download basic and evolved images, plus equipment images
		if dl_state == DL_OK: dl_state = downloadCharaImage(inputID,IconName,IMG_ICON,0)
		if dl_state == DL_OK: dl_state = downloadCharaImage(inputID,IconName,IMG_STAND,0)
		if dl_state == DL_OK: dl_state = downloadCharaImage(inputID,IconName,IMG_ICON,1)
		if dl_state == DL_OK: dl_state = downloadCharaImage(inputID,IconName,IMG_STAND,1)
		try:
			if dl_state == DL_OK:
				dl_state = downloadEquipImage(IconName,EquipImgID,"1")
		except KeyboardInterrupt: dl_state = DL_QUIT
		except: print(IconName + "'s personal equip is unavailable")
	return dl_state
	
getCharaURL = "http://dugrqaqinbtcq.cloudfront.net/product/images/character/"
imgPreLink  = { IMG_ICON:'i/',      IMG_STAND:'s/' }
imgTypeName = { IMG_ICON:'_icon0',  IMG_STAND:'_chara0'}
imgType     = { IMG_ICON:'icon_l_', IMG_STAND:'stand_s_' }
def downloadCharaImage(inputID,IconName,type,stage):

	#Check the Flower Knight's evolution stage, and refactor the ID appropriately.
	if (stage == 2): inputID += 300000
	else: inputID += stage
	
	#Calculate the hashed filename of the character images.
	KeyName = imgType[type] + str(inputID)
	hash = hashlib.md5(KeyName.encode('utf-8')).hexdigest()
	
	#Define the image link and filename.
	ImgFileLink = getCharaURL + imgPreLink[type] + hash + ".bin"
	ImgFileName = IconName + imgTypeName[type] + str(stage) + ".png"
	
	#Pass the variables to download function call.
	return downloadImage(ImgFileLink,ImgFileName,True)

def downloadEquipImage(ENName,imgID,stage):
	getEquipURL = "http://dugrqaqinbtcq.cloudfront.net/product/images/item/100x100/"
	
	ImgFileLink = getEquipURL + imgID + ".png"
	ImgFileName = ENName + "_equip0" + stage + ".png"

	return downloadImage(ImgFileLink,ImgFileName,False)
	

def downloadImage(inputLink,outputImageName,decflag):
	dl_state = DL_FAIL
	outputFile = os.path.join(DEFAULT_ASSETPATH, outputImageName)
	
	with open(outputFile,'wb') as imgFile:
		try:
			imgBuffer = urlopen(inputLink).read()
			if decflag: imgBuffer = zlib.decompress(imgBuffer)
		except KeyboardInterrupt:
			dl_state = DL_QUIT
		except:
			print("Unable to download " + outputImageName)
		else:
			imgFile.write(imgBuffer)
			print("Downloaded " + outputImageName)
			dl_state = DL_OK
	return dl_state

#def UploadImage(Image):

#def UploadData(dataKnight):

class UnitTest(object):
	"""Checks the validity of various parts of the program.

	To use this class, create an instance and call run_tests().

	UnitTest().run_tests()
	"""

	def __init__(my):
		pass

	def run_tests(my):
		my.unit_test_split_and_check_count()

	def unit_test_split_and_check_count(my):
		"""Tests the split_and_check_count function."""
		def test_print(vals, success, actual_count, expected_count):
			print('Vals: {{{0}}}. '\
				'Success: {1}. Actual count: {2}.'.format(
				','.join(vals), success, actual_count))
		oracle_str = 'a,b,c,'
		print('Testing with this CSV string: ' + oracle_str)
		print('This one should be shortened.')
		vals, success, actual_count = split_and_check_count(oracle_str, 1)
		test_print(vals, success, actual_count, len(oracle_str))
		print('This one should be correct.')
		vals, success, actual_count = split_and_check_count(oracle_str, 3)
		test_print(vals, success, actual_count, len(oracle_str))
		print('This one should be extended.')
		vals, success, actual_count = split_and_check_count(oracle_str, 6)
		test_print(vals, success, actual_count, len(oracle_str))

def action_prompt(master_data, input_name_or_id=None, english_name=''):
	"""Asks the user which function they want to use."""
	# Make the list of potential actions.
	ACT_EXIT = 'exit'
	ACT_HELP = 'help'
	ACT_INTROSPECT = 'introspect'
	ACT_UNIT_TEST = 'unit test'
	ACT_FIND_CHAR = 'find'
	ACT_GET_CHAR_TEMPLATE = 'char template'
	ACT_GET_CHAR_MODULE = 'char module'
	ACT_WRITE_SKILL_LIST = 'skill list'
	ACT_WRITE_ABILITY_LIST = 'ability list'
	ACT_WRITE_CHAR_NAME_LIST = 'char list'
	action_list = {
		ACT_EXIT:'Exit and return the parsed master data.',
		ACT_HELP:'List all actions.',
		ACT_UNIT_TEST:'Unit test some things.',
		ACT_INTROSPECT:'Activate the interactive prompt.',
		ACT_FIND_CHAR:'Find a character.',
		ACT_GET_CHAR_TEMPLATE:'Output a Character template.',
		ACT_GET_CHAR_MODULE:'Output a Character module.',
		ACT_WRITE_SKILL_LIST:'Write the Skill list (Skill ID:Skill Info).',
		ACT_WRITE_ABILITY_LIST:'Write the Ability list (Ability ID:Ability Info).',
		ACT_WRITE_CHAR_NAME_LIST:'Write the Character list (FKG ID:JP Name).',
	}
	def list_actions():
		for key, action in action_list.items():
			print('{0}: {1}'.format(key, action))

	# Begin the prompt loop for which action to take.
	list_actions()
	user_input = ''
	while user_input != ACT_EXIT:
		try:
			user_input = input('>>> Input the action you want to do: ')
		except ValueError:
			continue

		output_text = ''
		if user_input == ACT_INTROSPECT:
			introspecting = True
			print('Entering introspection mode.')
			#print('Set introspecting=False to stop.') # Apparently this doesn't work...
			print('Use Ctrl+C or input exit() to stop.')
			print('For convenience, p = print, and m = master_data')
			print("Hints: Try p(dir(m)), or a=m.preEvo_char_entries, or p(a[11].getval('id0'))")
			p = print
			m = master_data
			while introspecting:
				import logging
				# Warning: This logging code is only partially tested.
				# It is probably being used incorrectly.
				logging.basicConfig()
				logger = logging.getLogger('catch_all')
				try:
					# This 3-tuple format for exec works in Python 2 and 3.
					exec(input('>>> '), globals(), locals())
				except Exception as e:
					logger.exception(str(e))
		elif user_input == ACT_HELP:
			list_actions()
		elif user_input == ACT_UNIT_TEST:
			UnitTest.run_tests()
		elif user_input == ACT_WRITE_CHAR_NAME_LIST:
			output_text = master_data.get_char_list_page()
		elif user_input == ACT_GET_CHAR_TEMPLATE:
			output_template(master_data.get_char_template(input_name_or_id, english_name))
		elif user_input == ACT_GET_CHAR_MODULE:
			output_text = master_data.get_char_module(input_name_or_id)
		elif user_input == ACT_WRITE_SKILL_LIST:
			output_text = master_data.get_skill_list_page()
		elif user_input == ACT_WRITE_ABILITY_LIST:
			output_text = master_data.get_ability_list_page()
		elif user_input == ACT_FIND_CHAR:
			char_name_or_id = input("Input the character's Japanese name or ID: ")
			entries = master_data.get_char_entries(char_name_or_id)
			for entry in entries:
				print(entry.getlua() + '\n')
		elif user_input == ACT_GET_CHAR_MODULE:
			char_name_or_id = input("Input the character's Japanese name or ID: ")
			output_text = master_data.get_char_module(char_name_or_id)

		if output_text:
			with open(DEFAULT_OUTFILENAME, 'w', encoding="utf-8") as outfile:
				outfile.write(output_text)
			print('Completed the processing.')

def main(input_name_or_id=None, english_name=''):
	# Open and parse the master database
	master_data = MasterData(DEFAULT_INFILENAME)

	# Choose how to process the data.
	# Someday, it would be nice to turn this into a GUI.
	action_prompt(master_data, input_name_or_id, english_name)

	return master_data
	
if __name__ == '__main__':
	if ((type(findID) is list) and (type(english_nameList) is list)):
		li = 0
		for ID in findID:
			main(ID,english_nameList[li])
			li += 1
	else:
		if (type(english_nameList) is list):
			main(findID,english_nameList[0])
		else:
			if (type(english_nameList) is str):
				main(findID,english_nameList)
