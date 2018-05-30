#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-

import os
from subprocess import call
import optparse

geoserver_rest_url = 'url'
geoserver_products_path = 'data_path'
geoserver_user = 'geoserver_user'
geoserver_pass = '123#geoserver_pass'

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
parser.add_option("-p", "--productspath", dest="products_path", action="store", type="string",
                  help="Products path.", default=None)
parser.add_option("--product_list", dest="product_list", action="store", type="string",
                  help="Space separated list of products to publish (l8ndvib l8rgb654 l8rgb753 s2ndvib s2rgb1184 s2rgb1283).",
                  default="l8ndvib l8rgb654 l8rgb753 s2ndvib s2rgb1184 s2rgb1283")
parser.add_option("-d", "--debug", dest="debug", action="store_true",
                  help="Only print command")


(options, args) = parser.parse_args()

product_list = options.product_list.split(" ")
for product in product_list:
    product_path = os.path.join(options.products_path, product)
    print '****************************************************'
    print 'Publishing {} directory'.format(product_path)
    print '****************************************************'
    for file_name in os.listdir(product_path):
        if file_name.upper().endswith('.TIF'):
            print '****************************************************'
            print 'Publishing {} File'.format(file_name)
            print '****************************************************'
            file_path = os.path.join(product_path, file_name)
            url = geoserver_rest_url.replace('*coverage_name*', product)
            cmd = 'curl -v -u {0}:{1} -XPOST -H "Content-type: text/plain" -d "file://{2}" "{3}"'.format(
                geoserver_user, geoserver_pass, file_path, url)
            print cmd
            if not options.debug:
                stdfile = open('curl.log', 'a')
                errfile = open('curl.err.log', 'a')
                call(cmd, shell=True, stdin=None, stdout=stdfile, stderr=errfile)

