#!/usr/bin/python3
# coding: utf-8
import os
import sys
import math
import random
import json
import zlib
import binascii
from glob import glob
from hashlib import md5
from io import BytesIO
from base64 import b64decode
from datetime import date
from collections import OrderedDict

if sys.version_info.major < 3:
	# The script is being run under Python 2.
	# Use the codecs library for files.
	import codecs, urllib2
	open = codecs.open
	range = xrange
	urllibrary = urllib2
else:
	import urllib.request
	urllibrary = urllib.request

try:
	import imaging
	IconMerger = imaging.Imaging()
except ImportError:
	_HAS_LIB = False
	print('Imaging script is unavailable. The generated icon would be frameless.\n')

RAWDATA_NEW = [f for f in glob("inputs/*.zlib")]
MASTERDATA_CURRENT = "getMaster_latest.txt"
ASSET_DIRECTORY = "../asset_fm"

(IMG_CHARA_ICON,IMG_PORTRAIT,IMG_FULLCG,IMG_FM_ICON,IMG_FM_PLATE) = range(5)

class ImageClass(object):
	def __init__(my, entrylist):
		(my.imgDirLink,
		my.imgLinkPred,
		my.imgSaveName,) = entrylist

class DownloadImage(object):
	def __init__(my):
		my.getCharaURL = "http://dugrqaqinbtcq.cloudfront.net/product/ynnFQcGDLfaUcGhp/assets/ultra/images/{0}/{1}.bin"
		my.getEquipURL = "http://dugrqaqinbtcq.cloudfront.net/product/ynnFQcGDLfaUcGhp/assets/ultra/images/item/100x100/{0}.png"
		my.getPlateURL = "http://dugrqaqinbtcq.cloudfront.net/product/ynnFQcGDLfaUcGhp/assets/ultra/images/flower_memory/general/{0}/{1}.bin"

	def getCharacterImage(my, flowerKnightEntry):
		
		IMG_FULLCG   = ImageClass(["character/dmm/stand","stand_","stand_"])
		IMG_FKG_ICON = ImageClass(["character/dmm/i","icon_l_","icon_"])
		IMG_PORTRAIT = ImageClass(["character/dmm/stand_m","stand_m","portrait_"])

		#Refactored download code, need testing
		fkg_icon = my.downloadCharaImage(flowerKnightEntry.image_id0,IMG_FKG_ICON)
		my.downloadCharaImage(flowerKnightEntry.image_id0,IMG_PORTRAIT)
		my.iconFrame(flowerKnightEntry.image_id0,flowerKnightEntry.rarity,flowerKnightEntry.type)
		
	def getFlowerMemoryImage(my, flowerMemoryEntry):
		
		IMG_FM_ICON  = ImageClass(["flower_memory/general/icon","fm_icon_","Fm_icon_"])
		IMG_FM_ICON2 = ImageClass(["flower_memory/general/icon_half","fm_icon_half_","Fm_icon_half_"])
		IMG_FM_IMAGE = ImageClass(["flower_memory/general/main_l","fm_main_l_","Fm_main_l_"])
		IMG_FM_TITLE = ImageClass(["flower_memory/general/name_l","fm_name_l_","Fm_title_"])
		
		my.downloadCharaImage(flowerMemoryEntry['itemId'],IMG_FM_ICON)
		my.downloadCharaImage(flowerMemoryEntry['itemId'],IMG_FM_ICON2)
		my.downloadCharaImage(flowerMemoryEntry['itemId'],IMG_FM_IMAGE)
		my.downloadCharaImage(flowerMemoryEntry['itemId'],IMG_FM_TITLE)

		my.iconFrame(flowerMemoryEntry['itemId'], IMG_FM_ICON, flowerMemoryEntry['rarity'])
		my.iconHalfFrame(flowerMemoryEntry['itemId'], IMG_FM_ICON2, flowerMemoryEntry['rarity'])

		fm_image_filename = os.path.join(ASSET_DIRECTORY,"{0}{1}.png".format(IMG_FM_IMAGE.imgSaveName,flowerMemoryEntry['itemId']))
		fm_image_output_filename = os.path.join(ASSET_DIRECTORY,"{0}{1}.png".format("Fm_wallpaper_",flowerMemoryEntry['itemId']))
		fm_title_filename = os.path.join(ASSET_DIRECTORY,"{0}{1}.png".format(IMG_FM_TITLE.imgSaveName,flowerMemoryEntry['itemId']))
		try:
			IconMerger.get_framed_memory(fm_image_filename, fm_title_filename, fm_image_output_filename, int(flowerMemoryEntry['rarity']))
		except Exception as e:
			print(e)
		else:
			print("Successfully framed {0}{1}.png".format("Fm_wallpaper_",flowerMemoryEntry['itemId']))
			#os.remove(IMG_FM_TITLE.imgSaveName)))
		
	def getFilenameHash(my, predicate, inputID):
		#Calculate the hashed filename of the character images.
		KeyName = predicate + str(inputID)
		return md5(KeyName.encode('utf-8')).hexdigest()
		
	def downloadCharaImage(my, inputID, image_type):
		#Define the image link and filename.
		ImgFileHash = my.getFilenameHash(image_type.imgLinkPred,inputID)
		ImgFileLink = my.getCharaURL.format(image_type.imgDirLink,ImgFileHash)
		ImgFileName = "{0}{1}.png".format(image_type.imgSaveName,inputID)
		
		#Pass the variables to download function call.
		my.getDownloadImage(ImgFileLink,ImgFileName)
	
	def downloadEquipImage(my, equipID):
		ImgFileLink =  my.getEquipURL.format(equipID)
		ImgFileName = "equip_{0}.png".format(equipID)
		
		return my.getDownloadImage(ImgFileLink,ImgFileName)
		
	def getDownloadImage(my,inputLink,outputImageName,decFlag=False):
		outputFile = os.path.join(ASSET_DIRECTORY, outputImageName)
		
		with open(outputFile,'wb') as imgFile:
			try:
				imgBuffer = urllibrary.urlopen(inputLink).read()
				if decFlag: imgBuffer = zlib.decompress(imgBuffer)
			except KeyboardInterrupt:
				print("Download interrupted by user")
			except:
				print("Unable to download " + outputImageName)
			else:
				imgFile.write(imgBuffer)
				print("Downloaded " + outputImageName)

	def iconFrame(my,inputID,image_type,rarity,attribute=''):
		filepath = os.path.join(ASSET_DIRECTORY, "{0}{1}.png".format(image_type.imgSaveName,inputID))
		
		try:
			if attribute == '':
				IconMerger.get_framed_icon(filepath,filepath,int(rarity))
			else:
				IconMerger.get_framed_icon(filepath,filepath,int(rarity),int(attribute))
		except Exception as e:
			print("Unable to frame {0}{1}.png".format(image_type.imgSaveName,inputID))
			print(e)
		else:
			print("Successfully framed {0}{1}.png".format(image_type.imgSaveName,inputID))

	def iconHalfFrame(my,inputID,image_type,rarity):
		filepath = os.path.join(ASSET_DIRECTORY, "{0}{1}.png".format(image_type.imgSaveName,inputID))
		
		try:
			IconMerger.get_framed_halficon(filepath,filepath,int(rarity))
		except Exception as e:
			print("Unable to frame {0}{1}.png".format(image_type.imgSaveName,inputID))
			print(e)
		else:
			print("Successfully framed {0}{1}.png".format(image_type.imgSaveName,inputID))

