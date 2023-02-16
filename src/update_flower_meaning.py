#!/usr/bin/python
# -*- coding: utf-8  -*-
import pywikibot
from pywikibot import i18n
from update_lists import ListUpdaterBot
import sys

MASTERDATA_CURRENT = "outputs\getMaster.txt"

class AddFlowerLanguage(object):
	def __init__(my):
		my.bot = ListUpdaterBot()
		my.master_data = "outputs\getMaster.txt"
		my.site = pywikibot.Site('en','fkg')
		my.site.login(False, 'NazunaBot')
		my.comment = 'Added Flower Knight\'s flower meaning.'
		my.flowerlist = pywikibot.Category(my.site, 'Category: LoF missing from CharacterStatTable').articles()
	
	def readText(my,infilename):
		with open(infilename, 'r', encoding='utf8') as infile:
			return infile.read()

	def updateFlowerMeaning(my,page):
		wikiText = page.get()
		flowerKnightName = wikiText.partition("|JP = ")[2].partition("\n")[0].replace(' ','')
		comment = 'Added Flower Knight\'s flower meaning'
		api_data = my.readText(MASTERDATA_CURRENT).partition('masterCharacterBook')[2][1:].partition('master')[0].strip().split('\n')
		flowerMeaning = ''
		textLines = []

		for entry in api_data:
			if entry.split(',')[3] == flowerKnightName.partition("(")[0]:
				flowerMeaning = entry.split(',')[5]

		text = wikiText.replace('|languageoftheflowers =\n','|languageoftheflowers = \n').replace('|languageoftheflowers = \n','|languageoftheflowers = ' + flowerMeaning + '\n')
		my.bot.save(text, page, comment)
		print("{0} {1} {2}".format(page.title(),flowerKnightName,flowerMeaning))

	def run(my):
		for page in my.flowerlist:
			my.updateFlowerMeaning(page)

def main():
	lof = AddFlowerLanguage()
	lof.run()

if __name__ == "__main__":
	main()
