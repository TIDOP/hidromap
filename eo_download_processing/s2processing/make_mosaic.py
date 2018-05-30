#!/usr/bin/python
# -*- coding: utf-8 -*-

import optparse
import os
from collections import defaultdict
from subprocess import call
import re
import inspect
from datetime import date

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
catalog_dir = os.path.join(os.path.dirname(currentdir), 'catalog')
os.sys.path.insert(0,catalog_dir)
import catalog_manager

###########################################################################

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
parser.add_option("-g", "--granulespath", dest="granules_path", action="store", type="string",
                  help="Granules input path.", default=None)
parser.add_option("--date", dest="date", action="store", type="string",
                  help="Date to mosaic (YYYYmmdd). Generate only one mosaic for this date.", default=None)
parser.add_option("-o", "--outputprefix", dest="output_prefix", action="store", type="string",
                  help="Path and prefix of the output files", default=None)
parser.add_option("-z", "--zeroraster", dest="zero", action="store", type="string",
                  help="input base file defining de value in no data areas.", default=None)
parser.add_option("--dateposition", dest="date_position", action="store", type="int",
                  help="Position of the date field in the input file names, starting in 0", default=1)
parser.add_option("-p", "--pattern", dest="pattern", action="store", type="string",
                  help="prefix for filter inputs files to process", default=None)
parser.add_option("-m", "--maxmemory", dest="max_memory", action="store", type="string",
                  help="Max memory", default=None)
parser.add_option("-d", "--debug", dest="debug", action="store_true",
                  help="Only print command")
parser.add_option("-n", "--nodata", dest="nodata", action="store", type="string",
                  help="output nodata value.", default=None)
parser.add_option("-w", "--write", dest="write", action="store_true",
                  help="Write output from vrt to TIF")
parser.add_option("--producttype", dest="product_type", action="store", type="string",
                  help="Product type.", default='S2NDVIb_mosaic')

(options, args) = parser.parse_args()

granules_dict = defaultdict(list)

noPattern = False

if not options.pattern:
	noPattern = True
	
for file in os.listdir(options.granules_path):
    if noPattern or (re.match(options.pattern,file) != None):
        sensing_date = file.split('_')[options.date_position]
        if options.date == sensing_date or options.date == None:
            granules_dict[sensing_date].append(file)

nodata_str = ""
if options.nodata:
        nodata_str = "-vrtnodata " + options.nodata + " "

# catalog_manager = catalog_manager.CatalogManager(catalog_db, user=catalog_user,
#                                                                  password=catalog_pass, host=catalog_host,
#                                                                  port=catalog_port)
config_file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir, 'config.txt')
catalog_manager = catalog_manager.CatalogManager.from_file(config_file_path)

for date_group in granules_dict.keys():

    print " "
    print "************************"
    print date_group
    print "************************"

    # prepare output name:
    sensor_id = ''
    orbit_id = ''
    product_id = ''
    splitted_file_name = granules_dict[date_group][0].split('_')
    for item in splitted_file_name:
        if item.startswith('S2'):
            sensor_id = '_' + item 
        elif item.startswith('R'):
            orbit_id = '_' + item
        elif re.match(options.pattern,item) != None:
            product_id = '_' + item.split('.')[0]

    print '*****************' + date_group + sensor_id + '_mosaic' + orbit_id + product_id + '.tif ***************'
    if catalog_manager.exist_derived_product(date_group + sensor_id + '_mosaic' + orbit_id + product_id+'.tif'):
        print "Mosaic already in catalog"
        continue

    output_file_path = options.output_prefix + date_group + sensor_id + '_mosaic' + orbit_id + product_id 

    gdal_cmd = "gdalbuildvrt " + nodata_str + output_file_path + '.vrt '
    if options.zero:
        gdal_cmd += options.zero + " "
    for granule in granules_dict[date_group]:
        gdal_cmd += os.path.join(options.granules_path, granule) + " "

    print gdal_cmd
    if not options.debug:
        call(gdal_cmd, shell=True)

    if options.write:
        cmd = 'gdal_translate '\
              + output_file_path + ".vrt " +\
              output_file_path + ".tif"
        print cmd
        if not options.debug:
            call(cmd, shell=True)
            catalog_manager.ingest_derived_product(output_file_path + ".tif",
                                                   date.today(), options.product_type, None)
            os.remove(output_file_path + ".vrt")

