#!/usr/bin/python3
# coding=utf-8
from __future__ import print_function
import os, sys, math, re, random, zlib, hashlib, json, binascii, time
from base64 import b64decode
import six
from io import open
from textwrap import dedent, indent
from common import *

if sys.version_info.major >= 3:
	# The script is being run under Python 3.
	from urllib.request import urlopen
elif sys.version_info.major < 3:
	# The script is being run under Python 2.
	from urllib2 import urlopen
	# Make some changes so that the code looks and acts like Python 3.
	range = xrange
	input = raw_input

__doc__ = '''Parses getMaster and stores data in human-readable formats.'''

# Download state flags.
(DL_OK, # The download succeeded.
DL_FAIL, # The download failed.
DL_QUIT) = range(3) # The user forcefully stopped the download.

CmdPrint = True

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
	'2':['50','60','80'],
	'3':['50','60','80'],
	'4':['50','60','80'],
	'5':['60','70','80'],
	'6':['60','70','80'],
}

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
	"""Removes pairs of double-quotes around strings."""
	if text.startswith('"') and text.endswith('"'):
		return text[1:-1]
	return text

def add_quotes(text):
	"""Puts pairs of double-quotes around strings."""
	if text.startswith('"') and text.endswith('"'):
		return text
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
	# These are the rarity growth tiers the character is capable of.
	(NO_RARITY_GROWTH,
	HAS_RARITY_GROWTH) = range(2)

	# If a bug was found regarding how the data was parsed, state it only once.
	# When False, a message is printed and it turns to True.
	# When True, no message is printed.
	stated_integrity_bug = False

	def __init__(my, entries=[]):
		"""Constructor.

		@param entries: A list of 0~3 CharacterEntry instances.
			They would be the pre-evolved, evolved, and bloomed forms.
		"""

		# Unset the full name. When we get the 1st entry, this will be filled.
		my.fullName = ''
		# Organize the entries based on evolution tier.
		# They use the Lua list format: Indices start at 1.
		my.tiers = {1:{}, 2:{}, 3:{}, 4:{}}
		# Assume the character can't bloom or rarity grow.
		my.bloomability = FlowerKnight.NO_BLOOM
		my.growability = FlowerKnight.NO_RARITY_GROWTH
		# Store the latest date out of all CSV values.
		# This will be only calculated once on the fly once
		# get_latest_date is called.
		my.latest_date = None
		my.add_entries(entries)

	def add_entries(my, entries):
		"""Adds a list of CharacterEntry instances to this knight's data."""
		try:
			for entry in entries:
				# entries is a list of CharacterEntry instances.
				my.add_entry(entry)
		except TypeError:
			# entries was a single CharacterEntry instance.
			my.add_entry(entries)

	def add_entry(my, entry):
		"""Adds a CharacterEntry instance to this knight's data."""
		tier = entry.getval('evolutionTier')
		isRarityGrown = entry.getval('isRarityGrown') == '1'
		unknown03 = entry.getval('unknown03') == '1'
		unknown04 = entry.getval('unknown04') == '1'
		if tier == '1':
			my._add_tier1_entry(entry)
		elif tier == '2':
			my._add_tier2_entry(entry)
		elif (tier == '3' and not isRarityGrown) or \
			(tier == '99' and isRarityGrown and not unknown03 and unknown04):
			# tier = 3 means it is a 5* or 6* that can bloom.
			# tier = 99 means it is a 2-4* that can go beyond evolution.
			my._add_tier3_entry(entry)
		elif (tier == '4' and isRarityGrown) or \
			(tier == '99' and isRarityGrown and unknown03 and not unknown04):
			my._add_tier4_entry(entry)
		elif not FlowerKnight.stated_integrity_bug:
			print('Warning: CharacterEntry w/an invalid evolution tier.\n' \
				'The logic may be wrong or the CSVs have changed meanings.\n' \
				'Character {0} w/id {1} was an exception.\n'.format(
					entry.getval('fullName'), entry.getval('id0')) + \
				'Will ignore bugged entries and stop stating this message.')
			FlowerKnight.stated_integrity_bug = True

	def _add_common_data(my, entry):
		"""Stores info which should be the same for all evolution tiers."""
		if my.fullName:
			# The data is already stored.
			return
		my.fullName = entry.getval('fullName')
		my.rarity = entry.getval('rarity')
		my.spd = entry.getval('lvlOneSpd')
		# TODO: Rely on my.tiers[NUMBER]['skill'] instead.
		# The skill is no longer the same between all evolution tiers.
		# It changes if the character undergoes rarity growth.
		my.skill = entry.getval('skill1ID')
		my.family = entry.getval('family')
		my.type = entry.getval('type')
		my.nation = entry.getval('nation')
		my.gift = entry.getval('gift')
		my.is_event = entry.getval('isEventKnight')
		my.is_powers_only_bloom = entry.getval('isBloomedPowersOnly')
		my._determine_romaji()

	def _add_tier1_entry(my, entry):
		"""Stores the CharacterEntry's data as the pre-evolved info.

		As a side-effect of calling this method, some of the common
		information between all evolution tiers is stored in the class.
		"""
		
		my._add_common_data(entry)
		my.tiers[1]['id'] = entry.getval('id0')
		my.tiers[1]['lvlCap'] = maxLevel[my.rarity][0]
		my.tiers[1]['skill'] = entry.getval('skill1ID')
		my.tiers[1]['abilities'] = [entry.getval('ability1ID'), entry.getval('ability2ID')]
		my.tiers[1]['lvlOne'] = [entry.getval('lvlOneHP'), entry.getval('lvlOneAtk'), entry.getval('lvlOneDef')]
		my.tiers[1]['lvlMax'] = [entry.getval('lvlMaxHP'), entry.getval('lvlMaxAtk'), entry.getval('lvlMaxDef')]
		my.tiers[1]['aff1'] = [entry.getval('aff1MultHP'), entry.getval('aff1MultAtk'), entry.getval('aff1MultDef')]
		my.tiers[1]['aff2'] = [entry.getval('aff2MultHP'), entry.getval('aff2MultAtk'), entry.getval('aff2MultDef')]
		# Both date values and the game-version-when-added strings can differ between tiers.
		my.tiers[1]['date0'] = entry.getval('date0')
		my.tiers[1]['date1'] = entry.getval('date1')
		my.tiers[1]['gameVersionWhenAdded'] = entry.getval('gameVersionWhenAdded')
		# Only the pre-evolved entry has a sort ID because evolved/bloomed
		# pics aren't used in the library / 図鑑.
		my.charID1 = entry.getval('sortID')

	def _add_tier2_entry(my, entry):
		"""Stores the CharacterEntry's data as the evolved info."""
		my.tiers[2]['id'] = entry.getval('id0')
		my.tiers[2]['skill'] = entry.getval('skill1ID')
		my.tiers[2]['lvlCap'] = maxLevel[my.rarity][1]
		my.tiers[2]['abilities'] = [entry.getval('ability1ID'), entry.getval('ability2ID')]
		my.tiers[2]['lvlOne'] = [entry.getval('lvlOneHP'), entry.getval('lvlOneAtk'), entry.getval('lvlOneDef')]
		my.tiers[2]['lvlMax'] = [entry.getval('lvlMaxHP'), entry.getval('lvlMaxAtk'), entry.getval('lvlMaxDef')]
		my.tiers[2]['aff1'] = [entry.getval('aff1MultHP'), entry.getval('aff1MultAtk'), entry.getval('aff1MultDef')]
		my.tiers[2]['aff2'] = [entry.getval('aff2MultHP'), entry.getval('aff2MultAtk'), entry.getval('aff2MultDef')]
		my.tiers[2]['date0'] = entry.getval('date0')
		my.tiers[2]['date1'] = entry.getval('date1')
		my.tiers[2]['gameVersionWhenAdded'] = entry.getval('gameVersionWhenAdded')

	def _add_tier3_entry(my, entry):
		"""Stores the CharacterEntry's data as the bloomed info.

		Aa a side-effect of calling this method, the "bloomability" is set.
		"""

		if entry.getval('isBloomedPowersOnly') == "1":
			my.bloomability = FlowerKnight.BLOOM_POWERS_ONLY
		else:
			my.bloomability = FlowerKnight.BLOOMABLE
		my.tiers[3]['id'] = entry.getval('id0')
		my.tiers[3]['skill'] = entry.getval('skill1ID')
		my.tiers[3]['lvlCap'] = maxLevel[my.rarity][2]
		my.tiers[3]['abilities'] = [entry.getval('ability1ID'), entry.getval('ability2ID')]
		my.tiers[3]['lvlOne'] = [entry.getval('lvlOneHP'), entry.getval('lvlOneAtk'), entry.getval('lvlOneDef')]
		my.tiers[3]['lvlMax'] = [entry.getval('lvlMaxHP'), entry.getval('lvlMaxAtk'), entry.getval('lvlMaxDef')]
		my.tiers[3]['aff1'] = [entry.getval('aff1MultHP'), entry.getval('aff1MultAtk'), entry.getval('aff1MultDef')]
		my.tiers[3]['aff2'] = [entry.getval('aff2MultHP'), entry.getval('aff2MultAtk'), entry.getval('aff2MultDef')]
		my.tiers[3]['date0'] = entry.getval('date0')
		my.tiers[3]['date1'] = entry.getval('date1')
		my.tiers[3]['gameVersionWhenAdded'] = entry.getval('gameVersionWhenAdded')

	def _add_tier4_entry(my, entry):
		"""Stores the CharacterEntry's data as the rarity grown info.

		Aa a side-effect of calling this method, the "growability" is set.
		"""

		my.growability = FlowerKnight.HAS_RARITY_GROWTH
		my.tiers[4]['id'] = entry.getval('id0')
		# Rarity growth turns the character's rarity into a 6-star.
		my.tiers[4]['lvlCap'] = maxLevel['6'][2]
		my.tiers[4]['skill'] = entry.getval('skill1ID')
		my.tiers[4]['abilities'] = [entry.getval('ability1ID'), entry.getval('ability2ID')]
		my.tiers[4]['lvlOne'] = [entry.getval('lvlOneHP'), entry.getval('lvlOneAtk'), entry.getval('lvlOneDef')]
		my.tiers[4]['lvlMax'] = [entry.getval('lvlMaxHP'), entry.getval('lvlMaxAtk'), entry.getval('lvlMaxDef')]
		my.tiers[4]['aff1'] = [entry.getval('aff1MultHP'), entry.getval('aff1MultAtk'), entry.getval('aff1MultDef')]
		my.tiers[4]['aff2'] = [entry.getval('aff2MultHP'), entry.getval('aff2MultAtk'), entry.getval('aff2MultDef')]
		my.tiers[4]['date0'] = entry.getval('date0')
		my.tiers[4]['date1'] = entry.getval('date1')
		my.tiers[4]['gameVersionWhenAdded'] = entry.getval('gameVersionWhenAdded')

	def _determine_romaji(my):
		"""Determines the romaji spelling of the full name."""
		# TODO
		my.romajiName = '""'

	def can_evolve(my):
		"""Returns True if the character can evolve.

		Characters that can't evolve are either materials or skins."""
		return 'id' in my.tiers[2]

	def can_bloom(my):
		"""Returns True if the character can bloom."""
		return my.bloomability != FlowerKnight.NO_BLOOM

	def can_rarity_grow(my):
		"""Returns True if the character can rarity grow."""
		return my.growability != FlowerKnight.NO_RARITY_GROWTH

	def get_latest_date(my):
		"""Gets the latest date in all evolution tiers."""
		if my.latest_date:
			# The latest date was determined and stored.
			# Just return the pre-calculated value.
			return my.latest_date
		# Determine the latest date amongst all available dates.
		if my.bloomability == FlowerKnight.NO_BLOOM:
			# Cannot bloom or rarity grow.
			my.latest_date = max([
				my.tiers[1]['date0'],
				my.tiers[1]['date1'],
				my.tiers[2]['date0'],
				my.tiers[2]['date1'],])
		elif my.growability == FlowerKnight.NO_RARITY_GROWTH:
			# Can bloom, but not rarity grow.
			my.latest_date = max([
				my.tiers[1]['date0'],
				my.tiers[1]['date1'],
				my.tiers[2]['date0'],
				my.tiers[2]['date1'],
				my.tiers[3]['date0'],
				my.tiers[3]['date1'],])
		else:
			# Can bloom and rarity grow.
			my.latest_date = max([
				my.tiers[1]['date0'],
				my.tiers[1]['date1'],
				my.tiers[2]['date0'],
				my.tiers[2]['date1'],
				my.tiers[3]['date0'],
				my.tiers[3]['date1'],
				my.tiers[4]['date0'],
				my.tiers[4]['date1'],])
		return my.latest_date

	def has_id(my, id):
		"""Checks if the passed ID is related to this flower knight.

		@param id: String or integer. The ID to check.

		@returns: Boolean. True if the ID is related to this flower knight.
			False if the id is 0, a blank string, or an unrelated number.
		"""

		id = str(id)
		if not id:
			return False
		elif 'id' not in my.tiers[2]:
			# This flower knight is only a skin. It can't evolve.
			return id == my.tiers[1]['id']
		elif my.bloomability == FlowerKnight.NO_BLOOM:
			# This flower knight is evolvable, but not bloomable.
			return id in (my.tiers[1]['id'], my.tiers[2]['id'])
		elif my.growability == FlowerKnight.NO_RARITY_GROWTH:
			# This flower knight can bloom, but not rarity grow.
			return id in (my.tiers[1]['id'], my.tiers[2]['id'],
				my.tiers[3]['id'])
		else:
			# This flower knight can bloom and rarity grow.
			return id in (my.tiers[1]['id'], my.tiers[2]['id'],
				my.tiers[3]['id'], my.tiers[4]['id'])

	def get_lua(my, quoted=False):
		"""Returns the stored data as a Lua list.

		@param quoted: Boolean. When True, encloses string values
			of this class' variables in double-quotes.

		@returns: String. All variables of the class in Lua table format.
		"""

		#Fill out a string format table with descriptive variable names.
		formatDict = {
			'id':my.tiers[1]['id'],
			'charID':my.charID1,
			'type':my.type,
			'rarity':my.rarity,
			'isEvent':my.is_event,
			# Has bloom features?
			'tier3PowersOnlyBloom':my.is_powers_only_bloom,
			'gift':my.gift,
			'nation':my.nation,
			'family':my.family,
			'japanese':quotify_non_number(my.fullName),
			'dateAdded':quotify_non_number(my.tiers[1]['date0']),
			# Stats
			'speed':my.spd,
			# Pre-evolution stats.
			'tier1Lv1HP':my.tiers[1]['lvlOne'][HP],
			'tier1Lv1Atk':my.tiers[1]['lvlOne'][ATK],
			'tier1Lv1Def':my.tiers[1]['lvlOne'][DEF],
			'tier1LvMaxHP':my.tiers[1]['lvlMax'][HP],
			'tier1LvMaxAtk':my.tiers[1]['lvlMax'][ATK],
			'tier1LvMaxDef':my.tiers[1]['lvlMax'][DEF],
			# Bonus stats from affection 1 and 2.
			# Pre-evolution affection bonuses.
			'tier1Aff1HP':my.tiers[1]['aff1'][HP],
			'tier1Aff1Atk':my.tiers[1]['aff1'][ATK],
			'tier1Aff1Def':my.tiers[1]['aff1'][DEF],
			'tier1Aff2HP':my.tiers[1]['aff2'][HP],
			'tier1Aff2Atk':my.tiers[1]['aff2'][ATK],
			'tier1Aff2Def':my.tiers[1]['aff2'][DEF],
			# Abilities
			# Skill
			'skill':my.tiers[1]['skill'],
			}

		if my.can_evolve():
			formatDict.update({
				# Evolution stats.
				'tier2Lv1HP':my.tiers[2]['lvlOne'][HP],
				'tier2Lv1Atk':my.tiers[2]['lvlOne'][ATK],
				'tier2Lv1Def':my.tiers[2]['lvlOne'][DEF],
				'tier2LvMaxHP':my.tiers[2]['lvlMax'][HP],
				'tier2LvMaxAtk':my.tiers[2]['lvlMax'][ATK],
				'tier2LvMaxDef':my.tiers[2]['lvlMax'][DEF],
				# Evolution affection bonuses.
				'tier2Aff1HP':my.tiers[2]['aff1'][HP],
				'tier2Aff1Atk':my.tiers[2]['aff1'][ATK],
				'tier2Aff1Def':my.tiers[2]['aff1'][DEF],
				'tier2Aff2HP':my.tiers[2]['aff2'][HP],
				'tier2Aff2Atk':my.tiers[2]['aff2'][ATK],
				'tier2Aff2Def':my.tiers[2]['aff2'][DEF],
			})

		if my.can_bloom():
			formatDict.update({
				# Bloom stats.
				'tier3Lv1HP':my.tiers[3]['lvlOne'][HP],
				'tier3Lv1Atk':my.tiers[3]['lvlOne'][ATK],
				'tier3Lv1Def':my.tiers[3]['lvlOne'][DEF],
				'tier3LvMaxHP':my.tiers[3]['lvlMax'][HP],
				'tier3LvMaxAtk':my.tiers[3]['lvlMax'][ATK],
				'tier3LvMaxDef':my.tiers[3]['lvlMax'][DEF],
				# Bloom affection bonuses.
				'tier3Aff1HP':my.tiers[3]['aff1'][HP],
				'tier3Aff1Atk':my.tiers[3]['aff1'][ATK],
				'tier3Aff1Def':my.tiers[3]['aff1'][DEF],
				'tier3Aff2HP':my.tiers[3]['aff2'][HP],
				'tier3Aff2Atk':my.tiers[3]['aff2'][ATK],
				'tier3Aff2Def':my.tiers[3]['aff2'][DEF],
			})

		if my.can_rarity_grow():
			formatDict.update({
				'tier4skill':my.tiers[4]['skill'],
				# Rarity grown stats.
				'tier4Lv1HP':my.tiers[4]['lvlOne'][HP],
				'tier4Lv1Atk':my.tiers[4]['lvlOne'][ATK],
				'tier4Lv1Def':my.tiers[4]['lvlOne'][DEF],
				'tier4LvMaxHP':my.tiers[4]['lvlMax'][HP],
				'tier4LvMaxAtk':my.tiers[4]['lvlMax'][ATK],
				'tier4LvMaxDef':my.tiers[4]['lvlMax'][DEF],
				# Rarity grown affection bonuses.
				'tier4Aff1HP':my.tiers[4]['aff1'][HP],
				'tier4Aff1Atk':my.tiers[4]['aff1'][ATK],
				'tier4Aff1Def':my.tiers[4]['aff1'][DEF],
				'tier4Aff2HP':my.tiers[4]['aff2'][HP],
				'tier4Aff2Atk':my.tiers[4]['aff2'][ATK],
				'tier4Aff2Def':my.tiers[4]['aff2'][DEF],
			})

		#Generate specific portions of the table.
		ability1DEPRECATED = my.tiers[1]['abilities'][0]
		ability2DEPRECATED = ability3DEPRECATED = ability4DEPRECATED = ''

		tier2StatsString = tier2AffString = ''
		abilityString = '{{{0}, {1},}},'.format(
			my.tiers[1]['abilities'][0], my.tiers[1]['abilities'][1])
		if my.can_evolve():
			tier2StatsString = dedent('''
				tier2Lv1 = {{ {tier2Lv1HP}, {tier2Lv1Atk}, {tier2Lv1Def} }},
				tier2LvMax = {{ {tier2LvMaxHP}, {tier2LvMaxAtk}, {tier2LvMaxDef} }},
				''').lstrip().format(**formatDict)
			tier2AffString = dedent('''
				tier2Aff1Bonus = {{ {tier2Aff1HP}, {tier2Aff1Atk}, {tier2Aff1Def} }},
				tier2Aff2Bonus = {{ {tier2Aff2HP}, {tier2Aff2Atk}, {tier2Aff2Def} }},
				''').lstrip().format(**formatDict)
			my.tiers[1]['abilities'][0],
			if my.tiers[2]['abilities'][1]:
				ability2DEPRECATED = my.tiers[2]['abilities'][1]
			abilityString = abilityString + '\n    {{{0}, {1},}},'.format(
				my.tiers[2]['abilities'][0], my.tiers[2]['abilities'][1])

		tier3StatsString = tier3AffString = ''
		if my.can_bloom():
			tier3StatsString = dedent('''
				tier3Lv1 = {{ {tier3Lv1HP}, {tier3Lv1Atk}, {tier3Lv1Def} }},
				tier3LvMax = {{ {tier3LvMaxHP}, {tier3LvMaxAtk}, {tier3LvMaxDef} }},
				''').lstrip().format(**formatDict)
			tier3AffString = dedent('''
				tier3Aff1Bonus = {{ {tier3Aff1HP}, {tier3Aff1Atk}, {tier3Aff1Def} }},
				tier3Aff2Bonus = {{ {tier3Aff2HP}, {tier3Aff2Atk}, {tier3Aff2Def} }},
				''').lstrip().format(**formatDict)
			if my.tiers[3]['abilities'][0]:
				ability3DEPRECATED = my.tiers[3]['abilities'][0]
			if my.tiers[3]['abilities'][1]:
				ability4DEPRECATED = my.tiers[3]['abilities'][1]
			abilityString = abilityString + '\n    {{{0}, {1},}},'.format(
				my.tiers[3]['abilities'][0], my.tiers[3]['abilities'][1])

		tier4StatsString = tier4AffString = ''
		tier4SkillString = ''
		if my.can_rarity_grow():
			tier4StatsString = dedent('''
				tier4Lv1 = {{ {tier4Lv1HP}, {tier4Lv1Atk}, {tier4Lv1Def} }},
				tier4LvMax = {{ {tier4LvMaxHP}, {tier4LvMaxAtk}, {tier4LvMaxDef} }},
				''').lstrip().format(**formatDict)
			tier4AffString = dedent('''
				tier4Aff1Bonus = {{ {tier4Aff1HP}, {tier4Aff1Atk}, {tier4Aff1Def} }},
				tier4Aff2Bonus = {{ {tier4Aff2HP}, {tier4Aff2Atk}, {tier4Aff2Def} }},
				''').lstrip().format(**formatDict)
			if my.tiers[4]['abilities'][0]:
				ability3DEPRECATED = my.tiers[4]['abilities'][0]
			if my.tiers[4]['abilities'][1]:
				ability4DEPRECATED = my.tiers[4]['abilities'][1]
			abilityString = abilityString + '\n    {{{0}, {1},}},'.format(
				my.tiers[4]['abilities'][0], my.tiers[4]['abilities'][1])
			tier4SkillString = dedent('''
				tier4skill = {tier4skill},
				''').lstrip().format(**formatDict)

		# Make a comma-separated list of the ability IDs.
		abilityStringDEPRECATED = u', '.join([a for a in [ability1DEPRECATED, ability2DEPRECATED, ability3DEPRECATED, ability4DEPRECATED] if a])
		abilityStringDEPRECATED = '{{ {0} }}'.format(abilityStringDEPRECATED)

		# Add all of the generated strings to the string format table.
		formatDict.update({
			'tier2StatsString':tier2StatsString,
			'tier2AffString':tier2AffString,
			'tier3StatsString':tier3StatsString,
			'tier3AffString':tier3AffString,
			'tier4StatsString':tier4StatsString,
			'tier4AffString':tier4AffString,
			'abilityStringDEPRECATED':abilityStringDEPRECATED,
			'abilityString':abilityString,
			'tier4skill':tier4SkillString,
		})

		lua_table = dedent(u'''
			{{id = {id},
			charID = {charID},
			name = {japanese},
			type = {type},
			rarity = {rarity},
			isEvent = {isEvent},
			tier3PowersOnlyBloom = {tier3PowersOnlyBloom},
			likes = {gift},
			nation = {nation},
			family = {family},
			dateAdded = {dateAdded},
			skill = {skill},
			{tier4skill}ability = {abilityStringDEPRECATED}, -- Deprecated. Use bundledAbilities.
			bundledAbilities = {{ {abilityString} }},
			tier1Lv1 = {{ {tier1Lv1HP}, {tier1Lv1Atk}, {tier1Lv1Def} }},
			tier1LvMax = {{ {tier1LvMaxHP}, {tier1LvMaxAtk}, {tier1LvMaxDef} }},
			{tier2StatsString}{tier3StatsString}{tier4StatsString}speed = {speed},
			tier1Aff1Bonus = {{ {tier1Aff1HP}, {tier1Aff1Atk}, {tier1Aff1Def} }},
			tier1Aff2Bonus = {{ {tier1Aff2HP}, {tier1Aff2Atk}, {tier1Aff2Def} }},
			{tier2AffString}{tier3AffString}{tier4AffString}}}''').lstrip().format(**formatDict)

		return lua_table

	def __str__(my):
		return 'FlowerKnight: {0} who is a {1}* {2} type with pre-evo ID {3}.'.format(
			remove_quotes(my.fullName), my.rarity, attribList[my.type],
			my.tiers[1]['id'])

