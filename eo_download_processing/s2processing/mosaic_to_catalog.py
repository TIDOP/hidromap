#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-

import optparse
from subprocess import call
import os
import zipfile
import shutil
from datetime import date
import inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
catalog_dir = os.path.join(os.path.dirname(currentdir),'catalog')
os.sys.path.insert(0,catalog_dir)
import catalog_manager

class OptionParser(optparse.OptionParser):
    def check_required(self, opt):
        option = self.get_option(opt)

        # Assumes the option's 'default' is set to None!
        if getattr(self.values, option.dest) is None:
            self.error("%s option not supplied" % option)


###########################################################################

# ==================
# parse command line
# ==================
usage = "usage: %prog [options] "
parser = OptionParser(usage=usage)
parser.add_option("-m", "--mosaicspath", dest="mosaics_path", action="store", type="string",
                  help="Mosaics input path.", default=None)
parser.add_option("-p", "--producttype", dest="product_type", action="store", type="string",
                  help="Product type.", default=None)

(options, args) = parser.parse_args()

# catalog_manager = catalog_manager.CatalogManager(catalog_db, user=catalog_user,
#                                                                  password=catalog_pass, host=catalog_host,
#                                                                  port=catalog_port)
config_file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir, 'config.txt')
catalog_manager = catalog_manager.CatalogManager.from_file(config_file_path)

for file in os.listdir(options.mosaics_path):
    if file.endswith('.tif'):
        if not catalog_manager.exist_derived_product(file):
            catalog_manager.ingest_derived_product(os.path.join(options.mosaics_path, file),
                                                   date.today(), options.product_type, None)
