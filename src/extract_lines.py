#!/usr/bin/env python
# coding: utf-8

import argparse
import zlib
from sys import version_info
if version_info.major <= 2:
	# Replace Python 2's open() with one that deals with Japanese.
	import codecs
	open = codecs.open

__doc__ = """Extracts the dialog from a FKG event script.

This script is meant to be compatible with both Python 2 and 3."""

def unzip_text(input_stream):
	"""Deflates zipped text."""
	return zlib.decompress(input_stream.read())

def extract_raw(input_text, outfilename, quiet):
	"""Extracts the data from the input without formatting it."""
	with open(outfilename, 'wb') as outfile:
		outfile.write(input_text)
	if not quiet:
		print('Extracted the data to {0} unformatted (Raw).'.format(outfilename))

def extract_messages(input_text, outfilename, quiet):
	"""Extracts the dialog from the game text to a file."""
	# Remove the ".txt" ending and replace it with "_out.txt".
	with open(outfilename, 'wb') as outfile:
		for line in input_text.split():
			# Only extract lines that are messages.
			# The game recognizes these as lines starting with "mess".
			if line.startswith('mess,'):
				outfile.write(line[5:] + '\n')
	if not quiet:
		print('Outputted the dialog to {0} with script data removed (Minimal).'.
			format(outfilename))

def extract_messages_wikitable(input_text, outfilename, quiet):
	"""Extracts the dialog from the game text to a file in wikitable format."""
	# Remove the ".txt" ending and replace it with "_out.txt".
	with open(outfilename, 'wb') as outfile:
		# Write the header of the table.
		outfile.write('{| class="wikitable"\n')
		outfile.write('!Speaker\n')
		outfile.write('!Text\n')
		# Parse the input text and output it as a table.
		for line in input_text.split():
			# Only extract lines that are messages.
			# The game recognizes these lines as "mess,speaker,dialog".
			if line.startswith('mess,'):
				# Skip over the "mess," and look for the next comma.
				sep_idx = line.find(',', 5)
				speaker = line[5:sep_idx]
				dialog = line[sep_idx + 1:]

				# Clean up the dialog. Remove quotes and replace newline codes
				dialog = codecs.decode(dialog, 'utf-8')
				# Replace newlines. Also remove the full-width space.
				dialog = dialog.replace(u'\\n\u3000', '<br>')
				# Look for quotes. They look like L-brackets in Japanese.
				if dialog.startswith(u'\u300c') and dialog.endswith(u'\u300d'):
					dialog = dialog[1:-1]
				dialog = codecs.encode(dialog, 'utf-8')

				# Output the text in wikitable format.
				outfile.write('|-\n|{0}||{1}\n'.format(speaker, dialog))
		# Close the wikitable.
		outfile.write('|}')
	if not quiet:
		print('Outputted the dialog to {0} formatted for the Wiki (Wiki).'.
			format(outfilename))

def main(infilename, args):
	outputfilename = infilename[:-4] + '_out.txt'

	# Input the data.
	# Try reading the input file as plain text.
	try_as_zipped_content = False
	with open(infilename, 'r', encoding='utf-8') as infile:
		# Remove the ".txt" ending and replace it with "_out.txt".
		try:
			input_text = infile.read()
		except UnicodeDecodeError:
			# If it's an invalid start byte, this might be compressed data.
			#print('Failed to extract text. Trying file as compressed data.')
			try_as_zipped_content = True

	if try_as_zipped_content:
		with open(infilename, 'rb') as infile:
			input_text = unzip_text(infile)
	
	# Output the data.
	if args.minimal:
		extract_messages(input_text, outputfilename, args.quiet)
	elif args.wiki:
		extract_messages_wikitable(input_text, outputfilename, args.quiet)
	elif args.raw:
		extract_raw(input_text, outputfilename, args.quiet)
	else:
		# No option chosen. Extract the data in a raw format.
		extract_raw(input_text, outputfilename, args.quiet)

if __name__ == '__main__':
	parser = argparse.ArgumentParser(
		description='Parses a FKG event script for its dialog or raw data',
		formatter_class=argparse.ArgumentDefaultsHelpFormatter)
	parser.add_argument('-q', '--quiet', action='store_true',
		help='Quietly process with less feedback')
	# Give options for how to format the output.
	# If any of these options are given as an arg, they become True.
	# Only one of these args can appear at once.
	group = parser.add_mutually_exclusive_group()
	group.add_argument('-m', '--minimal', action='store_true',
		help='Output the dialog minimally')
	group.add_argument('-w', '--wiki', action='store_true',
		help='Output the dialog for the Wiki')
	group.add_argument('-r', '--raw', action='store_true',
		help='Output the data unformatted')
	# The input file comes last.
	required = parser.add_argument_group('required arguments')
	required.add_argument('input', type=str, help='Text file to parse')

	args = parser.parse_args()

	main(args.input, args)