# Globalize the FlowerKnight constants for short access.
HP = FlowerKnight.HP
ATK = FlowerKnight.ATK
DEF = FlowerKnight.DEF

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
		if not success and not BaseEntry._WARN_WRONG_SIZE[entry_type]:
			print('WARNING: There are {0} values in a/an {1} entry instead of {2}.'.format(
				actual_count, entry_type, len(entries)))
			print('The format of getMaster may have changed.\n')
			# Don't state the warning again.
			BaseEntry._WARN_WRONG_SIZE[entry_type] = True

		# Store the values. We can access it with integer indices, or
		# indirectly using my._named_values. The latter is done through
		# the class instance's getval() function.
		my.values = values

		# Determine which values are strings.
		# It helps to store this because strings need enclosed in double-quotes
		# in the Lua code.
		#
		# NOTE: This list may be unused in the code right now.
		# Do a string search in the source code.
		if entry_type not in my._string_valued_indices:
			# This is the first time assigning double-quotes to strings for
			# CSV entries of this type of Entry. Make a list of all values
			# that are strings instead of numbers.

			# Implementation note: Check for equivalance to None instead of
			# duck-typing and checking for not(value). get_float can return
			# 0 or 0.0 for valid numbers, but None for non-numbers.
			my._string_valued_indices[entry_type] = \
				[i for i in range(len(my.values)) if \
				get_float(my.values[i]) is None]

		# Store a list of names to relate to the values.
		# This should be created in the child class.
		my._named_values = {}

	def getval(my, name_or_index):
		"""Returns a stored value by its name or index in the CSV."""
		if type(name_or_index) is int:
			return my.values[name_or_index]
		# The name_or_index is a string.
		return my.values[my._named_values[name_or_index]]

	def getlua(my, quoted=False):
		"""Returns the stored data as a Lua list.

		@param quoted: Boolean. When True, encloses string values
			of this class' variables in double-quotes.

		@returns: String. All variables of the class in Lua table format.
		"""

		string_transformer = get_quotify_or_do_nothing_func(quoted)

		# Generate the Lua table.
		if my._named_values:
			# Relate the named entries to their value.
			# This relies on how Python maintains order in dicts.
			# Example output: {name="Bob", type="cat", hairs=5},
			lua_table = u', '.join([u'{0}={1}'.format(
				k, string_transformer(my.values[v])) \
				for k, v in sorted(my._named_values.items())])
		else:
			# There's no dict of named entries-to-indices.
			# Just output all of the values separated by commas.
			# Example output: {"Bob", "cat", 5},
			lua_table = u', '.join([string_transformer(v) for v in my.values])

		# Surround the Lua table in angle brackets.
		return u'{{{0}}}'.format(lua_table)

	def __lt__(my, other):
		return my.tiers[1]['id'] < other.tiers[1]['id']

	def __repr__(my, named_entries=[]):
		"""Gets a string stating nearly everything about this instance."""
		if named_entries:
			return u'CSV fields by index, name, value:\n' + \
				u'\n'.join([u'{0:02}: {1} = {2}'.format(
					i, named_entries[i], my.getval(i)) \
				for i in range(len(my.values))])
		else:
			return my.__str__()

	def __str__(my):
		"""Gets a succinct string describing this instance."""
		return my.getlua()

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
		'ampule2BonusHP',
		'ampule2BonusAtk',
		'ampule2BonusDef',
		'goldSellValue',
		'sortCategory', # Unverified
		'sortID', # Used when viewing the library and sorting by "図鑑No"
		'isNotPreEvo',
		'isFlowerKnight1',
		'aff1MultHP',
		'aff1MultAtk',
		'aff1MultDef',
		'charID2',
		'evolutionTier',
		'isFlowerKnight2',
		'aff2MultHP',
		'aff2MultAtk',
		'aff2MultDef',
		'unknown01',
		'unknown02',
		'unknown03',
		'unknown04',
		'fullName',
		'isBloomedPowersOnly',
		'variant',
		'reading',
		'libraryID',
		'isSpecialSynthMat', # Added 12/4/2017. When 1, it's a Kodaibana, Ampule, or Naae.
		'isEventKnight', # Added 1/22/2018. When 1, it's an event character of any evolution tier. Doesn't include serial code girls.
		'date0',
		'date1',
		'unknown06',
		'gameVersionWhenAdded',
		# Added 3/5/2018. When non-zero, points to the character ID of what this
		# character would become after being rarity grown.
		'rarityGrownID',
		'isRarityGrown', # Added 3/12/2018.
		'canRarityGrow', # Added 3/12/2018.
		]

	def __init__(my, data_entry_csv):
		super(CharacterEntry, my).__init__(data_entry_csv, 'character',
			my.__NAMED_ENTRIES)
		if not my._named_values:
			# Create a dict that gives descriptive names to indices in the CSV.
			# As an example of what this does, it could set
			# my._named_values['id'] = 0
			my._named_values = dict(zip(my.__NAMED_ENTRIES,
				range(len(CharacterEntry.__NAMED_ENTRIES))))

	def getlua_name_to_id(my):
		return u'[{0}] = {1},'.format(
			add_quotes(my.getval('fullName')), my.getval('id0'))

	def getlua_id_to_name(my):
		return u'[{0}] = {1},'.format(
			my.getval('id0'), add_quotes(my.getval('fullName')))

	def __lt__(my, other):
		return my.getval('id0') < other.getval('id0')

	def __repr__(my):
		return super(CharacterEntry, my).__repr__(my.__NAMED_ENTRIES)

	def __str__(my):
		return 'CharacterEntry for {0} at evolution tier {1}: '.format(
			my.getval('fullName'), my.getval('evolutionTier')) + \
		super(CharacterEntry, my).__str__()

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
		'unknown01',
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

	def __lt__(my, other):
		return my.getval('uniqueID') < other.getval('uniqueID')

	def getlua(my, quoted=False):
		return u'[{0}] = {1},'.format(my.getval('uniqueID'),
			super(SkillEntry, my).getlua(quoted))

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
		'ability1Val3',
		'ability2ID',
		'ability2Val0',
		'ability2Val1',
		'ability2Val2',
		'ability2Val3',
		'ability3ID',
		'ability3Val0',
		'ability3Val1',
		'ability3Val2',
		'ability3Val3',
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

	def __lt__(my, other):
		return my.getval('uniqueID') < other.getval('uniqueID')

	def __repr__(my):
		return super(AbilityEntry, my).__repr__(my.__NAMED_ENTRIES)

	def getlua(my, quoted=False):
		"""Returns the stored data as a Lua list."""
		# Copy our dict of named values. Then remove the unneeded elements.
		named_values = dict(my._named_values)
		named_values.pop('shortDescJapanese')
		# Get a function that double-quotes strings if requested.
		string_transformer = get_quotify_or_do_nothing_func(quoted)
		# Compile a list of variable names-values pairs.
		lua_list = u', '.join([u'{0}={1}'.format(
			k, string_transformer(my.values[v])) \
			for k, v in sorted(named_values.items())])
		# Relate the list of values to the unique ID.
		return u'[{0}] = {{{1}}},'.format(my.getval('uniqueID'), lua_list)

