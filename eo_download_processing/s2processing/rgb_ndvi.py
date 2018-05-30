#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-

import optparse
from subprocess import call
import os
import sys
import zipfile
import shutil
from datetime import date
import inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
catalog_dir = os.path.join(os.path.dirname(currentdir),'catalog')
os.sys.path.insert(0, catalog_dir)
import catalog_manager

#Catalog conection data:
# catalog_db = "revela_duero"
# catalog_user = "postgres"
# catalog_pass = "l8s2rd"
# catalog_host = "localhost"
# catalog_port = "5432"

def read_granules_list(orbit, granules_by_orbit_file):
    try:
        with open(granules_by_orbit_file) as f:
            lines = f.readlines()
    except:
        print "Error with granules file"
        sys.exit(-3)

    # Remove whitespace characters like `\n` at the end of each line
    stripped_granules_list = []
    for line in lines:
        splitted_line = line.split(':')
        if splitted_line[0]==orbit:
            granules_list = splitted_line[1].split(' ')
            granules_list = map(str.strip, granules_list)
            break
    f.close()
    return granules_list


def compute_rgb432(l1c_xml_path, output_file_path, coef_r = 0.05, coef_g = 0.05, coef_b = 0.05):
    l1c_vrt = output_file_path + "_VRT.vrt"
    l1c_dataset_1 = output_file_path + "_VRT_1.vrt"
    l1c_b4_10cm_vrt = output_file_path + "_b4.vrt"
    l1c_b3_10cm_vrt = output_file_path + "_b3.vrt"
    l1c_b2_10cm_vrt = output_file_path + "_b2.vrt"
    l1c_b4_10cm_tif = output_file_path + "_b4.tif"
    l1c_b3_10cm_tif = output_file_path + "_b3.tif"
    l1c_b2_10cm_tif = output_file_path + "_b2.tif"
    tmp_output_file_path = output_file_path + "_original_srs.tif"

    #*****************************************
    # generate l1c vrt (gdal translate)
    # ****************************************
    cmd = "gdal_translate -of VRT -sds {0} {1}".format(
        l1c_xml_path, l1c_vrt)
    call(cmd, shell=True)

    # *****************************************
    # extract virtual raster bands (gdal translate)
    # ****************************************
    cmd = "gdal_translate -of VRT -b 1 {0} {1}".format(
        l1c_dataset_1, l1c_b4_10cm_vrt)
    call(cmd, shell=True)

    cmd = "gdal_translate -of VRT -b 2 {0} {1}".format(
        l1c_dataset_1, l1c_b3_10cm_vrt)
    call(cmd, shell=True)

    cmd = "gdal_translate -of VRT -b 3 {0} {1}".format(
        l1c_dataset_1, l1c_b2_10cm_vrt)
    call(cmd, shell=True)

    # *****************************************
    # apply coeficient to bands (gdal_calc.py)
    # ****************************************
    coef_r_str = str(coef_r)
    cmd = "gdal_calc.py -A {0} -B {1} -C {2} --outfile={3} " \
          "--calc '(A.astype(float)*B*C!=0)*(A*{4}*(A*{4}<=255)+(A*{4}>255)*255)' " \
          "--type=Byte --NoDataValue=0".format(l1c_b4_10cm_vrt, l1c_b3_10cm_vrt, l1c_b2_10cm_vrt, l1c_b4_10cm_tif, coef_r_str)
    call(cmd, shell=True)

    coef_g_str = str(coef_g)
    cmd = "gdal_calc.py -A {0} -B {1} -C {2} --outfile={3} " \
          "--calc '(A.astype(float)*B*C!=0)*(A*{4}*(A*{4}<=255)+(A*{4}>255)*255)'" \
          " --type=Byte --NoDataValue=0".format(l1c_b3_10cm_vrt, l1c_b4_10cm_vrt, l1c_b2_10cm_vrt, l1c_b3_10cm_tif, coef_g_str)
    call(cmd, shell=True)

    coef_b_str = str(coef_b)
    cmd = "gdal_calc.py -A {0} -B {1} -C {2} --outfile={3} " \
          "--calc '(A.astype(float)*B*C!=0)*(A*{4}*(A*{4}<=255)+(A*{4}>255)*255)'" \
          " --type=Byte --NoDataValue=0".format(l1c_b2_10cm_vrt, l1c_b4_10cm_vrt, l1c_b3_10cm_vrt, l1c_b2_10cm_tif, coef_b_str)
    call(cmd, shell=True)

    # *****************************************
    # generate RGB output file (gdal_merge.py)
    # ****************************************
    cmd = "gdal_merge.py -separate -ot Byte -o {0} {1} {2} {3}".format(
        tmp_output_file_path, l1c_b4_10cm_tif, l1c_b3_10cm_tif, l1c_b2_10cm_tif)
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

    os.remove(output_file_path + "_VRT_1.vrt")
    os.remove(output_file_path + "_VRT_2.vrt")
    os.remove(output_file_path + "_VRT_3.vrt")
    os.remove(output_file_path + "_VRT_4.vrt")
    os.remove(l1c_b4_10cm_vrt)
    os.remove(l1c_b3_10cm_vrt)
    os.remove(l1c_b2_10cm_vrt)
    os.remove(l1c_b4_10cm_tif)
    os.remove(l1c_b3_10cm_tif)
    os.remove(l1c_b2_10cm_tif)
    os.remove(tmp_output_file_path)


