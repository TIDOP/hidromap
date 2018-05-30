#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-

import optparse
from subprocess import call
import os
import tarfile
import shutil
import math
from datetime import date
import inspect
import datetime
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
catalog_dir = os.path.join(os.path.dirname(currentdir),'catalog')
os.sys.path.insert(0,catalog_dir)
import catalog_manager

def compute_rgb432(l1_product_path, output_file_path, coef_r = 0.05, coef_g = 0.05, coef_b = 0.05):

    for file in os.listdir(l1_product_path):
        if file.endswith('_B4.TIF'):
            l1_b4_30m = os.path.join(l1_product_path, file)
            l1_b4_30m_coef = os.path.join(l1_product_path, 'coef_' + file)
        elif file.endswith('_B3.TIF'):
            l1_b3_30m = os.path.join(l1_product_path, file)
            l1_b3_30m_coef = os.path.join(l1_product_path, 'coef_' + file)
        elif file.endswith('_B2.TIF'):
            l1_b2_30m = os.path.join(l1_product_path, file)
            l1_b2_30m_coef = os.path.join(l1_product_path, 'coef_' + file)

    tmp_output_file_path = output_file_path + "_original_srs.tif"

    sunElevation = readL8Metadata(l8_metadata_path, 'SUN_ELEVATION')
    reflectanceMult4 = readL8Metadata(l8_metadata_path, 'REFLECTANCE_MULT_BAND_4')
    reflectanceMult3 = readL8Metadata(l8_metadata_path, 'REFLECTANCE_MULT_BAND_3')
    reflectanceMult2 = readL8Metadata(l8_metadata_path, 'REFLECTANCE_MULT_BAND_2')
    reflectanceAdd4 = readL8Metadata(l8_metadata_path, 'REFLECTANCE_ADD_BAND_4')
    reflectanceAdd3 = readL8Metadata(l8_metadata_path, 'REFLECTANCE_ADD_BAND_3')
    reflectanceAdd2 = readL8Metadata(l8_metadata_path, 'REFLECTANCE_ADD_BAND_2')

    sunElevationSin = math.sin(math.radians(float(sunElevation)))

    # *****************************************
    # apply coeficient to bands (gdal_calc.py)
    # ****************************************
    coef_r_str = str(coef_r*10000)
    cmd = "gdal_calc.py -A {0} --outfile={1} --calc " \
          "'((A*{4}+{5})/{3})*{2}*(((A*{4}+{5})/{3})*{2}<=255)+(((A*{4}+{5})/{3})*{2}>255)*255' " \
          "--type=Byte --NoDataValue=0".format(l1_b4_30m, l1_b4_30m_coef, coef_r_str, sunElevationSin,
                                                 reflectanceMult4, reflectanceAdd4)
    call(cmd, shell=True)

    coef_g_str = str(coef_g*10000)
    cmd = "gdal_calc.py -A {0} --outfile={1} --calc " \
          "'((A*{4}+{5})/{3})*{2}*(((A*{4}+{5})/{3})*{2}<=255)+(((A*{4}+{5})/{3})*{2}>255)*255' " \
          "--type=Byte --NoDataValue=0".format(l1_b3_30m, l1_b3_30m_coef, coef_g_str, sunElevationSin, reflectanceMult3, reflectanceAdd3)
    call(cmd, shell=True)

    coef_b_str = str(coef_b*10000)
    cmd = "gdal_calc.py -A {0} --outfile={1} --calc " \
          "'((A*{4}+{5})/{3})*{2}*(((A*{4}+{5})/{3})*{2}<=255)+(((A*{4}+{5})/{3})*{2}>255)*255' " \
          "--type=Byte --NoDataValue=0".format(l1_b2_30m, l1_b2_30m_coef, coef_b_str, sunElevationSin, reflectanceMult2, reflectanceAdd2)
    call(cmd, shell=True)

    # *****************************************
    # generate RGB output file (gdal_merge.py)
    # ****************************************
    cmd = "gdal_merge.py -separate -ot Byte -o {0} {1} {2} {3}".format(
        tmp_output_file_path, l1_b4_30m_coef, l1_b3_30m_coef, l1_b2_30m_coef)
    call(cmd, shell=True)

    # *****************************************
    # reproject to 25830  (gdalwarp)
    # ****************************************
    cmd = 'gdalwarp -dstnodata 0 -t_srs EPSG:25830 -co "COMPRESS=LZW" {0} {1}'.format(
        tmp_output_file_path, output_file_path)
    call(cmd, shell=True)

    # *****************************************
    # generate overviews  (gdalado)
    # ****************************************
    cmd = 'gdaladdo  {0} 2 4 8 16 32 64 128 256'.format(output_file_path)
    call(cmd, shell=True)

    os.remove(l1_b4_30m_coef)
    os.remove(l1_b3_30m_coef)
    os.remove(l1_b2_30m_coef)
    os.remove(tmp_output_file_path)


