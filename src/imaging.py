#!/usr/bin/python
# coding=utf-8
from __future__ import print_function
import os

_HAS_LIB = False
try:
	from PIL import Image
	_HAS_LIB = True
except ImportError:
	print('Please use PIP to install Pillow for image manipulation.')

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
	'../res/rarity-bg5.png',
	'../res/rarity-bg6.png']
	ICON_FRAMES = [
	'../res/rarity-frame1.png',
	'../res/rarity-frame2.png',
	'../res/rarity-frame3.png',
	'../res/rarity-frame4.png',
	'../res/rarity-frame5.png',
	'../res/rarity-frame6.png']
	ICON_HALF_FRAMES = [
	'../res/rarity-halframe2.png',
	'../res/rarity-halframe3.png',
	'../res/rarity-halframe4.png',
	'../res/rarity-halframe5.png',
	'../res/rarity-halframe6.png']
	ICON_TYPES = [
	'../res/type-slash.png',
	'../res/type-blunt.png',
	'../res/type-pierce.png',
	'../res/type-magic.png']
	ICON_STAGES = [
	'../res/stage-preEvolved.png',
	'../res/stage-evolved.png',
	'../res/stage-bloom.png']
	MEMORY_FRAMES = [
	'../res/rarity-memory-frame3.png',
	'../res/rarity-memory-frame4.png',
	'../res/rarity-memory-frame5.png',
	'../res/rarity-memory-frame6.png']
	MEMORY_PLATES = [
	'../res/rarity-nameplate3.png',
	'../res/rarity-nameplate4.png',
	'../res/rarity-nameplate5.png',
	'../res/rarity-nameplate6.png']

	def __init__(my):
		my.icon_bgs = [my.load_image(filename) for filename in Imaging.ICON_BACKGROUNDS]
		my.icon_frames = [my.load_image(filename) for filename in Imaging.ICON_FRAMES]
		my.icon_half_frames = [my.load_image(filename) for filename in Imaging.ICON_HALF_FRAMES]
		my.icon_types = [my.load_image(filename) for filename in Imaging.ICON_TYPES]
		my.icon_stages = [my.load_image(filename) for filename in Imaging.ICON_STAGES]
		my.fm_frames = [my.load_image(filename) for filename in Imaging.MEMORY_FRAMES]
		my.fm_plates = [my.load_image(filename) for filename in Imaging.MEMORY_PLATES]

	def load_image(my, filename):
		"""Loads an image or returns the image as-is."""
		if not _HAS_LIB:
			return None
		elif type(filename) is str:
			if Image.open(filename).mode != 'RGBA':
				return Image.open(filename).convert('RGBA')
			else:
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

	def paste_layer(my, top_image, bottom_image, position):
		"""Merges two images with different resolutions.
		@param top_image: An Image instance or filename. The overlay image.
		@param bottom_image: An Image instance or filename. The bottom image.
		@param position: A set of two integers. Specifies the coordinates of the top image within the canvas.
		@returns An Image instance where the passed images are merged, or
			None if the image library is unavailable.
		"""
		if not _HAS_LIB: my._print_no_library_warning(); return None
		top_image = my.load_image(top_image)
		bottom_image = my.load_image(bottom_image)
		result = Image.new("RGBA", bottom_image.size)
		result.paste(top_image, position)
		result = my.apply_layer(result, bottom_image)
		return result

	def get_framed_icon(my, icon_filename, outfilename, rarity, typing=None, stage=None):
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
		frame = my.icon_frames[rarity - 1]
		bg = my.icon_bgs[rarity - 1]
		if typing : icon_typing = my.icon_types[typing - 1]
		if stage  : stage_level = my.icon_stages[stage - 1]
		# Apply the layers.
		result = my.apply_layer(char_icon, bg)
		result = my.apply_layer(frame, result)
		if typing : result = my.apply_layer(icon_typing, result)
		if stage  : result = my.apply_layer(stage_level, result)
		# Save and return the result.
		result.save(outfilename, 'png')
		return result

	def get_framed_halficon(my, icon_filename, outfilename, rarity):
		"""Produces the half-height icon for a character.

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
		frame = my.icon_half_frames[rarity - 2]
		# Apply the layers.
		result = my.paste_layer(char_icon, frame,(0,1))
		result = my.apply_layer(frame, result)
		# Save and return the result.
		result.save(outfilename, 'png')
		return result

	def get_framed_memory(my, fm_wallpaper, fm_title, outfilename, rarity):
		"""Produces the fully framed for a Flower Memory wallpaper.
		@param fm_wallpaper: An Image instance or filename.
			The wallpaper picture to use as a base.
		@param fm_title: An Image instance or filename.
			The title name picture to use as a base.
		@param outfilename: String. The output file's name.
		@returns An Image instance of the framed character icon on success,
			or None on failure.
		"""
		# Select the layers to use, based on icon arrays.
		fm_frame = my.fm_frames[rarity - 3]
		fm_plate = my.fm_plates[rarity - 3]
		# Crop the wallpaper if exceeds the width of the wallpaper frame, Flower Memory 1000031, 1000044, 1000046 was guilty of this.
		if Image.open(fm_wallpaper).size[0] == 1138:
			fm_wallpaper = Image.open(fm_wallpaper).crop((1,0,1137,640)).convert('RGBA')
			print("{0} {1}".format(fm_wallpaper.size[0],fm_wallpaper.size[1]))
		# Apply the layers.
		result = my.apply_layer(fm_frame, fm_wallpaper)
		result = my.paste_layer(fm_plate, result,(155,449))
		result = my.paste_layer(fm_title, result,(156,524))
		# Save and return the result.
		result.save(outfilename, 'png')
		return result