def compute_rgb1184(l1c_xml_path, output_file_path, coef_r = 0.05, coef_g = 0.05, coef_b = 0.05):
    l1c_vrt = output_file_path + "_VRT.vrt"
    l1c_dataset_1 = output_file_path + "_VRT_1.vrt"
    l1c_dataset_2 = output_file_path + "_VRT_2.vrt"
    l1c_b4_10cm_vrt = output_file_path + "_b4.vrt"
    l1c_b8_10cm_vrt = output_file_path + "_b8.vrt"
    l1c_b11_20cm_vrt = output_file_path + "_b11_20.vrt"
    l1c_b11_10cm_vrt = output_file_path + "_b11.vrt"
    l1c_b4_10cm_tif = output_file_path + "_b4.tif"
    l1c_b8_10cm_tif = output_file_path + "_b8.tif"
    l1c_b11_10cm_tif = output_file_path + "_b11.tif"
    tmp_output_file_path = output_file_path + "_original_srs.tif"

    # *****************************************
    # generate l1c vrt (gdal translate)
    # ****************************************
    cmd = "gdal_translate -of VRT -sds {0} {1}".format(
        l1c_xml_path, l1c_vrt)
    call(cmd, shell=True)

    # *****************************************
    # extract virtual raster bands (gdal translate)
    # ****************************************
    cmd = "gdal_translate -of VRT -b 5 {0} {1}".format(
        l1c_dataset_2, l1c_b11_20cm_vrt)
    call(cmd, shell=True)

    cmd = "gdal_translate -of VRT -b 4 {0} {1}".format(
        l1c_dataset_1, l1c_b8_10cm_vrt)
    call(cmd, shell=True)

    cmd = "gdal_translate -of VRT -b 1 {0} {1}".format(
        l1c_dataset_1, l1c_b4_10cm_vrt)
    call(cmd, shell=True)

    # *****************************************
    # Resample band 11 to 10 m
    # ****************************************
    cmd = "gdalwarp -tr 10 10 -of VRT {0} {1}".format(
        l1c_b11_20cm_vrt, l1c_b11_10cm_vrt)
    call(cmd, shell=True)

    # *****************************************
    # apply coeficient to bands (gdal_calc.py)
    # ****************************************
    coef_r_str = str(coef_r)
    cmd = "gdal_calc.py -A {0} -B {1} -C {2} --outfile={3} " \
          "--calc '(A.astype(float)*B*C!=0)*(A*{4}*(A*{4}<=255)+(A*{4}>255)*255)' " \
          "--type=Byte --NoDataValue=0".format(l1c_b11_10cm_vrt, l1c_b8_10cm_vrt, l1c_b4_10cm_vrt, l1c_b11_10cm_tif, coef_r_str)
    call(cmd, shell=True)

    coef_g_str = str(coef_g)
    cmd = "gdal_calc.py -A {0} -B {1} -C {2} --outfile={3} " \
          "--calc '(A.astype(float)*B*C!=0)*(A*{4}*(A*{4}<=255)+(A*{4}>255)*255)' " \
          "--type=Byte --NoDataValue=0".format(l1c_b8_10cm_vrt, l1c_b11_10cm_vrt, l1c_b4_10cm_vrt, l1c_b8_10cm_tif, coef_g_str)
    call(cmd, shell=True)

    coef_b_str = str(coef_b)
    cmd = "gdal_calc.py -A {0} -B {1} -C {2} --outfile={3} " \
          "--calc '(A.astype(float)*B*C!=0)*(A*{4}*(A*{4}<=255)+(A*{4}>255)*255)' " \
          "--type=Byte --NoDataValue=0".format(l1c_b4_10cm_vrt, l1c_b11_10cm_vrt, l1c_b8_10cm_vrt, l1c_b4_10cm_tif, coef_b_str)
    call(cmd, shell=True)

    # *****************************************
    # generate RGB output file (gdal_merge.py)
    # ****************************************
    cmd = "gdal_merge.py -separate -ot Byte -o {0} {1} {2} {3}".format(
        tmp_output_file_path, l1c_b11_10cm_tif, l1c_b8_10cm_tif, l1c_b4_10cm_tif)
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

    os.remove(output_file_path + "_VRT_1.vrt")
    os.remove(output_file_path + "_VRT_2.vrt")
    os.remove(output_file_path + "_VRT_3.vrt")
    os.remove(output_file_path + "_VRT_4.vrt")
    os.remove(l1c_b4_10cm_vrt)
    os.remove(l1c_b8_10cm_vrt)
    os.remove(l1c_b11_10cm_vrt)
    os.remove(l1c_b11_20cm_vrt)
    os.remove(l1c_b8_10cm_tif)
    os.remove(l1c_b11_10cm_tif)
    os.remove(l1c_b4_10cm_tif)
    os.remove(tmp_output_file_path)