def compute_rgb654(l1_product_path, output_file_path, coef_r = 0.05, coef_g = 0.05, coef_b = 0.05):
    for file in os.listdir(l1_product_path):
        if file.endswith('_B6.TIF'):
            l1_b6_30m = os.path.join(l1_product_path, file)
            l1_b6_30m_coef = os.path.join(l1_product_path, 'coef_' + file)
        elif file.endswith('_B5.TIF'):
            l1_b5_30m = os.path.join(l1_product_path, file)
            l1_b5_30m_coef = os.path.join(l1_product_path, 'coef_' + file)
        elif file.endswith('_B4.TIF'):
            l1_b4_30m = os.path.join(l1_product_path, file)
            l1_b4_30m_coef = os.path.join(l1_product_path, 'coef_' + file)

    tmp_output_file_path = output_file_path + "_original_srs.tif"

    sunElevation = readL8Metadata(l8_metadata_path, 'SUN_ELEVATION')
    reflectanceMult6 = readL8Metadata(l8_metadata_path, 'REFLECTANCE_MULT_BAND_6')
    reflectanceMult5 = readL8Metadata(l8_metadata_path, 'REFLECTANCE_MULT_BAND_5')
    reflectanceMult4 = readL8Metadata(l8_metadata_path, 'REFLECTANCE_MULT_BAND_4')
    reflectanceAdd6 = readL8Metadata(l8_metadata_path, 'REFLECTANCE_ADD_BAND_6')
    reflectanceAdd5 = readL8Metadata(l8_metadata_path, 'REFLECTANCE_ADD_BAND_5')
    reflectanceAdd4 = readL8Metadata(l8_metadata_path, 'REFLECTANCE_ADD_BAND_4')

    sunElevationSin = math.sin(math.radians(float(sunElevation)))

    # *****************************************
    # apply coeficient to bands (gdal_calc.py)
    # ****************************************
    coef_r_str = str(coef_r*10000)
    cmd = "gdal_calc.py -A {0} --outfile={1} --calc " \
          "'((A*{4}+{5})/{3})*{2}*(((A*{4}+{5})/{3})*{2}<=255)+(((A*{4}+{5})/{3})*{2}>255)*255' " \
          "--type=Byte --NoDataValue=0".format(l1_b6_30m, l1_b6_30m_coef, coef_r_str, sunElevationSin, reflectanceMult6, reflectanceAdd6)
    call(cmd, shell=True)

    coef_g_str = str(coef_g*10000)
    cmd = "gdal_calc.py -A {0} --outfile={1} --calc " \
          "'((A*{4}+{5})/{3})*{2}*(((A*{4}+{5})/{3})*{2}<=255)+(((A*{4}+{5})/{3})*{2}>255)*255' " \
          "--type=Byte --NoDataValue=0".format(l1_b5_30m, l1_b5_30m_coef, coef_g_str, sunElevationSin, reflectanceMult5, reflectanceAdd5)
    call(cmd, shell=True)

    coef_b_str = str(coef_b*10000)
    cmd = "gdal_calc.py -A {0} --outfile={1} --calc " \
          "'((A*{4}+{5})/{3})*{2}*(((A*{4}+{5})/{3})*{2}<=255)+(((A*{4}+{5})/{3})*{2}>255)*255' " \
          "--type=Byte --NoDataValue=0".format(l1_b4_30m, l1_b4_30m_coef, coef_b_str, sunElevationSin, reflectanceMult4, reflectanceAdd4)
    call(cmd, shell=True)

    # *****************************************
    # generate RGB output file (gdal_merge.py)
    # ****************************************
    cmd = "gdal_merge.py -separate -ot Byte -o {0} {1} {2} {3}".format(
        tmp_output_file_path, l1_b6_30m_coef, l1_b5_30m_coef, l1_b4_30m_coef)
    call(cmd, shell=True)

    # *****************************************
    # reproject to 25830  (gdalwarp)
    # ****************************************
    cmd = 'gdalwarp -dstnodata 0 -t_srs EPSG:25830 -co "COMPRESS=LZW" {0} {1}'.format(
        tmp_output_file_path, output_file_path)
    call(cmd, shell=True)

    # *****************************************
    # generate overviews  (gdalado)
    # ****************************************
    cmd = 'gdaladdo  {0} 2 4 8 16 32 64 128 256'.format(output_file_path)
    call(cmd, shell=True)

    os.remove(l1_b6_30m_coef)
    os.remove(l1_b5_30m_coef)
    os.remove(l1_b4_30m_coef)
    os.remove(tmp_output_file_path)

