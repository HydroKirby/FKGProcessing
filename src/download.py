#!/usr/bin/python3
# coding: utf-8
import os
import re
import sys
import math
import zlib
import parse_master
from hashlib import md5
from base64 import b64decode
from collections import OrderedDict
from urllib import request as urllibrary

try:
	import imaging
	IconMerger = imaging.Imaging()
except ImportError:
	_HAS_LIB = False
	print('Imaging script is unavailable. The generated icon would be frameless.\n')

IMAGE_ASSET_DIRECTORY = "../asset_dl/upload"
VOICE_ASSET_DIRECTORY = "../asset_dl/mp3"
IMAGE_DOWNLOAD = True
VOICE_DOWNLOAD = True
DOWNLOAD_TEST = False

(IMG_ICON,IMG_PORTRAIT,IMG_FULLCG) = range(3)

class DownloadImage(object):
	def __init__(my,dryRun=False):
		my.dryRun = dryRun
		my.getCharaURL = "http://dugrqaqinbtcq.cloudfront.net/product/ynnFQcGDLfaUcGhp/assets/ultra/images/character/dmm/{0}/{1}.bin"
		my.getEquipURL = "http://dugrqaqinbtcq.cloudfront.net/product/ynnFQcGDLfaUcGhp/assets/ultra/images/item/100x100/{0}.png"
		my.imgDirLink  = { IMG_FULLCG:'stand',  IMG_PORTRAIT:'stand_m'  , IMG_ICON:'i' }
		my.imgLinkPred = { IMG_FULLCG:'stand_', IMG_PORTRAIT:'stand_m_' , IMG_ICON:'icon_l_' }
		my.imgSaveName = { IMG_FULLCG:'stand_', IMG_PORTRAIT:'portrait_', IMG_ICON:'icon_' }
		
		#stand   = http://dugrqaqinbtcq.cloudfront.net/product/ynnFQcGDLfaUcGhp/assets/ultra/images/character/dmm/stand/3815ffc3e8d8db6f2647ad881bcbe92c.bin?1.201.0
		#stand_m = http://dugrqaqinbtcq.cloudfront.net/product/ynnFQcGDLfaUcGhp/assets/ultra/images/character/dmm/stand_m/6bff7b5226c825b1b2c2479293baf5fb.bin?1.165.1
		#bustup  = http://dugrqaqinbtcq.cloudfront.net/product/ynnFQcGDLfaUcGhp/assets/ultra/images/character/dmm/s/1b9d74f96a77ce09a24eff3c1e3fd4ac.bin?1.165.1
		#icon_l  = http://dugrqaqinbtcq.cloudfront.net/product/ynnFQcGDLfaUcGhp/assets/ultra/images/character/dmm/i/1f47249903348bb184e2a4d154b7efec.bin?1.41.0
		#hscene  = https://dugrqaqinbtcq.cloudfront.net/product/ynnFQcGDLfaUcGhp/assets/ultra/images/hscene_r18/hscene_r18_112811.bin
		#hscene  = https://dugrqaqinbtcq.cloudfront.net/product/ynnFQcGDLfaUcGhp/assets/ultra/images/hscene_r18/hscene_r18_131803_2.bin
		#equip   = http://dugrqaqinbtcq.cloudfront.net/product/ynnFQcGDLfaUcGhp/assets/ultra/images/item/100x100/360313.png?i1.229.0
		#bgm	 = http://dugrqaqinbtcq.cloudfront.net/product/ynnFQcGDLfaUcGhp/assets/bgm/fkg_bgm_general001.mp3?s1.208.0
		#"icon_0%d" % fkgID 
		
		#bustup_json = https://dugrqaqinbtcq.cloudfront.net/product/ynnFQcGDLfaUcGhp/assets/json/bustup/dmm/faeb449cfc95d3b7267dbbd44e5d8ea2.json?1.302.0
		#https://dugrqaqinbtcq.cloudfront.net/product/ynnFQcGDLfaUcGhp/assets/ultra/images/character/dmm/bustup/faeb449cfc95d3b7267dbbd44e5d8ea2.bin?1.302.0 (bustup_112812_all)
		
	def getCharacterImage(my, flowerKnightEntry):
		my.iconFrame(flowerKnightEntry.id0,flowerKnightEntry.rarity,flowerKnightEntry.type)
		my.downloadCharaImage(flowerKnightEntry.id0,IMG_PORTRAIT)
		my.downloadCharaImage(flowerKnightEntry.id0,IMG_FULLCG)
		
	def downloadCharaImage(my,inputID,type,getBinary=False):
		#Calculate the hashed filename of the character images.
		KeyName = my.imgLinkPred[type] + inputID
		hash = md5(KeyName.encode('utf-8')).hexdigest()
		
		#Ensures path to image directory exists.
		if not os.path.exists(IMAGE_ASSET_DIRECTORY):
			os.makedirs(IMAGE_ASSET_DIRECTORY)
		
		#Define the image link and filename.
		ImgFileLink = my.getCharaURL.format(my.imgDirLink[type],hash)
		ImgFileName = "{0}{1}.png".format(my.imgSaveName[type],inputID)
		
		#Pass the variables to download function call.
		return my.getDownloadImage(ImgFileLink,ImgFileName,getBinary)
	
	def downloadEquipImage(my, equipID):
		ImgFileLink =  my.getEquipURL.format(equipID)
		ImgFileName = "equip_{0}.png".format(equipID)
		
		return my.getDownloadImage(ImgFileLink,ImgFileName)
		
	def getDownloadImage(my,inputLink,outputImageName,getBinary=False,decFlag=False):
		if not os.path.exists(IMAGE_ASSET_DIRECTORY): os.makedirs(IMAGE_ASSET_DIRECTORY)
		outputFile = os.path.join(IMAGE_ASSET_DIRECTORY, outputImageName)
		downloadText = "Downloaded "

		try:
			imgBuffer = urllibrary.urlopen(inputLink).read()
			if decFlag: imgBuffer = zlib.decompress(imgBuffer)
		except KeyboardInterrupt:
			print("Download interrupted by user")
		except:
			print("Unable to download " + outputImageName)
		else:
			if my.dryRun:
				downloadText = "Test d" + downloadText[1:-3]+ " "
			elif not getBinary:
				with open(outputFile,'wb') as imgFile:
					imgFile.write(imgBuffer)
			elif getBinary:
				return imgBuffer
				outputImageName += " to memory, framing..."
			print(downloadText + outputImageName)

	def iconFrame(my,inputID,rarity,atk_type):
		filepath = os.path.join(IMAGE_ASSET_DIRECTORY, "icon_{0}.png".format(inputID))
		filedata = my.downloadCharaImage(inputID,IMG_ICON,True)

		if not my.dryRun:
			try:
				IconMerger.get_framed_icon(filedata,filepath,int(rarity),int(atk_type))
			except Exception as error:
				print("Unable to frame {0}.png".format(inputID))
				print(type(error).__name__)
			else:
				print("Successfully framed {0}.png".format(inputID))