def compute_rgb1283(l1c_xml_path, output_file_path, coef_r = 0.05, coef_g = 0.05, coef_b = 0.05):
    l1c_vrt = output_file_path + "_VRT.vrt"
    l1c_dataset_1 = output_file_path + "_VRT_1.vrt"
    l1c_dataset_2 = output_file_path + "_VRT_2.vrt"
    l1c_b3_10cm_vrt = output_file_path + "_b4.vrt"
    l1c_b8_10cm_vrt = output_file_path + "_b8.vrt"
    l1c_b12_20cm_vrt = output_file_path + "_b12_20.vrt"
    l1c_b12_10cm_vrt = output_file_path + "_b12.vrt"
    l1c_b3_10cm_tif = output_file_path + "_b4.tif"
    l1c_b8_10cm_tif = output_file_path + "_b8.tif"
    l1c_b12_10cm_tif = output_file_path + "_b11.tif"
    tmp_output_file_path = output_file_path + "_original_srs.tif"

    # *****************************************
    # generate l1c vrt (gdal translate)
    # ****************************************
    cmd = "gdal_translate -of VRT -sds {0} {1}".format(
        l1c_xml_path, l1c_vrt)
    call(cmd, shell=True)

    # *****************************************
    # extract virtual raster bands (gdal translate)
    # ****************************************
    cmd = "gdal_translate -of VRT -b 6 {0} {1}".format(
        l1c_dataset_2, l1c_b12_20cm_vrt)
    call(cmd, shell=True)

    cmd = "gdal_translate -of VRT -b 4 {0} {1}".format(
        l1c_dataset_1, l1c_b8_10cm_vrt)
    call(cmd, shell=True)

    cmd = "gdal_translate -of VRT -b 2 {0} {1}".format(
        l1c_dataset_1, l1c_b3_10cm_vrt)
    call(cmd, shell=True)

    # *****************************************
    # Resample band 11 to 10 m
    # ****************************************
    cmd = "gdalwarp -tr 10 10 -of VRT {0} {1}".format(
        l1c_b12_20cm_vrt, l1c_b12_10cm_vrt)
    call(cmd, shell=True)

    # *****************************************
    # apply coeficient to bands (gdal_calc.py)
    # ****************************************
    coef_r_str = str(coef_r)
    cmd = "gdal_calc.py -A {0} -B {1} -C {2} --outfile={3} " \
          "--calc '(A.astype(float)*B*C!=0)*(A*{4}*(A*{4}<=255)+(A*{4}>255)*255)' " \
          "--type=Byte --NoDataValue=0".format(l1c_b12_10cm_vrt, l1c_b8_10cm_vrt, l1c_b3_10cm_vrt, l1c_b12_10cm_tif, coef_r_str)
    call(cmd, shell=True)

    coef_g_str = str(coef_g)
    cmd = "gdal_calc.py -A {0} -B {1} -C {2} --outfile={3} " \
          "--calc '(A.astype(float)*B*C!=0)*(A*{4}*(A*{4}<=255)+(A*{4}>255)*255)' " \
          "--type=Byte --NoDataValue=0".format(l1c_b8_10cm_vrt, l1c_b12_10cm_vrt, l1c_b3_10cm_vrt, l1c_b8_10cm_tif, coef_g_str)
    call(cmd, shell=True)

    coef_b_str = str(coef_b)
    cmd = "gdal_calc.py -A {0} -B {1} -C {2} --outfile={3} " \
          "--calc '(A.astype(float)*B*C!=0)*(A*{4}*(A*{4}<=255)+(A*{4}>255)*255)' " \
          "--type=Byte --NoDataValue=0".format(l1c_b3_10cm_vrt, l1c_b12_10cm_vrt, l1c_b8_10cm_vrt, l1c_b3_10cm_tif, coef_b_str)
    call(cmd, shell=True)

    # *****************************************
    # generate RGB output file (gdal_merge.py)
    # ****************************************
    cmd = "gdal_merge.py -separate -ot Byte -o {0} {1} {2} {3}".format(
        tmp_output_file_path, l1c_b12_10cm_tif, l1c_b8_10cm_tif, l1c_b3_10cm_tif)
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

    os.remove(output_file_path + "_VRT_1.vrt")
    os.remove(output_file_path + "_VRT_2.vrt")
    os.remove(output_file_path + "_VRT_3.vrt")
    os.remove(output_file_path + "_VRT_4.vrt")
    os.remove(l1c_b3_10cm_vrt)
    os.remove(l1c_b8_10cm_vrt)
    os.remove(l1c_b12_10cm_vrt)
    os.remove(l1c_b12_20cm_vrt)
    os.remove(l1c_b8_10cm_tif)
    os.remove(l1c_b12_10cm_tif)
    os.remove(l1c_b3_10cm_tif)
    os.remove(tmp_output_file_path)


