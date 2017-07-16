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

from parse_master import *

__doc__ = """Checks the getMaster Data to generate the template data"""

DEFAULT_INFILENAME = 'getMaster_latest.txt'
DEFAULT_OUTFILENAME = 'result.txt'
DEFAULT_ASSETPATH = 'asset'

# Specify the Flower Knight ID and their English name (which is not available in getMaster)
# Note: Always make sure findID and english_nameList are list types!
findID = [158101]
english_nameList = ["Aizoon Stonecrop"]
ImgDownload = False

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

def get_char_module(master_data):
	"""Gets the text to fill in a character module.

	If the user chooses to abort the operation, an empty string is returned.

	@returns The full text for a character module.
	"""
	_METHODS = ['By using the embedded "findID" in the source code.',
		'By inputting the character name or ID.',
		'By getting all of the newly updated/added characters.',
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
	output_text = ''
	if method == 0:
		output_text += '\n\n'.join([master_data.get_char_module(id) for id in findID])
	elif method == 1:
		name_or_id = input('>>> Input the character\'s Japanese name or ID: ')
		output_text = master_data.get_char_module(name_or_id)
	elif method == 2:
		# TODO
		print('Not implemented yet!')
	elif method == 3:
		print('Cancelled.')
	return output_text

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
	ACT_WRITE_SKILL_LIST = 'skill list'
	ACT_WRITE_ABILITY_LIST = 'ability list'
	ACT_WRITE_CHAR_NAME_LIST = 'char list'
	action_list = {
		ACT_EXIT:'Exit and return the parsed master data.',
		ACT_HELP:'List all actions.',
		ACT_UNIT_TEST:'Unit test some things.',
		ACT_INTROSPECT:'Activate the interactive prompt.',
		ACT_FIND_CHAR:'Find a character.',
		ACT_SEE_ABILITIES:'See the list of unique abilities.',
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
		elif user_input == ACT_HELP:
			list_actions()
		elif user_input == ACT_UNIT_TEST:
			UnitTest.run_tests()
		elif user_input == ACT_WRITE_CHAR_NAME_LIST:
			output_text = master_data.get_char_list_page()
		elif user_input == ACT_GET_CHAR_TEMPLATE:
			output_template(master_data.get_char_template(input_name_or_id, english_name))
		elif user_input == ACT_GET_CHAR_MODULE:
			output_text = get_char_module(master_data)
		elif user_input == ACT_WRITE_SKILL_LIST:
			output_text = master_data.get_skill_list_page()
		elif user_input == ACT_WRITE_ABILITY_LIST:
			output_text = master_data.get_ability_list_page()
		elif user_input == ACT_FIND_CHAR:
			char_name_or_id = input("Input the character's Japanese name or ID: ")
			entries = master_data.get_char_entries(char_name_or_id)
			for entry in entries:
				print(entry.getlua() + '\n')
		elif user_input == ACT_SEE_ABILITIES:
			# Note: You may optionally do something with the return value.
			ability_list = master_data.find_referenced_abilities()
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
