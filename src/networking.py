#!/usr/bin/env python
# coding=utf-8
import os, zlib, time, hashlib, random
import requests
from imaging import Imaging
from parse_master import FlowerKnight

__doc__ = """Handles all downloading of assets from FKG's servers.

The Networking class does NOT handle uploading to the Wikia.
"""

class Networking(object):
    DEFAULT_ASSETPATH = 'asset'
    DL_OUTPUT_FOLDER = 'dl'

    # Download state flags.
    (DL_OK,  # The download succeeded.
    DL_FAIL, # The download failed.
    DL_QUIT, # The user forcefully stopped the download.
    ) = range(3)

    # Character image types.
    (IMG_ICON,
    IMG_STAND) = range(2)

    # Character tiers.
    (PRE_EVO,
    EVO,
    BLOOM,
    ) = range(3)

    getCharaURL = "http://dugrqaqinbtcq.cloudfront.net/product/images/character/"
    getEquipURL = "http://dugrqaqinbtcq.cloudfront.net/product/images/item/100x100"
    imgPreLink  = { IMG_ICON:'i/',      IMG_STAND:'s/' }
    imgTypeNameOld = { IMG_ICON:'_icon0',  IMG_STAND:'_chara0'}
    imgTypeName = { IMG_ICON:'icon_{0}.png',  IMG_STAND:'portrait_{0}.png'}
    imgType     = { IMG_ICON:'icon_l_', IMG_STAND:'stand_s_' }

    def __init__(my):
        my.imaging = Imaging()
        my.out_dir = Networking.DL_OUTPUT_FOLDER
        my._state = Networking.DL_OK

    def sleep(my, duration=0.0, message=True):
        """Sleeps for a random amount of time.

        @param duration: Float. The sleep time in ms.
            If 0 or negative, sleeps for a few seconds.
        @param message: Bool. If True, prints the sleep time.
        """

        if duration <= 0.0:
            duration = random.random() * 5.0 + 1.0
        if message:
            print('Sleeping for {0:3} seconds.'.format(duration))
        time.sleep(duration)

    def dowload_flower_knight_pics(my, knight):
        """Downloads all images for a flower knight.

        @param knight: A FlowerKnight entity.
        @returns Networking.DL_OK on success, or Networking.DL_FAIL otherwise.
        """

        return my.downloadCharacterImages(knight)

    def download_flower_knight_equip_pics(my, knight):
        """Downloads all person equipment images for a flower knight.

        @param knight: A FlowerKnight entity.
        @returns Networking.DL_OK on success, or Networking.DL_FAIL otherwise.
        """

        pass

    def downloadCharacterImages(my,knight,tiers=[PRE_EVO,EVO,BLOOM]):
        inputID = int(knight.tiers['preEvo']['id'])

        dl_state = my.DL_OK
        
        for tier in tiers:
            dl_state = my.downloadCharaImage(knight,inputID,my.IMG_ICON,tier,dl_state)
            dl_state = my.downloadCharaImage(knight,inputID,my.IMG_STAND,tier,dl_state)
            if dl_state != my.DL_OK:
                break
        return dl_state
    downloadImageFunction = downloadCharacterImages

    def downloadCharaImage(my,knight,inputID,iconType,stage,dl_state=DL_OK):
        # Do not allow consecutive failed downloads.
        if dl_state != my.DL_OK: return dl_state

        #Check the Flower Knight's evolution stage, and refactor the ID appropriately.
        if (stage == 2): inputID += 300000
        else: inputID += stage
        
        #Calculate the hashed filename of the character images.
        KeyName = my.imgType[iconType] + str(inputID)
        linkHash = hashlib.md5(KeyName.encode('utf-8')).hexdigest()
        
        #Define the image link and filename.
        imgFileLink = my.getCharaURL + my.imgPreLink[iconType] + linkHash + ".bin"
        #imgFileName = knight.fullName + my.imgTypeName[iconType] + str(stage) + ".png"
        imgFileName = my.imgTypeName[iconType].format(inputID)
        if not os.path.exists(my.out_dir):
            os.makedirs(my.out_dir)
        outputPath = os.path.join(my.out_dir, imgFileName)
        if os.path.exists(outputPath):
            print(outputPath + ' already exists. Skipping.')
            return dl_state
        
        #Download the image.
        dl_state = my.downloadImage(imgFileLink,outputPath,True)
        if dl_state == my.DL_OK and iconType == my.IMG_ICON:
            #For icons, apply the background, frame, and typing to the image.
            #Note: For this function, downloadCharaImage, it'd be better put it
            #into a Class because of all the involved variables.
            if not my.imaging.get_framed_icon(outputPath, outputPath, int(knight.rarity), int(knight.type)):
                dl_state = my.DL_FAIL
        return dl_state

    def downloadEquipImage(my, equip_id_or_csv):
        #### This was the old way to call this function.
        #### It was called from downloadCharaImage().
        # try:
        #     if dl_state == my.DL_OK:
        #         dl_state = downloadEquipImage(EquipImgID,"1")
        # except KeyboardInterrupt: dl_state = my.DL_QUIT
        # except: print("Personal equip for {0} is unavailable".format(knight.fullName))

        # Determine the ID.
        equip_id = equip_id_or_csv
        if type(equip_id_or_csv) is EquipmentEntry:
            equip_id = equip_id_or_csv.getval('equipID')

        # Setup the download location.
        imgFileLink = "{0}/{1}.png".format(Networking.getEquipURL, equip_id)
        imgFileName = 'equip_{0}.png'.format(equip_id)

        # Download the image.
        return my.downloadImage(imgFileLink,imgFileName,False)

    def downloadImage(my,inputLink,outputImageName,decompress):
        dl_state = my.DL_FAIL
        response = requests.get(inputLink)
        if response.ok:
            content = response.content
            if decompress:
                content = zlib.decompress(content)
            with open(outputImageName,'wb') as imgFile:
                imgFile.write(content)
            print("Downloaded " + outputImageName)
            dl_state = my.DL_OK
            my.sleep()
        else:
            print("Error: Unable to download " + outputImageName)
        return dl_state
