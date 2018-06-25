#!/usr/bin/python
# coding=utf-8
from __future__ import print_function
import os, sys, math, re, random, zlib, hashlib, json, binascii, time
from base64 import b64decode
import six
from io import open
from common import *
from entry import *
from flowerknight import *

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
		my.characters = {c.id0:c for c in character_entries}
		my.pre_evo_chars = {c.id0:c for c in character_entries if
			c.isFlowerKnight1 == '1' and c.evolutionTier == '1'}
		# Compile a list of all flower knights from the CSVs.
		my.knights = {}
		# Dereference the dict for faster access.
		knights = my.knights
		unique_characters = my.unique_characters
		for char in character_entries:
			name = remove_quotes(char.fullName)
			if char.isFlowerKnight1 != '1':
				# This is not a flower knight. Remove its ability.
				if char.ability1ID in my.abilities:
					my.abilities.pop(char.ability1ID)
				unique_characters[name] = char
			elif name not in knights:
				knights[name] = FlowerKnight(char)
			else:
				knights[name].add_entry(char)

	def _parse_skill_entries(my):
		"""Creates a list of skill entries from masterCharacterSkill."""
		skill_entries = [SkillEntry(entry) for entry in my.masterTexts['masterSkill']]
		my.skills = {s.uniqueID:s for s in skill_entries}

	def _parse_ability_entries(my):
		"""Creates a list of ability entries from masterCharacterLeaderSkill."""
		ability_entries = [AbilityEntry(entry) for entry in my.masterTexts['masterAbility']]
		# Remove abilities related to Strengthening Synthesis.
		ability_entries = [entry for entry in ability_entries if
			u'合成' not in entry.shortDescJapanese]
		my.abilities = {a.uniqueID:a for a in ability_entries}

	def _parse_ability_desc_entries(my):
		"""Creates a list of ability description entries from the master data.

		It comes from masterCharacterLeaderSkillDescription.
		"""

		ability_desc_entries = [AbilityDescEntry(entry) for entry in my.masterTexts['masterAbilityDescs']]
		my.ability_descs = {a.id0:a for a in ability_desc_entries}
		
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
			remove_quotes(entry.gameVersionWhenAdded).split('.')
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
			knight_id = int(knight.charID2)
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
			return int(entry.uniqueID or 0)
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
			return int(entry.uniqueID)
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
			return int(entry.equipID)
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
		
	def get_personal_equip_list_page(my):
		"""Outputs the table of skill IDs and their related skill info."""
		# Write the page header.
		module_name = 'Module:SkillList'
		def getid(entry):
			return int(entry.uniqueID or 0)
		output = u'\n'.join([
			'--[[Category:Flower Knight description modules]]',
			'--[[Category:Equipment modules]]',
			'--[[Category:Automatically updated modules]]',
			'--Contains autogenerated list of personal equipments.\n',

			# Write the page body.
			'\t' +  u'\n\t'.join('{for FlowerKnight.full_name in MasterCharacterData}:{personalEquip()}'),

			# Write the page footer.
			'}\n',
			'return p',
			])
		return output

	def get_master_char_data_page(my):
		"""Outputs the table of every char's data and their related names."""
		module_name = 'Module:MasterCharacterData'
		def getname(entry):
			return entry.fullName
		def getid(entry):
			return int(entry.id0)
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

	EQUIPMENT_AFFIXES = [u'指輪', u'腕輪', u'首飾り', u'耳飾り',]
	def __remove_equipment_affix(my, name):
		"""Removes the type of equipment from the Japanese name.

		If the name does not have a generic affix, the name is returned as is.
		As a result, unique equipment will have their names returned in full.

		@param name: The Japanese name of the equipment.
		@returns The name without an affix.
		"""

		for affix in MasterData.EQUIPMENT_AFFIXES:
			if name.endswith(affix):
				return name[:-len(affix)]
		return name

	def __get_new_equipment_names_page_parse_page(my, page):
		"""Parses the Wikia page and returns the dict of equipment names.

		@returns: A dict of {'JP name':'EN name'} pairs.
		"""
		
		# Crop all text from the "return" statement and following { symbol.
		idx_start = page.text.find('return')
		idx_start += page.text[idx_start + 1:].find('{')
		idx_end = page.text.rfind('}')
		if idx_start < 0 or idx_end < 0:
			print("Error: Module:Equipment/Names doesn't have a table in it.")
			return {}

		# This text should be the entire table of equipment names.
		page_table = page.text[idx_start:idx_end]
		names = {}
		# Make the dict of {jp_name:en_name} entries.
		# Loop over all items except the "return {" start and "}" end.
		for line in page_table.split('\n')[1:-1]:
			line = line.strip()
			jp_name, en_name = line.split('=')

			# Get the Japanese name.
			idx_start = jp_name.find('["')
			idx_end = jp_name.find('"]')
			if idx_start < 0 or idx_end < 0:
				# This line doesn't have a proper table entry in it.
				print("Warning: Removing this line from Module:Equipment:")
				print(line)
				continue
			jp_name = jp_name[idx_start + 2:idx_end]
			# At this point, we have the entire Japanese name.
			# Cut off the の... part that designates the type of accessory.
			jp_name = my.__remove_equipment_affix(jp_name)
			if not jp_name:
				# Chances are, this is an Okitaeeru / Forge Spirit.
				# Do not add this to the list of equippable things.
				continue

			# Get the English name.
			idx_start = en_name.find('"')
			# +1 to skip over the first double-quote.
			idx_end = en_name[idx_start + 1:].find('"')
			if idx_start < 0 or idx_end < 0:
				# This line doesn't have a proper table entry in it.
				print("Warning: Removing this line from Module:Equipment:")
				print(line)
				continue
			# idx_start + 1 skips over the first double-quote.
			# idx_end + 2 accounts for the first double-quote and something else?
			en_name = en_name[idx_start + 1:idx_end + 2]
			names[jp_name] = en_name
		return names

	def get_new_equipment_names_page(my, page):
		"""Outputs the table of equipment names.

		The original Wikia page is passed into this function.
		This function recreates the list of Japanese equipment names and
		assigned English names. If the Japanese name is not found,
		it is inserted into the list with a default value.
		"""

		output = u''
		names = my.__get_new_equipment_names_page_parse_page(page)
		# Add all missing equipment from the master data to the Wikia's list.
		master_names = {}
		for equip in my.equipment:
			jp = equip.name
			jp = my.__remove_equipment_affix(jp)
			if jp in names:
				master_names[jp] = names[jp]
			else:
				master_names[jp] = ''
		# Sort the fully filled list for easy lookups on the Wikia page.
		sorted_name_indices = sorted(list(master_names))

		# Generate the Wikia page.
		equips = '\n    '.join(
			['["{0}"] = "{1}",'.format(idx, master_names[idx]) \
			for idx in sorted_name_indices])
		output = dedent(u'''
			--[[Category:Equipment modules]]
			--[[Category:Automatically updated modules]]
			--[[Category:Manually updated modules]]
			-- Relates Japanese equipment names to translated names.
			
			return {{
			    {0}
			}}''').lstrip().format(equips)
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
				fullName = my.characters[char_id].fullName
			else:
				print('Warning: No character by this ID exists: ' + \
					str(char_name_or_id))
				return []

		# Either we found the full name based on the ID or it was passed in.
		fullName = fullName or str(char_name_or_id)
		# Search for all evolution tiers for the character.
		def same_name(entry):
			return entry.fullName == fullName
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
			ability1ID = abilityInstance.ability1ID
			ability2ID = abilityInstance.ability2ID
			desc = abilityInstance.descJapanese

			# Increment the number of references found for this ability ID.
			# Also store some useful info as an example implementation of it.
			if ability1ID not in ref_counts:
				ref_counts[ability1ID] = [-1, '', 0, 0, 0]
				ref_counts[ability1ID][1] = abilityInstance.ability1Val0
				ref_counts[ability1ID][2] = abilityInstance.ability1Val1
				ref_counts[ability1ID][3] = abilityInstance.ability1Val2
				ref_counts[ability1ID][4] = u'See FIRST description / \n\t' +\
					desc
			ref_counts[abilityInstance.ability1ID][0] += 1

			if int(ability2ID) <= 0:
				# ID 0 is actually the "empty" ability for when the character doesn't
				# have an ability. We don't care about it.
				continue
			if ability2ID not in ref_counts:
				ref_counts[ability2ID] = [-1, '', 0, 0, 0]
				ref_counts[ability2ID][1] = abilityInstance.ability2Val0
				ref_counts[ability2ID][2] = abilityInstance.ability2Val1
				ref_counts[ability2ID][3] = abilityInstance.ability2Val2
				ref_counts[ability2ID][4] = u'See SECOND description / \n\t' +\
					desc
			ref_counts[abilityInstance.ability2ID][0] += 1

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
		dataEquipBase = []
		dataEquipEvolved = []
		personal_equip = False
		
		for line in my.equipment_entries:
			if ((line != '') and (line[21].partition('|')[0] == knight.tiers[1]['id'])):
				if ((int(line[2]) >= 360000) and (int(line[2]) < 380000)):
					dataEquipBase.append(line)
				elif (int(line[2]) >= 380000):
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
			"\n|JP = ", knight.fullName,])
		template_text = ''.join([template_text,
			"\n|rarity = ", rarityStar(knight.rarity),])
		if personal_equip:
			template_text += "\n|BasicEquipName = \n|BasicEquipJP = " + dataEquipBase[0][1]
			template_text += "\n|EvoEquipName = \n|EvoEquipJP = " + dataEquipEvolved[0][1]
		else:
			template_text += "\n|BasicEquipName = \n|BasicEquipJP = \n|EvoEquipName = \n|EvoEquipJP = "
		template_text = ''.join([template_text,
			"\n|likes = ", giftList[knight.gift],
			"\n|breed = ", family[1],
			"\n|nation = ", nationList[knight.nation],])
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
		template_text += "\n|EvoEquipAbilityDescription = "
		if personal_equip:
			template_text += "During combat, increase attack and defense power of all members with matching attribute by 2%."
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