def compute_ndvi(l1c_xml_path, output_file_path):
    l1c_vrt = output_file_path + "_VRT.vrt"
    l1c_dataset_1 = output_file_path + "_VRT_1.vrt"
    l1c_b4_10cm_vrt = output_file_path + "_b4.vrt"
    l1c_b8_10cm_vrt = output_file_path + "_b8.vrt"
    tmp_output_file_path = output_file_path + "_original_srs.tif"


    # *****************************************
    # generate l1c vrt (gdal translate)
    # ****************************************
    cmd = "gdal_translate -of VRT -sds {0} {1}".format(
        l1c_xml_path, l1c_vrt)
    call(cmd, shell=True)

    # *****************************************
    # extract virtual raster bands (gdal translate)
    # ****************************************
    cmd = "gdal_translate -of VRT -b 1 {0} {1}".format(
        l1c_dataset_1, l1c_b4_10cm_vrt)
    call(cmd, shell=True)

    cmd = "gdal_translate -of VRT -b 4 {0} {1}".format(
        l1c_dataset_1, l1c_b8_10cm_vrt)
    call(cmd, shell=True)


    # *****************************************
    # Calculate NDVI (gdal_calc.py)
    # ****************************************
    cmd = "gdal_calc.py -A {0} -B {1} --outfile={2} " \
          "--calc '(A.astype(float)*B!=0)*(A.astype(float)-B)/" \
          "(A.astype(float)+B+(A.astype(float)*B==0))+(A.astype(float)*B==0)*9999' " \
          "--type=Float32 --NoDataValue=9999".format(l1c_b8_10cm_vrt, l1c_b4_10cm_vrt, tmp_output_file_path)
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

    os.remove(output_file_path + "_VRT_1.vrt")
    os.remove(output_file_path + "_VRT_2.vrt")
    os.remove(output_file_path + "_VRT_3.vrt")
    os.remove(output_file_path + "_VRT_4.vrt")
    os.remove(l1c_b4_10cm_vrt)
    os.remove(l1c_b8_10cm_vrt)
    os.remove(tmp_output_file_path)

