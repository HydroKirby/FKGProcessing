#!/usr/bin/python
# coding=utf-8
from __future__ import print_function
from common import *

__doc__ = """Stores classes for parsing CSV entries in the master data.

Do NOT make instances of BaseEntry. It is an abstract parent class.
Children of BaseEntry are called Entry classes in this project's source code.
Each instance of an Entry stores a single CSV line from the master data.
"""

def add_quotes(text):
	"""Surrounds the passed text to make it a valid Lua string.

	The result is ALWAYS encapsulated even if it was
	already a valid Lua string.

	@example foo			---> returns "foo"
	@example "foo"			---> returns '"foo"'
	@example "foo's bar"	---> returns [["foo's bar"]]
	@example 'foo'			---> returns "'foo'"
	"""

	if '"' in text:
		# Cannot encapsulate in double-quotes.
		if "'" in text:
			# Cannot encapsulate in quotes or double-quotes.
			# Gotta waste bytes and use double square-brackets.
			return '[[' + text + ']]'
		return "'" + text + "'"
	return '"' + text + '"'

def get_float(val):
	"""Checks if a value is a floating point number or not."""
	try:
		return float(val)
	except ValueError:
		return None

def quotify_non_number(text):
	"""Surrounds a non-numerical string in double quotes.

	This function is intended for outputting strings for Lua.
	Hence, numbers should be strings or numbers in Python, but
	strings themselves should be surrounded in double quotes.

	For example, this is a valid Lua table.
	sample_table = {val1=5, val2="cat"}
	If the passed "text" for this function is 5 or cat, it would be
	processed in that fashion.

	@param text: String. Intended to be a Lua table value.
	@returns: String. The value which gets double quotes if it is a string.
	"""

	try:
		float(text)
	except ValueError:
		return add_quotes(text)
	return text

def get_quotify_or_do_nothing_func(quoted):
	"""Gets a function that double-quotes strings or does nothing.

	The returned function can be used to make Lua tables.
	See "quotify_non_number" for more info.

	@param quoted: Boolean. Whether or not to add quotes.
	@returns: Function. It transforms strings.
	"""

	if quoted:
		string_transformer = quotify_non_number
	else:
		def asis(val):
			"""Returns the value as-is."""
			return val
		string_transformer = asis
	return string_transformer