class DownloadAudio(object):
	def __init__(my,dryRun=False):
		my.dryRun = dryRun
		my.voiceGeneralLineList = [
			{"remotename":"introduction001", "localname":"libraryintro"},
			{"remotename":"gachaget", "localname":"introduction"},
			{"remotename":"battlestart001", "localname":"battlestart001", "mariageFlag":True},
			{"remotename":"battlestart002", "localname":"battlestart002", "mariageFlag":True},
			{"remotename":"normalattack001", "localname":"normalattack001"},
			{"remotename":"normalattack002", "localname":"normalattack002"},
			{"remotename":"skillattack001", "localname":"skillattack001"},
			{"remotename":"skillattack002", "localname":"skillattack002"},
			{"remotename":"damage001", "localname":"damage001"},
			{"remotename":"criticaldamage001", "localname":"criticaldamage001"},
			{"remotename":"dead001", "localname":"defeated001"},
			{"remotename":"victory001", "localname":"victory001"},
			{"remotename":"narrowvictory001", "localname":"narrowvictory001"},
			{"remotename":"easyvictory001", "localname":"easyvictory001"},
			{"remotename":"existence001", "localname":"enemypersist001"},
			{"remotename":"existence002", "localname":"enemypersist002"},
			{"remotename":"defeat001", "localname":"enemydefeat001"},
			{"remotename":"defeat002", "localname":"enemydefeat002"},
			{"remotename":"findout001", "localname":"foundtreasure001"},
			{"remotename":"finddoor001", "localname":"foundextrastage001"},
			{"remotename":"damagetrap001", "localname":"damagetrap001"},
			{"remotename":"ptselect001", "localname":"joinparty001", "mariageFlag":True},
			{"remotename":"ptselect002", "localname":"joinparty002", "mariageFlag":True},
			{"remotename":"equipchange001", "localname":"equipchange001", "mariageFlag":True},
			{"remotename":"charalevelup001", "localname":"charalevelup001"},
			{"remotename":"evolut001", "localname":"evolution001"},
			{"remotename":"enjoyment001", "localname":"conversation001"},
			{"remotename":"enjoyment002", "localname":"conversation002"},
			{"remotename":"enjoyment003", "localname":"conversation003"},
			{"remotename":"mypagetalk001", "localname":"mypagetalk001", "mariageFlag":True},
			{"remotename":"mypagetalk002", "localname":"mypagetalk002", "mariageFlag":True},
			{"remotename":"mypagetalk003", "localname":"mypagetalk003", "mariageFlag":True},
			{"remotename":"mypageignore", "localname":"mypageidle", "mariageFlag":True},
			{"remotename":"present001", "localname":"present001"},
			{"remotename":"present002", "localname":"present002"},
			{"remotename":"loginbonus", "localname":"loginbonus", "mariageFlag":True},
			{"remotename":"generalvoice002", "localname":"generalvoice002", "mariageFlag":True},
			{"remotename":"generalvoice001", "localname":"generalvoice001", "mariageFlag":True},
			{"remotename":"generalvoice003", "localname":"generalvoice003", "mariageFlag":True},
			{"remotename":"generalvoice004", "localname":"generalvoice004", "mariageFlag":True},
			{"remotename":"freegachaplay", "localname":"freegachaplay", "mariageFlag":True},
			{"remotename":"staminamax", "localname":"staminamax", "mariageFlag":True},
			{"remotename":"bootmypagetalk001", "localname":"bootmypagetalk001", "mariageFlag":True},
			{"remotename":"bootmypagetalk002", "localname":"bootmypagetalk002", "mariageFlag":True},
			{"remotename":"bootmypagetalk003", "localname":"bootmypagetalk003", "mariageFlag":True},
			{"remotename":"stagestart001", "localname":"stagestart001"},
			{"remotename":"stagestart002", "localname":"stagestart002"},
			{"remotename":"title001", "localname":"title001"},
			{"remotename":"newyear001", "localname":"newyear001", "mariageFlag":True},
			{"remotename":"newyear002", "localname":"newyear002", "mariageFlag":True},
			{"remotename":"tanabata001", "localname":"tanabata001", "mariageFlag":True},
			{"remotename":"tanabata002", "localname":"tanabata002", "mariageFlag":True},
			{"remotename":"summer001", "localname":"summer001", "mariageFlag":True},
			{"remotename":"summer002", "localname":"summer002", "mariageFlag":True},
			{"remotename":"tsukimi001", "localname":"tsukimi001", "mariageFlag":True},
			{"remotename":"tsukimi002", "localname":"tsukimi002", "mariageFlag":True},
			{"remotename":"autumn001", "localname":"autumn001", "mariageFlag":True},
			{"remotename":"autumn002", "localname":"autumn002", "mariageFlag":True},
			{"remotename":"halloween001", "localname":"halloween001", "mariageFlag":True},
			{"remotename":"halloween002", "localname":"halloween002", "mariageFlag":True},
			{"remotename":"winter001", "localname":"winter001", "mariageFlag":True},
			{"remotename":"winter002", "localname":"winter002", "mariageFlag":True},
			{"remotename":"holychristmas001", "localname":"holychristmas001", "mariageFlag":True},
			{"remotename":"holychristmas002", "localname":"holychristmas002", "mariageFlag":True},
			{"remotename":"valentine001", "localname":"valentine001", "mariageFlag":True},
			{"remotename":"valentine002", "localname":"valentine002", "mariageFlag":True},
			{"remotename":"whiteday001", "localname":"whiteday001", "mariageFlag":True},
			{"remotename":"whiteday002", "localname":"whiteday002", "mariageFlag":True},
			{"remotename":"spring001", "localname":"spring001", "mariageFlag":True},
			{"remotename":"spring002", "localname":"spring002", "mariageFlag":True},
			]
		my.voiceBloomLineList = [
			{"remotename":"flowering001", "localname":"flowering001"},
			{"remotename":"skillattack003", "localname":"skillattack003"},
			{"remotename":"skillattack004", "localname":"skillattack004"},
			{"remotename":"enjoyment004", "localname":"conversation004"},
			{"remotename":"enjoyment005", "localname":"conversation005"},
			{"remotename":"enjoyment006", "localname":"conversation006"},
			{"remotename":"mypagetalk004", "localname":"mypagetalk004", "mariageFlag":True},
			{"remotename":"mypagetalk005", "localname":"mypagetalk005", "mariageFlag":True},
			{"remotename":"mypagetalk006", "localname":"mypagetalk006", "mariageFlag":True},
			]
		my.voiceSeasonalList = [
			{"remotename":"christmas001", "localname":"christmas001"},
			{"remotename":"christmas002", "localname":"christmas002"},
			{"remotename":"tanabata003", "localname":"tanabata003"},
			{"remotename":"summer003", "localname":"summer003"},
			{"remotename":"tsukimi003", "localname":"tsukimi003"},
			{"remotename":"autumn003", "localname":"autumn003"},
			{"remotename":"halloween003", "localname":"halloween003"},
			{"remotename":"winter003", "localname":"winter003"},
			{"remotename":"holychristmas003", "localname":"holychristmas003"},
			{"remotename":"newyear003", "localname":"newyear003"},
			{"remotename":"valentine003", "localname":"valentine003"},
			{"remotename":"whiteday003", "localname":"whiteday003"},
			{"remotename":"spring003", "localname":"spring003"},
			{"remotename":"tanabata004", "localname":"tanabata004"},
			{"remotename":"summer004", "localname":"summer004"},
			{"remotename":"tsukimi004", "localname":"tsukimi004"},
			{"remotename":"autumn004", "localname":"autumn004"},
			{"remotename":"halloween004", "localname":"halloween004"},
			{"remotename":"winter004", "localname":"winter004"},
			{"remotename":"holychristmas004", "localname":"holychristmas004"},
			{"remotename":"newyear004", "localname":"newyear004"},
			{"remotename":"valentine004", "localname":"valentine004"},
			{"remotename":"whiteday004", "localname":"whiteday004"},
			{"remotename":"spring004", "localname":"spring004"},
			{"remotename":"tanabata005", "localname":"tanabata005"},
			{"remotename":"summer005", "localname":"summer005"},
			{"remotename":"tsukimi005", "localname":"tsukimi005"},
			{"remotename":"autumn005", "localname":"autumn005"},
			{"remotename":"halloween005", "localname":"halloween005"},
			{"remotename":"winter005", "localname":"winter005"},
			{"remotename":"holychristmas005", "localname":"holychristmas005"},
			{"remotename":"newyear005", "localname":"newyear005"},
			{"remotename":"valentine005", "localname":"valentine005"},
			{"remotename":"whiteday005", "localname":"whiteday005"},
			{"remotename":"spring005", "localname":"spring005"}
			]
		my.voiceMariageList = [
			{"remotename":"kscene001", "localname":"mariage001"}, #fkg_000261_kscene003_forever
			{"remotename":"kscene002", "localname":"mariage002"}, #fkg_000261_kscene003_forever
			{"remotename":"kscene003", "localname":"mariage003"}, #fkg_000261_kscene003_forever
			{"remotename":"teien001",  "localname":"garden001" }, #fkg_000261_teien003_forever
			{"remotename":"teien002",  "localname":"garden002" }, #fkg_000261_teien003_forever
			{"remotename":"teien003",  "localname":"garden003" }, #fkg_000261_teien003_forever
			#{"remotename":"battlestart001", "localname":"battlestart001"}, #fkg_000261_battlestart001_forever
			#{"remotename":"battlestart002", "localname":"battlestart002"}, #fkg_000261_battlestart002_forever
			#if "mariageFlag" in VoiceEntry: https://dugrqaqinbtcq.cloudfront.net/product/ynnFQcGDLfaUcGhp/assets/voice/f/{libid}/return fkg_00{charaID}_{voiceline}_forever
		]
		my.voiceBatchList = []
		my.rootURL_voice = "http://dugrqaqinbtcq.cloudfront.net/product/ynnFQcGDLfaUcGhp/assets/voice/{0}/{1}/{2}.mp3"
		#my.rootURL_voice_mariage = https://dugrqaqinbtcq.cloudfront.net/product/ynnFQcGDLfaUcGhp/assets/voice/f/000261/11b2b969f92a7654e469e385d4a09f0c.mp3
		#my.rootURL_voice_mariage = https://dugrqaqinbtcq.cloudfront.net/product/ynnFQcGDLfaUcGhp/assets/voice/f/{libid}/{fkg_000261_kscene001_forever}.mp3
		#my.rootURL_voice = "http://dugrqaqinbtcq.cloudfront.net/product/voice/c/{0}/{1}.bin"
		#http://dugrqaqinbtcq.cloudfront.net/product/voice/c/125007/f1ffea07ee080f9e3e90283c97c87123.mp3
		#http://dugrqaqinbtcq.cloudfront.net/product/voice/c/125007/fkg_gachaget.mp3
		#http://dugrqaqinbtcq.cloudfront.net/product/ynnFQcGDLfaUcGhp/assets/voice/c/111703/1dc72c7085354dcb95972898e74c69b2.mp3?1.293.0
		
		#getmrriagelistfrom masterCharacterSamePerson
		
	def _getVoiceURL(my, voiceLine, flowerKnightID, MariageFlag=False):
		if MariageFlag:
			fileHash = md5("fkg_{0}_{1}_forever".format(flowerKnightID.zfill(6),voiceLine).encode('utf-8')).hexdigest()
			return my.rootURL_voice.format('f',flowerKnightID.zfill(6),fileHash)
		else:
			fileHash = md5("fkg_{0}".format(voiceLine).encode('utf-8')).hexdigest()
			return my.rootURL_voice.format('c',flowerKnightID,fileHash)
		
	def _getVoiceFilePath(my, voiceLine, flowerKnightID):
		if int(flowerKnightID) < 10000:
			voiceLine += "_oath"
		return "{0}_{1}.mp3".format(flowerKnightID.zfill(6),voiceLine).replace('\\n','')
		
	def addVoiceLink(my, voiceLine, flowerKnightID, MariageFlag=False):
		if not MariageFlag and not flowerKnightID.startswith("1"): flowerKnightID = "1"+flowerKnightID[1:]
		voiceLink = {"remotelink":my._getVoiceURL(voiceLine["remotename"],flowerKnightID,MariageFlag), "localfile":my._getVoiceFilePath(voiceLine["localname"],flowerKnightID)}
		my.voiceBatchList.append(voiceLink)
		
	def addOathVoiceLink(my, voiceLine, charaID):
		voiceLink = {"remotelink":my._getVoiceURL(voiceLine["remotename"],flowerKnightID,True), "localfile":my._getVoiceFilePath(voiceLine["localname"],flowerKnightID)}
		my.voiceBatchList.append(voiceLink)

	def getSeasonalCharacterVoice(my, flowerKnightEntry):
		for voiceLine in my.voiceSeasonalList:
			my.addVoiceLink(voiceLine,flowerKnightEntry.id0)

	def getCharacterVoice(my, flowerKnightEntry, allVoiceLine=False):
		if allVoiceLine:
			for voiceLine in my.voiceGeneralLineList+my.voiceBloomLineList:
				my.addVoiceLink(voiceLine,flowerKnightEntry.id0)
		#elif (flowerKnightEntry.is_bloomed_powers_only == '0' and flowerKnightEntry.evolution_tier == '3' and int(flowerKnightEntry.id0) > 400000):
		elif (int(flowerKnightEntry.id0) > 400000):
			for voiceLine in my.voiceBloomLineList:
				my.addVoiceLink(voiceLine,flowerKnightEntry.id0)
		else:
			for voiceLine in my.voiceGeneralLineList:
				my.addVoiceLink(voiceLine,flowerKnightEntry.id0)

	def getOathCharacterVoice(my, charaID):
		for voiceLine in my.voiceMariageList:
			my.addVoiceLink(voiceLine,charaID,True)
		for voiceLine in my.voiceGeneralLineList+my.voiceBloomLineList:
			if "mariageFlag" in voiceLine:
				my.addVoiceLink(voiceLine,charaID,True)
	
	def downloadAllVoice(my):
		if not os.path.exists(VOICE_ASSET_DIRECTORY): os.makedirs(VOICE_ASSET_DIRECTORY)
		downloadText = "Downloaded "
		if my.dryRun: downloadText = "Test d" + downloadText[1:]
		for queue in my.voiceBatchList:
			voiceFilePath = os.path.join(VOICE_ASSET_DIRECTORY, queue["localfile"])
			if os.path.isfile(voiceFilePath):
				print("{0} has been downloaded, skipped".format(queue["localfile"]))
			else:
				try:
					voiceBinary = urllibrary.urlopen(queue["remotelink"]).read()
					#voiceBinary = zlib.decompress(voiceRawBinary) No longer zlib decompressed
				except:
					print("Couldn't download " + queue["localfile"] + " " + queue["remotelink"])
				else:
					if not my.dryRun:
						with open(voiceFilePath, 'wb') as outfile:
							outfile.write(voiceBinary)
					print(downloadText + queue["localfile"])


