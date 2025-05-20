#!/usr/bin/python
# -*- coding: utf-8  -*-
import pywikibot
import parse_master
import requests
from pywikibot import i18n
from update_lists import ListUpdaterBot
from collections import OrderedDict
#import os, sys, re, requests

json_data = {}

#Retrieve the source text from japanese wiki
wikiLink = "http://フラワーナイトガール.攻略wiki.com/index.php?"
masterData = "outputs/getMaster.txt"

class GenerateQuote(object):
	def __init__(my):
		my.api_data = None
		#Defines the list of quotes to retrieve
		my.quoteList = ["初登場",
		"戦闘開始①",
		"汎用(喜)",
		"戦闘開始②",
		"攻撃①",
		"攻撃②",
		"汎用(哀)",
		"戦闘スキル①",
		"戦闘スキル②",
		"戦闘スキル③(開花)",
		"戦闘スキル④(開花)",
		"汎用(怒)",
		"被ダメージ",
		"被ダメージ(致命傷)",
		"戦闘不能",
		"汎用(楽)",
		"戦闘勝利①通常",
		"戦闘勝利②辛勝",
		"ログイン時①",
		"戦闘勝利③快勝",
		"敵を倒せなかった時①",
		"敵を倒せなかった時②",
		"ログイン時②",
		"敵を倒した時①",
		"敵を倒した時②",
		"ログイン時③",
		"ステージ発見",
		"宝箱",
		"会話①<br>(好感度0～29%)",
		"パーティメンバーに選出①",
		"パーティメンバーに選出②",
		"装備変更",
		"会話②<br>(好感度30～74%)",
		"レベルアップ",
		"進化",
		"開花",
		"1日1回無料ガチャがプレイ可能",
		"マイページ汎用①",
		"会話③<br>(好感度75～100%)",
		"マイページ汎用②",
		"スタミナが全回復している状態",
		"マイページ汎用③",
		"マイページ放置",
		"贈り物プレゼント時①",
		"贈り物プレゼント時②",
		"移動開始時①",
		"移動開始時②",
		"ログインボーナス",
		"マイページ汎用④(開花)",
		"マイページ汎用⑤(開花)",
		"マイページ汎用⑥(開花)",
		"会話④",
		"会話⑤",
		"会話⑥",
		"害虫の巣パネル通過時"]

		#Define a series of extra texts
		my.outputTextList = [
		"\n| libraryintro = <!--Library Introduction-->",
		"| introduction = <!--First-time Introduction-->",
		"| battlestart001 = <!--Battle Start 1-->",
		"| generalvoice001 = <!--Generic Response (Positive)-->",
		"| battlestart002 = <!--Battle Start 2-->",
		"| normalattack001 = <!--Attacking 1-->",
		"| normalattack002 = <!--Attacking 2-->",
		"| generalvoice002 = <!--Generic Response (Grief)-->",
		"| skillattack001 = <!--Combat Skill Use 1-->",
		"| skillattack002 = <!--Combat Skill Use 2-->",
		"| skillattack003 = <!--Combat Skill Use 3 (Bloomed)-->",
		"| skillattack004 = <!--Combat Skill Use 4 (Bloomed)-->",
		"| generalvoice003 = <!--Generic Response (Angry)-->",
		"| damage001 = <!--Takes Damage-->",
		"| criticaldamage001 = <!--Takes Fatal Damage-->",
		"| defeated001 = <!--Battle Defeat-->",
		"| generalvoice004 = <!--Generic Response (Joy)-->",
		"| victory001 = <!--Victory Cheer 1 (Generic)-->",
		"| narrowvictory001 = <!--Victory Cheer 2 (Narrow)-->",
		"| bootmypagetalk001 = <!--Login 1-->",
		"| easyvictory001 = <!--Victory Cheer 3 (Sweeping)-->",
		"| enemypersist001 = <!--Fail to Vanquish Opponent 1-->",
		"| enemypersist002 = <!--Fail to Vanquish Opponent 2-->",
		"| bootmypagetalk002 = <!--Login 2-->",
		"| enemydefeat001 = <!--Defeat Enemy 1-->",
		"| enemydefeat002 = <!--Defeat Enemy 2-->",
		"| bootmypagetalk003 = <!--Login 3-->",
		"| foundextrastage001 = <!--Stage Discovery-->",
		"| foundtreasure001 = <!--Treasure Chest-->",
		"| conversation001 = <!--Conversation 1 (affection 0-29%)-->",
		"| joinparty001 = <!--Add to Party 1-->",
		"| joinparty002 = <!--Add to Party 2-->",
		"| equipchange001 = <!--Change Equipment-->",
		"| conversation002 = <!--Conversation 2 (affection 30-74%)-->",
		"| charalevelup001 = <!--Level Up-->",
		"| conversation003 = <!--Conversation 3 (affection 75-100%)-->",
		"| evolution001 = <!--Evolution-->",
		"| flowering001 = <!--Blooming-->",
		"| freegachaplay = <!--Pulling Free Daily Gacha-->",
		"| mypagetalk001 = <!--My Page Generic Phrase 1-->",
		"| mypagetalk002 = <!--My Page Generic Phrase 2-->",
		"| staminamax = <!--Recovering Stamina-->",
		"| mypagetalk003 = <!--My Page Generic Phrase 3-->",
		"| mypageidle = <!--My Page Idle-->",
		"| present001 = <!--Give Gift 1-->",
		"| present002 = <!--Give Gift 2-->",
		"| stagestart001 = <!--Moving 1-->",
		"| stagestart002 = <!--Moving 2-->",
		"| loginbonus = <!--Login Bonus-->",
		"| mypagetalk004 = <!--My Page Generic Phrase 4-->",
		"| mypagetalk005 = <!--My Page Generic Phrase 5-->",
		"| mypagetalk006 = <!--My Page Generic Phrase 6-->",
		"| conversation004 = <!--My Page Generic Phrase 4 (Bloomed)-->",
		"| conversation005 = <!--My Page Generic Phrase 5 (Bloomed)-->",
		"| conversation006 = <!--My Page Generic Phrase 6 (Bloomed)-->",
		"}}"]

	def downloadText(my, charaName):
		retry = 5
		for r in range(retry + 1):
			try:
				dltext = requests.get(wikiLink + charaName).text
			except requests.RequestException as error:
				if r < retry:
					print(f"loading {charaName} attempt failed, retrying...")
				else:
					print(f"Unable to load {charaName}")
					print(type(error).__name__)
			else:
				if dltext.find('<div class="ie5">') == -1 :
					redirect = charaName.replace("(","（").replace(")","）")
					dltext  = requests.get(wikiLink + redirect).text
				return dltext.replace(' class="spacer" /','').replace(' class="style_td"','').replace('"','\\"')

	def translateLink(my, inputText):
		#No longer used due to difficulty handling external links
		#for <a> tag and index is found until -1, transform links
		while inputText.find('</a>') != -1:
			hyperLink = inputText.partition('<a')[2].partition('>')[0].partition('href=\\"')[2].partition('\\"')[0]
			hyperText = inputText.partition('">')[2].partition('</a>')[0]
			if hyperLink != "":
				linkedText = '[{0} {1}]'.format(hyperLink,hyperText)
			else:
				linkedText = hyperText
			inputText = inputText.partition('<a')[0] + linkedText + inputText.partition('</a>')[2]

		return inputText

	def removeLink(my, inputText):
		#for <a> tag and index is found until -1, transform links
		while inputText.find('<a') != -1:
			inputText = inputText.partition("<a")[0] + inputText.partition("<a")[2].partition(">")[2]

		return inputText.replace('</a>','')
	
	def testIndex(my, mylist, key):
		try:
			return mylist[key]
		except KeyError:
			print(str(key) + " doesn't have text entry.")
			return ""

	def addExceptions(my, inputText, CharaName):
		outputText = inputText
		
		exceptionList = {
                        "コオニタビラコ(新春)": ["戦闘スキル③(開花) = \n| 戦闘スキル④(開花) = ","| 戦闘スキル③(開花) = 手加減しません！\n| 戦闘スキル④(開花) = これでおしまいです！"],
			"ランタナ(花祭り)": ["初登場 = イエスロリータ・ゴータッチ！","初登場 = 花祭りのニギニギしさを浴びて！<br>ロリっ子美少女ランタナ、新たな衣装でコーリンどぅわあああああ！<br>さぁ、愛でまくるがいい、だんちょ！　イエスロリータ・ゴータッチ！"],
			"サテラ": ["移動開始時① = ","移動開始時① = サテラについてこい！"],
			"セントポーリア(きぐるみのんびり貴族)": ["| 会話④ = \n| 会話⑤ = \n| 会話⑥ = ","| 会話④ = 団長さん、新しいドレスどうでしょう？　えへへへ、いっぱい見てくれますね。 何だか、インコの服よりもこちらの方が恥ずかしいですね♪\n| 会話⑤ = インコの衣装を着たら～何だか…身も心も軽くなった気がしました。 色んな衣装を着たら、もっと違う私になれるかも知れませんね～♪\n| 会話⑥ = ドレスの私も～インコの私も～どちらも私です～　団長さんは色々な私を受け入れてくれるからとっても嬉しいんですよ♪<br>ずっと一緒に居てくださいね、団長さ～ん♪"]
		}
		
		if CharaName in exceptionList:
			outputText = inputText.replace(exceptionList[CharaName][0], exceptionList[CharaName][1])

		return my.removeLink(outputText)

	def parseMasterData(my):
		#Retrieves quotes from master data if Japanese wiki is not updated yet.
		debugFlag = False
		fkgidindex = OrderedDict()
		quoteindex = OrderedDict()

		with open(masterData, 'r', encoding='utf8') as input:
			masterDataEntry = input.read()
		
		textResource = masterDataEntry.partition("masterCharacterTextResource\n\n")[2].partition("\n\n")[0].split('\n') + masterDataEntry.partition("masterCharacterTextResource2\n\n")[2].partition("\n\n")[0].split('\n')
		
		for entry in textResource:
			if entry != '':
				fkgid     = entry.split(',')[1]
				if int(fkgid) % 2 == 1:
					voiceline = entry.split(',')[3]
					voicetype = entry.split(',')[4]
				
					quoteindex[fkgid + voicetype] = voiceline

		for entry in masterDataEntry.partition("masterCharacter\n\n")[2].partition("\n200003")[0].split('\n'):
			fkgid   = entry.split(',')[0]
			isfkg   = entry.split(',')[39]
			if int(fkgid) % 2 == 1 and isfkg == '1':
				fkgname = entry.split(',')[53].replace('"','')

				fkgidindex[fkgname] = {
					"fkgid":fkgid,
					"fkg_libraryintro": my.testIndex(quoteindex, fkgid + "fkg_introduction001"),
					"fkg_stagestart001": my.testIndex(quoteindex, fkgid + "fkg_stagestart001"),
					"fkg_present001": my.testIndex(quoteindex, fkgid + "fkg_present001"),
					"fkg_present002": my.testIndex(quoteindex, fkgid + "fkg_present002"),
				}

		if debugFlag:
			for x in fkgidindex:
				print(x + "\t" + fkgidindex[x]["fkg_libraryintro"])

		if not my.api_data:
			my.api_data = fkgidindex
			#print("MasterData loaded")

		#	print(x.split(",")[0] + " " + x.split(",")[55])
		#https://dugrqaqinbtcq.cloudfront.net/product/ynnFQcGDLfaUcGhp/assets/event/
		#https://dugrqaqinbtcq.cloudfront.net/product/ynnFQcGDLfaUcGhp/assets/event/new/ new_


	def printquote(my, charaName, wikiText, updateFlag=False):
		charaName = charaName.replace('10thAnniversary','10th Anniversary')
		rawdata = my.downloadText(charaName)
		if not my.api_data: my.parseMasterData()
		#masterdata = my.getText(charaName) get intro line from get master

		#Filter the text with a series of text delimiter partitioning and formatting.
		libintro = rawdata.partition("自己紹介")[2].partition("<strong>")[2].partition("</strong>")[0].partition("</td>")[0] + "\n"
		
		if libintro.find("図鑑のテキストを記載") != -1:
		# not updateFlag or
			libintro = my.api_data[charaName]["fkg_libraryintro"] + "\n"

		quotetext = rawdata.partition("ボイス")[2].partition(">シーン")[2]#.partition("</table>")[0]
		textList = []

		for quote in my.quoteList:

			quoteEntry  = quote.replace('<br>','')
			quoteInput  = "<td>"+quote.partition("(好感度")[0].partition("(開花)")[0].partition("<br>")[0]
			quoteSpeech = quotetext.partition(quoteInput)[2].partition("<td>")[2].partition("</td>")[0].replace('&quot;','"').replace("#REF!","<br>")
			#if (quoteInput == "<td>害虫の巣パネル通過時") and (quoteSpeech == "") : print(quoteEntry+" "+quoteInput+" "+quoteSpeech)
			
			if (quoteInput == "<td>移動開始時①") and (quoteSpeech == "") :
				quoteSpeech = my.api_data[charaName]["fkg_stagestart001"]
			if (quoteInput == "<td>贈り物プレゼント時①") and (quoteSpeech == "") :
				quoteSpeech = my.api_data[charaName]["fkg_present001"]
			if (quoteInput == "<td>贈り物プレゼント時②") and (quoteSpeech == "") :
				quoteSpeech = my.api_data[charaName]["fkg_present002"]
			if (quoteInput == "<td>戦闘スキル③") and (quoteSpeech == "") :
				quoteSpeech = quotetext.partition("戦闘スキル開花①")[2].partition("<td>")[2].partition("</td>")[0].replace('&quot;','"').replace("#REF!","<br>")
			if (quoteInput == "<td>戦闘スキル④") and (quoteSpeech == "") :
				quoteSpeech = quotetext.partition("戦闘スキル開花②")[2].partition("<td>")[2].partition("</td>")[0].replace('&quot;','"').replace("#REF!","<br>")
			if (quoteInput == "<td>害虫の巣パネル通過時") and (quoteSpeech == "") :
				quoteSpeech = quotetext.partition('ダメージギミック接触時')[2].partition("<td>")[2].partition("</td>")[0].replace('&quot;','"') + quotetext.partition('ダメージパネル接触時')[2].partition("<td>")[2].partition("</td>")[0].replace('&quot;','"')
			textList.append("| " + quoteEntry + " = " + quoteSpeech)

		if updateFlag :
			endText = "{{{{Knightquote\n| CharaName = {0}\n\n| 自己紹介 = {1}{2}".format(charaName,libintro,'\n'.join(textList))
		else:
			endText = "\n==Quotes==\n{{{{Knightquote\n| CharaName = {0}\n\n| 自己紹介 = {1}{2}".format(charaName,libintro,'\n'.join(textList+my.outputTextList))

		#if "| 移動開始時① =\n|" append stagestart text 
		
		

		fileName = charaName + "_quote.txt"

		return my.addExceptions(endText,charaName)

