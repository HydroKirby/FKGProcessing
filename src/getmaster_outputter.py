#!/usr/bin/python
# coding=utf-8
import six
from common import *
from textwrap import dedent

__doc__ = """Handles the output of the master data into Wikia pages.

getmaster_loader is for decoding the data.
parse_master is for interpreting and organizing the data.
getmaster_outputter is for outputting the organized data for the Wikia.
"""

class MasterDataOutputter(object):
	def __init__(self, master_data=None):
		self.md = master_data

	def get_skill_list_page(self):
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
				sorted(self.md.skills.values(), key=getid)]),

			# Write the page footer.
			'}\n',
			'return p',
			])
		return output

	def get_bundled_ability_list_page(self):
		"""Outputs the table of bundled ability IDs and their related ability info."""
		# Write the page header.
		module_name = 'Module:BundledAbilityList'
		def getid(entry):
			return int(entry.uniqueID)
		output = u'\n'.join([
			'--[[Category:Flower Knight description modules]]',
			'--[[Category:Automatically updated modules]]',
			'-- Relates ability IDs with their accompanying data.',
			'return {',

			# Write the page body.
			u'\n'.join([entry.getlua(True) for entry in
				sorted(self.md.abilities.values(), key=getid)]),
			# Write the page footer.
			'}'
			])
		return output

	def get_equipment_list_page(self):
		"""Outputs the table of equipment IDs and their related info."""
		# Write the page header.
		module_name = 'Module:Equipment/Data'
		def getid(entry):
			return int(entry.equipID)
		equips = u',\n\t'.join([entry.getmodularlua("misc", True) for entry in
			sorted(self.md.equipment, key=getid)])
		output = dedent(u'''
			--[[Category:Equipment modules]]
			--[[Category:Automatically updated modules]]
			-- Relates equipment IDs with accompanying data.

			local EquipmentData = {{
				{0}
			}}

			return EquipmentData
			''').strip().format(equips).replace(', extra3=0','')
		return output

	def get_equipment_stats_list_page(self):
		"""Outputs the table of equipment IDs and their related info."""
		# Write the page header.
		module_name = 'Module:Equipment/StatsData'
		def getid(entry):
			return int(entry.equipID)
		equips = u',\n\t'.join([entry.getmodularlua("stats", True) for entry in
			sorted(self.md.equipment, key=getid)])
		output = dedent(u'''
			--[[Category:Equipment modules]]
			--[[Category:Automatically updated modules]]
			-- Relates equipment IDs with stats data.

			return {{
				{0}
			}}''').strip().format(equips)
		return output

	def get_user_equip_list_page(self): 
		"""Outputs the table of equipment IDs and their related info."""
		# Write the page header.
		module_name = 'Module:Equipment/OwnerData'
		def getid(entry):
			return int(entry.equipID)
		equips = u',\n\t'.join([entry.getmodularlua("unique", True) for entry in
			sorted(self.md.equipment, key=getid)])
		output = dedent(u'''
			--[[Category:Flower Knight description modules]]
			--[[Category:Equipment modules]]
			--[[Category:Automatically updated modules]]
			--Relates equipment IDs with equip name and ownership.

			return {{
				{0}
			}}''').strip().format(equips)
		return output

	def get_personal_equip_list_page(self):
		"""Outputs the reverse lookup of personal equipments."""
		# Write the page header.
		module_name = "Module:Equipment/LookupData"

		personalEquipData = {
			int(entry.owners): [entry.equipID]
			for entry in self.md.equipment
			if (entry.classification2 == "21" or entry.classification2 == "30") and entry.owners.find("|") == -1
		}
		ownerIDList = list(personalEquipData.keys())
		personalEquipData = {i: personalEquipData[i] for i in sorted(ownerIDList)}

		for key in personalEquipData:
			# Find and append shared equipment for each character.
			personalEquipData[key] += [
				entry.equipID
				for entry in self.md.equipment
				if str(key) in entry.owners.split("|")
				and entry.equipID.startswith("38")
				and entry.classification2 == "30"
			]
			
			# Find and append rainbow equipment for each character.
			personalEquipData[key] += [
				entry.equipID
				for entry in self.md.equipment
				if str(key) in entry.owners.split("|")
				and len(entry.equipID) == 7
			]

		equips = u',\n\t'.join(['[{0}]={{{1}}}'.format(key,','.join(personalEquipData[key])) for key in personalEquipData])
		output = (
			dedent(
				"""
			--[[Category:Flower Knight description modules]]
			--[[Category:Equipment modules]]
			--[[Category:Automatically updated modules]]
			--Relates equipment IDs with ownership.

			return {{
				{0}
			}}""").strip().format(equips)
		)
		return output

	def get_master_char_data_page(self):
		"""Outputs the table of every char's data and their related names."""
		module_name = 'Module:MasterCharacterData'
		def getname(entry):
			return entry.fullName
		def getid(entry):
			return int(entry.id0)
		knights_str = u''
		for name in sorted(self.md.knights):
			knights_str += '["{0}"] =\n	{1},\n'.format(
				self.md.knights[name].fullName,
				'\n	'.join(self.md.knights[name].get_lua().split('\n')))
		output = dedent(u'''
			--[[Category:Flower Knight description modules]]
			--[[Category:Automatically updated modules]]
			-- Relates character data to their IDs.

			return {{
			{0}}}
			''').strip().format(knights_str)
		return output

	def get_master_char_data_nation_page(self, nation):
		"""Outputs the table of every char's data by nations."""
		module_name = 'Module:MasterCharacterData/Nation'
		if int(nation) == 6: nation = '7'
		if type(nation) is int:
			nation = str(nation)
		
		def getname(entry):
			return entry.fullName
		def getid(entry):
			return int(entry.id0)
		knights_str = u''
		for name in sorted(self.md.knights):
			if (len(self.md.knights[name].tiers[1]['id']) == 6
			and self.md.knights[name].nation == nation):
				knights_str += '["{0}"] =\n	{1},\n'.format(
					self.md.knights[name].fullName,
					'\n	'.join(self.md.knights[name].get_lua().split('\n')))
		output = dedent(u'''
			--[[Category:Flower Knight description modules]]
			--[[Category:Automatically updated modules]]
			-- Relates character data to their IDs.

			return {{
			{0}}}
			''').strip().format(knights_str)
		return output

	EQUIPMENT_AFFIXES = [u'指輪', u'腕輪', u'首飾り', u'耳飾り',]
	def __remove_equipment_affix(self, name):
		"""Removes the type of equipment from the Japanese name.

		If the name does not have a generic affix, the name is returned as is.
		As a result, unique equipment will have their names returned in full.

		@param name: The Japanese name of the equipment.
		@returns The name without an affix.
		"""

		for affix in self.EQUIPMENT_AFFIXES:
			if name.endswith(affix):
				return name[:-len(affix)]
		return name

	def __get_new_equipment_names_page_parse_page(self, page):
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
			jp_name = self.__remove_equipment_affix(jp_name)
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

	def get_new_equipment_names_page(self, page):
		"""Outputs the table of equipment names.

		The original Wikia page is passed into this function.
		This function recreates the list of Japanese equipment names and
		assigned English names. If the Japanese name is not found,
		it is inserted into the list with a default value.
		"""

		output = u''
		names = self.__get_new_equipment_names_page_parse_page(page)
		# Add all missing equipment from the master data to the Wikia's list.
		master_names = {}
		for equip in self.md.equipment:
			jp = equip.name
			jp = self.__remove_equipment_affix(jp)
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

			--[[
			Relates Japanese equipment names to translated names.

			The Wikia updating scripts automatically add new equipment to this page.
			Editors need to add translations for these names manually.

			The four generic equipment types are automatically translated from Japanese.
			They are earrings, rings, bracelets, and necklaces.
			But for other types of equipment, they need to be written explicitly.

			Machine translations and copy-pastes from Nutaku are NOT ALLOWED.
			--]]

			return {{
			    {0}
			}}''').lstrip().format(equips)
		return output

	def get_char_template(self, char_name_or_id, english_name=''):
		"""Outputs a single character's template text to a file."""
		knight = self.md.get_knight(char_name_or_id)
		skill = self.md.skills[knight.skill]

		#Lookup flower family
		for line in self.md.flower_family:
			if line.startswith(knight.family):
				family = line.split(",")
				break

		#Lookup flower meaning
		for line in self.md.data_book:
			if line.startswith(knight.charID1):
				meaning = line.split(",")
				break

		#Modifies English name to conform to IconName rule.
		icon_name = english_name.replace(' ','').replace('(','_').replace(')','')

		#Assembles the template data via repeated join and concatenations.
		template_text = ''.join(["{{CharacterStat\n|",
			"\n|JP = ", knight.fullName,
			"\n|languageoftheflowers = ", meaning[5],
			"\n}}",])

		return template_text

	def get_skin_info_page(self):
		"""Outputs the table of skin IDs and their related info."""
		# Write the page header.
		module_name = 'Module:Skin/Data'
		def getid(entry):
			return int(entry.uniqueID or 0)
		# Determine which entries to output
		entries = sorted(self.md.skins, key=getid)
		entries = [entry for entry in entries if entry.isSkin == '1' or entry.isSkin == '2']

		# Make the table that resembles the master data's info
		full_info_strings = ["['{0}'] = {1},".format(
			entry.uniqueID, entry.getlua(True)) for entry in entries]
		skin_id_to_info_as_str = '    ' + '\n    '.join(full_info_strings)

		# Make the table relating character IDs back to the skin info
		lib_id_to_info = {}
		for entry in entries:
			# Convert to a number to cause proper sorting
			char_id = int(entry.libraryID)
			if not char_id in lib_id_to_info:
				lib_id_to_info[char_id] = []
			uid = "'{0}'".format(entry.uniqueID)
			lib_id_to_info[char_id].append(uid)

		# Make the list of character IDs that have exclusive skins
		lib_ids_with_exclusive_skins = set([int(entry.libraryID) for \
			entry in entries if entry.isExclusive == '1'])
		lib_ids_with_exclusive_skins = ["['{0}'] = 1,".format(
			char_id) for char_id in sorted(lib_ids_with_exclusive_skins)]
		lib_ids_with_exclusive_skins = '    ' + '\n    '.join(
			lib_ids_with_exclusive_skins)

		# Make the list of character IDs that have paid skins
		lib_ids_with_paid_skins = set([int(entry.libraryID) for \
			entry in entries if entry.isSkin == '2'])
		lib_ids_with_paid_skins = ["['{0}'] = 1,".format(
			char_id) for char_id in sorted(lib_ids_with_paid_skins)]
		lib_ids_with_paid_skins = '    ' + '\n    '.join(
			lib_ids_with_paid_skins)

		# With all data organized, stringify each line of info
		lib_id_to_info = {charID : ', '.join(uniqueIdTuple) \
			for charID, uniqueIdTuple in lib_id_to_info.items()}
		lib_id_to_info = ["['{0}'] = {{{1}}},".format(
			charID, infoStr) for charID, infoStr in \
				sorted(lib_id_to_info.items())]
		lib_id_to_info = '    ' + '\n    '.join(lib_id_to_info)

		# Make the like of unique knight ids who have minor variants
		unique_char_ids_with_minor_skins = set([int(entry.replaceID) for \
			entry in entries if entry.isDiffVer == '1'])
		unique_char_ids_with_minor_skins = ["['{0}'] = 1,".format(
			pre_evo_id) for pre_evo_id in sorted(unique_char_ids_with_minor_skins)]
		unique_char_ids_with_minor_skins = '    ' + '\n    '.join(
			unique_char_ids_with_minor_skins)

		# Make the full page
		intro = dedent(u"""
			--[[Category:Flower Knight description modules]]
			--[[Category:Automatically updated modules]]
			-- Relates skin IDs to their data.
			--
			-- Exclusive skins come with a character as a free bonus.
			-- They have a very unique appearance and SD.
			-- For example, obtaining ANY version of Cattleya instantly
			-- earns you the exclusive 幼少期 / Early Childhood skin.
			-- The in-game data labels these skins with (専用) / (Exclusive)
			--
			-- Paid skins are available for purchase by spending Flower Stones.
			-- Like Exclusive skins, they have a very unique appearance and SD.
			-- For example, purchasing the wedding skin for Blushing Bride
			-- allows you to apply the skin to any version of Blushing Bride.
			-- These skins are NOT labelled as (専用) / (Exclusive)
			--
			-- Different version skins are minor changes on specific skins.
			-- You earn them by obtaining that character's skin at the
			-- evolution tier which the different skin applies to.
			-- For example, June Bride Water Lily (Suiren)'s evolved form
			-- has an alternate picture that shows more hair. This skin
			-- cannot be obtained with the original Water Lily.
			""").lstrip()
		output = dedent(u"""
		{0}

		return {{
		libIdToSkinIds = {{
		{1}
		}},

		skinIdToInfo = {{
		{2}
		}},

		libIdsWithExclusiveSkins = {{
		{3}
		}},

		libIdsWithPaidSkins = {{
		{4}
		}},

		uniqueCharIdsWithMinorSkins = {{
		{5}
		}},
		}}
		""").lstrip().format(intro, lib_id_to_info, skin_id_to_info_as_str,
			lib_ids_with_exclusive_skins, lib_ids_with_paid_skins, unique_char_ids_with_minor_skins)
		return output

	def get_char_list_page(self):
		"""Outputs the table of knight IDs to names, and vice-versa."""
		# Write the page header.
		module_name = 'Module:KnightIdAndName/Data'

		def getid(knight):
			return knight.tiers[1]['id']
		ids_to_names = '\n'.join(["    ['{0}'] = '{1}',".format(
			knight.tiers[1]['id'], knight.fullName) for knight in \
				sorted(self.md.knights.values(), key=getid)])

		def getname(knight):
			return knight.fullName
		names_to_ids = '\n'.join(["    ['{0}'] = '{1}',".format(
			knight.fullName, knight.tiers[1]['id']) for knight in \
				sorted(self.md.knights.values(), key=getname)])

		output = dedent(u'''
			--[[Category:Flower Knight description modules]]
			--[[Category:Automatically updated modules]]
			-- Relates character names to their IDs and vice-versa.
			-- Use this module when MasterCharacterData is overkill.

			return {{
			idToName = {{
			{0}
			}},

			nameToId = {{
			{1}
			}}
			}}
			''').lstrip().format(ids_to_names, names_to_ids)
		return output

	def get_char_list_page(self):
		"""Outputs the table of knight IDs to names, and vice-versa."""
		# Write the page header.
		module_name = 'Module:FlowerMemories/Data'

		def getid(knight):
			return knight.tiers[1]['id']
		ids_to_names = '\n'.join(["    ['{0}'] = '{1}',".format(
			knight.tiers[1]['id'], knight.fullName) for knight in \
				sorted(self.md.knights.values(), key=getid)])

		def getname(knight):
			return knight.fullName
		names_to_ids = '\n'.join(["    ['{0}'] = '{1}',".format(
			knight.fullName, knight.tiers[1]['id']) for knight in \
				sorted(self.md.knights.values(), key=getname)])

		output = dedent(u'''
			--[[Category:Flower Knight description modules]]
			--[[Category:Automatically updated modules]]
			-- Relates character names to their IDs and vice-versa.
			-- Use this module when MasterCharacterData is overkill.

			return {{
			idToName = {{
			{0}
			}},

			nameToId = {{
			{1}
			}}
			}}
			''').lstrip().format(ids_to_names, names_to_ids)
		return output

	def get_flower_memories_list_page(self):
		"""Outputs the table of Flower Memory IDs and their related info."""
		# Write the page header.
		module_name = 'Module:FlowerMemories/Data'
		def getname(entry):
			return int(entry.name)
		def getid(entry):
			return int(entry.flowerMemoryID)
		memories = u',\n\t'.join([entry.getlua(True) for entry in
			sorted(self.md.flower_memories, key=getid)])
		output = dedent(u'''
			--[[Category:Flower Memory modules]]
			--[[Category:Automatically updated modules]]
			-- Relates Flower Memories with their accompanying data.
			
			return {{
				{0}
			}}
			''').strip().format(memories)
		return output

	def get_flower_memories_abilities_page(self):
		"""Outputs the table of Memory Abilities IDs and their related info."""
		# Write the page header.
		module_name = 'Module:FlowerMemories/AbilityData'
		def getid(entry):
			return int(entry.id)
		memories = u',\n\t'.join([entry.getlua(True) for entry in
			sorted(self.md.memory_abilities.values(), key=getid)])
		output = dedent(u'''
			--[[Category:Flower Memory modules]]
			--[[Category:Automatically updated modules]]
			-- Contains ability parameters used by Flower Memories.
			
			return {{
				{0}
			}}
			''').strip().format(memories)
		return output

	def get_eternal_oath_page(self):
		"""Outputs the table of Memory Abilities IDs and their related info."""
		# Write the page header.
		module_name = 'Module:BlessedOathList'
		def getid(entry):
			return int(entry.sameCharacterID)
		oath = u',\n\t'.join([entry.getlua(True) for entry in
			sorted(self.md.bless_oath, key=getid)])
		output = dedent(u'''
			--[[Category:Flower Knight description modules]]
			--[[Category:Automatically updated modules]]
			-- Contain the list of Flower Knights that can be given a Blessed Oath Ring.
			
			return {{
				{0}
			}}
			''').strip().format(oath)
		return output
