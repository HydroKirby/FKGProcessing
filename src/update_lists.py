#!/usr/bin/python
# -*- coding: utf-8  -*-
import pywikibot
from pywikibot import i18n
import IDlookup
import sys

class ListUpdaterBot(object):
    def __init__(my):
        my.master_data = IDlookup.MasterData(IDlookup.DEFAULT_INFILENAME)
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

    def update_char_list(my):
        page = pywikibot.Page(my.site, u'Module:CharacterList')
        text = my.master_data.get_char_list_page()
        my.save(text, page)

    def update_skill_list(my):
        page = pywikibot.Page(my.site, u'Module:SkillList')
        text = my.master_data.get_skill_list_page()
        my.save(text, page)

    def update_ability_list(my):
        page = pywikibot.Page(my.site, u'Module:BundledAbilityList')
        text = my.master_data.get_bundled_ability_list_page()
        my.save(text, page)

    def update_equipment_list(my):
        page = pywikibot.Page(my.site, u'Module:Equipment/Data')
        text = my.master_data.get_equipment_list_page()
        my.save(text, page)

    def update_ingame_char_data(my):
        page = pywikibot.Page(my.site, u'Module:MasterCharacterData')
        text = my.master_data.get_master_char_data_page()
        my.save(text, page)

    def update_character_images(my, auto=False):
        if auto:
            print('Not implemented yet!')
        else:
            knights = my.master_data.choose_knights()
            for knight in knights:
                networking.dowload_flower_knight_pics(knight)

    def update_card_sheets(my):
        import translate_sheets
        page = pywikibot.Page(my.site, u'The_Mystery_Case_of_the_Glass_Mansion/Card_Flip')
        text = translate_sheets.get_sheets_page(infilename=None, outfilename=None, quiet=False)
        my.save(text, page)

    def update(my):
        my.update_char_list()
        my.update_skill_list()
        my.update_ability_list()
        my.update_equipment_list()
        my.update_ingame_char_data()

def main(argv=[]):
    bot = ListUpdaterBot()
    if '-h' in argv or '--help' in argv:
        print('Updates the Wikia with these scripts and logging into a bot.')
        print('-h / --help: Prints this message.')
        print('-c / --card: Updates the card sheets translations instead.')
        print('-i / --image: Updates character images.')
    elif '-c' in argv or '--card' in argv:
        bot.update_card_sheets()
    elif '-i' in argv or '--image' in argv:
        bot.update_character_images()
    else:
        bot.update()

if __name__ == "__main__":
    main(sys.argv)
