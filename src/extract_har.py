#!/usr/bin/python3
###########################################################################
#  usage: fkg_har_asset_grabber.py [-h] har_file
#
#  Parses a HAR file for FKG assets and downloads them out of Cloudfront
#
#  positional arguments:
#    har_file    HAR file to parse
#
#  optional arguments:
#    -h, --help  show this help message and exit
############################################################################

import argparse
import json
import requests
import traceback
import zlib
from time import sleep

supported_types = ['images', 'voice', 'story']
tried_urls = {}

def write_image(asset_url):
	response = requests.get(asset_url)
	outfilename = asset_url.split('/')[-1].split('?')[0]
	if not outfilename.endswith('.png'):
		outfilename += '.png'
	with open(outfilename, 'wb') as f:
		try:
			f.write(zlib.decompress(response.content))
		except zlib.error as err:
			# This content may not be zlib compressed. Write it out directly.
			f.write(response.content)
	tried_urls[asset_url] = 1

def write_audio(asset_url):
	response = requests.get(asset_url)
	with open('{}_{}.{}'.format(asset_url.split('/')[-2],
			asset_url.split('/')[-1].split('?')[0],
			'mp3'), 'wb') as f:
		f.write(zlib.decompress(response.content))
	tried_urls[asset_url] = 1

def write_text(asset_url):
	response = requests.get(asset_url)
	with open('{}_{}.{}'.format(asset_url.split('/')[-2],
			asset_url.split('/')[-1].split('?')[0],
			'txt'), 'wb') as f:
		f.write(zlib.decompress(response.content))
	tried_urls[asset_url] = 1

def download_asset(asset_url, asset_type):
	if asset_url in tried_urls.keys():
		return True

	try:
		if asset_type == 'images':
			write_image(asset_url)
		elif asset_type == 'audio':
			write_audio(asset_url)
		else:
			write_text(asset_url)
	except KeyboardInterrupt:
		return False
	except:
		print('Error grabbing asset: {}\n{}'.format(asset_url, traceback.format_exc()))
	finally:
		sleep(0.5)
	return True

def main():
	parser = argparse.ArgumentParser(
		description='Parses a HAR file for FKG assets and downloads them out of Cloudfront',
		formatter_class=argparse.ArgumentDefaultsHelpFormatter)
	parser.add_argument('har_file', type=str, help='HAR file to parse')

	args = parser.parse_args()

	har_content = json.load(open(args.har_file, 'r'))
	cont = True
	for entry in har_content['log']['entries']:
		url = entry['request']['url']
		if 'twitter' in url or url.endswith('.js'):
			continue
		if entry['request']['url'] not in supported_types:
			print(entry['request']['url'])
			pass
		if not cont:
			break
#for atype in supported_types:
	#if atype in entry['request']['url']:
		if not download_asset(entry['request']['url'], 'images'):
			cont = False
			break

if __name__ == '__main__':
	main()