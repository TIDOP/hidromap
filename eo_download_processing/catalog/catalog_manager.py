#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-

import psycopg2
import ntpath
from subprocess import call
import os
import sys
from zipfile import *


class CatalogManager:
    def __init__(self, database, user, password, host, port, geoserver_rest_url=None, geoserver_products_path=None,
                 geoserver_user=None, geoserver_pass=None):
        self.connection = psycopg2.connect(database=database,
                                           user=user,
                                           password=password,
                                           host=host,
                                           port=port,)

        self.geoserver_rest_url = geoserver_rest_url
        self.geoserver_products_path = geoserver_products_path
        self.geoserver_user = geoserver_user
        self.geoserver_pass = geoserver_pass

        if not self.connection:
            print "Error connecting"
            exit(1)

    @classmethod
    def from_file(class_object, config_file_path):
        try:
            with open(config_file_path) as f:
                lines = f.readlines()
        except:
            print "Error with granules file"
            sys.exit(-3)

        catalog_db = None
        catalog_user = None
        catalog_pass = None
        catalog_port = None
        catalog_host = None
        geoserver_products_path = None
        geoserver_user = None
        geoserver_pass = None

        # Remove whitespace characters like `\n` at the end of each line
        stripped_granules_list = []
        for line in lines:
            splitted_line = line.split('=')
            if splitted_line[0].strip() == 'catalog_db':
                catalog_db = splitted_line[1].strip()
            elif splitted_line[0].strip() == 'catalog_user':
                catalog_user = splitted_line[1].strip()
            elif splitted_line[0].strip() == 'catalog_pass':
                catalog_pass = splitted_line[1].strip()
            elif splitted_line[0].strip() == 'catalog_port':
                catalog_port = splitted_line[1].strip()
            elif splitted_line[0].strip() == 'catalog_host':
                catalog_host = splitted_line[1].strip()
            elif splitted_line[0].strip() == 'geoserver_products_path':
                geoserver_products_path = splitted_line[1].strip()
            elif splitted_line[0].strip() == 'geoserver_user':
                geoserver_user = splitted_line[1].strip()
            elif splitted_line[0].strip() == 'geoserver_pass':
                geoserver_pass = splitted_line[1].strip()
            elif splitted_line[0].strip() == 'geoserver_rest_url':
                geoserver_rest_url = splitted_line[1].strip()

        f.close()

        return class_object(catalog_db, catalog_user, catalog_pass, catalog_host, catalog_port,
                            geoserver_rest_url, geoserver_products_path, geoserver_user, geoserver_pass)

    def ingest_original_product(self,
                                file_path,
                                ingestion_date,
                                sensing_date,
                                platform_identifier,
                                footprint,
                                cloud_coverage,
                                orbit_number,
                                granule_id,
                                product_id,
                                workspace=None):
        if self.connection:
            cursor = self.connection.cursor()
            cursor.execute("insert into catalog.original_products(url, ingestion_date, sensing_date, cloud_coverage,"
                           "sensor, orbit_number, tile_id, product_id, workspace, tile_data_geometry) "
                           "values (%s, %s, %s, %s, %s, %s, %s, %s, %s, "
                           "ST_GeomFromText(%s,4326))",
                           (file_path, ingestion_date, sensing_date, cloud_coverage, platform_identifier,
                            orbit_number, granule_id, product_id, workspace, footprint))

            self.connection.commit()
            return 0

        else:
            print "No connection"
            return -1

    def ingest_derived_product(self, file_path, ingestion_date, product_type, original_product_id,
                                workspace=None):
        if self.connection:
            cursor = self.connection.cursor()
            if original_product_id:
                cursor.execute("SELECT id FROM catalog.original_products WHERE product_id = %s", (original_product_id,))
                record = cursor.fetchone()
                if record:
                    original_product_key = record[0]
                    cursor.execute("insert into catalog.derived_products(url, ingestion_date, "
                                   "original_product_id, product_type, workspace) "
                                   "values (%s, %s, %s, %s, %s)",
                                   (file_path, ingestion_date, original_product_key, product_type, workspace))
                    self.connection.commit()
                    return 0
                else:
                    print "Product ID not found: {}".format(original_product_id)
                    return -1
            else:
                cursor.execute("insert into catalog.derived_products(url, ingestion_date, "
                               "product_type) "
                               "values (%s, %s, %s)",
                               (file_path, ingestion_date, product_type))
                self.connection.commit()
                return 0

        else:
            print "No connection"
            return -1

    def exist_product(self, product_id):
        if self.connection:
            cursor = self.connection.cursor()
            # cursor.execute("SELECT COUNT(id) from catalog.original_products WHERE product_id = %s", (product_id))
            data = [product_id]
            cursor.execute("SELECT COUNT(id) from catalog.original_products WHERE product_id = %s;", data)
            result = cursor.fetchone()
            if result[0]:
                return 1
            else:
                return 0

        else:
            print "No connection"
            return -1

    def exist_derived_product(self, url):
        if self.connection:
            cursor = self.connection.cursor()
            # cursor.execute("SELECT COUNT(id) from catalog.original_products WHERE product_id = %s", (product_id))
            data = ['%'+url]
            cursor.execute("SELECT COUNT(url) from catalog.derived_products WHERE url LIKE %s;", data)
            result = cursor.fetchone()
            if result[0]:
                return 1
            else:
                return 0

        else:
            print "No connection"
            return -1

    def products_without_derived(self, product_type):
        product_list = []
        if self.connection:
            cursor = self.connection.cursor()
            data = [product_type]
            cursor.execute("kkkkkkkk", data)
            result = cursor.fetchone()
            if result[0]:
                return 1
            else:
                return 0
        else:
            print "No connection"
        return product_list

    def is_s2_mosaic_ready(self, sensig_date, product_type, granules_list, granule_id_position=2):
        if self.connection:
            cursor = self.connection.cursor()
            # cursor.execute("SELECT COUNT(id) from catalog.original_products WHERE product_id = %s", (product_id))
            data = ['%'+sensig_date+'%', product_type]
            cursor.execute("SELECT url from catalog.derived_products WHERE url LIKE %s AND "
                                       "product_type = %s;", data)
            db_granules_list = []
            row = cursor.fetchone()
            while row is not None:
                url = str(row[0])
                db_granules_list.append(ntpath.basename(url).split('_')[granule_id_position])
                row = cursor.fetchone()
            print "************************"
            print "***** DB Granules list ..."
            print db_granules_list
            print "***** Granules list: ..."
            print granules_list
            print "************************"
            if db_granules_list.__len__() < granules_list.__len__():
                return False
            for granule in granules_list:
                if granule not in db_granules_list:
                    return False
            return True
        else:
            print "No connection"
            return False

    def publish_product(self, product_type, product_file):
        if self.geoserver_products_path and self.geoserver_user and self.geoserver_pass and self.geoserver_rest_url:
            # product_path = os.path.join(self.geoserver_products_path, product_type, product_file)
            product_path = '{0}/{1}/{2}'.format(self.geoserver_products_path, product_type, product_file)
            url = self.geoserver_rest_url.replace('*coverage_name*', product_type)
            cmd = 'curl -v -u {0}:{1} -XPOST -H "Content-type: text/plain" -d "{2}" "{3}"'.format(
                self.geoserver_user, self.geoserver_pass, product_path, url)
            print '********************************************'
            print 'Publishing {}'.format(product_file)
            print cmd
            print '********************************************'
            call(cmd, shell=False)

        else:
            print 'Geoserver connection data not aviable.'

    def clean_catalog(self, zero = True, not_existing = True, not_derrived = False, delete_files = False,
                      initial_date = None, final_date = None, corrupted_zip = False, debug = False):
        """Remove product records with no existing files or zero file size
        """
        cursor = self.connection.cursor()
        cursor.execute('SELECT id, url from catalog.derived_products;')
        row = cursor.fetchone()
        ids_zero = []
        ids_no_existing = []
        while row is not None:
            url = str(row[1])
            if os.path.exists(url):
                stat = os.stat(url)
                if stat.st_size == 0:
                    ids_zero.append(str(row[0]))
            else:
                ids_no_existing.append(str(row[0]))
            row = cursor.fetchone()
        if zero and ids_zero.__len__() > 0:
            print '{} Zero size derived products to delete.'.format(ids_zero.__len__())
            sql_query = 'DELETE FROM catalog.derived_products WHERE id in (' + ','.join(map(str, ids_zero)) + ')'
            print sql_query
            print 'Zero size products:'
            print ids_zero
            if not debug:
                cursor.execute(sql_query)
                self.connection.commit()

        if not_existing and ids_no_existing.__len__() > 0:
            print '{} Not existing derived products to delete.'.format(ids_no_existing.__len__())
            sql_query = 'DELETE FROM catalog.derived_products WHERE id in (' + ','.join(map(str, ids_no_existing)) + ')'
            print sql_query
            print 'Not existing products:'
            print ids_no_existing
            if not debug:
                cursor.execute(sql_query)
                self.connection.commit()

        cursor.execute('SELECT id, url from catalog.original_products;')
        row = cursor.fetchone()
        ids_zero = []
        ids_no_existing = []
        while row is not None:
            url = str(row[1])
            if os.path.exists(url):
                stat = os.stat(url)
                if stat.st_size == 0:
                    ids_zero.append(str(row[0]))
            else:
                ids_no_existing.append(str(row[0]))
            row = cursor.fetchone()
        if zero and ids_zero.__len__() > 0:
            print '{} Zero size original products to delete.'.format(ids_zero.__len__())
            sql_query = 'DELETE FROM catalog.original_products WHERE id in (' + ','.join(map(str, ids_zero)) + ')'
            print sql_query
            print 'Zero size original products:'
            print ids_zero
            if not debug:
                cursor.execute(sql_query)
                self.connection.commit()
        if not_existing and ids_no_existing.__len__() > 0:
            print '{} Not existing original products to delete.'.format(ids_no_existing.__len__())
            sql_query = 'DELETE FROM catalog.original_products WHERE id in (' + ','.join(map(str, ids_no_existing)) + ')'
            print sql_query
            print 'Not existing original products:'
            print ids_no_existing
            if not debug:
                cursor.execute(sql_query)
                self.connection.commit()

        if not_derrived:
            ids_not_derived = []
            sql_query = 'SELECT original.id,product_id,sensor,sensing_date, original.url ' \
                        'FROM catalog.original_products AS original ' \
                        'LEFT JOIN catalog.derived_products AS derived ON original.id=derived.original_product_id ' \
                        'WHERE derived.original_product_id IS NULL'
            if (initial_date and final_date):
                sql_query += ' AND sensing_date >= %s AND sensing_date <= %s;'
                cursor.execute(sql_query, (initial_date, final_date,))
            else:
                sql_query += ';'
                cursor.execute(sql_query)
            if debug:
                print 'Select not derived:'
                print sql_query

            row = cursor.fetchone()
            while row is not None:
                ids_not_derived.append(str(row[0]))
                if delete_files and os.path.exists(str(row[4])) and not debug:
                    os.remove(str(row[4]))
                if debug:
                    print 'Delete {} file'.format(str(row[4]))
                row = cursor.fetchone()
            sql_query = 'DELETE FROM catalog.original_products WHERE id in (' + ','.join(map(str, ids_not_derived)) + ')'
            print sql_query
            print 'Products without derived:'
            print ids_not_derived
            if not debug:
                cursor.execute(sql_query)
                self.connection.commit()

        if corrupted_zip:
            ids_corrupted = []
            sql_query = 'SELECT original.id,product_id,sensor,sensing_date, original.url ' \
                        'FROM catalog.original_products AS original ' \
                        'LEFT JOIN catalog.derived_products AS derived ON original.id=derived.original_product_id ' \
                        'WHERE derived.original_product_id IS NULL'
            if (initial_date and final_date):
                sql_query += ' AND sensing_date >= %s AND sensing_date <= %s;'
                cursor.execute(sql_query, (initial_date, final_date,))
            else:
                sql_query += ';'
                cursor.execute(sql_query)
            if debug:
                print 'Select corrupted:'
                print sql_query

            row = cursor.fetchone()
            while row is not None:
                url = str(row[4])
                if url.endswith('zip') and os.path.exists(url):
                    print 'Testing zip: {}'.format(url)
                    original_zip = None
                    try:
                        original_zip = ZipFile(url, 'r')
                    except:
                        print '{} Not a zip file.'.format(url)
                    if original_zip is None or not original_zip.testzip() is None:
                        ids_corrupted.append(str(row[0]))
                        if not debug:
                            os.remove(url)
                        print 'Delete {} file'.format(str(row[4]))
                row = cursor.fetchone()

            sql_query = 'DELETE FROM catalog.original_products WHERE id in (' + ','.join(map(str, ids_corrupted)) + ')'
            print sql_query
            print 'Corrupted products:'
            print ids_corrupted
            if not debug:
                cursor.execute(sql_query)
                self.connection.commit()


    def original_product_id(self, date, granule, sensor):
        if self.connection:
            cursor = self.connection.cursor()
            cursor.execute("SELECT product_id from catalog.original_products WHERE sensing_date = %s and "
                           "tile_id = %s and sensor = %s;", [date, granule, sensor])
            result = cursor.fetchone()
            if result:
                return result[0]
            else:
                return None
