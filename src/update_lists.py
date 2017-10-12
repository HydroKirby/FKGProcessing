#!/usr/bin/python
# -*- coding: utf-8  -*-
import pywikibot
from pywikibot import i18n
import IDlookup

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

    def update(my):
        my.update_char_list()
        my.update_skill_list()
        my.update_ability_list()

def main():
    bot = ListUpdaterBot()
    bot.update()

if __name__ == "__main__":
    main()