def lua_indentify(text):
	"""Creates consistent indentation for Lua code.

	This removes all indentation and then adds indents after curly braces.
	It is intended to be used with triple-quoted strings.

	For example, this Lua code:
	p = {
		name="Foo",
		age=5,
	}

	... will have this type of indentation style, but "p" and "}" will
	have no indentation.

	@param text: A multi-line string.
	@returns: A string of the beautified text.
	"""

	num_indents = 0
	lines = []
	for line in text.splitlines():
		increment_indents = False
		if line.endswith('{'):
			increment_indents = True
		elif line.endswith('}'):
			num_indents = min(0, num_indents - 1)
		line = '\t' * num_indents + line.strip()
		if increment_indents:
			num_indents += 1
		lines += [line]
	return '\n'.join(lines)

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
		as many CSV as can fit into "entries" will be returned. success = False.

	Returns (entries, success, actual_count)
	"""

	data_entry_csv = data_entry_csv.rstrip()
	entries = [remove_quotes(entry) for entry in data_entry_csv.split(',')]

	actual_count = len(entries)
	if data_entry_csv.endswith(',') and entries[-1] == '':
		# Accomodate for the SOMETIMES trailing comma
		data_entry_csv = data_entry_csv[:-1]
		entries = entries[:-1]
		actual_count = len(entries)

	if actual_count < expected_count:
		# Add empty strings to fill in the blanks.
		entries += ['' for i in range(expected_count - actual_count)]
	elif actual_count > expected_count:
		# Crop off the excess entries.
		entries = entries[:expected_count]

	return (entries, expected_count == actual_count, actual_count)

class BaseEntry(object):
	"""Base class for deriving Entry classes.

	Usage: Make a child class from this and create two static variables:
	_MASTER_DATA_TYPE and _CSV_NAMES.
	_MASTER_DATA_TYPE is a string that simply states where in the master data
	the child class is getting its data from. It is only for diagnostics.
	_CSV_NAMES is a list of strings. It gives names to each CSV entry in
	a section of the master data. The names need to be valid variable names
	or else the setattr() function in the ctor will fail.

	Note: The CSV entries in the master data are stored such that
	numerical values are strings, and
	string values are strings enclosed in double-quotes.
	"""

	INVALID_ENTRY_TYPE = 'invalid'
	# Used to track which entries to enclose in double-quotes.
	_string_valued_indices = {}
	# If we encounter an invalid number of CSV entries, warn the user and set
	# the corresponding entry type to True. Only state the warning once.
	_WARN_WRONG_SIZE = {}

	def __init__(my, data_entry_csv):
		"""Ctor. To be overrridden and called by child classes."""
		if not len(my._CSV_NAMES) or not my._MASTER_DATA_TYPE:
			raise Exception(
			'Error: Instantiating BaseEntry class instead of a child class.')

		# Turn the CSV into a list.
		values, success, actual_count = split_and_check_count(
			data_entry_csv, len(my._CSV_NAMES))
		# Add this type of master data section to the list of checked sections.
		if my._MASTER_DATA_TYPE not in BaseEntry._WARN_WRONG_SIZE:
			BaseEntry._WARN_WRONG_SIZE[my._MASTER_DATA_TYPE] = False

		# Store the values.
		my.values_dict = dict(zip(my._CSV_NAMES, values))

		# Assign the CSV entries to member variables of this instance.
		# For example, if you have a CharacterEntry with _CVS_NAMES as
		# ['id0', 'id1', 'fullName']
		# then this lets you access the fields like so.
		# my_character_csv_instance.id0
		# my_character_csv_instance.fullName
		temp = dict(zip(range(len(my._CSV_NAMES)),
			my._CSV_NAMES))
		[setattr(my, temp[i], values[i]) for i in range(len(values))]

		# If the CSV parsing failed and there has not been a message given
		# about that, print an warning report.
		if not success and not BaseEntry._WARN_WRONG_SIZE[my._MASTER_DATA_TYPE]:
			print('WARNING: There are {0} values in a/an {1} entry instead of {2}.'.format(
				actual_count, my._MASTER_DATA_TYPE, len(my._CSV_NAMES)))
			print('The offending CSV was this:')
			# Remove any trailing newlines.
			print(data_entry_csv.rstrip())
			if actual_count <= 1:
				print('This is probably a parsing bug.')
			else:
				print('The format of getMaster may have changed. ' \
					'This is the current interpretation:')
				print(repr(my))
			# Don't state the warning again.
			BaseEntry._WARN_WRONG_SIZE[my._MASTER_DATA_TYPE] = True

		# Determine which values are strings.
		# It helps to store this because strings need enclosed in double-quotes
		# in the Lua code.
		#
		# NOTE: This list may be unused in the code right now.
		# Do a string search in the source code.
		#
		# TODO: Make this code work if it seems useful to have.
		if False and my._MASTER_DATA_TYPE not in my._string_valued_indices:
			# This is the first time assigning double-quotes to strings for
			# CSV entries of this type of Entry. Make a list of all values
			# that are strings instead of numbers.

			# Implementation note: Check for equivalance to None instead of
			# duck-typing and checking for not(value). get_float can return
			# 0 or 0.0 for valid numbers, but None for non-numbers.
			my._string_valued_indices[my._MASTER_DATA_TYPE] = \
				[i for i in range(len(values)) if \
				get_float(values[i]) is None]

	def getlua(my, quoted=False):
		"""Returns the stored data as a Lua list.

		@param quoted: Boolean. When True, encloses string values
			of this class' variables in double-quotes.

		@returns: String. All variables of the class in Lua table format.
		"""

		string_transformer = get_quotify_or_do_nothing_func(quoted)

		# Generate the Lua table.
		lua_table = u', '.join([u'{0}={1}'.format(
			name, string_transformer(my.values_dict[name])) \
			for name in sorted(my._CSV_NAMES)])

		# Surround the Lua table in angle brackets.
		return u'{{{0}}}'.format(lua_table)

	def __lt__(my, other):
		return my.tiers[1]['id'] < other.tiers[1]['id']

	def __repr__(my):
		"""Gets a string stating nearly everything about this instance."""
		return u'CSV fields by index, name, value:\n' + \
			u'\n'.join([u'{0:02}: {1} = {2}'.format(
				i, my._CSV_NAMES[i], my.values_dict[my._CSV_NAMES[i]]) \
			for i in range(len(my.values_dict))])

	def __str__(my):
		"""Gets a succinct string describing this instance."""
		return my.getlua()

class CharacterEntry(BaseEntry):
	"""Stores one line of data from the masterCharacter section."""
	_CSV_NAMES = [
		'id0',
		'id1',
		'family',
		'nation',
		'charID1', # Used as reference
		'baseName0',
		# 'baseName1', Deprecated on May 29, 2023.
		'rarity',
		'type',
		'gift',
		'ability1ID',
		'ability2ID',
		'ability3ID',
		'ability4ID',
		'ability5ID',
		'ability6ID',
		'ability7ID',
		'ability8ID',
		'ability9ID',
		'skill1ID',
		'skill2ID',
		# 'unused01', Added Feb 15, 2020. Deprecated on May 29, 2023.
		'lvlOneHP',
		'lvlMaxHP',
		'lvlOneAtk',
		'lvlMaxAtk',
		'lvlOneDef',
		'lvlMaxDef',
		'lvlOneSpd',
		'lvlMaxSpd', # Renamed Dec 24, 2019
		'ampuleBonusHP',
		'ampuleBonusAtk',
		'ampuleBonusDef',
		'ampule2BonusHP',
		'ampule2BonusAtk',
		'ampule2BonusDef',
		'goldSellValue',
		'sortCategory', #called MasterCharacterLVGroup in masterData
		'hasAlternateForm', # called MasterCharacterSecondLVGroup in masterData
		'evolvedCharacterID',
		'isNotPreEvo',
		'isFlowerKnight1',
		'aff1MultHP',
		'aff1MultAtk',
		'aff1MultDef',
		'charID2', # Used when viewing the library and sorting by "図鑑No"
		'evolutionTier',
		'isFlowerKnight2',
		'aff2MultHP',
		'aff2MultAtk',
		'aff2MultDef',
		'aff2EnableFlag',
		'bloomedCharacterID',
		'maxEvolutionFlag',
		'bloomingEnableFlag',
		'fullName',
		'isBloomedPowersOnly',
		'variant',
		'reading',
		'libraryID', # Note 11/4/2020: We now know this is used to matching skins to characters
		'isSpecialSynthMat', # Added 12/4/2017. When 1, it's a Kodaibana, Ampule, or Naae.
		'isEventKnight', # Added 1/22/2018. When 1, it's an event character of any evolution tier. Doesn't include serial code girls.
		'date0',
		# 'date1',  Appears to be no longer in use.
		# 'unused02', Appears to be no longer in use.
		'gameVersionWhenAdded',
		# Added 3/5/2018. When non-zero, points to the character ID of what this
		# character would become after being rarity grown.
		'rarityGrownID',
		'isRarityGrown', # Added 3/12/2018.
		'canRarityGrow', # Added 3/12/2018.
		#'date2', # Seems to be added around 01-Jan-2020. Appears to be no longer in use.
		'isNazuna', # Added February 06, 2023.
		]
	_MASTER_DATA_TYPE = 'character'

	def __init__(my, data_entry_csv):
		super(CharacterEntry, my).__init__(data_entry_csv)

	def getlua_name_to_id(my):
		return u'[{0}] = {1},'.format(add_quotes(my.fullName), my.id0)

	def getlua_id_to_name(my):
		return u'[{0}] = {1},'.format(my.id0, add_quotes(my.fullName))

	def __lt__(my, other):
		return my.id0 < other.id0

	def __str__(my):
		return 'CharacterEntry for {0} at evolution tier {1}: '.format(
			my.fullName, my.evolutionTier) + \
			super(CharacterEntry, my).__str__()

class SkillEntry(BaseEntry):
	"""Stores one line of data from the masterCharacterSkill section."""
	_CSV_NAMES = [
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
		'unknown01',
		'date00',
		'date01',
		'unknown02',
	]
	_MASTER_DATA_TYPE = 'skill'

	def __init__(my, data_entry_csv):
		super(SkillEntry, my).__init__(data_entry_csv)

	def __lt__(my, other):
		return my.uniqueID < other.uniqueID

	def getlua(my, quoted=False):
		return u'[{0}] = {1},'.format(my.uniqueID,
			super(SkillEntry, my).getlua(quoted))

class AbilityEntry(BaseEntry):
	"""Stores one line of data from the ability section.

	In the master data, this section is named masterCharacterLeaderSkill.
	"""
	_CSV_NAMES = [
		'uniqueID',
		'ability1ID',
		'ability1Val5',
		'ability1Val0',
		'ability1Val1',
		'ability1Val2',
		'ability1Val3',
		'ability1Val4',
		'ability1Val6',
		'ability2ID',
		'ability2Val5',
		'ability2Val0',
		'ability2Val1',
		'ability2Val2',
		'ability2Val3',
		'ability2Val4',
		'ability2Val6',
		'ability3ID',
		'ability3Val5',
		'ability3Val0',
		'ability3Val1',
		'ability3Val2',
		'ability3Val3',
		'ability3Val4',
		'ability3Val6',
	]
	_MASTER_DATA_TYPE = 'ability'

	def __init__(my, data_entry_csv):
		super(AbilityEntry, my).__init__(data_entry_csv)

	def __lt__(my, other):
		return my.uniqueID < other.uniqueID

	def getlua(my, quoted=False):
		"""Returns the stored data as a Lua list."""
		#New CSV format
		my.abilityList1 = [
			my.ability1ID, my.ability1Val0,
			my.ability1Val1, my.ability1Val2, my.ability1Val3,
			my.ability1Val4, my.ability1Val5, my.ability1Val6,
		]
		my.abilityList2 = [
			my.ability2ID, my.ability2Val0,
			my.ability2Val1, my.ability2Val2, my.ability2Val3,
			my.ability2Val4, my.ability2Val5, my.ability2Val6,
		]
		my.abilityList3 = [
			my.ability3ID, my.ability3Val0,
			my.ability3Val1, my.ability3Val2, my.ability3Val3,
			my.ability3Val4, my.ability3Val5, my.ability3Val6,
		]
        #Flags used to prune unused abilities.
		my.abilityFlag2 = sum(int(p) for p in my.abilityList2) != 0
		my.abilityFlag3 = sum(int(p) for p in my.abilityList3) != 0

        #Append abilities
		lua_list = [u'{{{0}}}'.format(",".join(my.abilityList1))]
		if my.abilityFlag2 or my.abilityFlag3:
			lua_list.append(u'{{{0}}}'.format(",".join(my.abilityList2)))
		if my.abilityFlag3:
			lua_list.append(u'{{{0}}}'.format(",".join(my.abilityList3)))
		# Relate the list of values to the unique ID.
		return u'[{0}]={{{1}}},'.format(my.uniqueID, ",".join(lua_list))

class AbilityDescEntry(BaseEntry):
	"""Stores one line of data from the ability description section.

	In the master data, this section is named masterCharacterLeaderSkillDescription.
	"""

	_CSV_NAMES = [
		'id0',
		'id1',
		'ability1icon',
		'ability1desc',
		'ability2icon',
		'ability2desc',
		'ability3icon',
		'ability3desc',
		'ability4icon',
		'ability4desc',
	]
	_MASTER_DATA_TYPE = 'ability description'

	def __init__(my, data_entry_csv):
		super(AbilityDescEntry, my).__init__(data_entry_csv)

	def is_synthesis_ability(my):
		"""Returns True if the ability ID is for synthesis materials."""
		return u'合成' in my.ability1desc

	def __lt__(my, other):
		return my.id0 < other.id0

	def getlua(my, quoted=False):
		"""Returns the stored data as a Lua list."""
		return u'[{0}] = '.format(my.id0) + \
			super(AbilityDescEntry, my).getlua(quoted)

class EquipmentEntry(BaseEntry):
	_CSV_NAMES = [
		'id0',
		'name',
		'equipID',
		'lvlOneHP',
		'lvlOneAtk',
		'lvlOneDef',
		'lvlMaxHP',
		'lvlMaxAtk',
		'lvlMaxDef',
		'baseAbilityID',
		'ability1ID',
		'ability1Val0',
		'ability1Val1',
		'ability1Val2',
		'ability2ID',
		'ability2Val0',
		'ability2Val1',
		'ability2Val2',
		#'equipPart', # See note 1 below
		'equipType',
		'isPersonalEquip',
		'owners',
		'classification', # See note 2 below
		'isLevelable', # 0 for forging fairy or ability bracelet; 1 otherwise
		'isForgingFairy',
		'desc',
		'commonEquipPlusValue',
		'personalEquipSortID',
		'evolveID',
		'MaxEvolveFlag',
		'WorldFlowerPowerType', # Boosts damage in World Flower missions with matching nation.
		'classification2', # See note 3 below
		'EffectType', # 20001 for all rainbow-rarity event equipments, 0 otherwise.
	]	
	# Note 1: CSV "equipPart" has the following meanings. Is now deprecated.
	# 300001: All gacha rings.
	# 300002: All gacha bracelets.
	# 300003: All gacha necklaces.
	# 300004: Everything else.

	# Note 2: CSV "classification" is the easiest way to determine the rarity.
	# It has the following meanings.
	# 1:   1* bracelets and necklaces (gacha low tier).
	# 3:   3* bracelets and necklaces (gacha mid & high tier;
	#          not EX for either),
	#      2* rings and earrings (gacha low tier).
	# 5:   4* event equipment (not the bracelet),
	#      4* rings and earrings (gacha mid & high tier; not EX for either),
	#      EX bracelet and necklace.
	# 7:   EX ring and earrings,
	#      5* event bracelet,
	#      personal earrings and personal evolved equips.
	# 101: Copper forge spirits.
	# 102: Silver forge spirits.
	# 103: Gold forge spirits.

	# Note 3: CSV "classification2" indicates the equipment type.
	# It has the following meanings.
	# 10:  Generic equipments, promotional equipments and forging fairies.
	# 20:  Personal earrings.
	# 21:  5* personal equipment.
	# 22:  6* personal equipment.
	# 30:  5* anniversary personal equipment.
	# 32:  6* anniversary personal equipment.
	# 40:  5* event and whaleship-stage equipments.
	# 42:  6* event equipments.
	# 50:  EX equipments.
	_MASTER_DATA_TYPE = 'equipment'

	def __init__(my, data_entry_csv):
		super(EquipmentEntry, my).__init__(data_entry_csv)

	def __lt__(my, other):
		return my.id0 < other.id0

	def __str__(my):
		return 'EquipmentEntry ID {0} named {1} owned by {2}.'.format(
			my.equipID, my.name, my.owners or 'nobody')

	def get_owner_ids(my):
		"""Gets the IDs of flower knights that own this equipment.

		Returns a list of 0 or more stringly-typed integers.
		No elements means this equipment can be publicly used.
		One element means it's a personal equipment.
		Two or more elements means it's a special personal equipment
			awarded to all base forms of some flower knight.

		The owners value separates multiple flower knights with
			pipe | characters.

		@returns A list of 0 or more integers.
		"""

		if not my.owners:
			return []
		return [int(id) for id in my.owners.split(u'|')]

	def string_transformer(my, key, val, quoted):
		if key == 'owners':
			# Change the format of owners from a stringly-type,
			# pipe-separated list of integers to a Lua list.
			# ex: owners=71|341 becomes owners={71, 341}
			return '{{{0}}}'.format( ', '.join(val.split('|')) )
		elif quoted:
			return quotify_non_number(val)
		return val

	def table_transformer(my, list, quoted=False):
		if sum([int(val) for val in list]) == 0:
			# Remove zero entries 
			# ex: {0,0,0,0} becomes {}
			return '{}'
		elif quoted:
			return quotify_non_number("{{{0}}}".format(",".join(list)))
		return "{{{0}}}".format(",".join(list))

	def getlua(my, quoted=False):
		#Removes unused variables.
		my.values_dict.pop('desc')
		my.values_dict.pop('equipID')

		# Generate the Lua table.
		# Relate the named entries to their value.
		# Example output: {name="Bob", type="cat", hairs=5},
		lua_table = u'[{0}] = {{'.format(my.equipID)
		pairs = []
		for k, v in sorted(my.values_dict.items()):
			v = my.string_transformer(k, v, quoted)
			pairs.append([k, v])
		lua_table += u', '.join([u'{0}={1}'.format(
			pair[0], pair[1]) for pair in pairs])
		lua_table += '}'
		return lua_table
		
	def getcompactlua(my, quoted=False):
		"""Returns the stored data as a Lua list."""
		#New CSV format
		my.values_dict.pop('desc')
		# Relate the list of values to the unique ID.
		return "[{0}]={{{1}}}".format(
			my.values_dict.pop("equipID"),
			",".join([v for k, v in my.values_dict.items()])
		)

	def getmodularlua(my, moduleType=False, quoted=False):
		"""Returns the stored data as a Lua list."""
		#New CSV format
		
		#Control text if the equipment data entry is invalid for whatever reason.
		outputEntry = '{}'
		
		if moduleType == "stats":
			statsTable = [
				my.table_transformer([my.lvlOneAtk, my.lvlMaxAtk, my.lvlOneDef, my.lvlMaxDef]),
			]

			if my.ability1ID != "0" and my.ability2ID != "0":
				statsTable.append(
					my.table_transformer(
						[my.ability1ID, my.ability1Val0, my.ability1Val1, my.ability1Val2]
					)
				)

			if my.ability2ID != "0":
				statsTable.append(
					my.table_transformer(
						[my.ability2ID, my.ability2Val0, my.ability2Val1, my.ability2Val2]
					)
				)

			outputEntry = "{0}".format(",".join(statsTable))

		elif moduleType == "unique":
			outputEntry = "{0}".format(
				",".join(
					[
						quotify_non_number(my.name),
						my.personalEquipSortID,
						my.isPersonalEquip,
						my.string_transformer("owners", my.owners, quoted),
					]
				)
			)
		elif moduleType == "misc" :
			outputEntry = "{0}".format(
				",".join(
					[
						my.id0,
						my.equipType,
						my.classification,
						my.isLevelable,
						my.isForgingFairy,
						my.commonEquipPlusValue,
						my.evolveID,
						my.MaxEvolveFlag,
						my.WorldFlowerPowerType,
						my.classification2,
						my.EffectType,
					]
				)
			)
		else:
			outputEntry = ",".join([v for k,v, in my.values_dict.items()])

		#lua_list = [u'{{{0}}}'.format(",".join(my.values_dict))]
		# Relate the list of values to the unique ID.
		return u'[{0}]={{{1}}}'.format(my.equipID, outputEntry)

class SkinEntry(BaseEntry):
	"""Stores one line of data from the masterCharacterSkin section."""
	_CSV_NAMES = [
		# This ID matches the character's unique ID
		'uniqueID',
		'libraryID',
		# replaceID for "different version" skins is uniqueID w/"000" appended
		# Ex: If uniqueID is 134207000, replaceID is 134207
		# replaceID for "exclusive" skins is just zero
		# Ex: If uniqueID is 132901001, replaceID is 0
		'replaceID',
		# isSkin is set for any skins. When true, it implies
		# (uniqueID != replaceID) and (isDiffVer or isExclusive)
		'isSkin',
		# For minor skin changes like Warunasubi/Nightshade without her mask
		# skinName is always "別バージョン"
		'isDiffVer',
		# For skin-only characters like Young Cattleya or Swimsuit Anemone
		# This flag is mutually exclusive with isDiffVer
		# Example skinName: "モコモコした服(専用)" for Oenothera/Pinkladies
		'isExclusive',
		# Name category as shown on the skin selection modal
		'skinName',
		# Order of icons for on the skin selection modal
		'pos',
		'dateAdded',
		# Perhaps this flag is only for Ping Pong Mum?
		'unknown00',
	]
	# This defines which vars get shown in getlua()
	_LUA_ORDER = [
		'libraryID', 'replaceID', 'isDiffVer', 'isExclusive', 'skinName'
	]
	_MASTER_DATA_TYPE = 'skin'

	def __init__(my, data_entry_csv):
		super(SkinEntry, my).__init__(data_entry_csv)

	def __lt__(my, other):
		return my.uniqueID < other.uniqueID

	def getlua(my, quoted=False):
		"""Returns the stored data as a Lua list.

		@param quoted: Boolean. When True, encloses string values
			of this class' variables in double-quotes.

		@returns: String. All variables of the class in Lua table format.
		"""

		string_transformer = get_quotify_or_do_nothing_func(quoted)

		# Generate the Lua table.
		lua_table = u', '.join([u'{0}={1}'.format(
			name, string_transformer(my.values_dict[name])) \
			for name in my._LUA_ORDER])

		# Surround the Lua table in angle brackets.
		return u'{{{0}}}'.format(lua_table)

class FlowerMemoryEntry(BaseEntry):
	"""Stores one line of data from the masterFlowerMemory section."""
	_CSV_NAMES = [
		'id',
		'flowerMemoryID',
		'name',
		'readingName',
		'rarity',
		'orderNum',
		'growthType',
		'lvlOneHP',
		'HPPerLevel',
		'lvlOneAtk',
		'AtkPerLevel',
		'lvlOneDef',
		'DefPerLevel',
		'desc',
		'AbilityLv0LimitBreak',
		'AbilityMaxLimitBreak',
	]
	# This defines the additional data to be appended to Lua entry
	_LUA_EXTRA_DATA = [
		'AbilityLv0LimitBreak', 'AbilityMaxLimitBreak'
	]
	_MASTER_DATA_TYPE = 'flower_memory'

	def __init__(my, data_entry_csv):
		super(FlowerMemoryEntry, my).__init__(data_entry_csv)

	def __lt__(my, other):
		return my.id < other.id

	def string_transformer(my, val, quoted):
		if val.find('|') != -1 :
			# Change the format of owners from a stringly-type,
			# pipe-separated list of integers to a Lua list.
			# ex: owners=71|341 becomes owners={71, 341}
			return '{{{0}}}'.format( ', '.join(val.split('|')) )
		elif quoted:
			return quotify_non_number(val)
		return val

	def getlua_debug(my, quoted=False):
		return u'[{0}] = {1},'.format(my.id,
			super(FlowerMemoryEntry, my).getlua(quoted))
			
		lua_table = u'[{0}] = {{'.format(my.id)
		pairs = []
		for k, v in sorted(my.values_dict.items()):
			v = my.string_transformer(v, quoted)
			pairs.append([k, v])
		lua_table += u', '.join([u'{0}={1}'.format(
			pair[0], pair[1]) for pair in pairs])
		lua_table += '}'
		return lua_table

	def getlua(my, quoted=False):
		"""Returns the stored data as a Lua list."""
		# Removes unused data entries.
		my.values_dict.pop('id')
		my.values_dict.pop('desc')
		# Relate the list of values to the unique ID.
		return "[{0}]={{{1}}}".format(
			my.values_dict.pop('flowerMemoryID'), ",".join([my.string_transformer(v, quoted) for k, v in my.values_dict.items()])
		)

class FlowerMemoryAbilityEntry(BaseEntry):
	"""Stores one line of data from the masterAbility section.
	
	Used as ability reference for Flower Memories across Limit Breaks.
	"""
	_CSV_NAMES = [
		'id',
		'name',
		'effectID',
		'optionID',
		'desc',
		'value1',
		'value2',
		'value3',
		'value4'
	]
	_MASTER_DATA_TYPE = 'flower_memory_ability'

	def __init__(my, data_entry_csv):
		super(FlowerMemoryAbilityEntry, my).__init__(data_entry_csv)

	def __lt__(my, other):
		return my.id0 < other.id0

	def getlua(my, quoted=False):
		"""Returns the stored data as a Lua list."""
		# Removes unused data entries.
		my.values_dict.pop('name')
		my.values_dict.pop('desc')
		# Relate the list of values to the unique ID.
		return "[{0}]={{{1}}}".format(
			my.values_dict.pop('id'), ",".join([v for k, v in my.values_dict.items()])
		)

class FlowerMemoryAbilityLookup(BaseEntry):
	"""Stores one line of data from the masterFlowerMemorysAbilitys section.
	
	Used as ability reference for Flower Memories across Limit Breaks.
	"""
	_CSV_NAMES = [
		'id',
		'flowerMemoryID',
		'limitBreakVal',
		'abilityId',
	]
	_MASTER_DATA_TYPE = 'flower_memory_ability_lookup'

	def __init__(my, data_entry_csv):
		super(FlowerMemoryAbilityLookup, my).__init__(data_entry_csv)

class BlessedOathLookup(BaseEntry):
	"""Stores one line of data from the masterCharacterSamePerson section.
	
	Used as character ID reference for Blessed Eternal Oath (in-game wedding) flags.
	"""
	_CSV_NAMES = [
		'sameCharacterID',
		'name',
		'marriageBlessingFlag',
	]
	_MASTER_DATA_TYPE = 'eternal_oath'

	def __init__(my, data_entry_csv):
		super(BlessedOathLookup, my).__init__(data_entry_csv)

	def getlua(my, quoted=False):
		"""Returns the sameCharacterID as a Lua list."""
		if my.marriageBlessingFlag == '1':
			return "{0}".format(my.sameCharacterID)
		else:
			return ''
