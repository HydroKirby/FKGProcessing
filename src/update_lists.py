#!/usr/bin/python
# -*- coding: utf-8  -*-
import os
import json
import pywikibot
from pywikibot import i18n
from pywikibot.bot import SingleSiteBot
from pathlib import Path
from common import nationList
import parse_master
import update_flower_meaning
import sys

json_data = {}

class ListUpdaterBot(object):
    def __init__(my):
        my.master_data = parse_master.MasterData()
        my.site = pywikibot.Site('en','fkg')
        my.site.login(False, 'NazunaBot')
        my.comment = u'Automatic update by bot.'
        my.externalBot = True
        my.dry = False
        my.verbose = True
        my.json_dir = Path(r'X:\AHPP Exteria\fleur\research\api\FKGProcessing-master\voice\jsnode\editlist.json')
        my.moduleList = {
            'Module:MasterCharacterData':my.master_data.get_master_char_data_page(),
            'Module:KnightIdAndName/Data':my.master_data.outputter.get_char_list_page(),
            'Module:SkillList':my.master_data.get_skill_list_page(),
            'Module:BundledAbilityList':my.master_data.get_bundled_ability_list_page(),
            'Module:BlessedOathList':my.master_data.outputter.get_eternal_oath_page(),
            'Module:Skin/Data':my.master_data.outputter.get_skin_info_page(),
            'Module:FlowerMemories/Data':my.master_data.get_flower_memories_list_page(),
            'Module:FlowerMemories/AbilityData':my.master_data.get_flower_memories_abilities_page(),
            'Module:Equipment/Data':my.master_data.get_equipment_list_page(),
            'Module:Equipment/StatsData':my.master_data.get_equipment_stats_list_page(),
            'Module:Equipment/OwnerData':my.master_data.get_user_equip_list_page(),
            'Module:Equipment/LookupData':my.master_data.get_personal_equip_list_page(),
        }

    def checkPage(my, page):
        """Check if the page exists and returns ."""
        try:
            return page.get()
        except pywikibot.exceptions.NoPageError:
            print("\nArticle {0} is empty, generating new page".format(page.title()))
            return ""

    def save(my, text, page, comment=None, minorEdit=True,
             botflag=True):
        """Update the given page with new text."""
        hasPage = my.checkPage(page)
        # only save if something was changed
        if text != hasPage:
            # Show the title of the page we're working on.
            # Highlight the title in purple.
            pywikibot.output(u"\n\n>>> <<lightpurple>>%s<<default>> <<<"
                             % page.title())
            # show what was changed if verbose mode is enabled.
            if my.verbose : pywikibot.showDiff(hasPage, text)
            pywikibot.output(u'Comment: %s' % comment)
            if not my.dry:
                if pywikibot.input_yn(
                        u'Do you want to accept these changes?',
                        default=False, automatic_quit=False):
                    try:
                        if my.externalBot:
                            json_data[page.title()] = {
                                "name":page.title(),
                                "content":text,
                                "dryrun":0,
                                "liverun":0
                            }
                            my.output_json()
                        else:
                            page.text = text
                            # Save the page
                            page.save(summary=comment or my.comment,
                            minor=minorEdit, botflag=botflag)
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
		
    def enable_json(my):
        my.externalBot = True
		
    def output_json(my):
        has_data = os.path.exists(my.json_dir) and os.path.getsize(my.json_dir) > 0
        with open(my.json_dir, 'w', encoding='UTF8') as data:
            data.write(json.dumps(json_data, indent=4, sort_keys=True))

    def update_equipment_names(my):
        page = pywikibot.Page(my.site, u'Module:Equipment/Names')
        text = my.master_data.get_new_equipment_names_page(page)
        my.save(text, page)

    def update_ingame_char_data_module(my):
        title = u'Module:MasterCharacterData/{0}'
        for n in nationList:
            page = pywikibot.Page(my.site, title.format(nationList[n]))
            text = my.master_data.get_master_char_data_nation_page(n)
            my.save(text, page)

    def update(my):
        for module in my.moduleList:
            my.save(my.moduleList[module], pywikibot.Page(my.site, module))
        
        my.update_equipment_names()
        #my.update_ingame_char_data_module()

    def print_update(my):
        for module in my.moduleList:
            print(my.moduleList[module] + "\n\n")

        print(my.master_data.get_new_equipment_names_page(pywikibot.Page(my.site, u'Module:Equipment/Names')) + "\n\n")

def run(argv=[]):
    bot = ListUpdaterBot()
    if '-j' in argv or '--json' in argv:
        bot.enable_json()
    if '-h' in argv or '--help' in argv:
        print('Updates the Wikia with these scripts and logging into a bot.')
        print('-h / --help: Prints this message.')
        print('-j / --json: Prints editlist.json for NodeJS bot.')
        print('-p / --image: Prints the updated modules.')
    elif '-p' in argv or '--print' in argv:
        bot.print_update()
    else:
        bot.update()

if __name__ == "__main__":
    run(sys.argv)
    update_flower_meaning.main()