def compute_rgb753(l1_product_path, output_file_path, coef_r = 0.05, coef_g = 0.05, coef_b = 0.05):
    for file in os.listdir(l1_product_path):
        if file.endswith('_B7.TIF'):
            l1_b7_30m = os.path.join(l1_product_path, file)
            l1_b7_30m_coef = os.path.join(l1_product_path, 'coef_' + file)
        elif file.endswith('_B5.TIF'):
            l1_b5_30m = os.path.join(l1_product_path, file)
            l1_b5_30m_coef = os.path.join(l1_product_path, 'coef_' + file)
        elif file.endswith('_B3.TIF'):
            l1_b3_30m = os.path.join(l1_product_path, file)
            l1_b3_30m_coef = os.path.join(l1_product_path, 'coef_' + file)

    tmp_output_file_path = output_file_path + "_original_srs.tif"

    sunElevation = readL8Metadata(l8_metadata_path, 'SUN_ELEVATION')
    reflectanceMult7 = readL8Metadata(l8_metadata_path, 'REFLECTANCE_MULT_BAND_7')
    reflectanceMult5 = readL8Metadata(l8_metadata_path, 'REFLECTANCE_MULT_BAND_5')
    reflectanceMult3 = readL8Metadata(l8_metadata_path, 'REFLECTANCE_MULT_BAND_3')
    reflectanceAdd7 = readL8Metadata(l8_metadata_path, 'REFLECTANCE_ADD_BAND_7')
    reflectanceAdd5 = readL8Metadata(l8_metadata_path, 'REFLECTANCE_ADD_BAND_5')
    reflectanceAdd3 = readL8Metadata(l8_metadata_path, 'REFLECTANCE_ADD_BAND_3')

    sunElevationSin = math.sin(math.radians(float(sunElevation)))

    # *****************************************
    # apply coeficient to bands (gdal_calc.py)
    # ****************************************
    coef_r_str = str(coef_r*10000)
    cmd = "gdal_calc.py -A {0} --outfile={1} --calc " \
          "'((A*{4}+{5})/{3})*{2}*(((A*{4}+{5})/{3})*{2}<=255)+(((A*{4}+{5})/{3})*{2}>255)*255' " \
          "--type=Byte --NoDataValue=0".format(l1_b7_30m, l1_b7_30m_coef, coef_r_str, sunElevationSin, reflectanceMult7, reflectanceAdd7)
    call(cmd, shell=True)

    coef_g_str = str(coef_g*10000)
    cmd = "gdal_calc.py -A {0} --outfile={1} --calc " \
          "'((A*{4}+{5})/{3})*{2}*(((A*{4}+{5})/{3})*{2}<=255)+(((A*{4}+{5})/{3})*{2}>255)*255' " \
          "--type=Byte --NoDataValue=0".format(l1_b5_30m, l1_b5_30m_coef, coef_g_str, sunElevationSin, reflectanceMult5, reflectanceAdd5)
    call(cmd, shell=True)

    coef_b_str = str(coef_b*10000)
    cmd = "gdal_calc.py -A {0} --outfile={1} --calc " \
          "'((A*{4}+{5})/{3})*{2}*(((A*{4}+{5})/{3})*{2}<=255)+(((A*{4}+{5})/{3})*{2}>255)*255' " \
          "--type=Byte --NoDataValue=0".format(l1_b3_30m, l1_b3_30m_coef, coef_b_str, sunElevationSin, reflectanceMult3, reflectanceAdd3)
    call(cmd, shell=True)

    # *****************************************
    # generate RGB output file (gdal_merge.py)
    # ****************************************
    cmd = "gdal_merge.py -separate -ot Byte -o {0} {1} {2} {3}".format(
        tmp_output_file_path, l1_b7_30m_coef, l1_b5_30m_coef, l1_b3_30m_coef)
    call(cmd, shell=True)

    # *****************************************
    # reproject to 25830  (gdalwarp)
    # ****************************************
    cmd = 'gdalwarp -dstnodata 0 -t_srs EPSG:25830 -co "COMPRESS=LZW" {0} {1}'.format(
        tmp_output_file_path, output_file_path)
    call(cmd, shell=True)

    # *****************************************
    # generate overviews  (gdalado)
    # ****************************************
    cmd = 'gdaladdo  {0} 2 4 8 16 32 64 128 256'.format(output_file_path)
    call(cmd, shell=True)

    os.remove(l1_b7_30m_coef)
    os.remove(l1_b5_30m_coef)
    os.remove(l1_b3_30m_coef)
    os.remove(tmp_output_file_path)

