#!/usr/bin/python
# -*- coding: utf-8  -*-
import pywikibot
from pywikibot import i18n
import parse_master
import update_lists
import requests
#import os, sys, re, requests

class ListUpdaterBot(object):
    def __init__(my):
        my.site = pywikibot.Site()
        my.default_summary = i18n.twtranslate(my.site, 'basic-changing')
        my.comment = u'Automatic update by bot.'
        my.dry = False

    def save(self, text, page, comment=None, minorEdit=True,
             botflag=True):
        """Update the given page with new text."""
        # only save if something was changed
        if text != page.get():
            # Show the title of the page we're working on.
            # Highlight the title in purple.
            pywikibot.output(u"\n\n>>> \03{lightpurple}%s\03{default} <<<"
                             % page.title())
            # show what was changed
            pywikibot.showDiff(page.get(), text)
            pywikibot.output(u'Comment: %s' % comment)
            if not self.dry:
                if pywikibot.input_yn(
                        u'Do you want to accept these changes?',
                        default=False, automatic_quit=False):
                    try:
                        page.text = text
                        # Save the page
                        page.save(summary=comment or self.comment,
                                  minor=minorEdit, botflag=botflag)
                    except pywikibot.LockedPage:
                        pywikibot.output(u"Page %s is locked; skipping."
                                         % page.title(asLink=True))
                    except pywikibot.EditConflict:
                        pywikibot.output(
                            u'Skipping %s because of edit conflict'
                            % (page.title()))
                    except pywikibot.SpamfilterError as error:
                        pywikibot.output(
                            u'Cannot change %s because of spam blacklist entry %s'
                            % (page.title(), error.url))
                    else:
                        return True
        return False

#Retrieve the source text from japanese wiki
wikiLink = "http://フラワーナイトガール.攻略wiki.com/index.php?"

class GenerateQuote(object):
	def __init__(my):
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
		'戦闘スキル④(開花)',
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
		dltext = requests.get(wikiLink + charaName).text
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

	def printquote(my, charaName, updateFlag=False):
		rawdata = my.downloadText(charaName)

		#Filter the text with a series of text delimiter partitioning and formatting.
		libintro = rawdata.partition("自己紹介")[2].partition("<strong>")[2].partition("</strong>")[0] + "\n"
		
		quotetext = rawdata.partition(">図鑑収録ボイス</th></tr><tr>")[2].partition("</table>")[0]
		quotetext = quotetext
		textList = []

		for quote in my.quoteList:
			
			quoteEntry  = quote.replace('<br>','')
			quoteInput  = "<td>"+quote.partition("(開花)")[0]
			quoteSpeech = quotetext.partition(quoteInput)[2].partition("<td>")[2].partition("</td>")[0].replace('&quot;','"')
			textList.append("| " + quoteEntry + " = " + quoteSpeech)
		
		if updateFlag :
			endText = "{{{{Knightquote\n| CharaName = {0}\n\n| 自己紹介 = {1}{2}".format(charaName,libintro,'\n'.join(textList))
		else:
			endText = "\n==Quotes==\n{{{{Knightquote\n| CharaName = {0}\n\n| 自己紹介 = {1}{2}".format(charaName,libintro,'\n'.join(textList+my.outputTextList))
		
		fileName = charaName + "_quote.txt"

		return my.removeLink(endText)

def test():
	site = pywikibot.Site()
	page = pywikibot.Page(site, u'Colchicum')
	wikiText = page.get()
	comment = 'Added quotes'
	flowerKnightName = wikiText.partition("|JP = ")[2].partition("\n")[0].replace(' ','')
	textLines = []
	
	if wikiText.find('Quotes') == -1 or wikiText.find('{{Knightquote') == -1:
		changeline = True
		for line in wikiText.split('\n'):
			if line.find('}}') != -1 and line.find(' = ') == -1 and changeline:
				line += GenerateQuote.printquote(flowerKnightName)
				changeline = False
			if not line.replace(' ', '').startswith('==Quotes'):
				textLines.append(line)
		text = '\n'.join(textLines)
		comment = 'Added quotes'
	elif wikiText.find('<a') != -1:
		text = GenerateQuote.removeLink(wikiText)
		comment = 'Removed external link in quotes'
	else:
		text = wikiText.partition("{{Knightquote")[0] + GenerateQuote.printquote(flowerKnightName,True) + "\n\n| libraryintro =" + wikiText.partition("libraryintro =")[2]
		comment = 'Updated quotes'
	
	ListUpdater.save(text, page, comment)

def output_template(text, outfilename):
	with open(outfilename, 'w', encoding='UTF8') as outfile:
		outfile.write(text)
		
def main():
	site = pywikibot.Site()
	flowerKnightBaseList = pywikibot.Category(site, 'Category:6-Star').articles()
	flowerKnightAltList  = pywikibot.Category(site, 'Category:5-Star').articles()
	flowerKnightCoList   = pywikibot.Category(site, 'Category:4-Star').articles()
	
	for page in flowerKnightBaseList:
		updateKnightQuote(page)
		
	for page in flowerKnightAltList:
		updateKnightQuote(page)
		
	for page in flowerKnightCoList:
		updateKnightQuote(page)


def updateKnightQuote(page):
	wikiText = page.get()
	flowerKnightName = wikiText.partition("|JP = ")[2].partition("\n")[0].replace(' ','')
	comment = ""
	textLines = []
	
	if wikiText.find('Quotes') == -1 or wikiText.find('{{Knightquote') == -1:
		changeline = True
		for line in wikiText.split('\n'):
			if line.find('}}') != -1 and line.find(' = ') == -1 and changeline:
				line += GenerateQuote.printquote(flowerKnightName)
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
		text = wikiText.partition("{{Knightquote")[0] + GenerateQuote.printquote(flowerKnightName,True) + "\n\n| libraryintro =" + wikiText.partition("libraryintro =")[2]
		comment = 'Updated quotes'
	
	print(flowerKnightName)
	ListUpdater.save(text, page, comment)

if __name__ == "__main__":
	ListUpdater = ListUpdaterBot()
	GenerateQuote = GenerateQuote()
	main()
