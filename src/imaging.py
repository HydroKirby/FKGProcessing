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

class Imaging(object):
	"""Manages all image processing.

	The main purpose of this class is to take flower knight icons and
	re-apply the background, frame, and type icons to it.
	See: get_framed_icon()

	It is only necessary to make one instance of this class and reuse it.
	"""

	ICON_BACKGROUNDS = [
	'../res/rarity-bg1.png',
	'../res/rarity-bg2.png',
	'../res/rarity-bg3.png',
	'../res/rarity-bg4.png',
	'../res/rarity-bg5.png']
	ICON_FRAMES = [
	'../res/rarity-frame1.png',
	'../res/rarity-frame2.png',
	'../res/rarity-frame3.png',
	'../res/rarity-frame4.png',
	'../res/rarity-frame5.png']
	ICON_TYPES = [
	'../res/type-slash.png',
	'../res/type-blunt.png',
	'../res/type-pierce.png',
	'../res/type-magic.png']

	def __init__(my):
		my.icon_bgs = [my.load_image(filename) for filename in Imaging.ICON_BACKGROUNDS]
		my.icon_frames = [my.load_image(filename) for filename in Imaging.ICON_FRAMES]
		my.icon_types = [my.load_image(filename) for filename in Imaging.ICON_TYPES]

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
		# Load the icon. Cancel on failure.
		char_icon = my.load_image(icon_filename)
		if not char_icon:
			return None
		# Select the layers to use.
		icon_typing = my.icon_types[typing - 1]
		frame = my.icon_frames[rarity - 1]
		bg = my.icon_bgs[rarity - 1]
		# Apply the layers.
		result = my.apply_layer(char_icon, bg)
		result = my.apply_layer(frame, result)
		result = my.apply_layer(icon_typing, result)
		# Save and return the result.
		result.save(outfilename, 'png')
		return result