###########################################################################

def compute_ndvi_byte(l1c_xml_path, output_file_path):
    l1c_vrt = output_file_path + "_VRT.vrt"
    l1c_dataset_1 = output_file_path + "_VRT_1.vrt"
    l1c_b4_10cm_vrt = output_file_path + "_b4.vrt"
    l1c_b8_10cm_vrt = output_file_path + "_b8.vrt"
    tmp_output_file_path = output_file_path + "_original_srs.tif"


    # *****************************************
    # generate l1c vrt (gdal translate)
    # ****************************************
    cmd = "gdal_translate -of VRT -sds {0} {1}".format(
        l1c_xml_path, l1c_vrt)
    call(cmd, shell=True)

    # *****************************************
    # extract virtual raster bands (gdal translate)
    # ****************************************
    cmd = "gdal_translate -of VRT -b 1 {0} {1}".format(
        l1c_dataset_1, l1c_b4_10cm_vrt)
    call(cmd, shell=True)

    cmd = "gdal_translate -of VRT -b 4 {0} {1}".format(
        l1c_dataset_1, l1c_b8_10cm_vrt)
    call(cmd, shell=True)


    # *****************************************
    # Calculate NDVI (gdal_calc.py)
    # ****************************************
    cmd = "gdal_calc.py -A {0} -B {1} --outfile={2} " \
          "--calc '(A.astype(float)*B!=0)*(A.astype(float)-B)/" \
          "(A.astype(float)+B+(A.astype(float)*B==0))*100+(A.astype(float)*B==0)*255' " \
          "--type=Byte --NoDataValue=255".format(l1c_b8_10cm_vrt, l1c_b4_10cm_vrt, tmp_output_file_path)

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

    os.remove(output_file_path + "_VRT_1.vrt")
    os.remove(output_file_path + "_VRT_2.vrt")
    os.remove(output_file_path + "_VRT_3.vrt")
    os.remove(output_file_path + "_VRT_4.vrt")
    os.remove(l1c_b4_10cm_vrt)
    os.remove(l1c_b8_10cm_vrt)
    os.remove(tmp_output_file_path)

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
                  help="Space separated list of products to process (RGB432 RGB1184 RGB1283 NDVI NDVIb).",
                  default="RGB1184 RGB1283 NDVI NDVIb NDVIb_mosaic")
