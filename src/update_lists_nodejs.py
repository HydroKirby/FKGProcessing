#!/usr/bin/python
# -*- coding: utf-8  -*-
import os
import json
import pywikibot
from pywikibot import i18n
from pywikibot.bot import SingleSiteBot
from pathlib import Path
import parse_master
import sys

json_data = {}

class ListUpdaterBot(object):
    def __init__(my):
        my.master_data = parse_master.MasterData()
        my.site = pywikibot.Site()
        my.comment = u'Automatic update by bot.'
        my.dry = False
        my.json_dir = Path(r'.\editlist.json')

    def save(my, text, page, comment=None, minorEdit=True,
             botflag=True):
        """Update the given page with new text."""
        # only save if something was changed
        if text != page.get():
            # Show the title of the page we're working on.
            # Highlight the title in purple.
            pywikibot.output(u"\n\n>>> <<lightpurple>>%s<<default>> <<<"
                             % page.title())
            # show what was changed
            pywikibot.showDiff(page.get(), text)
            pywikibot.output(u'Comment: %s' % comment)
            if not my.dry:
                if pywikibot.input_yn(
                        u'Do you want to accept these changes?',
                        default=False, automatic_quit=False):
                    try:
                        json_data[page.title()] = {
                               "name":page.title(),
                               "content":text,
                               "dryrun":0,
                               "liverun":0
                            }
                        my.output_json()
                    except pywikibot.exceptions.LockedPageError:
                        pywikibot.output(u"Page %s is locked; skipping."
                                         % page.title(asLink=True))
                    except pywikibot.exceptions.EditConflictError:
                        pywikibot.output(
                            u'Skipping %s because of edit conflict'
                            % (page.title()))
                    except pywikibot.exceptions.SpamblacklistError as error:
                        pywikibot.output(
                            u'Cannot change %s because of spam blacklist entry %s'
                            % (page.title(), error.url))
                    else:
                        return True
        return
		
    def output_json(my):
        has_data = os.path.exists(my.json_dir) and os.path.getsize(my.json_dir) > 0
        with open(my.json_dir, 'w', encoding='UTF8') as data:
            data.write(json.dumps(json_data, indent=4, sort_keys=True))

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

    def update_equipment_names(my):
        page = pywikibot.Page(my.site, u'Module:Equipment/Names')
        text = my.master_data.get_new_equipment_names_page(page)
        my.save(text, page)

    def update_skin_list(my):
        page = pywikibot.Page(my.site, u'Module:Skin/Data')
        text = my.master_data.outputter.get_skin_info_page()
        my.save(text, page)

    def update_char_list(my):
        page = pywikibot.Page(my.site, u'Module:KnightIdAndName/Data')
        text = my.master_data.outputter.get_char_list_page()
        my.save(text, page)

    def update(my):
        my.update_skill_list()
        my.update_ability_list()
        my.update_equipment_list()
        my.update_equipment_names()
        my.update_ingame_char_data()
        my.update_skin_list()
        my.update_char_list()

    def print_update(my):
        print(my.master_data.get_skill_list_page() + "\n\n")
        print(my.master_data.get_bundled_ability_list_page() + "\n\n")
        print(my.master_data.get_equipment_list_page() + "\n\n")
        print(my.master_data.get_master_char_data_page() + "\n\n")
        print(my.master_data.get_new_equipment_names_page(page) + "\n\n")
        print(my.master_data.get_skin_info_page())

def run(argv=[]):
    bot = ListUpdaterBot()
    if '-h' in argv or '--help' in argv:
        print('Updates the Wikia with these scripts and logging into a bot.')
        print('-h / --help: Prints this message.')
        print('-p / --image: Prints the updated modules.')
    elif '-p' in argv or '--print' in argv:
        bot.print_update()
    else:
        bot.update()

if __name__ == "__main__":
    run(sys.argv)
