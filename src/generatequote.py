#!/usr/bin/python3
# coding: utf-8
import os, sys, re, requests

#Retrieve the source text from japanese wiki
flowerKnightList = ["アルストロメリア","フクジュソウ","アネモネ"]
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
		"| generalvoice002 = <!--Generic Response (Positive)-->",
		"| battlestart002 = <!--Battle Start 2-->",
		"| normalattack001 = <!--Attacking 1-->",
		"| normalattack002 = <!--Attacking 2-->",
		"| generalvoice001 = <!--Generic Response (Grief)-->",
		"| skillattack001 = <!--Combat Skill Use 1-->",
		"| skillattack002 = <!--Combat Skill Use 2-->",
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
		"| flowering001 = <!--Blooming-->",
		"| conversation004 = <!--My Page Generic Phrase 4 (Bloomed)-->",
		"| conversation005 = <!--My Page Generic Phrase 5 (Bloomed)-->",
		"| conversation006 = <!--My Page Generic Phrase 6 (Bloomed)-->",
		"| skillattack003 = <!--Combat Skill Use 3 (Bloomed)-->",
		"| skillattack004 = <!--Combat Skill Use 4 (Bloomed)-->",
		"}}"]
	
	def downloadText(my, charaName):
		notice = "Processing " + charaName
		dltext = requests.get(wikiLink + charaName).text

		if dltext.find('<div class="ie5">') == -1 :
			redirect = charaName.replace("(","（").replace(")","）")
			dltext  = requests.get(wikiLink + redirect).text
			notice  += ".redirected -> " + redirect
		print(notice)
		
		return dltext.replace(' class="spacer" /','').replace(' class="style_td"','').replace('"','\\"')

	def printquote(my):
		for flowerKnight in flowerKnightList:
		
			rawdata = my.downloadText(flowerKnight)

			#Filter the text with a series of text delimiter partitioning and formatting.
			libintro = rawdata.partition("自己紹介")[2].partition("<strong>")[2].partition("</strong>")[0] + "\n"
			
			quotetext = rawdata.partition(">図鑑収録ボイス</th></tr><tr>")[2].partition("</table>")[0]
			quotetext = quotetext
			textList = []

			for quote in my.quoteList:
				
				quoteEntry  = quote.replace('<br>','')
				quoteSpeech = quotetext.partition(quote)[2].partition("<td>")[2].partition("</td>")[0]
				textList.append("| " + quoteEntry + " = " + quoteSpeech)
				
			#print(endtext)
			
			endText = "{{{{Knightquote\n| CharaName = {0}\n\n| 自己紹介 = {1}{2}".format(flowerKnight,libintro,'\n'.join(textList+my.outputTextList))
			fileName = flowerKnight + "_quote.txt"
			output_template(endText,fileName)

def output_template(text, outfilename):
	with open(outfilename, 'w', encoding='UTF8') as outfile:
		outfile.write(text)
		
if __name__ == '__main__':
	GenerateQuote = GenerateQuote()
	GenerateQuote.printquote()