parser.add_option("--publish_list", dest="publish_list", action="store", type="string",
                  help="Space separated list of products to publish (RGB432 RGB1184 RGB1283 NDVIb).",
                  default="RGB1184 RGB1283 NDVIb")
parser.add_option("--product_folders", dest="product_folders", action="store_true",
                  help="Store outputs in separated folders by product type")
parser.add_option("--initial_date", dest="initial_date", action="store", type="string",
                  help="",
                  default=None)
parser.add_option("--final_date", dest="final_date", action="store", type="string",
                  help="",
                  default=None)
parser.add_option("--date_field", dest="date_field", action="store", type="int",
                  help="",
                  default=2)
parser.add_option("-d", "--debug", dest="debug", action="store_true",
                  help="Only print command")
parser.add_option("--workspace", dest="workspace", action="store", type="string", \
                      help="Workspace id", default=None)

(options, args) = parser.parse_args()

if options.input_file:
    input_list = [os.path.basename(options.input_file)]
    options.input_path = os.path.dirname(options.input_file)
else:
    input_list = os.listdir(options.input_path)

product_list = options.product_list.split(" ")
publish_list = options.publish_list.split(" ")

date_field = options.date_field

initial_date = '0'
if options.initial_date:
    initial_date = options.initial_date

final_date = '30001231'
if options.final_date:
    final_date = options.final_date

