#!/usr/bin/python
# coding=utf-8
from __future__ import print_function
import os, sys
import six
from io import open
from getmaster_loader import *
from common import *
from entry import *
from flowerknight import *
from getmaster_outputter import MasterDataOutputter

if sys.version_info.major >= 3:
	# The script is being run under Python 3.
	from urllib.request import urlopen
elif sys.version_info.major < 3:
	# The script is being run under Python 2.
	from urllib2 import urlopen
	# Make some changes so that the code looks and acts like Python 3.
	range = xrange
	input = raw_input

__doc__ = '''Parses getMaster and stores data in human-readable formats.

getmaster_loader is for decoding the data.
parse_master is for interpreting and organizing the data.
getmaster_outputter is for outputting the organized data for the Wikia.
'''

class MasterData(object):
	"""Handles various info from the master data."""
	# Debugging variables.
	# When True, only store flower knights.
	remove_characters = False

	def __init__(my):
		# Most of these are deprecated 
		my.masterTexts = {}
		my.characters = {}
		my.knights = {}
		my.unique_characters = {}
		my.skills = {}
		my.abilities = {}
		my.ability_descs = {}
		my.equipment_entries = []
		my.equipment = {}
		my.skins = {}

		# This is the new way to access the master data.
		my.entries = {}
		my.entry_ids = {}
		my.load_getMaster()

		my.outputter = MasterDataOutputter(my)

	def _extract_section(my, section, rawdata):
		"""Gets all text from one section of the master data."""
		# Find the section header
		full_str_pos = 0
		section_idx = 0
		found_section = None
		while full_str_pos < len(rawdata) and found_section != section:
			section_idx = rawdata.find(section, full_str_pos)
			if section_idx < 0:
				print('Could not find the section called ' + section)
				return ''
			newline_idx = max(0, rawdata.find('\n', section_idx))
			found_section = rawdata[section_idx:newline_idx].strip()
			full_str_pos = section_idx + 1
		# We found the header, so take all text after it
		str_beyond_section = rawdata[section_idx + len(section):].lstrip()
		str_until_next_section = str_beyond_section.partition('master')[0]
		str_until_next_section = str_until_next_section.strip()
		data_lines = str_until_next_section.split('\n')
		return data_lines

	def _parse_character_entries(my, api_data=[]):
		"""Creates a list of character entries from masterCharacter."""
		# Start by parsing the CSV.
		# Store the CSV into understandable variable names.
		character_entries = [CharacterEntry(entry) for entry in api_data]
		# Store CSV entries in a dict such that their ID is their key.
		my.characters = {c.id0:c for c in character_entries}
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

	def _parse_skill_entries(my, api_data=[]):
		"""Creates a list of skill entries from masterCharacterSkill."""
		skill_entries = [SkillEntry(entry) for entry in api_data]
		my.skills = {s.uniqueID:s for s in skill_entries}

	def _parse_ability_entries(my, api_data=[]):
		"""Creates a list of ability entries from masterCharacterLeaderSkill."""
		ability_entries = [AbilityEntry(entry) for entry in api_data]
		# Remove abilities related to Strengthening Synthesis.
		ability_entries = [entry for entry in ability_entries if
			u'合成' not in entry.shortDescJapanese]
		my.abilities = {a.uniqueID:a for a in ability_entries}

	def _parse_ability_desc_entries(my, api_data=[]):
		"""Creates a list of ability description entries from the master data.

		It comes from masterCharacterLeaderSkillDescription.
		"""

		ability_desc_entries = [AbilityDescEntry(entry) for entry in api_data]
		my.ability_descs = {a.id0:a for a in ability_desc_entries}
		
	def _parse_equipment_entries(my, api_data=[]):
		"""Creates a list of equipment entries from masterCharacterEquipment."""
		my.equipment_entries = [entry.split(',')[:-1] for entry in api_data]
		my.equipment = [EquipmentEntry(entry) for entry in api_data]

	def _parse_skin_entries(my, api_data=[]):
		"""Creates a list of skin entries from masterCharacterSkin."""
		my.skin_entries = [entry.split(',')[:-1] for entry in api_data]
		my.skins = [SkinEntry(entry) for entry in api_data]

	def load_getMaster(my):
		"""Loads and parses getMaster.

		This function is called automatically if the constructor is given
		getMaster's filename in advance.
		"""

		# Open the master database.
		loader = MasterDataLoader()
		api_data = loader.master_json

		# Output the result for debugging purposes
		loader.output_getMaster_plaintext()
		
		# Extract relevant data from master database
		
		if loader.master_text:
			# Parse data from the old format as a massive CSV string
			mt = loader.master_text
			my.masterTexts['masterCharacter'] = my._extract_section('masterCharacter', mt)
			my.masterTexts['masterSkill'] = my._extract_section('masterCharacterSkill', mt)
			my.masterTexts['masterAbility'] = my._extract_section('masterCharacterLeaderSkill', mt)
			my.masterTexts['masterAbilityDescs'] = my._extract_section('masterCharacterLeaderSkillDescription', mt)
			my.masterTexts['masterPlantFamily'] = my._extract_section('masterCharacterCategory', mt)
			my.masterTexts['masterFlowerBook'] = my._extract_section('masterCharacterBook', mt)
			my.masterTexts['masterEquipment'] = my._extract_section('masterCharacterEquipment', mt)
			data_skill = my.masterTexts['masterSkill']
			data_abil = my.masterTexts['masterAbility']
			data_abil_desc = my.masterTexts['masterAbilityDescs']
			data_equip = my.masterTexts['masterEquipment']
			data_char = my.masterTexts['masterCharacter']
			data_skin = my.masterTexts['masterCharacterSkin']
		else:
			# Parse data from the new format stored as a dict
			data_skill = [dat for dat in api_data['masterCharacterSkill'].split('\n') if dat]
			data_abil = [dat for dat in api_data['masterCharacterLeaderSkill'].split('\n') if dat]
			data_abil_desc = [dat for dat in api_data['masterCharacterLeaderSkillDescription'].split('\n') if dat]
			data_equip = [dat for dat in api_data['masterCharacterEquipment'].split('\n') if dat]
			data_char = [dat for dat in api_data['masterCharacter'].split('\n') if dat]
			data_skin = [dat for dat in api_data['masterCharacterSkin'].split('\n') if dat]

		# Parse character and equipment entries
		my._parse_skill_entries(data_skill)
		my._parse_ability_entries(data_abil)
		my._parse_ability_desc_entries(data_abil_desc)
		my._parse_equipment_entries(data_equip)
		my._parse_skin_entries(data_skin)
		# Parse character entries AFTER ability and ability descriptions.
		# We need to remove abilities that belong to non-flower knights.
		my._parse_character_entries(data_char)

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

	def get_skill_list_page(self):
		"""Outputs the table of skill IDs and their related skill info."""
		return self.outputter.get_skill_list_page()

	def get_bundled_ability_list_page(self):
		"""Outputs the table of bundled ability IDs and their related ability info."""
		return self.outputter.get_bundled_ability_list_page()

	def get_equipment_list_page(self):
		"""Outputs the table of equipment IDs and their related info."""
		return self.outputter.get_equipment_list_page()
		
	def get_personal_equip_list_page(self):
		"""Outputs the table of skill IDs and their related skill info."""
		return self.outputter.get_personal_equip_list_page()

	def get_master_char_data_page(self):
		"""Outputs the table of every char's data and their related names."""
		return self.outputter.get_master_char_data_page()

	def get_new_equipment_names_page(self, page):
		"""Outputs the table of equipment names."""
		return self.outputter.get_new_equipment_names_page(page)

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

	def get_char_template(self, char_name_or_id, english_name=''):
		"""Outputs a single character's template text to a file."""
		return self.outputter.get_char_template(char_name_or_id, english_name)

	def get_skin_info_page(self):
		"""Outputs the table of skin IDs and their related info."""
		return self.outputter.get_skin_info_page()
