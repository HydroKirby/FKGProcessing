#!/usr/bin/python
# coding=utf-8
from __future__ import print_function
from common import *
from entry import *
from textwrap import dedent

__doc__ = """Stores collective data for individual flower knights.

The master data stores data for each and every flower knight across
multiple CSV entries. Each entry pertains to one evolution stage.
The FlowerKnight class connects all the data from the CharacterEntry instances
and makes a single representable flower knight out of them. It is easier
to manage character data this way.
"""

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
		# Force the param to be iterable
		if type(entries) is not list:
			entries = [entries]
		for entry in entries:
			my.add_entry(entry)

	def add_entry(my, entry):
		"""Adds a CharacterEntry instance to this knight's data."""
		if int(entry.id0) >= 700000 and entry.fullName == 'ツツジ':
			# This is an NPC character. Do not store their data.
			# Otherwise, it might overwrite the playable character's data.
			# An example is the one-star Tsutsuji/Azalea.
			return
		tier = entry.evolutionTier
		isRarityGrown = entry.isRarityGrown == '1'
		unknown03 = entry.unknown03 == '1'
		unknown04 = entry.unknown04 == '1'
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
					entry.fullName, entry.id0) + \
				'Will ignore bugged entries and stop stating this message.')
			FlowerKnight.stated_integrity_bug = True

	def _add_common_data(my, entry):
		"""Stores info which should be the same for all evolution tiers."""
		if my.fullName:
			# The data is already stored.
			return
		my.fullName = entry.fullName
		my.reading = entry.reading
		my.rarity = entry.rarity
		my.spd = entry.lvlOneSpd
		# TODO: Rely on my.tiers[NUMBER]['skill'] instead.
		# The skill is no longer the same between all evolution tiers.
		# It changes if the character undergoes rarity growth.
		my.skill = entry.skill1ID
		my.family = entry.family
		my.type = entry.type
		my.nation = entry.nation
		my.gift = entry.gift
		my.is_event = entry.isEventKnight
		my.is_powers_only_bloom = entry.isBloomedPowersOnly
		my._determine_romaji()

	def _add_tier1_entry(my, entry):
		"""Stores the CharacterEntry's data as the pre-evolved info.

		As a side-effect of calling this method, some of the common
		information between all evolution tiers is stored in the class.
		"""
		
		my._add_common_data(entry)
		my.tiers[1]['id'] = entry.id0
		my.tiers[1]['lvlCap'] = maxLevel[my.rarity][0]
		my.tiers[1]['skill'] = entry.skill1ID
		my.tiers[1]['abilities'] = [entry.ability1ID, entry.ability2ID, entry.ability3ID]
		my.tiers[1]['lvlOne'] = [entry.lvlOneHP, entry.lvlOneAtk, entry.lvlOneDef]
		my.tiers[1]['lvlMax'] = [entry.lvlMaxHP, entry.lvlMaxAtk, entry.lvlMaxDef]
		my.tiers[1]['aff1'] = [entry.aff1MultHP, entry.aff1MultAtk, entry.aff1MultDef]
		my.tiers[1]['aff2'] = [entry.aff2MultHP, entry.aff2MultAtk, entry.aff2MultDef]
		# Both date values and the game-version-when-added strings can differ between tiers.
		my.tiers[1]['date0'] = entry.date0
		my.tiers[1]['date1'] = entry.date1
		my.tiers[1]['gameVersionWhenAdded'] = entry.gameVersionWhenAdded
		# Only the pre-evolved entry has a sort ID because evolved/bloomed
		# pics aren't used in the library / 図鑑.
		my.charID1 = entry.sortID
		my.charID2 = entry.charID2
		my.libID = entry.libraryID

	def _add_tier2_entry(my, entry):
		"""Stores the CharacterEntry's data as the evolved info."""
		my.tiers[2]['id'] = entry.id0
		my.tiers[2]['skill'] = entry.skill1ID
		my.tiers[2]['lvlCap'] = maxLevel[my.rarity][1]
		my.tiers[2]['abilities'] = [entry.ability1ID, entry.ability2ID, entry.ability3ID]
		my.tiers[2]['lvlOne'] = [entry.lvlOneHP, entry.lvlOneAtk, entry.lvlOneDef]
		my.tiers[2]['lvlMax'] = [entry.lvlMaxHP, entry.lvlMaxAtk, entry.lvlMaxDef]
		my.tiers[2]['aff1'] = [entry.aff1MultHP, entry.aff1MultAtk, entry.aff1MultDef]
		my.tiers[2]['aff2'] = [entry.aff2MultHP, entry.aff2MultAtk, entry.aff2MultDef]
		my.tiers[2]['date0'] = entry.date0
		my.tiers[2]['date1'] = entry.date1
		my.tiers[2]['gameVersionWhenAdded'] = entry.gameVersionWhenAdded

	def _add_tier3_entry(my, entry):
		"""Stores the CharacterEntry's data as the bloomed info.

		Aa a side-effect of calling this method, the "bloomability" is set.
		"""

		if entry.isBloomedPowersOnly == "1":
			my.bloomability = FlowerKnight.BLOOM_POWERS_ONLY
		else:
			my.bloomability = FlowerKnight.BLOOMABLE
		my.tiers[3]['id'] = entry.id0
		my.tiers[3]['skill'] = entry.skill1ID
		my.tiers[3]['lvlCap'] = maxLevel[my.rarity][2]
		my.tiers[3]['abilities'] = [entry.ability1ID, entry.ability2ID, entry.ability3ID]
		my.tiers[3]['lvlOne'] = [entry.lvlOneHP, entry.lvlOneAtk, entry.lvlOneDef]
		my.tiers[3]['lvlMax'] = [entry.lvlMaxHP, entry.lvlMaxAtk, entry.lvlMaxDef]
		my.tiers[3]['aff1'] = [entry.aff1MultHP, entry.aff1MultAtk, entry.aff1MultDef]
		my.tiers[3]['aff2'] = [entry.aff2MultHP, entry.aff2MultAtk, entry.aff2MultDef]
		my.tiers[3]['date0'] = entry.date0
		my.tiers[3]['date1'] = entry.date1
		my.tiers[3]['gameVersionWhenAdded'] = entry.gameVersionWhenAdded

	def _add_tier4_entry(my, entry):
		"""Stores the CharacterEntry's data as the rarity grown info.

		Aa a side-effect of calling this method, the "growability" is set.
		"""

		my.growability = FlowerKnight.HAS_RARITY_GROWTH
		my.tiers[4]['id'] = entry.id0
		# Rarity growth turns the character's rarity into a 6-star.
		my.tiers[4]['lvlCap'] = maxLevel['6'][2]
		my.tiers[4]['skill'] = entry.skill1ID
		my.tiers[4]['abilities'] = [entry.ability1ID, entry.ability2ID, entry.ability3ID]
		my.tiers[4]['lvlOne'] = [entry.lvlOneHP, entry.lvlOneAtk, entry.lvlOneDef]
		my.tiers[4]['lvlMax'] = [entry.lvlMaxHP, entry.lvlMaxAtk, entry.lvlMaxDef]
		my.tiers[4]['aff1'] = [entry.aff1MultHP, entry.aff1MultAtk, entry.aff1MultDef]
		my.tiers[4]['aff2'] = [entry.aff2MultHP, entry.aff2MultAtk, entry.aff2MultDef]
		my.tiers[4]['date0'] = entry.date0
		my.tiers[4]['date1'] = entry.date1
		my.tiers[4]['gameVersionWhenAdded'] = entry.gameVersionWhenAdded

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
			'charID2':my.charID2,
			'libID':my.libID,
			'type':my.type,
			'rarity':my.rarity,
			'isEvent':my.is_event,
			'reading':my.reading,
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
		tier2StatsString = tier2AffString = ''
		abilityString = '{{{0}, {1}, {2}}},'.format(
			my.tiers[1]['abilities'][0], my.tiers[1]['abilities'][1],
			my.tiers[1]['abilities'][2])
		if my.can_evolve():
			tier2StatsString = dedent('''
				tier2Lv1 = {{ {tier2Lv1HP}, {tier2Lv1Atk}, {tier2Lv1Def} }},
				tier2LvMax = {{ {tier2LvMaxHP}, {tier2LvMaxAtk}, {tier2LvMaxDef} }},
				''').lstrip().format(**formatDict)
			tier2AffString = dedent('''
				tier2Aff1Bonus = {{ {tier2Aff1HP}, {tier2Aff1Atk}, {tier2Aff1Def} }},
				tier2Aff2Bonus = {{ {tier2Aff2HP}, {tier2Aff2Atk}, {tier2Aff2Def} }},
				''').lstrip().format(**formatDict)
			abilityString = abilityString + '\n    {{{0}, {1}, {2}}},'.format(
				my.tiers[2]['abilities'][0], my.tiers[2]['abilities'][1],
				my.tiers[2]['abilities'][2])

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
			abilityString = abilityString + '\n    {{{0}, {1}, {2}}},'.format(
				my.tiers[3]['abilities'][0], my.tiers[3]['abilities'][1],
				my.tiers[3]['abilities'][2])

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
			abilityString = abilityString + '\n    {{{0}, {1}, {2}}},'.format(
				my.tiers[4]['abilities'][0], my.tiers[4]['abilities'][1],
				my.tiers[4]['abilities'][2])
			tier4SkillString = dedent('''
				tier4skill = {tier4skill},
				''').lstrip().format(**formatDict)

		# Add all of the generated strings to the string format table.
		formatDict.update({
			'tier2StatsString':tier2StatsString,
			'tier2AffString':tier2AffString,
			'tier3StatsString':tier3StatsString,
			'tier3AffString':tier3AffString,
			'tier4StatsString':tier4StatsString,
			'tier4AffString':tier4AffString,
			'abilityString':abilityString,
			'tier4skill':tier4SkillString,
		})

		lua_table = dedent(u'''
			{{id = {id},
			charID = {charID},
			libID = {libID},
			name = {japanese},
			reading = "{reading}",
			type = {type},
			rarity = {rarity},
			isEvent = {isEvent},
			tier3PowersOnlyBloom = {tier3PowersOnlyBloom},
			likes = {gift},
			nation = {nation},
			family = {family},
			personalEquipOwnerID = {charID2},
			dateAdded = {dateAdded},
			skill = {skill},
			{tier4skill}bundledAbilities = {{ {abilityString} }},
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