def test():
	ListUpdater = ListUpdaterBot()
	site = pywikibot.Site()
	page = pywikibot.Page(site, u'Colchicum')
	wikiText = page.get()
	comment = 'Added quotes'
	flowerKnightName = wikiText.partition("|JP = ")[2].partition("\n")[0].replace(' ','').replace('10thAnniversary','10th Anniversary')
	textLines = []

	if wikiText.find('Quotes') == -1 or wikiText.find('{{Knightquote') == -1:
		changeline = True
		for line in wikiText.split('\n'):
			if line.find('}}') != -1 and line.find(' = ') == -1 and changeline:
				line += GenerateQuote.printquote(flowerKnightName,wikiText)
				changeline = False
			if not line.replace(' ', '').startswith('==Quotes'):
				textLines.append(line)
		text = '\n'.join(textLines)
		comment = 'Added quotes'
	elif wikiText.find('<a') != -1:
		text = GenerateQuote.removeLink(wikiText)
		comment = 'Removed external link in quotes'
	else:
		text = wikiText.partition("{{Knightquote")[0] + GenerateQuote.printquote(flowerKnightName,wikiText,True) + "\n\n| libraryintro =" + wikiText.partition("libraryintro =")[2]
		comment = 'Updated quotes'

	ListUpdater.save(text, page, comment)

	#get libintro from masterCharacterTextResource