class AbilityDescEntry(BaseEntry):
	"""Stores one line of data from the ability description section.

	In the master data, this section is named masterCharacterLeaderSkillDescription.
	"""

	__NAMED_ENTRIES = [
		'id0',
		'id1',
		'ability1icon',
		'ability1desc',
		'ability2icon',
		'ability2desc',
		'ability3icon',
		'ability3desc',
		'ability4icon',
		'ability4desc',]

	def __init__(my, data_entry_csv):
		super(AbilityDescEntry, my).__init__(data_entry_csv, 'ability description',
			my.__NAMED_ENTRIES)
		if not my._named_values:
			# Create a dict that gives descriptive names to indices in the CSV.
			# As an example of what this does, it could set
			# my._named_values['id'] = 0
			my._named_values = dict(zip(my.__NAMED_ENTRIES,
				range(len(AbilityDescEntry.__NAMED_ENTRIES))))

	def is_synthesis_ability(my):
		"""Returns True if the ability ID is for synthesis materials."""
		return u'合成' in my.getval('ability1desc')

	def __lt__(my, other):
		return my.getval('id0') < other.getval('id0')

	def __repr__(my):
		return super(AbilityDescEntry, my).__repr__(my.__NAMED_ENTRIES)

	def getlua(my, quoted=False):
		"""Returns the stored data as a Lua list."""
		return u'[{0}] = '.format(my.getval('id0')) + \
			super(AbilityDescEntry, my).getlua(quoted)

