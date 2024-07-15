#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import signal
import logging
import re
import os
import sys
import optparse
import csv
import fnmatch
import subprocess

# Default configuration
JPG_OUTPUT_DIR = 'jpg'        # Default JPEG output directory
JPG_RESOLUTION_DPI = 400      # Default JPEG resolution in DPI
TEXT_OUTPUT_DIR = 'text'      # Default text output directory
RESUME_OCR = False            # Resume OCR flag

# Path to executables (adjust these paths as per your environment)
if os.name == 'nt':
    GS_PROG = r"path_to_gswin32c.exe"       # Example: r"C:\Program Files\gs\gs9.54.0\bin\gswin32c.exe"
    TESSERACT_PROG = r"path_to_tesseract.exe"  # Example: r"C:\Program Files\Tesseract-OCR\tesseract.exe"
else:
    GS_PROG = '/usr/bin/gs'                # Example: '/usr/bin/gs'
    TESSERACT_PROG = '/usr/bin/tesseract'  # Example: '/usr/bin/tesseract'

logger = logging.getLogger('pdf2txt')
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)

usage = "Usage: %prog [options] <pdf_directory>"
def parse_command_line(argv):
    """Command line options parser
    """
    parser = optparse.OptionParser(add_help_option=True, usage=usage)
    
    parser.add_option("-d", "--dpi", action="store", type="int", dest="dpi", default=JPG_RESOLUTION_DPI,
                      help="JPEG Resolution in DPI (default: {0:d})".format(JPG_RESOLUTION_DPI))
    parser.add_option("-j", "--jpgdir", action="store", type="string", dest="jpgdir", default=JPG_OUTPUT_DIR,
                      help="JPEG output directory (default: {0!s})".format(JPG_OUTPUT_DIR))
    parser.add_option("-t", "--textdir", action="store", type="string", dest="txtdir", default=TEXT_OUTPUT_DIR,
                      help="Text output directory (default: {0!s})".format(TEXT_OUTPUT_DIR))
    parser.add_option("-r", "--resume", action="store_true", dest="resume", default=RESUME_OCR,
                      help="Resume OCR to Text (default: {0!s})".format(RESUME_OCR))
    return parser.parse_args(argv)
    
def getSize(filename):
    """Returns file size
    """
    try:
        return os.path.getsize(filename)
    except Exception as e:
        print(f"Error getting file size: {e}")
        return 0
        
def jpg_to_text(options, filename, rootdir):
    """OCR JPEG files and save as TEXT files
    """
    try:
        relpath = os.path.relpath(filename)
    except:
        relpath = os.path.splitdrive(filename)[1]
    relpath = re.sub('^' + re.escape(options.jpgdir), '', relpath, flags=re.I)
    relpath = re.sub(r'^[\.|\\|\/]*', '', relpath)
    extdir = rootdir + '/' + os.path.dirname(relpath)
    fname = extdir + '/' + os.path.basename(relpath)
    fname = os.path.splitext(fname)[0]
    print(f"OCR JPG to TEXT: {filename}")
    try:
        if not os.path.exists(extdir):
            os.makedirs(extdir)
        if getSize(fname + ".txt") == 0 or not options.resume:
            p = subprocess.Popen([TESSERACT_PROG, filename, fname], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = p.communicate()
            return out, err
        else:
            return "Resume, file exists, skipped", ""
    except Exception as e:
        print(f"Error processing {filename}: {e}")
        return "", "ERROR"

def pdf_to_jpg(filename, rootdir, dpi):
    """Convert PDF files to JPEG files
    """
    try:
        relpath = os.path.relpath(filename)
    except:
        relpath = os.path.splitdrive(filename)[1]
    relpath = re.sub(r'^[\.|\\|\/]*', '', relpath)
    extdir = rootdir + '/' + os.path.dirname(relpath)
    fname = extdir + '/' + os.path.basename(relpath)
    fname = os.path.splitext(fname)[0] + '-%d.jpg'
    print(f"Convert PDF to JPG: {filename}")
    try:
        if not os.path.exists(extdir):
            os.makedirs(extdir)
        p = subprocess.Popen([GS_PROG, "-dNOPAUSE", f"-r{dpi}", "-sDEVICE=jpeg", "-dBATCH", f"-sOutputFile={fname}", filename], 
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
        return out, err
    except Exception as e:
        print(f"Error converting {filename} to JPG: {e}")
        return None, None
    
def main(options, args):
    """ Main Entry Point
    """
    if len(args) < 2:
        print("Please specify the root directory of PDF input files (-h/--help for help)")
        sys.exit(-1)
    
    rootdir = args[1]

    if not options.resume:
        # For each PDF file in folder and sub-folders
        for root, dirnames, filenames in os.walk(rootdir):
            for filename in fnmatch.filter(filenames, '*.pdf'):
                fname = os.path.join(root, filename)
                out, err = pdf_to_jpg(fname, options.jpgdir, options.dpi)
                print(out, err)
    
    # For each JPG file in folder and sub-folders
    for root, dirnames, filenames in os.walk(options.jpgdir):
        for filename in fnmatch.filter(filenames, '*.jpg'):
            fname = os.path.join(root, filename)
            out, err = jpg_to_text(options, fname, options.txtdir)
            print(out, err)

def signal_handler(signal, frame):
    print('You pressed Ctrl+C!')
    sys.exit(1)
    
if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    
    print(f"{os.path.basename(sys.argv[0])} - r2 (2013/06/15)\n")
    
    (options, args) = parse_command_line(sys.argv)

    main(options, args)
