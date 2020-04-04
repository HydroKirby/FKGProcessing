#!/usr/bin/python
# -*- coding: utf-8  -*-
import pywikibot
from pywikibot import i18n
import sys

MASTERDATA_CURRENT = "getMasterDecoded.txt"

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

ListUpdater = ListUpdaterBot()

def readText(infilename):
	with open(infilename, 'r', encoding='utf8') as infile:
		return infile.read()
		
def main():
	site = pywikibot.Site()
	flowerKnight6StarList = pywikibot.Category(site, 'Category:6-Star').articles()
	flowerKnight5StarList = pywikibot.Category(site, 'Category:5-Star').articles()
	
	for page in flowerKnight6StarList:
		updateFlowerMeaning(page)
		
	for page in flowerKnight5StarList:
		updateFlowerMeaning(page)

def updateFlowerMeaning(page):
	wikiText = page.get()
	flowerKnightName = wikiText.partition("|JP = ")[2].partition("\n")[0].replace(' ','')
	comment = 'Added Flower Knight\'s flower meaning'
	api_data = readText(MASTERDATA_CURRENT).partition('masterCharacterBook')[2][1:].partition('master')[0].strip().split('\n')
	flowerMeaning = ''
	textLines = []
	
	for entry in api_data:
		if entry.split(',')[1] == flowerKnightName:
			flowerMeaning = entry.split(',')[5]
	
	text = wikiText.replace('|languageoftheflowers = \n','|languageoftheflowers = ' + flowerMeaning + '\n')
	ListUpdater.save(text, page, comment)
	print(page.title())

if __name__ == "__main__":
    main()
