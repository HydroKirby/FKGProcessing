#!/usr/bin/python3
# coding=utf-8
from __future__ import print_function
import os, sys, math, re, random, zlib, hashlib
from textwrap import dedent
import networking

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

from parse_master import *
from common import *

__doc__ = """Checks the getMaster Data to generate the template data"""

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

def get_char_template(master_data):
	"""Gets the text to fill in a character template.

	If the user chooses to abort the operation, an empty string is returned.

	@returns The full text for a character template.
	"""
	knights = master_data.choose_knights()
	output_text = ''
	for knight in knights:
		print('Going to make template for {0}'.format(knight))
		name = input('Input her English name: ')
		template = master_data.get_char_template(knight, name)
		if output_text:
			# Add a separator.
			output_text += '\n\n==========================\n\n'
		output_text += template
	return output_text

def get_char_module(master_data):
	"""Gets the text to fill in a character module.

	If the user chooses to abort the operation, an empty string is returned.

	@returns The full text for a character module.
	"""
	knights = master_data.choose_knights()
	return u'\n\n==========================\n\n'.join(
		[master_data.get_char_module(knight) for knight in knights if knight])

def introspect(master_data, imaging):
	"""Allows real-time introspection of the program and data."""
	introspecting = True
	print('Entering introspection mode.')
	#print('Set introspecting=False to stop.') # Apparently this doesn't work...
	print('Use Ctrl+C or input exit() to stop.')
	print('For convenience, p = print, and m = master_data')
	print("Hints: Try p(dir(m)), or a=m.pre_evo_chars, or p(a[11].getval('id0'))")
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

def apply_frames(master_data, imaging):
	"""Applies frames to character icons."""
	for entry in master_data.get_newest_characters():
		dl_state = downloadCharaImage(int(entry.getval('id0')),
			entry.getval('fullName'), IMG_ICON, int(entry.getval('evolutionTier')))
		if dl_state != DL_OK:
			print('The download did not work. Skipping for {0} in evolution state {1}'.format(
				remove_quotes(entry.getval('fullName')), entry.getval('evolutionTier')))
			continue
		ImgFileName = IconName + imgTypeName[iconType] + str(stage) + ".png"
		framed_icon = imaging.get_framed_icon(icon, ImgFileName,
			int(entry.getval('rarity')), int(entry.getval('type')))
		print('Completed the processing for {0}.'.format(remove_quotes(entry.getval('fullName'))))

def download_character_images(master_data, networking):
	"""Downloads all images for a character."""
	knights = master_data.choose_knights()
	for knight in knights:
		networking.dowload_flower_knight_pics(knight)

def action_prompt(master_data, input_name_or_id=None, english_name=''):
	"""Asks the user which function they want to use."""
	# Make the list of potential actions.
	ACT_EXIT = 'exit'
	ACT_HELP = 'help'
	ACT_INTROSPECT = 'introspect'
	ACT_UNIT_TEST = 'unit test'
	ACT_FIND_CHAR = 'find'
	ACT_SEE_ABILITIES = 'see abilities'
	ACT_GET_CHAR_TEMPLATE = 'char template'
	ACT_GET_CHAR_MODULE = 'char module'
	ACT_DL_CHAR_IMAGES = 'dl char images'
	ACT_WRITE_SKILL_LIST = 'skill list'
	ACT_WRITE_ABILITY_LIST = 'ability list'
	ACT_WRITE_CHAR_NAME_LIST = 'char list'
	ACT_WRITE_MASTER_CHAR_LIST = 'master char list'
	ACT_FRAME_ICONS = 'frame'
	action_list = {
		ACT_EXIT:'Exit and return the parsed master data.',
		ACT_HELP:'List all actions.',
		ACT_UNIT_TEST:'Unit test some things.',
		ACT_INTROSPECT:'Activate the interactive prompt.',
		ACT_FIND_CHAR:'Find a character.',
		ACT_SEE_ABILITIES:'See the list of unique abilities.',
		ACT_GET_CHAR_TEMPLATE:'Output a Character template.',
		ACT_GET_CHAR_MODULE:'Output a Character module.',
		ACT_DL_CHAR_IMAGES:'Download all images for a character.',
		ACT_WRITE_SKILL_LIST:'Write the Skill list (Skill ID:Skill Info).',
		ACT_WRITE_ABILITY_LIST:'Write the Ability list (Ability ID:Ability Info).',
		ACT_WRITE_CHAR_NAME_LIST:'Write the Character list (FKG ID:JP Name).',
		ACT_WRITE_MASTER_CHAR_LIST:'Write the Master Character List (FKG ID:All Data).',
		ACT_FRAME_ICONS:'Puts frames on all character icons in the "dl" folder.',
	}
	def list_actions():
		for key, action in action_list.items():
			print('{0}: {1}'.format(key, action))

	from imaging import Imaging
	imaging = Imaging()
	from networking import Networking
	networking = Networking()

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
			introspect(master_data, imaging)
		elif user_input == ACT_HELP:
			list_actions()
		elif user_input == ACT_UNIT_TEST:
			UnitTest().run_tests()
		elif user_input == ACT_WRITE_CHAR_NAME_LIST:
			output_text = master_data.get_char_list_page()
		elif user_input == ACT_GET_CHAR_TEMPLATE:
			output_text = get_char_template(master_data)
		elif user_input == ACT_GET_CHAR_MODULE:
			output_text = get_char_module(master_data)
		elif user_input == ACT_DL_CHAR_IMAGES:
			output_text = download_character_images(master_data, networking)
		elif user_input == ACT_WRITE_SKILL_LIST:
			output_text = master_data.get_skill_list_page()
		elif user_input == ACT_WRITE_ABILITY_LIST:
			output_text = master_data.get_bundled_ability_list_page()
		elif user_input == ACT_WRITE_MASTER_CHAR_LIST:
			output_text = master_data.get_master_char_data_page()
		elif user_input == ACT_FIND_CHAR:
			char_name_or_id = input("Input the character's Japanese name or ID: ")
			print('\n\n'.join([entry.getlua() for entry in
				master_data.get_char_entries(char_name_or_id)]))
		elif user_input == ACT_SEE_ABILITIES:
			# Note: You may optionally do something with the return value.
			# TODO: Remove this command when I feel like it is no longer needed. 
			ability_list = master_data.find_referenced_abilities()
		elif user_input == ACT_FRAME_ICONS:
			apply_frames(master_data, imaging)

		if output_text:
			with open(DEFAULT_OUTFILENAME, 'w', encoding="utf-8") as outfile:
				outfile.write(output_text)
			print('Completed the processing.')

def main(input_name_or_id=None, english_name=''):
	# Open and parse the master database
	master_data = MasterData(DEFAULT_INFILENAME)

	# Choose how to process the data.
	# Someday, it would be nice to turn this into a GUI.
	try:
		action_prompt(master_data, input_name_or_id, english_name)
	except KeyboardInterrupt:
		# Make Ctrl+C output quiet.
		pass

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