class MasterData(object):
	#Handles various info from master data.
	def __init__(my, datafile_list=None):
		my.masterJSON = OrderedDict()
		#my.masterTexts = "TimeStamp:{0}".format(date.today().strftime("%d-%m-%Y"))
		if datafile_list: my.load_getMaster(datafile_list)

	def load_getMaster(my, datafile_list):
		"""Loads and parses getMaster.

		This function is called automatically if the constructor is given
		getMaster's filename in advance.
		"""

		# Open the master database
		if type(datafile_list) is list:
			for infilename in datafile_list:
				my.parse_getMaster(infilename)
		elif datafile_list.endswith(".txt"):
			my.parse_getMaster_plaintext(datafile_list)
		else:
			try:
				#Probably old version of data.
				my.parse_getMaster(datafile_list,True) #prints borked masterCharacter for some reason.
			except:
				print('Could not load {0} as zlib-compressed data.'.format(datafile_list))

	def parse_getMaster(my, infilename='', b64encodeMode=False):
		with open(infilename, 'rb') as infile:
			raw_string = zlib.decompress(infile.read()).decode("utf-8")
			json_list = json.loads(raw_string, object_pairs_hook=OrderedDict)
						
			for key in json_list:
				element = json_list[key]
				if key not in my.masterJSON:
					my.masterJSON.update({key: None})
				if type(element) is list:
					my.masterJSON[key] = element

	def _extract_section_to_JSON(my, section, rawdata):
		#Gets all text from one section of the master data.
		data = rawdata.partition(section + '\n')[2][1:].partition('master')[0].strip().split('\n')
		my.masterJSON.update({section: data})
		
class compareData(object):
	def __init__(my):
		my.downloadImage = DownloadImage()
		my.new_master_data = MasterData(RAWDATA_NEW)

	def getFlowerMemory(my):
		FlowerMemoryJSONData = [entry for entry in my.new_master_data.masterJSON['masterSyncData']]
		FlowerMemoryData = OrderedDict()
		if not os.path.exists(ASSET_DIRECTORY): os.makedirs(ASSET_DIRECTORY)
		
		for entry in FlowerMemoryJSONData:
			FlowerMemoryData.update({entry['tableName']: entry['data']})

		for FlowerMemory in FlowerMemoryData['master_flower_memorys']:
			my.downloadImage.getFlowerMemoryImage(FlowerMemory)
		
if __name__ == '__main__':
	compareData = compareData()
	compareData.getFlowerMemory()