class EquipmentEntry(BaseEntry):
	__NAMED_ENTRIES = [
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
		'unknown00',
		'unknown01',
		'unknown02',
		'unknown03',
		'unknown04',
		'unknown05',
		'unknown06',
		'unknown07',
		'equipType', # Unverified
		'unknown08',
		'unknown09',
		'owners',
		'unknown10',
		'unknown11',
		'unknown12',
		'desc',
		'unknown13',
		'unknown14',
		'unknown15',
		'dateMade',
		'dateChanged',
		'zero',]

	def __init__(my, data_entry_csv):
		super(EquipmentEntry, my).__init__(data_entry_csv, 'equipment',
			my.__NAMED_ENTRIES)
		if not my._named_values:
			# Create a dict that gives descriptive names to indices in the CSV.
			# As an example of what this does, it could set
			# my._named_values['id'] = 0
			my._named_values = dict(zip(my.__NAMED_ENTRIES,
				range(len(EquipmentEntry.__NAMED_ENTRIES))))

	def __lt__(my, other):
		return my.getval('id0') < other.getval('id0')

	def __repr__(my):
		return super(EquipmentEntry, my).__repr__(my.__NAMED_ENTRIES)

	def __str__(my):
		return 'EquipmentEntry ID {0} named {1} owned by {2}.'.format(
			my.getval('id0'), my.getval('name'), my.getval('owners') or 'nobody')

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

		if not my.getval('owners'):
			return []
		return [int(id) for id in my.getval('owners').split(u'|')]

	def getlua(my, quoted=False):
		def string_transformer(key, val, quoted):
			if key == 'owners':
				# Change the format of owners from a stringly-type,
				# pipe-separated list of integers to a Lua list.
				# ex: owners=71|341 becomes owners={71, 341}
				return '{{{0}}}'.format( ', '.join(val.split('|')) )
			elif quoted:
				return quotify_non_number(val)
			return val

		# Generate the Lua table.
		# Relate the named entries to their value.
		# Example output: {name="Bob", type="cat", hairs=5},
		lua_table = u'[{0}] = {{'.format(my.getval('id0'))
		pairs = []
		for k, v in sorted(my._named_values.items()):
			v = string_transformer(k, my.values[v], quoted)
			pairs.append([k, v])
		lua_table += u', '.join([u'{0}={1}'.format(
			pair[0], pair[1]) for pair in pairs])
		lua_table += '}'
		return lua_table