for file in input_list:
    if file.endswith(".zip"):

        # Filter by date:
        if options.initial_date or options.final_date:
            file_date = file.split('_')[date_field].split('T')[0]
            if not (initial_date <= file_date <= final_date):
                continue

        unziped_l1c_path = os.path.join(options.tmp_path, file.replace('.zip', '').replace('.ZIP', ''))

        zip_ref = zipfile.ZipFile(os.path.join(options.input_path, file), 'r')
        zip_ref.extractall(options.tmp_path)
        zip_ref.close()

        s2_metadata_path = os.path.join(unziped_l1c_path, 'MTD_MSIL1C.xml')
        sensing_date = file.split('_')[2].split('T')[0]
        granule_id = file.split('_')[5]
        orbit_id = file.split('_')[4]
        platform_id = file.split('_')[0]
        srs = '25830'

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
            rgb432_file = sensing_date + '_' + platform_id + '_' + granule_id + '_' + orbit_id + '_RGB432.tif'
            rgb432_file_path = os.path.join(rgb432_output_path, rgb432_file)
            compute_rgb432(s2_metadata_path, rgb432_file_path, options.red_coef, options.green_coef, options.blue_coef)
            if options.ingest_id:
                catalog_manager.ingest_derived_product(rgb432_file_path, date.today(), "S2RGB432", options.ingest_id)
            if 'RGB432' in publish_list:
                print 'Publishing product: {}'.format(rgb432_file)
                catalog_manager.publish_product('s2rgb432', rgb432_file)

        if 'RGB1184' in product_list:
            rgb1184_output_path = options.output_path
            if options.product_folders:
                rgb1184_output_path = os.path.join(rgb1184_output_path, 'RGB1184')
                if not (os.path.exists(rgb1184_output_path)):
                    os.mkdir(rgb1184_output_path)
            rgb1184_file = sensing_date + '_' + platform_id + '_' + granule_id + '_' + orbit_id + '_RGB1184.tif'
            rgb1184_file_path = os.path.join(rgb1184_output_path,rgb1184_file)
            compute_rgb1184(s2_metadata_path, rgb1184_file_path, options.red_coef, options.green_coef,
                            options.blue_coef)
            if options.ingest_id:
                catalog_manager.ingest_derived_product(rgb1184_file_path, date.today(), "S2RGB1184", options.ingest_id)
            if 'RGB1184' in publish_list:
                print 'Publishing product: {}'.format(rgb1184_file)
                catalog_manager.publish_product('s2rgb1184', rgb1184_file)

        if 'RGB1283' in product_list:
            rgb1283_output_path = options.output_path
            if options.product_folders:
                rgb1283_output_path = os.path.join(rgb1283_output_path, 'RGB1283')
                if not (os.path.exists(rgb1283_output_path)):
                    os.mkdir(rgb1283_output_path)
            rgb1283_file = sensing_date + '_' + platform_id + '_' + granule_id + '_' + orbit_id + '_RGB1283.tif'
            rgb1283_file_path = os.path.join(rgb1283_output_path, rgb1283_file)
            compute_rgb1283(s2_metadata_path, rgb1283_file_path, options.red_coef, options.green_coef,
                            options.blue_coef)
            if options.ingest_id:
                catalog_manager.ingest_derived_product(rgb1283_file_path, date.today(), "S2RGB1283", options.ingest_id)
            if 'RGB1283' in publish_list:
                print 'Publishing product: {}'.format(rgb1283_file)
                catalog_manager.publish_product('s2rgb1283', rgb1283_file)

        if 'NDVI' in product_list:
            ndvi_output_path = options.output_path
            if options.product_folders:
                ndvi_output_path = os.path.join(ndvi_output_path, 'NDVI')
                if not (os.path.exists(ndvi_output_path)):
                    os.mkdir(ndvi_output_path)
            ndvi_file = sensing_date + '_' + platform_id + '_' + granule_id + '_' + orbit_id + '_NDVI.tif'
            ndvi_file_path = os.path.join(ndvi_output_path, ndvi_file)
            compute_ndvi(s2_metadata_path, ndvi_file_path)
            if options.ingest_id:
                catalog_manager.ingest_derived_product(ndvi_file_path, date.today(), "S2NDVI", options.ingest_id)

        if 'NDVIb' in product_list:
            ndvib_output_path = options.output_path
            if options.product_folders:
                ndvib_output_path = os.path.join(ndvib_output_path, 'NDVIb')
                if not (os.path.exists(ndvib_output_path)):
                    os.mkdir(ndvib_output_path)
            ndvib_file = sensing_date + '_' + platform_id + '_' + granule_id + '_' + orbit_id + '_NDVIb.tif'
            ndvi_file_path = os.path.join(ndvib_output_path, ndvib_file)
            compute_ndvi_byte(s2_metadata_path, ndvi_file_path)
            if options.ingest_id:
                catalog_manager.ingest_derived_product(ndvi_file_path, date.today(), "S2NDVIb", options.ingest_id)
            if 'NDVIb' in publish_list:
                print 'Publishing product: {}'.format(ndvib_file)
                catalog_manager.publish_product('s2ndvib', ndvib_file)

            if 'NDVIb_mosaic' in product_list:
                print "***** Checking granules for mosaic ..."
                granules_by_orbit_file = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                                      'granules_by_orbit.txt')
                granules_list = read_granules_list(orbit_id, granules_by_orbit_file)
                print "***** Granules list:"
                print granules_list
                if catalog_manager.is_s2_mosaic_ready(sensing_date, 'S2NDVIb', granules_list):
                    ndvib_mosaic_output_path = os.path.join(ndvib_output_path, 'mosaic')
                    if options.product_folders:
                        ndvib_mosaic_output_path = os.path.join(options.output_path, 'NDVIb_mosaic')
                    if not (os.path.exists(ndvib_mosaic_output_path)):
                        os.mkdir(ndvib_mosaic_output_path)
                    cmd = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'make_mosaic.py')
                    cmd += ' -g {} -o {} -p .*NDVIb.tif --dateposition 0 -w --date {}'\
                        .format(ndvib_output_path, ndvib_mosaic_output_path+'/', sensing_date)
                    stdfile = open('std.out', 'w')
                    errfile = open('err.out', 'w')
                    print "************************"
                    print "************************"
                    print "Making Mosaic {}".format(sensing_date)
                    print cmd
                    print "************************"
                    print "************************"
                    p = call(cmd, shell=False, stdin=None, stdout=stdfile, stderr=errfile)

        shutil.rmtree(unziped_l1c_path)
