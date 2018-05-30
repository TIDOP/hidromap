#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-


import optparse
import os
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
parser.add_option("-d", "--debug", dest="debug", action="store_true",
                  help="Only print command", default=False)
parser.add_option("-z", "--zero", dest="zero", action="store_true",
                  help="Clean zero size product entries", default=False)
parser.add_option("-n", "--notexisting", dest="not_existing", action="store_true",
                  help="Clean not existing product entries", default=False)
parser.add_option("--notderived", dest="not_derived", action="store_true",
                  help="Clean entries of original products without no derived products", default=False)
parser.add_option("--corrupted", dest="corrupted_zip", action="store_true",
                  help="Clean entries of original products with corrupted zip file", default=False)
parser.add_option("-f", "--deletefiles", dest="delete_files", action="store_true",
                  help="Delete files asociated to deleted entries", default=False)
parser.add_option("--initialdate", dest="initial_date", action="store", type="string",
                  help="Initial date for products without derived ", default=None)
parser.add_option("--finaldate", dest="final_date", action="store", type="string",
                  help="Final date for products without derived ", default=None)


(options, args) = parser.parse_args()

config_file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir, 'config.txt')
catalog_manager = catalog_manager.CatalogManager.from_file(config_file_path)
catalog_manager.clean_catalog(options.zero, options.not_existing, options.not_derived,
                              options.delete_files, options.initial_date, options.final_date, options.corrupted_zip,
                              options.debug)