def compute_ndvi(l1_product_path, output_file_path):
    for file in os.listdir(l1_product_path):
        if file.endswith('_B5.TIF'):
            l1_b5_30m = os.path.join(l1_product_path, file)
        elif file.endswith('_B4.TIF'):
            l1_b4_30m = os.path.join(l1_product_path, file)

    tmp_output_file_path = output_file_path + "_original_srs.tif"

    sunElevation = readL8Metadata(l8_metadata_path, 'SUN_ELEVATION')
    reflectanceMult5 = readL8Metadata(l8_metadata_path, 'REFLECTANCE_MULT_BAND_5')
    reflectanceMult4 = readL8Metadata(l8_metadata_path, 'REFLECTANCE_MULT_BAND_4')
    reflectanceAdd5 = readL8Metadata(l8_metadata_path, 'REFLECTANCE_ADD_BAND_5')
    reflectanceAdd4 = readL8Metadata(l8_metadata_path, 'REFLECTANCE_ADD_BAND_4')

    sunElevationSin = math.sin(math.radians(float(sunElevation)))

    # **********************************************
    # calculate NDVI (gdal_calc.py) (B5-B4)/(B5+B4)
    # **********************************************

    cmd = "gdal_calc.py -A {0} -B {1} --outfile={2} --calc " \
          "'(A.astype(float)*B!=0)*(((B.astype(float)*{6}+{7})/{3})-((A.astype(float)*{4}+{5})/{3}))/" \
          "(((B.astype(float)*{6}+{7})/{3})+((A.astype(float)*{4}+{5})/{3})+(A.astype(float)*B==0))" \
          "+(A.astype(float)*B==0)*(9999)' " \
          "--type=Float32 --NoDataValue=9999".format(l1_b4_30m, l1_b5_30m, tmp_output_file_path,
                                                     sunElevationSin, reflectanceMult4, reflectanceAdd4,
        reflectanceMult5, reflectanceAdd5)

    call(cmd, shell=True)

    # *****************************************
    # reproject to 25830  (gdalwarp)
    # ****************************************
    cmd = 'gdalwarp -dstnodata 9999 -t_srs EPSG:25830 -co "COMPRESS=LZW" {0} {1}'.format(
        tmp_output_file_path, output_file_path)
    call(cmd, shell=True)

    # *****************************************
    # generate overviews  (gdalado)
    # ****************************************
    cmd = 'gdaladdo  {0} 2 4 8 16 32 64 128 256'.format(output_file_path)
    call(cmd, shell=True)

    os.remove(tmp_output_file_path)

