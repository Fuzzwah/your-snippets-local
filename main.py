#!/usr/bin/env python
# -*- coding: utf-8 -*-

#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 2 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License along
#   with this program; if not, write to the Free Software Foundation, Inc.,
#   51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

"""
SYNOPSIS

    python main.py [-h,--help] [-l,--log] [--debug] IMAGE_FILE

DESCRIPTION

    A python script which allows uploading of local images to a
    Your Snippets website.

EXAMPLES

    python main.py c:\image.png

AUTHOR

    Robert Crouch (rob.crouch@gmail.com)

VERSION

    $Id$
"""

__program__ = "your-snippets-local"
__author__ = "Robert Crouch (rob.crouch@gmail.com)"
__copyright__ = "Copyright (C) 2016- Robert Crouch"
__license__ = "LGPL 3.0"
__version__ = "v0.161117"

import os
import sys
import argparse
import logging, logging.handlers
import imghdr
import base64
from tkinter import *

import configobj
import requests
from requests.packages import urllib3
from slugify import slugify

urllib3.disable_warnings()


class App(object):
    """ The main class of your application
    """

    def __init__(self, log, args, config):
        self.log = log
        self.args = args
        self.config = config
        self.version = "{}: {}".format(__program__, __version__)

        self.log.info(self.version)
        if self.args.debug:
            print(self.version)

        if not self.args.url:

            self.gui = Tk()
            self.gui.wm_title("Your Snippets Image Uploader")
            self.gui.geometry("400x150")
            label = Label(self.gui, text="Enter the URL this image is to be assigned to:", font=("Helvetica", 12), anchor=W, justify=LEFT)
            label.pack(fill=X, padx=10, pady=10)
            self.url_var = StringVar()
            url_entry = Entry(self.gui, textvariable=self.url_var, font=("Helvetica", 12))
            url_entry.pack(fill=X, padx=10, pady=10)
            submit = Button(self.gui, text="Submit", font=("Helvetica", 12), width=10, command=self.gui_submit)
            submit.pack()
            self.gui.bind('<Return>', self.gui_return_submit)

            self.gui.mainloop()
        else:
            self.url = self.args.url

    def gui_return_submit(self, event):
        self.gui_submit()

    def gui_submit(self):
        self.url = self.url_var.get()
        print(self.url)
        self.gui.destroy()

    def getToken(self):
        api_url = self.config['API']['url']
        api_headers = {"Content-Type": "application/json"}

        api_data = {
            "username": self.config['API']['user'],
            "password": self.config['API']['pass'],
        }
        response = requests.post("{}token/".format(api_url), headers=api_headers, json=api_data)

        if self.args.debug:
            print(response.status_code)

        return response

    def imageBase64(self, filepath):
        """ open an image file and return it as a base64 string
        """

        with open(filepath, "rb") as image_file:
            image64 = base64.b64encode(image_file.read())
        image_base64_string = image64.decode('ascii')

        return image_base64_string

    def sendImage(self, filename, image_base64_string):

        images_list = []
        images_list.append({"image": "file_name:{},data:image/jpeg;base64,{}".format(filename, image_base64_string)})

        api_url = self.config['API']['url']
        api_auth = (self.config['API']['user'], self.config['API']['pass'])
        api_headers = {"Content-Type": "application/json"}

        api_data = {
            "url": self.url,
            "images": images_list,
        }
        response = requests.post("{}add/images/".format(api_url), auth=api_auth, headers=api_headers, json=api_data)

        if self.args.debug:
            print(response.status_code)

        return response


def parse_args(argv):
    """ Read in any command line options and return them
    """

    # Define and parse command line arguments
    parser = argparse.ArgumentParser(description=__program__)
    parser.add_argument("imagefile", help="location of the image file to upload")
    parser.add_argument("--url", help="the URL of the Snippet this image is for", default=False)
    parser.add_argument("--logfile", help="file to write log to", default="%s.log" % __program__)
    parser.add_argument("--configfile", help="use a different config file", default="config.ini")
    parser.add_argument("--debug", action='store_true', default=False)

    if len(sys.argv)==1:
        parser.print_help()
        print("\nYou must specify the location of an image file to upload.")
        sys.exit(1)

    args = parser.parse_args()

    return args

def setup_logging(args):
    """ Everything required when the application is first initialized
    """

    basepath = os.path.dirname(os.path.realpath(sys.argv[0]))

    # set up all the logging stuff
    LOG_FILENAME = os.path.join(basepath, "{}.log".format(args.logfile))

    if args.debug:
        LOG_LEVEL = logging.DEBUG
    else:
        LOG_LEVEL = logging.INFO  # Could be e.g. "DEBUG" or "WARNING"

    # Configure logging to log to a file, making a new file at midnight and keeping the last 3 day's data
    # Give the logger a unique name (good practice)
    log = logging.getLogger(__name__)
    # Set the log level to LOG_LEVEL
    log.setLevel(LOG_LEVEL)
    # Make a handler that writes to a file, making a new file at midnight and keeping 3 backups
    handler = logging.handlers.TimedRotatingFileHandler(LOG_FILENAME, when="midnight", backupCount=3)
    # Format each log message like this
    formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')
    # Attach the formatter to the handler
    handler.setFormatter(formatter)
    # Attach the handler to the logger
    log.addHandler(handler)

def main(raw_args):
    """ Main entry point for the script.
    """

    # call function to parse command line arguments
    args = parse_args(raw_args)

    # setup logging
    setup_logging(args)

    # connect to the logger we set up
    log = logging.getLogger(__name__)

    basepath = os.path.dirname(os.path.realpath(sys.argv[0]))

    if not os.path.isfile(os.path.join(basepath, args.configfile)):
        config = configobj.ConfigObj()
        config.filename = args.configfile

        config['API'] = {}
        config['API']['url'] = 'http://your-snippets-api.com'
        config['API']['user'] = 'username'
        config['API']['pass'] = 'password'
        config.write()

        print("You need to add the details for Your Snippets API to the config.ini file.")
        sys.exit(1)

    # try to read in the config
    try:
        config = configobj.ConfigObj(os.path.join(basepath, args.configfile))
        if config['API']['url'] == 'http://your-snippets-api.com' and config['API']['user'] == 'username' and config['API']['pass'] == 'password':
            print("You need to add the details for Your Snippets API to the config.ini file.")
            sys.exit(1)

    except (IOError, KeyError, AttributeError) as e:
        print("Unable to successfully read config file: {}".format(os.path.join(basepath, args.configfile)))
        sys.exit(1)

    if not imghdr.what(args.imagefile):
        print("There doesn't appear to be a valid image file at: {}".format(os.path.join(basepath, args.configfile)))
        sys.exit(1)

    # fire up our base class and get this app cranking!
    app = App(log, args, config)

    response = app.getToken()
    if response.status_code != 200:
        print("Failed to successfully authenticate against your API")
        sys.exit(1)

    # things that the app does go here:
    imageBase64 = app.imageBase64(args.imagefile)
    response = app.sendImage(slugify(os.path.splitext(os.path.split(args.imagefile)[1])[0], to_lower=True), imageBase64)
    if response.status_code == 201:
        print("Successfully uploaded image.")
    else:
        print("Failed to upload image!")

    pass

if __name__ == '__main__':
    sys.exit(main(sys.argv))