class GetLuaModuleData(object):
	def __init__(my):
		my.moduleLink = r'https://flowerknight.fandom.com/wiki/Module:{0}?{1}action=raw'
		my.lua_charalist = my.getCharaIDList()
		my.lua_equiplist = my.getEquipIDList()
		my.lua_oathlist  = my.getOathIDList()
		print("Loading module data...")
	
	def getModuleData(my,ModuleLink,splitParam,oldID=''):
		if oldID != '':
			oldID = "oldid={0}&".format(oldID)
		return urllibrary.urlopen(my.moduleLink.format(ModuleLink,oldID)).read().decode("utf-8").split(splitParam)
	
	def getCharaIDList(my,oldID=''):
		lua_charadata = my.getModuleData('MasterCharacterData','},\n["',oldID)
		lua_charalist = {}
		lua_orderlist = []
		
		for x in lua_charadata:
			lua_orderlist.append(int(x.partition('id = ')[2].partition(',')[0]))
			lua_charalist[x.partition('id = ')[2].partition(',')[0]] = x.partition('tier3PowersOnlyBloom = ')[2].partition(',')[0]
		
		lua_orderlist = [str(x) for x in sorted(lua_orderlist)]
		return OrderedDict({x:lua_charalist[x] for x in lua_orderlist})

	def getEquipIDList(my,oldID=''):
		lua_equipdata = my.getModuleData('Equipment/Data','\n\t[',oldID)[1:]
		return sorted([str(int(x.partition(']')[0])) for x in lua_equipdata])

	def getOathIDList(my,oldID=''):		
		lua_oathdata = my.getModuleData('BlessedOathList','\t',oldID)[1:]#,'174552')
		return [re.sub(r'[^0-9]', '', x) for x in lua_oathdata]