def compute_ndvi_byte(l1_product_path, output_file_path):
    for file in os.listdir(l1_product_path):
        if file.endswith('_B5.TIF'):
            l1_b5_30m = os.path.join(l1_product_path, file)
        elif file.endswith('_B4.TIF'):
            l1_b4_30m = os.path.join(l1_product_path, file)

    tmp_output_file_path = output_file_path + "_original_srs.tif"

    sunElevation = readL8Metadata(l8_metadata_path, 'SUN_ELEVATION')
    reflectanceMult5 = readL8Metadata(l8_metadata_path, 'REFLECTANCE_MULT_BAND_5')
    reflectanceMult4 = readL8Metadata(l8_metadata_path, 'REFLECTANCE_MULT_BAND_4')
    reflectanceAdd5 = readL8Metadata(l8_metadata_path, 'REFLECTANCE_ADD_BAND_5')
    reflectanceAdd4 = readL8Metadata(l8_metadata_path, 'REFLECTANCE_ADD_BAND_4')

    sunElevationSin = math.sin(math.radians(float(sunElevation)))

    # **********************************************
    # calculate NDVI (gdal_calc.py) (B5-B4)/(B5+B4)
    # **********************************************

    # cmd = "gdal_calc.py -A {0} -B {1} --outfile={2} --calc " \
    #       "'100*(((B.astype(float)*{6}+{7})/{3})-((A.astype(float)*{4}+{5})/{3}))/" \
    #       "(((B.astype(float)*{6}+{7})/{3})+((A.astype(float)*{4}+{5})/{3})) +(A*B==0)*(255)' " \
    #       "--type=Byte --NoDataValue=255".format(l1_b4_30m, l1_b5_30m, tmp_output_file_path,
    #                                              sunElevationSin, reflectanceMult4, reflectanceAdd4,
    #     reflectanceMult5, reflectanceAdd5)

    cmd = "gdal_calc.py -A {0} -B {1} --outfile={2} --calc " \
          "'(A.astype(float)*B!=0)*100*(((B.astype(float)*{6}+{7})/{3})-((A.astype(float)*{4}+{5})/{3}))/" \
          "(((B.astype(float)*{6}+{7})/{3})+((A.astype(float)*{4}+{5})/{3})+(A.astype(float)*B==0)) " \
          "+(A.astype(float)*B==0)*(255)' " \
          "--type=Byte --NoDataValue=255".format(l1_b4_30m, l1_b5_30m, tmp_output_file_path,
                                                 sunElevationSin, reflectanceMult4, reflectanceAdd4,
                                                 reflectanceMult5, reflectanceAdd5)

    call(cmd, shell=True)

    # *****************************************
    # reproject to 25830  (gdalwarp)
    # ****************************************
    cmd = 'gdalwarp -dstnodata 255 -t_srs EPSG:25830 -co "COMPRESS=LZW" {0} {1}'.format(
        tmp_output_file_path, output_file_path)
    call(cmd, shell=True)

    # *****************************************
    # generate overviews  (gdalado)
    # ****************************************
    cmd = 'gdaladdo  {0} 2 4 8 16 32 64 128 256'.format(output_file_path)
    call(cmd, shell=True)

    os.remove(tmp_output_file_path)

