#!/usr/bin/python3
# coding: utf-8
import os, sys, re, requests

mainurl = "http://フラワーナイトガール.攻略wiki.com/index.php?"
output_dir = "outputs"
charaModule = "https://flowerknight.fandom.com/wiki/Module:CharacterNames?action=raw"
manualCharaList = ["オンシジューム（フォスの花嫁）","","ホワイトパンジー","イエローパンジー","パープルパンジー","ネムノキ","天久保百合(エクスティア・フローラ)"]# ,"ツバキ","ブラックバッカラ","ロイヤルプリンセス"]

class GenerateSeasonalQuote(object):
	def __init__(my):
		my.legacyFlag = False
		my.manualFlag = True
		my.charaList = []
		my.eventQuoteSymbol = ["①","②","③","④","⑤"]
		my.limitedEventIndicator = "【期間限定】"
		my.moduleTextList = {}
		my.moduleWrapper = '--[[Category:Seasonal quote modules]]\n\nreturn {{\n{0}'
		my.quoteEntryTemplate = u' ["{0}"] = {{"{1}"}},\n'
		my.startYear = "2016年"
		my.seasonList = [
			{'modulename':'Tanabata', 'count':5, 'JPName':'七夕', 'voiceline':'tanabata'},
			{'modulename':'Summer', 'count':5, 'JPName':'夏', 'voiceline':'summer'},
			{'modulename':'Mid-Autumn', 'count':5, 'JPName':'お月見', 'voiceline':'tsukimi'},
			{'modulename':'Autumn', 'count':5, 'JPName':'秋', 'voiceline':'autumn'},
			{'modulename':'Halloween', 'count':5, 'JPName':'ハロウィン', 'voiceline':'halloween'},
			{'modulename':'Winter', 'count':5, 'JPName':'冬', 'voiceline':'winter'},
			{'modulename':'Christmas', 'count':5, 'JPName':'クリスマス', 'voiceline':'holychristmas', 'year':2016},
			{'modulename':'New_Year', 'count':4, 'JPName':'お正月', 'voiceline':'newyear'},
			{'modulename':'Valentine', 'count':4, 'JPName':'バレンタイン', 'voiceline':'valentine'},
			{'modulename':'White_Day', 'count':4, 'JPName':'ホワイトデー', 'voiceline':'whiteday'},
			{'modulename':'Spring', 'count':4, 'JPName':'春', 'voiceline':'spring'},
		]
		
		my.seasonList_unique = [
			{'modulename':'Christmas_2015', 'count':2, 'JPName':'クリスマス', 'voiceline':'christmas', 'year':2015}
		]
		
	def initModuleTextList(my):
		module = requests.get(charaModule).text
		if my.manualFlag:
			my.charaList = manualCharaList
		else:
			my.charaList = [chara.partition('"]')[0] for chara in module.partition("local base = {")[2].partition("-- Do not edit ")[0].split('["')[1:]]
		
		#for chara in module.partition("local base = {")[2].partition("-- Do not edit ")[0].split('["'):
		#	print(chara.partition('"]')[0])
		
		for season in my.seasonList:# + my.seasonList_unique:
			name  = season['modulename']
			count = season['count']
			if my.legacyFlag:
				my.moduleTextList[name] = [
					"[\"{0}{1}\"] = {{\n" \
					.format(season['voiceline'], str(i+1).zfill(3)) \
					for i in range(count)
				]
			else:
				my.moduleTextList[name] = []
	
	def downloadText(my, charaName):
		notice = "Processing " + charaName
		dltext = requests.get(mainurl + charaName).text

		if dltext.find('<div class="ie5">') == -1 :
			redirect = charaName.replace("(","（").replace(")","）")
			dltext  = requests.get(mainurl + redirect).text
			notice  += ".redirected -> " + redirect
		
		textdata = (dltext.replace('\r','').replace('\n','')
					.partition("valign=\"top\"")[2]
					.partition("<strong>ボイス")[2]
					.partition("</table>")[0]
					.replace(' class="spacer" /','')
					.replace(' class="style_td"','') )
				
		print(notice)

		return textdata

	def extractCharacterPage(my, charaName):
		rawText = my.downloadText(charaName)
		moduleCharacterEntry = ["[\""+charaName+"\"] = {\n  "]

		if rawText == '':
			print("Warning:{}'s HTML data is empty".format(charaName))
		
		for season in my.seasonList:
			if my.legacyFlag:
				for i in range(season['count']):
					my.extractQuoteLegacy(charaName, season, i, rawText)
			else:
				my.extractQuote(charaName, season, range(season['count']), rawText)

	def extractQuote(my, charaName, season, count, rawText):
		quoteList = []
		quoteEntryTemplate = u'  ["{0}"] = {{\n\t"{1}"\n\t}},\n'
		for index in count:
			quoteList.append(rawText.partition(season['JPName']+my.eventQuoteSymbol[index])[2]
				.partition('<td>')[2].partition("</td>")[0]
				.replace(' class="spacer" /','').replace('"','\\"')
			)
		
		for index, inputQuote in enumerate(quoteList):
			if inputQuote == '' and rawText != '':
				quoteIndex = my.eventQuoteSymbol[index] or '0'
				print('Missing {0} {1} {2}'.format(charaName, season['modulename'], quoteIndex))
				
		#add conditionals : check if rawtext != '', check if quoteList is not all ''
		#remove all trailing quotes and remove linebreaks if first quote is empty.
		#

		if rawText != '' and any(i != '' for i in quoteList):
			my.moduleTextList[season['modulename']].append(
				quoteEntryTemplate.format(charaName,'\",\n\t\"'.join(quoteList))
			)
		
		
	def extractQuoteLegacy(my, charaName, season, index, rawText):
		inputQuote = (rawText.partition(season['JPName']+my.eventQuoteSymbol[index])[2]
			.partition('<td>')[2].partition("</td>")[0]
			.replace(' class="spacer" /','').replace('"','\\"')
		)
		
		if inputQuote != '':
			my.moduleTextList[season['modulename']][index] += \
				my.quoteEntryTemplate.format(charaName,inputQuote)
		else:
			print('Missing {0} {1} {2}'.format(charaName, season['modulename'], my.eventQuoteSymbol[index]))

	def printModules(my):
		chain = ''
		footer = '\n}'
		if my.legacyFlag:
			chain = '},\n'
			footer = '\n\t}' + footer
		for module in my.moduleTextList:
			textContent = chain.join(my.moduleTextList[module])[:-1] + footer
			moduleText = my.moduleWrapper.format(textContent)
			moduleName = os.path.join(output_dir, "{0}.lua".format(module))
			
			output_template(moduleText,moduleName)
			
				
	def main(my):
		my.initModuleTextList()
		for flowerKnight in my.charaList:
			if flowerKnight != '':
				my.extractCharacterPage(flowerKnight)
		
		my.printModules()
	

def add_quotes(text):
	"""Puts pairs of double-quotes around strings."""
	if text.startswith('"') and text.endswith('"'):
		return text
	return '"' + text + '"'
		
def output_template(text, outfilename):
	with open(outfilename, 'w', encoding='UTF8') as outfile:
		outfile.write(text)

def main():
	quote = GenerateSeasonalQuote()
	quote.main()
		
if __name__ == '__main__':
	main()
