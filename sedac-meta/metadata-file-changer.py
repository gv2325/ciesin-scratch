#!/usr/bin/python
# original by Andreas 2013
#
# updated to produce a script output file, output directory named with date
# and allow processing to continue if some metadata formats are missing
# jsquires 10.23.2015
#
# added chuid and shuid directory structure for file organization, removed fgdc directory
# fgdc fies now named _iso.xml, fgdc-usrdef files now named _fgdc-usrdef.xml
# fgdc-usrdef directories are now zipped
# jsquires 10.30.2015
#
# if a chuid directory already exists a new one with H and M appended will be used
# jsquires 11.13.2015

# note there are 3 xml files created:
# _iso.xml - this file has indentations in the format
# .xml - this has FGDC format with user defined section stripped out
# _fgdc-usrdef.xml - this has FGDC format with user defined section
#     a copy of this is in the /fgdcUserDefDir with just an .xml extension.


import os, shutil, re, stat, string, sys
import xml.etree.ElementTree as ET
from time import strftime

# list of valid extensions
validExtensions = [".xml", ".txt", ".html", ".gce"]

# file object for script output
outTxt = "processing_output_"+strftime("%Y%m%d-%H%M%S")+".txt"
scriptOut = open( os.path.join(os.getcwd(), outTxt),"w")

# define directory to process
basepath = os.getcwd()

# list to save chuid directories into so we can zip the fgdc-usrdef later
chuidDirs = []

# iterate through the directory
for name in os.listdir(basepath):
  # skip sub-directories, script and output file
  path = os.path.join(basepath, name)
  if os.path.isdir(path) or name == os.path.basename(sys.argv[0]) or name == outTxt:
    continue
  fileName =os.path.splitext(name)[0]
  fileExt = os.path.splitext(name)[1]
  # only process files with valid extensions
  if fileExt in validExtensions:
    # the FGDC records contain the HUIDs, so its where we originate
    if fileName.startswith("FGDC_"):
      scriptOut.write('processing: ' + name + '\n')
      xmldoc = ET.parse(name)
      for el in xmldoc.findall(".//smusrtxt"): # cycle through all smusrlbl elements
        if (el.find('smusrlbl').text == "collection-huid"): # only work those that are related to chuid
          chuid = el.find('smusrval').text
          
          # create directory for all files that have been processed under the chuid
          chuidDir = os.path.join(os.getcwd(), strftime("%Y%m%d")+'_'+chuid)
          # if directory already exists then create one with current time, if we haven't yet
          if os.path.exists(chuidDir) and chuidDir not in chuidDirs:
            chuidDir = os.path.join(os.getcwd(), strftime("%Y%m%d_%H%M")+'_'+chuid)
          # pass if we already made a directory for the chuid this run - this will happen if there are two or more sets sharing a chuid
          if chuidDir in chuidDirs:
            pass
          else:
            os.mkdir(chuidDir)
            chuidDirs.append(chuidDir)
            
        elif (el.find('smusrlbl').text == "data-set-huid"): # only work those that are related to shuid
          shuid = el.find('smusrval').text
          shuidDir = chuidDir+os.sep+shuid
          os.mkdir(shuidDir)

      # copy and rename iso xml, txt, html, and gce files
      for ext in validExtensions:
        filetoCopy = fileName[5:]+ext
        try:
          scriptOut.write('  processing: ' + filetoCopy + '\n')
##          if ext == ".txt":
##            shutil.copy2(filetoCopy, os.path.join(shuidDir, shuid+ext))
##          else:
##            shutil.copy2(filetoCopy, os.path.join(shuidDir, shuid+"_iso"+ext))
          if ext == ".xml":
            shutil.copy2(filetoCopy, os.path.join(shuidDir, shuid+"_iso"+ext))
          else:
            shutil.copy2(filetoCopy, os.path.join(shuidDir, shuid+ext))
        except IOError:
          scriptOut.write('  WARN: Could not locate: ' + filetoCopy + '\n')
        
      # copy and rename the fgdc xml file w/ user defined fields
      fgdcUsrDefDir = chuidDir+os.sep+'fgdc-usrdef'
      if os.path.exists(fgdcUsrDefDir):
        pass
      else:
        os.mkdir(fgdcUsrDefDir)
      shutil.copy2(name, os.path.join(fgdcUsrDefDir, shuid+fileExt))
      shutil.copy2(name, os.path.join(shuidDir, shuid+'_fgdc-usrdef'+fileExt))
      
      # strip user defined fields from fgdc xml
      root = xmldoc.getroot()
      usrDefEl = xmldoc.find("smusrdef")
      root.remove(usrDefEl)

      # save to new file - the '_iso.xml' used before is so that this file '.xml' won't clash with it 
      f = open(os.path.join(shuidDir, shuid+fileExt), 'w')
      xmldoc.write(f, encoding="ISO-8859-1")
      f.close()
  else:
    scriptOut.write('SKIPPING: ' + name + '\n')

# zip FGDC User Defined Directories
for cd in chuidDirs:
  archive_name = cd+os.sep+os.path.basename(cd)+"_fgdc-usrdef"
  zipDir = cd+os.sep+"fgdc-usrdef"
  zipLocation = cd
  shutil.make_archive(archive_name, 'zip', root_dir=zipDir)
  scriptOut.write('ZIPPING: ' + zipDir + ' to: ' + os.path.basename(archive_name) + '.zip\n')
scriptOut.close()
print ("Program complete")