def readL8Metadata(l8_metadata_path, tag):
    if not os.path.exists(l8_metadata_path):
        return None
    metadataFile = open(l8_metadata_path)
    for line in metadataFile:
        if line.strip().split('=')[0].strip() == tag:
            return line.strip().split('=')[1].strip()
    return None

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
parser.add_option("-i", "--input", dest="input_path", action="store", type="string",
                  help="Input directory containing L1C products (.zip) ", default=None)
parser.add_option("-f", "--inputfile", dest="input_file", action="store", type="string",
                  help="Input directory containing L1C products (.zip) ", default=None)
parser.add_option("-o", "--output", dest="output_path", action="store", type="string",
                  help="Output directory containing L1C products (.zip) ", default=None)
parser.add_option("-r", "--red", dest="red_coef", action="store", type="float",
                  help="Red band coeficient", default=0.05)
parser.add_option("-g", "--green", dest="green_coef", action="store", type="float",
                  help="Red band coeficient", default=0.05)
parser.add_option("-b", "--blue", dest="blue_coef", action="store", type="float",
                  help="Blue band coeficient", default=0.05)
parser.add_option("-t", "--tmp", dest="tmp_path", action="store", type="string",
                  help="Temporal directory for unzip and process.", default=None)
parser.add_option("--ingest_id", dest="ingest_id", action="store", type="string",
                  help="Original product ID fo ingest derived products in catalog.", default='0')
parser.add_option("--product_list", dest="product_list", action="store", type="string",
                  help="Original product ID fo ingest derived products in catalog (RGB432 RGB654 RGB753 NDVI NDVIb).",
                  default="RGB654 RGB753 NDVI NDVIb")
parser.add_option("--publish_list", dest="publish_list", action="store", type="string",
                  help="Space separated list of products to publish (RGB654 RGB753 RGB432 NDVIb).",
                  default="RGB654 RGB753 NDVIb")
parser.add_option("--product_folders", dest="product_folders", action="store_true",
                  help="Store outputs in separated folders by product type")

(options, args) = parser.parse_args()

if options.input_file:
    input_list = [os.path.basename(options.input_file)]
    options.input_path = os.path.dirname(options.input_file)
else:
    input_list = os.listdir(options.input_path)

product_list = options.product_list.split(" ")
publish_list = options.publish_list.split(" ")

