#!/usr/bin/python
# coding=utf-8
from __future__ import print_function
import os

_HAS_LIB = False
try:
	from PIL import Image
	_HAS_LIB = True
except ImportError:
	print('Warning: Library "Pillow" is not installed.')
	print('You will not be able to do image manipulation.')
	print('Install it with pip or easy_install.exe .')

ICON_BACKGROUND = '../res/icon_bg.png'
ICON_FRAME = '../res/icon_frame.png'
ICON_TYPES = [
'../res/icon_type1.png',
'../res/icon_type2.png',
'../res/icon_type3.png',
'../res/icon_type4.png']

class Imaging(object):
	def __init__(my):
		my.icon_bg = my.load_image(ICON_BACKGROUND)
		my.icon_frame = my.load_image(ICON_FRAME)
		my.icon_types = [my.load_image(weakType) for weakType in ICON_TYPES]

	def load_image(my, filename):
		"""Loads an image or returns the image as-is."""
		if not _HAS_LIB:
			return None
		elif type(filename) is str:
			return Image.open(filename)
		return filename

	def _print_no_library_warning(my):
		"""Prints a warning if the image library is unavailable."""
		print('Unable to do image operations.')

	def apply_layer(my, top_image, bottom_image):
		"""Merges two images.

		@param top_image: An Image instance or filename. The overlay image.
		@param bottom_image: An Image instance or filename. The bottom image.
		@returns An Image instance where the passed images are merged, or
			None if the image library is unavailable.
		"""

		if not _HAS_LIB: my._print_no_library_warning(); return None
		top_image = my.load_image(top_image)
		bottom_image = my.load_image(bottom_image)
		result = Image.new("RGBA", bottom_image.size)
		result = Image.alpha_composite(result, bottom_image)
		result = Image.alpha_composite(result, top_image)
		return result

	def get_framed_icon(my, icon_filename, outfilename, rarity, typing):
		"""Produces the full icon for a character.

		@param icon_filename: An Image instance or filename.
			The character icon to use as a base.
		@param outfilename: String. The output file's name.
		@returns An Image instance of the framed character icon on success,
			or None on failure.
		"""

		if not _HAS_LIB: my._print_no_library_warning(); return None
		char_icon = my.load_image(icon_filename)
		icon_typing = my.icon_types[typing - 1]
		frame = my.icon_frame
		result = my.apply_layer(char_icon, my.icon_bg)
		result = my.apply_layer(frame, result)
		result = my.apply_layer(icon_typing, result)
		result.save(outfilename, 'png')
		return result
