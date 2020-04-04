#!/usr/bin/python
# coding=utf-8
from __future__ import print_function

__doc__ = """Defines the variables and imports used by all scripts."""

DEFAULT_GETMASTER_INFILENAME = 'getMaster'
DEFAULT_GETMASTER_OUTFILENAME = 'getMasterDecoded.txt'
DEFAULT_INFILENAME = 'getMaster_latest.txt'
DEFAULT_OUTFILENAME = 'result.txt'

# Specify the Flower Knight ID and their English name (which is not available in getMaster)
# Note: Always make sure findID and english_nameList are list types!
findID = [142001]
english_nameList = ["Nerine"]

# Download state flags.
(DL_OK, # The download succeeded.
DL_FAIL, # The download failed.
DL_QUIT) = range(3) # The user forcefully stopped the download.

attribList = {
	'1':'Slash',
	'2':'Blunt',
	'3':'Pierce',
	'4':'Magic'
	}

nationList = {
	'1':'Winter Rose',
	'2':'Banana Ocean',
	'3':'Blossom Hill',
	'4':'Bergamot Valley',
	'5':'Lily Wood',
	'7':'Lotus Lake'
	}

giftList = {
	'1':'Gem',
	'2':'Teddy Bear',
	'3':'Cake',
	'4':'Book'
	}

# Maps a rarity to its maxmimum levels per evolution tier.
maxLevel = {
	'2':['50','60','80'],
	'3':['50','60','80'],
	'4':['50','60','80'],
	'5':['60','70','80'],
	'6':['60','70','80'],
}

def remove_quotes(text):
	"""Removes pairs of double-quotes around strings."""
	if text.startswith('"') and text.endswith('"'):
		return text[1:-1]
	return text