for file in input_list:
    if file.endswith(".tgz") and file.startswith('LC8'):
        product_name = file.replace('.tgz', '').replace('.TGZ', '')
        unziped_l1_path = os.path.join(options.tmp_path, product_name)
        if not os.path.exists(unziped_l1_path):
            os.mkdir(unziped_l1_path)

            tar_ref = tarfile.open(os.path.join(options.input_path, file), 'r')
            tar_ref.extractall(unziped_l1_path)
            tar_ref.close()

        for unzipedFile in os.listdir(unziped_l1_path):
            if unzipedFile.endswith('_MTL.txt'):
                l8_metadata_path = os.path.join(unziped_l1_path, unzipedFile)

        sensing_date = readL8Metadata(l8_metadata_path, 'DATE_ACQUIRED')
        sensing_date = datetime.datetime.strptime(sensing_date, "%Y-%m-%d").strftime("%Y%m%d")

        # # granule_id = file.split('_')[5]
        # # orbit_id = file.split('_')[4]
        # # platform_id = file.split('_')[0]
        # srs = '25830'
        #
        # ======================================
        # Create catalog connection
        # ======================================
        # catalog_manager = catalog_manager.CatalogManager(catalog_db, user=catalog_user,
        #                                                          password=catalog_pass, host=catalog_host,
        #                                                          port=catalog_port)

        config_file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir, 'config.txt')
        catalog_manager = catalog_manager.CatalogManager.from_file(config_file_path)

        if 'RGB432' in product_list:
            rgb432_output_path = options.output_path
            if options.product_folders:
                rgb432_output_path = os.path.join(rgb432_output_path, 'RGB432')
                if not (os.path.exists(rgb432_output_path)):
                    os.mkdir(rgb432_output_path)
            rgb432_file = sensing_date + '_' + product_name + '_RGB432.tif'
            rgb432_file_path = os.path.join(rgb432_output_path, rgb432_file)
            compute_rgb432(unziped_l1_path, rgb432_file_path, options.red_coef, options.green_coef,
                           options.blue_coef)
            if options.ingest_id:
                catalog_manager.ingest_derived_product(rgb432_file_path, date.today(), "L8RGB432", options.ingest_id)
            if 'RGB432' in publish_list:
                catalog_manager.publish_product('l8rgb432', rgb432_file)

        if 'RGB654' in product_list:
            rgb654_output_path = options.output_path
            if options.product_folders:
                rgb654_output_path = os.path.join(rgb654_output_path, 'RGB654')
                if not (os.path.exists(rgb654_output_path)):
                    os.mkdir(rgb654_output_path)
            rgb654_file = sensing_date + '_' + product_name + '_RGB654.tif'
            rgb1184_file_path = os.path.join(rgb654_output_path, rgb654_file)
            compute_rgb654(unziped_l1_path, rgb1184_file_path, options.red_coef, options.green_coef,
                           options.blue_coef)
            if options.ingest_id:
                catalog_manager.ingest_derived_product(rgb1184_file_path, date.today(), "L8RGB654", options.ingest_id)
            if 'RGB654' in publish_list:
                catalog_manager.publish_product('l8rgb654', rgb654_file)

        if 'RGB753' in product_list:
            rgb753_output_path = options.output_path
            if options.product_folders:
                rgb753_output_path = os.path.join(rgb753_output_path, 'RGB753')
                if not (os.path.exists(rgb753_output_path)):
                    os.mkdir(rgb654_output_path)
            rgb753_file = sensing_date + '_' + product_name + '_RGB753.tif'
            rgb1283_file_path = os.path.join(rgb753_output_path, rgb753_file)
            compute_rgb753(unziped_l1_path, rgb1283_file_path, options.red_coef, options.green_coef,
                           options.blue_coef)
            if options.ingest_id:
                catalog_manager.ingest_derived_product(rgb1283_file_path, date.today(), "L8RGB753", options.ingest_id)
            if 'RGB753' in publish_list:
                catalog_manager.publish_product('l8rgb753', rgb753_file)

        if 'NDVI' in product_list:
            ndvi_output_path = options.output_path
            if options.product_folders:
                ndvi_output_path = os.path.join(ndvi_output_path, 'NDVI')
                if not (os.path.exists(ndvi_output_path)):
                    os.mkdir(ndvi_output_path)
            ndvi_file_path = os.path.join(ndvi_output_path, sensing_date + '_' + product_name + '_NDVI.tif')
            compute_ndvi(unziped_l1_path, ndvi_file_path)
            if options.ingest_id:
                catalog_manager.ingest_derived_product(ndvi_file_path, date.today(), "L8NDVI", options.ingest_id)

        if 'NDVIb' in product_list:
            ndvib_output_path = options.output_path
            if options.product_folders:
                ndvib_output_path = os.path.join(ndvib_output_path, 'NDVIb')
                if not (os.path.exists(ndvib_output_path)):
                    os.mkdir(ndvib_output_path)
            ndvib_file = sensing_date + '_' + product_name + '_NDVIb.tif'
            ndvi_byte_file_path = os.path.join(ndvib_output_path, ndvib_file)
            compute_ndvi_byte(unziped_l1_path, ndvi_byte_file_path)
            if options.ingest_id:
                catalog_manager.ingest_derived_product(ndvi_byte_file_path, date.today(), "L8NDVIb", options.ingest_id)
            if 'NDVIb' in publish_list:
                catalog_manager.publish_product('l8ndvib', ndvib_file)

        shutil.rmtree(unziped_l1_path)