def output_template(text, outfilename):
	with open(outfilename, 'w', encoding='UTF8') as outfile:
		outfile.write(text)

def main():
	ListUpdater = ListUpdaterBot()
	site = pywikibot.Site()
	flowerKnightList = list(pywikibot.Category(site, 'Category:6-Star').articles()) \
	+ list(pywikibot.Category(site, 'Category:5-Star').articles()) \
	+ list(pywikibot.Category(site, 'Category:4-Star').articles())
	editorlist = []

	for page in flowerKnightList:
		editorlist.append(verifyKnightQuote(page))
	
	for page in editorlist:
		ListUpdater.save(page["text"], page["name"], page["comment"])

def verifyKnightQuote(page):
	wikiText = page.get()
	flowerKnightName = wikiText.partition("|JP = ")[2].partition("\n")[0].replace(' ','').replace('10thAnniversary','10th Anniversary')
	comment = ""
	textLines = []

	if wikiText.find('Quotes') == -1 or wikiText.find('{{Knightquote') == -1:
		changeline = True
		for line in wikiText.split('\n'):
			if line.find('}}') != -1 and line.find(' = ') == -1 and changeline:
				line += GenerateQuote.printquote(flowerKnightName,wikiText)
				changeline = False
			if not line.replace(' ', '').startswith('==Quotes'):
				textLines.append(line)
		text = '\n'.join(textLines)
		comment = 'Added quotes'
	elif wikiText.find('generalvoice002 = <!--Generic Response (Positive)') != -1:
		text = wikiText.replace("| generalvoice002 = <!--Generic Response (Positive)-->","| generalvoice001 = <!--Generic Response (Positive)-->").replace("| generalvoice001 = <!--Generic Response (Grief)-->","| generalvoice002 = <!--Generic Response (Grief)-->")
	elif wikiText.find('<a') != -1:
		text = GenerateQuote.removeLink(wikiText)
		comment = 'Removed external link from quotes'
	else:
		text = wikiText.partition("{{Knightquote")[0] + GenerateQuote.printquote(flowerKnightName,wikiText,True) + "\n\n| libraryintro =" + wikiText.partition("libraryintro =")[2]
		comment = 'Updated quotes'

	appendChange = ''
	if wikiText != text : appendChange = ' to be edited...'
	print("{0} {1}{2}".format(flowerKnightName, page.title(),appendChange))
	return {"text": text, "name": page, "comment": comment}
	#ListUpdater.save(text, page, comment)

if __name__ == "__main__":
	GenerateQuote = GenerateQuote()
	main()