class MasterData(object):
	"""Handles various info from the master data."""
	# Debugging variables.
	# When True, only store flower knights.
	remove_characters = False

	def __init__(my, infilename=''):
		my.masterTexts = {}
		my.characters = {}
		my.knights = {}
		my.pre_evo_chars = {}
		my.unique_characters = {}
		my.skills = {}
		my.abilities = {}
		my.ability_descs = {}
		my.equipment_entries = []
		my.equipment = {}
		my.load_getMaster(infilename)

	def _extract_section(my, section, rawdata):
		"""Gets all text from one section of the master data."""
		return rawdata.partition(section + '\n')[2][1:].partition('master')[0].strip().split('\n')

	def _parse_character_entries(my):
		"""Creates a list of character entries from masterCharacter."""
		# Start by parsing the CSV.
		# Store the CSV into understandable variable names.
		character_entries = [CharacterEntry(entry) for entry in my.masterTexts['masterCharacter']]
		# Store CSV entries in a dict such that their ID is their key.
		my.characters = {c.getval('id0'):c for c in character_entries}
		my.pre_evo_chars = {c.getval('id0'):c for c in character_entries if
			c.getval('isFlowerKnight1') == '1' and c.getval('evolutionTier') == '1'}
		# Compile a list of all flower knights from the CSVs.
		my.knights = {}
		# Dereference the dict for faster access.
		knights = my.knights
		unique_characters = my.unique_characters
		for char in character_entries:
			name = remove_quotes(char.getval('fullName'))
			if char.getval('isFlowerKnight1') != '1':
				# This is not a flower knight. Remove its ability.
				if char.getval('ability1ID') in my.abilities:
					my.abilities.pop(char.getval('ability1ID'))
				unique_characters[name] = char
			elif name not in knights:
				knights[name] = FlowerKnight(char)
			else:
				knights[name].add_entry(char)

	def _parse_skill_entries(my):
		"""Creates a list of skill entries from masterCharacterSkill."""
		skill_entries = [SkillEntry(entry) for entry in my.masterTexts['masterSkill']]
		my.skills = {s.getval('uniqueID'):s for s in skill_entries}

	def _parse_ability_entries(my):
		"""Creates a list of ability entries from masterCharacterLeaderSkill."""
		ability_entries = [AbilityEntry(entry) for entry in my.masterTexts['masterAbility']]
		# Remove abilities related to Strengthening Synthesis.
		ability_entries = [entry for entry in ability_entries if
			u'合成' not in entry.getval('shortDescJapanese')]
		my.abilities = {a.getval('uniqueID'):a for a in ability_entries}

	def _parse_ability_desc_entries(my):
		"""Creates a list of ability description entries from the master data.

		It comes from masterCharacterLeaderSkillDescription.
		"""

		ability_desc_entries = [AbilityDescEntry(entry) for entry in my.masterTexts['masterAbilityDescs']]
		my.ability_descs = {a.getval('id0'):a for a in ability_desc_entries}
		
	def _parse_equipment_entries(my):
		"""Creates a list of equipment entries from masterCharacterEquipment."""
		my.equipment_entries = [entry.split(',')[:-1] for entry in my.masterTexts['masterEquipment']]
		my.equipment = [EquipmentEntry(entry) for entry in my.masterTexts['masterEquipment']]

	def __decode_getMaster_encoded(my, infilename, diagnostics=False):
		"""Interprets getMaster's encoded data.

		Only call through _decode_getMaster.

		@param infilename: The raw getMaster file's name.
		@param diagnostics: If True, prints what the function is doing.
			Defaults to False.
		@returns On success, a string of the decoded data.
			On failure, False.
		"""

		with open(infilename, 'rb') as infile:
			bin_data = infile.read()

		try:
			bin_data_bytes = zlib.decompress(bin_data)
			bin_data_str = bin_data_bytes.decode("utf-8")
			jlist = json.loads(bin_data_str)
			out = u"";

			for key in jlist:
				element = jlist[key]
				try:
					if element:
						content = b64decode(element).decode('utf-8')
					else:
						content = u'nil'
					out += u'\n{0}\n\n{1}'.format(key, content)
				except (binascii.Error, TypeError):
					# This element might not be encrypted.
					content = element
					out += u'\n{0}\n\n{1}'.format(key, content)

			if diagnostics:
				print('Loaded {0} as zlib-compressed data.'.format(infilename))
			return out
		except:
			if diagnostics:
				print('Could not load {0} as zlib-compressed data.'.format(
					infilename))
		return False

	def __decode_getMaster_plain_text(my, infilename, diagnostics=False):
		"""Interprets getMaster's data as a pre-decoded text file.

		Only call through _decode_getMaster.

		@param infilename: The decoded getMaster file's name.
		@param diagnostics: If True, prints what the function is doing.
			Defaults to False.
		@returns On success, a string of the decoded data.
			On failure, False.
		"""

		try:
			# Assume it is the pre-decoded data.
			with open(infilename, 'rt', encoding='utf-8') as infile:
				bin_data = infile.read()
			if diagnostics:
				print('Loaded {0} as plain text.'.format(infilename))
			return bin_data
		except UnicodeDecodeError:
			if diagnostics:
				print('Could not load {0} as plain text.'.format(infilename))
		return False

	def _decode_getMaster(my, infilename='', diagnostics=False, output_result=False):
		"""Gets getMaster's data.

		@param infilename: The raw or decoded getMaster file's name.
			If unset, defaults to DEFAULT_GETMASTER_INFILENAME from common.py .
		@param diagnostics: If True, prints what the function is doing.
			Defaults to False.
		@param output_result: If True, also outputs the decoded data to
			DEFAULT_GETMASTER_OUTFILENAME from common.py . Defaults to False.
		@returns On success, a string of the decoded data.
			On failure, None.
		"""
		if not infilename:
			infilename = DEFAULT_GETMASTER_INFILENAME

		# Try as encoded (raw) data directly taken from in-game.
		master_data = my.__decode_getMaster_encoded(infilename, diagnostics)
		if not master_data:
			# Try as pre-decoded plain text.
			master_data = my.__decode_getMaster_plain_text(
				infilename, diagnostics)
		if not master_data:
			# Both methods failed. This isn't the master data file?
			return None

		if output_result:
			outfilename = DEFAULT_GETMASTER_OUTFILENAME
			with open(outfilename, 'w', encoding='utf-8') as outfile:
				outfile.write(time.strftime('Timestamp: %a, %m-%d-%Y\n', time.gmtime()))
				outfile.write(master_data)
			if diagnostics:
				print('Wrote the output to {0}.'.format(outfilename))
		return master_data

	def load_getMaster(my, infilename=''):
		"""Loads and parses getMaster.

		This function is called automatically if the constructor is given
		getMaster's filename in advance.
		"""

		# Open the master database
		api_data = my._decode_getMaster(infilename, True, True)
		
		# Extract relevant data from master database
		my.masterTexts['masterCharacter'] = my._extract_section('masterCharacter', api_data)
		my.masterTexts['masterSkill'] = my._extract_section('masterCharacterSkill', api_data)
		my.masterTexts['masterAbility'] = my._extract_section('masterCharacterLeaderSkill', api_data)
		my.masterTexts['masterAbilityDescs'] = my._extract_section('masterCharacterLeaderSkillDescription', api_data)
		my.masterTexts['masterPlantFamily'] = my._extract_section('masterCharacterCategory', api_data)
		my.masterTexts['masterFlowerBook'] = my._extract_section('masterCharacterBook', api_data)
		my.masterTexts['masterEquipment'] = my._extract_section('masterCharacterEquipment', api_data)

		# Parse character and equipment entries
		my._parse_skill_entries()
		my._parse_ability_entries()
		my._parse_ability_desc_entries()
		my._parse_equipment_entries()
		# Parse character entries AFTER ability and ability descriptions.
		# We need to remove abilities that belong to non-flower knights.
		my._parse_character_entries()

	def _convert_version_to_int(my, main_ver, major_ver, minor_ver):
		"""Turns a version date into a sortable integer.

		It converts version strings into a single number.
		For example, version "1.22.33" would become integer 1022033 .
		This allows you to sort Entry instances by version numbers.

		This is a helper function not meant to be called by other functions
		intending to sort Entry instances by version numbers.
		"""

		return int(main_ver)*10**6 + int(major_ver)*10**3 + int(minor_ver)

	def _sort_by_entrys_version_added(my, entry):
		"""Turns a CharacterEntry's version date into a sortable int.

		Use this function in a sort function like these examples.
		sorted(entry_list, key=MasterData._sort_by_entrys_version_added)
		sorted(my.characters.values(),
			key=MasterData._sort_by_entrys_version_added)
		"""

		main_ver, major_ver, minor_ver = \
			remove_quotes(entry.getval('gameVersionWhenAdded')).split('.')
		return my._convert_version_to_int(main_ver, major_ver, minor_ver)

	def get_newest_characters(my):
		"""Gets a list of only the most recently added characters.

		This function is good for finding which characters to update.
		"""

		# Get all character entries sorted by date from oldest to newest.
		def getdate(knight):
			return knight.get_latest_date()
		knights_by_date = [(getdate(char), char) for \
			char in sorted(my.knights.values(), key=getdate)]
		newest_date = knights_by_date[-1][0]
		# Remove all entries that aren't the newest date.
		knights_by_date = [(knight.fullName, knight) for date, knight in \
			knights_by_date if date == newest_date]
		return knights_by_date

	def get_knights_by_date(my):
		"""Gets a list of characters based on their stored dates.

		This function is good for finding which characters to update.

		To get the latest date of all flower knights, do this.
		master = MasterData()
		knights_by_date = master.get_knights_by_date()
		latest_date = max(knights_by_date)

		To get a sorted list of dates, do this.
		master = MasterData()
		knights_by_date = master.get_knights_by_date()
		dates = sorted(knights_by_date)

		To see the flower knights at the latest date, do this.
		latest_date = max(knights_by_date)
		for knight in knights_by_date[latest_date]:
			print(knight)

		@returns A dict of sets where keys are dates and
			values are FlowerKnights.
		"""

		def add_to_set(knight_dict, knight, val):
			"""Adds the flower knight to the set for some value.

			@param knight_dict: The dict of flower knights keyed by val.
			@param knight: A FlowerKnight instance. It becomes the value of
				the key-value pair.
			@param val: Any value you want to key the flower knights by.
				For example, dates or stats.

			If the set doesn't exist in the dict, it is initialized.
			If the flower knight is already in the dict, nothing happens.

			Returns the set with the knight added.
			"""

			if val not in knight_dict:
				knight_dict[val] = set()
			return knight_dict[val].union([knight])

		knights_by_date = {}
		for knight in my.knights.values():
			date = knight.tiers[1]['date0']; knights_by_date[date] = add_to_set(knights_by_date, knight, date)
			date = knight.tiers[1]['date1']; knights_by_date[date] = add_to_set(knights_by_date, knight, date)
			try:
				date = knight.tiers[2]['date0']; knights_by_date[date] = add_to_set(knights_by_date, knight, date)
				date = knight.tiers[2]['date1']; knights_by_date[date] = add_to_set(knights_by_date, knight, date)
			except KeyError:
				# This must be a skin-only flower knight. They do not evolve.
				pass
			if knight.bloomability != FlowerKnight.NO_BLOOM:
				date = knight.tiers[3]['date0']; knights_by_date[date] = add_to_set(knights_by_date, knight, date)
				date = knight.tiers[3]['date1']; knights_by_date[date] = add_to_set(knights_by_date, knight, date)

		return knights_by_date

	def get_personal_equipments(my, knight):
		"""Finds all equipment IDs tied to a FlowerKnight.

		The ID number is the shorter ID which does NOT change w/evolution.

		@param knight: A FlowerKnight entity or an ID number.
		@returns EquipmentEntry list. May be empty.
		"""

		if type(knight) is FlowerKnight:
			knight_id = int(knight.charID1)
		else:
			knight_id = int(knight)
		return [equip for equip in my.equipment if knight_id in equip.get_owner_ids()]

	def choose_knights_by_date(my):
		"""Gets a list of FlowerKnight instances based on their date.

		@returns A list of FlowerKnight instances. It can be empty.
		"""

		# Get the list of knights sorted by date.
		knights_by_date = my.get_knights_by_date()
		dates = sorted(knights_by_date, reverse=True)
		if not knights_by_date:
			print('Error: No list was compiled.')
			return []

		# State what options are available.
		print('Some of the available dates are as follows.')
		for i in range(min(len(dates), 3)):
			# Connect the names of the knights related to this date.
			names = ', '.join([k.fullName for k in knights_by_date[dates[i]]])
			# Make the description string.
			display_str = '{0}: {1} with {2}'.format(i, dates[i], names)
			# Crop the display string to fit in 80 characters.
			if len(display_str) > 80:
				display_str = display_str[:77] + u'...'
			print(display_str)

		# Get the option from the user.
		STOP_WORDS = ['exit', 'quit', 'stop', 'cancel', 'end']
		index = -1
		while index < 0 or index >= len(dates):
			index = input('Choose a date index from 0 to {0} (exit to end): '.format(
				len(dates)))

			# Stop if the user decided to quit.
			if index.lower() in STOP_WORDS:
				return []

			# Turn the inputted string into an integer.
			try:
				index = int(index)
			except ValueError:
				# Set the variable to redo the loop.
				index = -1
				continue

		return knights_by_date[dates[index]]

	def choose_knights(my):
		"""Prompts the user for which flower knights to work with.

		@returns: A list of FlowerKnight instances. May be empty.
		"""

		_METHODS = ["By inputting a character's name or ID.",
			'By getting all characters on some date.',
			'By using the embedded "findID" in the source code.',
			'Cancel.']

		# Determine how the user wants to look up the character.
		method = -1
		print('How do you want to look up the character?')
		for m in range(len(_METHODS)):
			print('{0}: {1}'.format(m, _METHODS[m]))
		while method < 0 or method >= len(_METHODS):
			try:
				method = int(input('>>> Input the method number: '))
			except ValueError:
				pass

		# The method is determined. Look up the character.
		knights = []
		if method == 0:
			name_or_id = input('>>> Input the character\'s Japanese name or ID: ')
			knights = [my.get_knight(name_or_id)]
		elif method == 1:
			knights = my.choose_knights_by_date()
		elif method == 2:
			knights = [my.get_knight(id) for id in findID]
		elif method == 3:
			print('Cancelled.')
		return knights

	def get_skill_list_page(my):
		"""Outputs the table of skill IDs and their related skill info."""
		# Write the page header.
		module_name = 'Module:SkillList'
		def getid(entry):
			return int(entry.getval('uniqueID') or 0)
		output = u'\n'.join([
			'--[[Category:Flower Knight description modules]]',
			'--[[Category:Automatically updated modules]]',
			'-- Relates skill IDs with their accompanying data.\n',
			'local p = {',

			# Write the page body.
			'\t' +  u'\n\t'.join([entry.getlua(True) for entry in
				sorted(my.skills.values(), key=getid)]),

			# Write the page footer.
			'}\n',
			'return p',
			])
		return output

	def get_bundled_ability_list_page(my):
		"""Outputs the table of bundled ability IDs and their related ability info."""
		# Write the page header.
		module_name = 'Module:BundledAbilityList'
		def getid(entry):
			return int(entry.getval('uniqueID'))
		output = u'\n'.join([
			'--[[Category:Flower Knight description modules]]',
			'--[[Category:Automatically updated modules]]',
			'-- Relates ability IDs with their accompanying data.\n',
			'local p = {',

			# Write the page body.
			'\t' + u'\n\t'.join([entry.getlua(True) for entry in
				sorted(my.abilities.values(), key=getid)]),

			# Write the page footer.
			'}\n',
			'return p',
			])
		return output

	def get_equipment_list_page(my):
		"""Outputs the table of equipment IDs and their related info."""
		# Write the page header.
		module_name = 'Module:Equipment/Data'
		def getid(entry):
			return int(entry.getval('id0'))
		equips = u',\n\t'.join([entry.getlua(True) for entry in
			sorted(my.equipment, key=getid)])
		output = dedent(u'''
			--[[Category:Equipment modules]]
			--[[Category:Automatically updated modules]]
			-- Relates equipment IDs with accompanying data.

			local EquipmentData = {{
				{0}
			}}

			return EquipmentData
			''').strip().format(equips)
		return output

	def get_master_char_data_page(my):
		"""Outputs the table of every char's data and their related names."""
		module_name = 'Module:MasterCharacterData'
		def getname(entry):
			return entry.getval('fullName')
		def getid(entry):
			return int(entry.getval('id0'))
		knights = u''
		for name in sorted(my.knights):
			knights += '["{0}"] =\n{1},\n'.format(
				my.knights[name].fullName,
				indent(my.knights[name].get_lua(), '    '))
		output = dedent(u'''
			--[[Category:Flower Knight description modules]]
			--[[Category:Automatically updated modules]]
			-- Relates character data to their IDs.
			
			return {{
			{0}}}
			''').strip().format(knights)
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
				print('Warning: No character by this ID exists: ' + \
					str(char_name_or_id))
				return []

		# Either we found the full name based on the ID or it was passed in.
		fullName = fullName or str(char_name_or_id)
		# Search for all evolution tiers for the character.
		def same_name(entry):
			return entry.getval('fullName') == fullName
		entries = list(filter(same_name, my.characters.values()))
		if len(entries) < 2 or len(entries) > 3:
			print('Warning: No character by that name has 2~3 evolution stages.')
			return []
		return entries

	def get_knight(my, name_or_id):
		"""Gets the FlowerKnight instance by ID or name."""
		# Test the name_or_id's type.
		# This is ordered loosely on processing speed and how often
		# it is expected to see name_or_id as some variable type.
		if type(name_or_id) is FlowerKnight:
			return name_or_id
		elif name_or_id in my.knights:
			# The passed value is a string: The character's name.
			return my.knights[name_or_id]
		elif type(name_or_id) is int or name_or_id.isdigit():
			# char_name_or_id was the character's ID.
			# Find the one entry for this character.
			matching_knights = [k for k in my.knights.values() \
				if k.has_id(name_or_id)]
			if len(matching_knights) == 1:
				return matching_knights[0]
			elif not len(matching_knights):
				print('Error: No character by ID {0} exists.'.format(
					name_or_id))
			else:
				print('Bug Error: There are {0} knights with ID {1}.'.format(
					len(matching_knights), name_or_id))
		else:
			print('There is no knight with the name {0}.'.format(name_or_id))
		return None

	def get_char_module(my, char_name_or_id):
		"""Outputs a single character's module."""
		knight = my.get_knight(char_name_or_id)
		skill = my.skills[knight.skill]
		bloomable = knight.bloomability != FlowerKnight.NO_BLOOM
		# Ability 1 is used by pre-evo and evo tiers.
		ability1 = knight.tiers[1]['abilities'][0]
		# Ability 2 is used by evo and bloom tiers.
		ability2 = knight.tiers[2]['abilities'][1]
		if bloomable:
			# Abilities 3 and 4 replace abilities 1 and 2 after blooming.
			ability3 = knight.tiers[3]['abilities'][0]
			ability4 = knight.tiers[3]['abilities'][1]
		
		module_name = 'Module:' + knight.fullName

		# TODO: Sanitize user data. It needs to start with a new line and end with }.
		userData = ''

		output = '''--[[Category:Flower Knight data modules]]
			-- Character module for {fullName}
			-- WARNING: This character's affection data is wrong.
			local p = {{}},

			-- Wikia editors can and should edit the userData table.
			p.userData = {{
				{userData}
			}}

			-- DO NOT EDIT!
			-- The master data comes from the game's data itself.
			p.masterData = {masterData}

			return p

			'''.format(fullName=knight.fullName, userData=userData,
				masterData=knight.get_lua(quoted=True))

		output = lua_indentify(output)

		return output

	def find_referenced_abilities(my):
		"""Finds all abilities that are referenced multiple times."""
		# Forewarning: The code below was thrown together as a hack job.
		# Please do not extend upon it unless you intend to clean it up.
		ref_counts = {}
		for abilityInstance in my.abilities.values():
			ability1ID = abilityInstance.getval('ability1ID')
			ability2ID = abilityInstance.getval('ability2ID')
			desc = abilityInstance.getval('descJapanese')

			# Increment the number of references found for this ability ID.
			# Also store some useful info as an example implementation of it.
			if ability1ID not in ref_counts:
				ref_counts[ability1ID] = [-1, '', 0, 0, 0]
				ref_counts[ability1ID][1] = abilityInstance.getval('ability1Val0')
				ref_counts[ability1ID][2] = abilityInstance.getval('ability1Val1')
				ref_counts[ability1ID][3] = abilityInstance.getval('ability1Val2')
				ref_counts[ability1ID][4] = u'See FIRST description / \n\t' +\
					desc
			ref_counts[abilityInstance.getval('ability1ID')][0] += 1

			if int(ability2ID) <= 0:
				# ID 0 is actually the "empty" ability for when the character doesn't
				# have an ability. We don't care about it.
				continue
			if ability2ID not in ref_counts:
				ref_counts[ability2ID] = [-1, '', 0, 0, 0]
				ref_counts[ability2ID][1] = abilityInstance.getval('ability2Val0')
				ref_counts[ability2ID][2] = abilityInstance.getval('ability2Val1')
				ref_counts[ability2ID][3] = abilityInstance.getval('ability2Val2')
				ref_counts[ability2ID][4] = u'See SECOND description / \n\t' +\
					desc
			ref_counts[abilityInstance.getval('ability2ID')][0] += 1

		# Organize all of the data.
		# The result, uniqueAbilities is a list of tuples with data members:
		# (ability ID, times referenced, example ability description)
		def sort_method(val):
			return int(val[0])
		uniqueAbilities = sorted( [(abilityID, count_and_desc) for
			abilityID, count_and_desc in ref_counts.items()], key=sort_method )

		# Output the results.
		print('The following unique abilities and example descriptions exist.')
		for info in uniqueAbilities:
			print('ID {0} referenced {1}x. Vals: {2}, {3}, {4}. Example: {5}'.format(
				info[0], info[1][0], info[1][1], info[1][2], info[1][3], info[1][4]))

		return uniqueAbilities

	def get_char_template(my, char_name_or_id, english_name=''):
		"""Outputs a single character's template text to a file."""
		knight = my.get_knight(char_name_or_id)
		skill = my.skills[knight.skill]
		# Ability 1 is used by pre-evo and evo tiers.
		ability1 = my.abilities[knight.tiers[1]['abilities'][0]]
		# Ability 2 is used by evo and bloom tiers.
		ability2 = my.abilities[knight.tiers[2]['abilities'][1]]
		# Abilities 3 and 4 replace abilities 1 and 2 after blooming.
		ability3 = ability4 = ''
		if knight.bloomability != FlowerKnight.NO_BLOOM:
			ability3 = my.abilities[knight.tiers[3]['abilities'][0]]
			ability4_id = knight.tiers[3]['abilities'][1]
			if ability4_id != '0':
				ability4 = my.abilities[ability4_id]
		
		#Lookup character equip
		dataEquipBase = dataEquipEvolved = []
		personal_equip = None
		
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
		template_text = ''.join(["{{CharacterStat\n|fkgID = ", knight.tiers[1]['id'],
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
			"\n|BasiclvlMax = ", knight.tiers[1]['lvlCap'],
			"\n|BasicHPheartBonus = ", affectionCalc(knight.tiers[1]['aff1'][0],0),
			"\n|BasicHPlv1 = ", knight.tiers[1]['lvlOne'][0],
			"\n|BasicHPlv60 = ", knight.tiers[1]['lvlMax'][0],
			"\n|BasicATKheartBonus = ", affectionCalc(knight.tiers[1]['aff1'][1],0),
			"\n|BasicATKlv1 = ", knight.tiers[1]['lvlOne'][1],
			"\n|BasicATKlv60 = ", knight.tiers[1]['lvlMax'][1],
			"\n|BasicDEFheartBonus = ", affectionCalc(knight.tiers[1]['aff1'][2],0),
			"\n|BasicDEFlv1 = ", knight.tiers[1]['lvlOne'][2],
			"\n|BasicDEFlv60 = ", knight.tiers[1]['lvlMax'][2],
			"\n|MVSpeed = ", knight.spd,
			"\n|EvolvlMax = ", knight.tiers[2]['lvlCap'],
			"\n|EvoHPbloomBonus = ", affectionCalc(knight.tiers[2]['aff1'][0], knight.tiers[2]['aff2'][0]),
			"\n|EvoHPlv1 = ", knight.tiers[2]['lvlOne'][0],
			"\n|EvoHPlv60 = ", knight.tiers[2]['lvlMax'][0],
			"\n|EvoATKbloomBonus = ", affectionCalc(knight.tiers[2]['aff1'][1], knight.tiers[2]['aff2'][1]),
			"\n|EvoATKlv1 = ", knight.tiers[2]['lvlOne'][1],
			"\n|EvoATKlv60 = ", knight.tiers[2]['lvlMax'][1],
			"\n|EvoDEFbloomBonus = ", affectionCalc(knight.tiers[2]['aff1'][2], knight.tiers[2]['aff2'][2]),
			"\n|EvoDEFlv1 = ", knight.tiers[2]['lvlOne'][2],
			"\n|EvoDEFlv60 = ", knight.tiers[2]['lvlMax'][2]])
		if knight.bloomability != FlowerKnight.NO_BLOOM:
			template_text = ''.join([template_text,
				"\n|BloomlvlMax = ", knight.tiers[3]['lvlCap'],
				"\n|BloomHPheartBonus = ", affectionCalc(knight.tiers[2]['aff1'][0], knight.tiers[3]['aff2'][0]),
				"\n|BloomHPlv1 = ", knight.tiers[3]['lvlOne'][0],
				"\n|BloomHPlv60 = ", knight.tiers[3]['lvlMax'][0],
				"\n|BloomATKheartBonus = ", affectionCalc(knight.tiers[2]['aff1'][1], knight.tiers[3]['aff2'][1]),
				"\n|BloomATKlv1 = ", knight.tiers[3]['lvlOne'][1],
				"\n|BloomATKlv60 = ", knight.tiers[3]['lvlMax'][1],
				"\n|BloomDEFheartBonus = ", affectionCalc(knight.tiers[2]['aff1'][2], knight.tiers[3]['aff2'][2]),
				"\n|BloomDEFlv1 = ", knight.tiers[3]['lvlOne'][2],
				"\n|BloomDEFlv60 = ", knight.tiers[3]['lvlMax'][2]])
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
			"\n|Passive1Description = ", ability1.getval('uniqueID'),
			"\n|Passive2Description = ", ability2.getval('uniqueID'),])
		if knight.bloomability != FlowerKnight.NO_BLOOM:
			template_text = ''.join([template_text,
				"\n|Passive3Description = ", ability3.getval('uniqueID'),
				"\n|Passive4Description = ", '0' if not ability4 else ability4.getval('uniqueID')])
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