class CompareData(object):
	def __init__(my, dryRun=False):
		my.dryRun = dryRun
		my.master_data = parse_master.MasterData()
		my.module_data = GetLuaModuleData()
		my.downloadImage = DownloadImage(DOWNLOAD_TEST)
		my.downloadAudio = DownloadAudio(DOWNLOAD_TEST)
		my.character_id_lookup = []
		my.equipment_id_lookup = []
		my.mariage_id_lookup = []

	def compareMasterData(my):
		character_entries_dict = {int(entry):my.master_data.characters[entry] for entry in my.master_data.characters if my.master_data.characters[entry].isFlowerKnight1 == '1'}
		character_module_data = my.module_data.lua_charalist
		my.equipment_id_lookup = [entry[2] for entry in my.master_data.equipment_entries if entry[2] not in my.module_data.lua_equiplist and int(entry[2]) >= 380000]
		my.mariage_id_lookup = [entry.sameCharacterID for entry in my.master_data.bless_oath if entry.sameCharacterID not in my.module_data.lua_oathlist]
		
		for key in character_entries_dict:
			entry = character_entries_dict[key]
			if int(entry.evolutionTier) == 1 and not entry.id0.startswith("7"):
				if entry.id0 not in character_module_data:
					my.character_id_lookup.append(entry)
					try:
						my.character_id_lookup.append(character_entries_dict[key+1])
					except:
						print("ID {0} has no valid data entry.".format(key))
				elif character_module_data[entry.id0] != entry.isBloomedPowersOnly:
					my.character_id_lookup.append(character_entries_dict[key+300000])
		print(my.character_id_lookup)
		print(my.mariage_id_lookup)
		
		for entry in my.character_id_lookup:
			if IMAGE_DOWNLOAD : my.downloadImage.getCharacterImage(entry)
			print(entry.id0+" "+entry.rarity+" "+entry.type+" "+entry.evolutionTier)
			if entry.evolutionTier != '2' and VOICE_DOWNLOAD:
				my.downloadAudio.getCharacterVoice(entry)

		if IMAGE_DOWNLOAD: 	
			for entry in my.equipment_id_lookup:
				my.downloadImage.downloadEquipImage(entry)

		for entry in my.mariage_id_lookup:
			my.downloadAudio.getOathCharacterVoice(entry)
		
		if VOICE_DOWNLOAD: my.downloadAudio.downloadAllVoice()
		

def main():
	compareData = CompareData()
	compareData.compareMasterData()

if __name__ == '__main__':
	main()
