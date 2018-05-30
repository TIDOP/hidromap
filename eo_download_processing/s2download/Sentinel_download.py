#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-

import os,sys,math
import optparse
from xml.dom import minidom
from datetime import date
import datetime
from subprocess import call
from subprocess import Popen
import inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
catalog_dir = os.path.join(os.path.dirname(currentdir),'catalog')
os.sys.path.insert(0,catalog_dir)
import catalog_manager
from zipfile import *

###########################################################################
class OptionParser (optparse.OptionParser):
 
    def check_required (self, opt):
      option = self.get_option(opt)
 
      # Assumes the option's 'default' is set to None!
      if getattr(self.values, option.dest) is None:
          self.error("%s option not supplied" % option)

###########################################################################


#get URL, name and type within xml file from Scihub
def get_elements(xml_file):
    urls=[]
    contentType=[]
    name=[]
    with open(xml_file) as fic:
        line=fic.readlines()[0].split('<entry>')
        for fragment in line[1:]:
            urls.append(fragment.split('<id>')[1].split('</id>')[0])
            contentType.append(fragment.split('<d:ContentType>')[1].split('</d:ContentType>')[0])
            name.append(fragment.split('<title type="text">')[1].split('</title>')[0])
            #print name
    os.remove(xml_file)
    return urls,contentType,name

# recursively download file tree of a Granule
def download_tree(rep,xml_file,wg,auth,wg_opt,value):
    urls,types,names=get_elements(xml_file)
    for i in range(len(urls)):
        urls[i]=urls[i].replace("eu/odata","eu/apihub/odata") #patch the url
        if types[i]=='Item' and not 'ECMWFT' in names[i]:
            nom_rep="%s/%s"%(rep,names[i])
            if not(os.path.exists(nom_rep)):
                os.mkdir(nom_rep)
            commande_wget='%s %s %s%s "%s"'%(wg,auth,wg_opt,'files.xml',urls[i]+"/Nodes")
            print commande_wget
            os.system(commande_wget)
            while os.path.getsize("files.xml")==0 : #in case of "bad gateway error"
                os.system(commande_wget)
            download_tree(nom_rep,'files.xml',wg,auth,wg_opt,value)
        else:
            commande_wget='%s %s %s%s "%s"'%(wg,auth,wg_opt,rep+'/'+names[i],urls[i]+'/'+value)
            os.system(commande_wget)
            while os.path.getsize(rep+'/'+names[i])==0 : #retry download in case of a Bad Gateway error"
                os.system(commande_wget)

def get_dir(dir_name,dir_url,product_dir_name,wg,auth,wg_opt,value):
    dir=("%s/%s"%(product_dir_name,dir_name))
    dir_url=dir_url.replace("eu/odata","eu/apihub/odata")  #patch the url
    if not(os.path.exists(dir)) :
        os.mkdir(dir)
    commande_wget='%s %s %s%s "%s"'%(wg,auth,wg_opt,'temp.xml',dir_url)
    print commande_wget
    os.system(commande_wget)
    while os.path.getsize("temp.xml")==0 : #in case of "bad gateway error"
        os.system(commande_wget)
    download_tree(product_dir_name+'/'+dir_name,"temp.xml",wg,auth,wg_opt,value)
   
    

##########################################################################




url_search="https://scihub.copernicus.eu/apihub/search?q="

#==================
#parse command line
#==================
if len(sys.argv) == 1:
    prog = os.path.basename(sys.argv[0])
    print '      '+sys.argv[0]+' [options]'
    print "     Aide : ", prog, " --help"
    print "        ou : ", prog, " -h"
    print "example python  %s --lat 43.6 --lon 1.44 -a apihub.txt "%sys.argv[0]
    print "example python  %s --lat 43.6 --lon 1.44 -a apihub.txt -t 31TCJ "%sys.argv[0]
    sys.exit(-1)
else:
    usage = "usage: %prog [options] "
    parser = OptionParser(usage=usage)
    parser.add_option("--downloader", dest="downloader", action="store", type="string", \
            help="downloader options are aria2 or wget (default is wget)",default=None)
    parser.add_option("--lat", dest="lat", action="store", type="float", \
            help="latitude in decimal degrees",default=None)
    parser.add_option("--lon", dest="lon", action="store", type="float", \
            help="longitude in decimal degrees",default=None)
    parser.add_option("--latmin", dest="latmin", action="store", type="float", \
            help="min latitude in decimal degrees",default=None)
    parser.add_option("--latmax", dest="latmax", action="store", type="float", \
            help="max latitude in decimal degrees",default=None)
    parser.add_option("--lonmin", dest="lonmin", action="store", type="float", \
            help="min longitude in decimal degrees",default=None)
    parser.add_option("--lonmax", dest="lonmax", action="store", type="float", \
            help="max longitude in decimal degrees",default=None)
    parser.add_option("--id", "--start_ingest_date", dest="start_ingest_date", action="store", type="string", \
            help="start ingestion date, fmt('2015-12-22')",default=None)
    parser.add_option("--if","--end_ingest_date", dest="end_ingest_date", action="store", type="string", \
            help="end ingestion date, fmt('2015-12-23')",default=None)     
    parser.add_option("-d", "--start_date", dest="start_date", action="store", type="string", \
            help="start date, fmt('20151222')",default=None)
    parser.add_option("-f","--end_date", dest="end_date", action="store", type="string", \
            help="end date, fmt('20151223')",default=None)
    parser.add_option("-o","--orbit", dest="orbit", action="store", type="int", \
            help="Orbit Number", default=None)			
    parser.add_option("-a","--apihub_passwd", dest="apihub", action="store", type="string", \
            help="ESA apihub account and password file")
    parser.add_option("-p","--proxy_passwd", dest="proxy", action="store", type="string", \
            help="Proxy account and password file",default=None)
    parser.add_option("-n","--no_download", dest="no_download", action="store_true",  \
            help="Do not download products, just print wget command",default=False)
    parser.add_option("-m","--max_cloud", dest="max_cloud", action="store",type="float",  \
            help="Do not download products with more cloud percentage ",default=110)
    parser.add_option("-w","--write_dir", dest="write_dir", action="store",type="string",  \
            help="Path where the products should be downloaded",default='.')
    parser.add_option("-s","--sentinel", dest="sentinel", action="store",type="string",  \
            help="Sentinel mission considered",default='S2')
    parser.add_option("-t","--tile", dest="tile", action="store",type="string",  \
            help="Sentinel-2 Tile number",default=None)
    parser.add_option("--dhus",dest="dhus",action="store_true",  \
            help="Try dhus interface when apihub is not working",default=False)
    parser.add_option("-r",dest="MaxRecords",action="store",type="int",  \
            help="maximum number of records to download (default=100)",default=100)

    #DGS:
    parser.add_option("--polygon", dest="polygon", action="store", type="string", \
                      help="wkt polygon file", default=None)
    parser.add_option("--granules", dest="granules_file", action="store", type="string", \
                      help="granules list file", default=None)
    parser.add_option("--time_range", dest="time_range", action="store", type="string", \
                      help="Download From time_range days till now", default=None)
    parser.add_option("--post_download", dest="post_download_script", action="store", type="string", \
                      help="Script to run after each download", default=None)
    parser.add_option("--post_params", dest="post_download_params", action="store", type="string", \
                      help="Parameters for post-download script", default=None)
    parser.add_option("-l", "--level", dest="level", action="store", type="string", \
                      help="L1C,L2A...", default="L1C")
    parser.add_option("--check_notdownloaded", dest="check_notdownloaded", action="store_true", \
                      help="Only list not downloaded products", default=False)
    parser.add_option("--workspace", dest="workspace", action="store", type="string", \
                      help="Workspace id", default=None)

    (options, args) = parser.parse_args()
    if options.lat == None or options.lon == None:
        if options.latmin == None or options.lonmin == None or options.latmax == None or options.lonmax == None:
            if options.polygon == None:
                print "provide at least a point or  rectangle"
                sys.exit(-1)
            else:
                geom = 'polygon'
        else:
            if options.polygon == None:
                geom = 'rectangle'
            else:
                print "please choose between point, rectance and polygon, but only one option"
                sys.exit(-1)
    else:
        if options.latmin == None and options.lonmin == None and options.latmax == None and options.lonmax == None:
            geom = 'point'
        else:
            print "please choose between point, rectance and polygon, but only one option"
            sys.exit(-1)
    if options.tile != None and options.sentinel != 'S2':
        print "The tile option (-t) can only be used for Sentinel-2"
        sys.exit(-1)
        
    parser.check_required("-a")    
    
#====================
# read password file
#====================
try:
    f=file(options.apihub)
    (account,passwd)=f.readline().split(' ')
    if passwd.endswith('\n'):
        passwd=passwd[:-1]
    f.close()
except :
    print "error with password file"
    sys.exit(-2)

#====================
# DGS. read Granules file
#====================
if options.granules_file:
    try:
        with open(options.granules_file) as f:
            granles_list = f.readlines()
        # Remove whitespace characters like `\n` at the end of each line
        granles_list = [x.strip() for x in granles_list]
        f.close()
    except :
        print "error with granules file"
        sys.exit(-3)

#==================================================
#      prepare wget command line to search catalog
#==================================================
if os.path.exists('query_results.xml'):
    os.remove('query_results.xml')



if options.downloader=="aria2":
    wg='aria2c --check-certificate=false'
    auth='--http-user="%s" --http-passwd="%s"'%(account,passwd)
    search_output=" --continue -o query_results.xml"
    wg_opt=" -o "
    if sys.platform.startswith('linux') or sys.platform.startswith('darwin'):
        value="\$value"
    else:
        value="$value"
else :
    wg="wget --no-check-certificate"
    auth='--user="%s" --password="%s"'%(account,passwd)
    search_output="--output-document=query_results.xml"
    wg_opt=" --continue --output-document="
    if sys.platform.startswith('linux') or sys.platform.startswith('darwin'):
        value="\\$value"
    else:
        value="$value"

producttype = None
if options.sentinel == "S2":
    if options.level == "L1C":
        producttype = "S2MSI1C"
    elif options.level == "L2A":
        producttype = "S2MSI2Ap"

if geom=='point':
    if sys.platform.startswith('linux') or sys.platform.startswith('darwin'):
        query_geom='footprint:\\"Intersects(%f,%f)\\"'%(options.lat,options.lon)
    else :
        query_geom='footprint:"Intersects(%f,%f)"'%(options.lat,options.lon)
	
elif geom=='rectangle':
    if sys.platform.startswith('linux') or sys.platform.startswith('darwin'):
        query_geom='footprint:\\"Intersects(POLYGON(({lonmin} {latmin}, {lonmax} {latmin}, {lonmax} {latmax}, {lonmin} {latmax},{lonmin} {latmin})))\\"'.format(latmin=options.latmin,latmax=options.latmax,lonmin=options.lonmin,lonmax=options.lonmax)
    else :
        query_geom='footprint:"Intersects(POLYGON(({lonmin} {latmin}, {lonmax} {latmin}, {lonmax} {latmax}, {lonmin} {latmax},{lonmin} {latmin})))"'.format(latmin=options.latmin,latmax=options.latmax,lonmin=options.lonmin,lonmax=options.lonmax)
    
# add code
elif geom == 'polygon':
    # ==================================================
    # Read polygon from WKT file
    # ==================================================
    wktfilepath = options.polygon
    wktfile = open(wktfilepath, "r")
    wktpolygonstr = wktfile.read()
    if sys.platform.startswith('linux') or sys.platform.startswith('darwin'):
        query_geom = 'footprint:\\"Intersects(' + wktpolygonstr.strip() + ')\\"'
    else:
        query_geom = 'footprint:"Intersects(' + wktpolygonstr.strip() + ')"'
# end add code

if options.orbit==None:
    query='%s filename:%s*'%(query_geom,options.sentinel)
else :
    query='%s filename:%s*R%03d*'%(query_geom,options.sentinel,options.orbit)


# ingestion date
if options.start_ingest_date!=None:    
    start_ingest_date=options.start_ingest_date+"T00:00:00.000Z"
else :
    start_ingest_date="2015-06-23T00:00:00.000Z"

if options.end_ingest_date!=None:
    end_ingest_date=options.end_ingest_date+"T23:59:50.000Z"
else:
    end_ingest_date="NOW"

if options.start_ingest_date!=None or options.end_ingest_date!=None:
    query_date=" ingestiondate:[%s TO %s]"%(start_ingest_date,end_ingest_date)
    query=query+query_date

if producttype !=None:
    query_producttype=" producttype:%s "%producttype
    query=query+query_producttype

# acquisition date    

if options.start_date!=None:    
    start_date=options.start_date
else :
    start_date="20150613" #Sentinel-2 launch date

# DGS:
if options.time_range:
    try:
        delta_days = int(options.time_range)
        today = date.today()
        start_date = (today - datetime.timedelta(days=delta_days)).strftime(format='%Y%m%d')
    except:
        print "error with time_range"
        sys.exit(-4)
    
if options.end_date!=None:
    end_date=options.end_date
else:
    end_date=date.today().strftime(format='%Y%m%d') 

if options.MaxRecords > 100:
    requests_needed = math.ceil(options.MaxRecords / 100.0)
    request_list = []
    current_records = 0
    for i in range(int(requests_needed)):
        if (i+1)*100 > options.MaxRecords:
            request_list.append('%s %s %s "%s%s&rows=%d&start=%d"' % (wg, auth, search_output, url_search, query, options.MaxRecords % 100, i * 100))
        else:
            request_list.append('%s %s %s "%s%s&rows=%d&start=%d"'%(wg,auth,search_output,url_search,query,100,i*100))
else:
    commande_wget='%s %s %s "%s%s&rows=%d"'%(wg,auth,search_output,url_search,query,options.MaxRecords)
    print commande_wget
    request_list = [commande_wget]


#======================================
# DGS: Create catalog connection
#======================================
# catalog = catalog_manager.CatalogManager(catalog_db, user=catalog_user, password=catalog_pass, host=catalog_host, port=catalog_port)

config_file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir, 'config.txt')
catalog = catalog_manager.CatalogManager.from_file(config_file_path)

#=======================
# parse catalog output
#=======================
for i in range(len(request_list)):
    os.system(request_list[i])
    xml=minidom.parse("query_results.xml")
    products=xml.getElementsByTagName("entry")
    for prod in products:
        ident=prod.getElementsByTagName("id")[0].firstChild.data
        link=prod.getElementsByTagName("link")[0].attributes.items()[0][1]
        #to avoid wget to remove $ special character
        link=link.replace('$value',value)


        for node in prod.getElementsByTagName("str"):
            (name,field)=node.attributes.items()[0]
            if field=="filename":
                filename= str(node.toxml()).split('>')[1].split('<')[0]   #ugly, but minidom is not straightforward
            elif field == "footprint":
                footprint = str(node.toxml()).split('>')[1].split('<')[0]
            elif field == "relativeorbitnumber":
                relativeorbitnumber = str(node.toxml()).split('>')[1].split('<')[0]
            elif field == "platformserialidentifier":
                platformserialidentifier = str(node.toxml()).split('>')[1].split('<')[0]
            elif field == "identifier":
                identifier = str(node.toxml()).split('>')[1].split('<')[0]
                granule_id = identifier.split('_')[5]

        for node in prod.getElementsByTagName("date"):
            (name, field) = node.attributes.items()[0]
            if field == "ingestiondate":
                ingestiondate = str(node.toxml()).split('>')[1].split('<')[0]
            elif field == "beginposition":
                beginposition = str(node.toxml()).split('>')[1].split('<')[0]

        for node in prod.getElementsByTagName("int"):
            (name, field) = node.attributes.items()[0]
            if field == "relativeorbitnumber":
                relativeorbitnumber = int(str(node.toxml()).split('>')[1].split('<')[0])

        #test if product is within the requested time period
        if options.sentinel.startswith("S2"):
            if len(filename.split("_")) == 7:
                date_prod=filename.split('_')[-1][:8]
            else:
                date_prod = filename.split('_')[7][1:9]
        elif  options.sentinel.startswith("S1"):
            date_prod=filename.split('_')[5][0:8]
        else :
            print "Please choose either S1 or S2"
            sys.exit(-1)

        if date_prod>=start_date and date_prod<=end_date:

            if options.check_notdownloaded==False:
                # print what has been found
                print "\n==============================================="
                print date_prod,start_date,end_date
                print filename
                print link
            if options.dhus==True:
                link=link.replace("apihub","dhus")

            cloud=0
            if options.sentinel.find("S2") >=0 :
                for node in prod.getElementsByTagName("double"):
                    (name,field)=node.attributes.items()[0]
                    if field=="cloudcoverpercentage":
                        cloud=float((node.toxml()).split('>')[1].split('<')[0])
                        if options.check_notdownloaded == False:
                            print "cloud percentage = %5.2f %%"%cloud
            if options.check_notdownloaded == False:
                print "===============================================\n"


            #==================================download  whole product
            if( cloud<options.max_cloud or (options.sentinel.find("S1")>=0)) and options.tile==None\
                    and (not options.granules_file or granule_id in granles_list):
                if not catalog.exist_product(identifier): #DGS
                    if options.check_notdownloaded==True:
                        print '%s NOT in catalog.' %identifier
                        continue

                    commande_wget='%s %s %s%s/%s "%s"'%(wg,auth,wg_opt,options.write_dir,filename+".zip",link)
                    #do not download the product if it was already downloaded and unzipped, or if no_download option was selected.
                    unzipped_file_exists= os.path.exists(("%s/%s")%(options.write_dir,filename))
                    print commande_wget
                    # DGS:
                    if options.write_dir:
                        file_path = os.path.join(options.write_dir, filename + '.zip')
                    else:
                        file_path = os.path.join(os.path.curdir, filename + '.zip')
                    if unzipped_file_exists==False and options.no_download==False:
                        os.system(commande_wget)
                        #DGS: Varificaci�n del fichero descargado
                        if os.path.exists(file_path):
                            with ZipFile(file_path, 'r') as myzip:
                                if myzip.testzip() is None:
                                    #DGS: Ingest product in catalog db
                                    catalog.ingest_original_product(file_path,
                                                                            ingestiondate,
                                                                            beginposition,
                                                                            platformserialidentifier,
                                                                            footprint,
                                                                            cloud,
                                                                            relativeorbitnumber,
                                                                            granule_id,
                                                                            identifier,
                                                                            options.workspace)
                                    #DGS: Execute post-download script:
                                    if options.post_download_script:
                                        # cmd = [
                                        #     options.postprocessing,
                                        #     '-f', os.path.join(os.path.join(options.write_dir, "downloaded"),
                                        #                        filename + ".zip")
                                        # ]
                                        cmd = [
                                            options.post_download_script,
                                            '-f', os.path.join(options.write_dir, filename + ".zip")
                                        ]
                                        post_params_list = options.post_download_params.split(" ")
                                        cmd += post_params_list + ['--ingest_id', identifier]
                                        stdfile = open('std.out', 'a')
                                        errfile = open('err.out', 'a')
                                        p = call(cmd, shell=False)
                                        # p = call(cmd, shell=False, stdin=None, stdout=stdfile, stderr=errfile)
                                        # p = Popen(cmd, shell=False, stdin=None, stdout=stdfile, stderr=errfile,
                                        #  close_fds=True)

                    else :
                        print unzipped_file_exists, options.no_download
                        # DGS - BORRAR:
                        catalog.ingest_original_product(file_path,
                                                                ingestiondate,
                                                                beginposition,
                                                                platformserialidentifier,
                                                                footprint,
                                                                cloud,
                                                                relativeorbitnumber,
                                                                granule_id,
                                                                identifier,
                                                                options.workspace)

        # download only one tile, file by file.
        elif options.tile!=None:
                #do not download the product if the tile is already downloaded.
                unzipped_tile_exists = False
                if os.path.exists(("%s/%s")%(options.write_dir,filename)):
                    if os.path.exists(("%s/%s/%s")%(options.write_dir,filename,"GRANULE")):
                        entries = os.listdir(("%s/%s/%s")%(options.write_dir,filename,"GRANULE"))
                        for entry in entries:
                            entry_split = entry.split("_")
                            if len(entry_split) == 11:
                                tile_identifier = "T"+options.tile
                                if tile_identifier in entry_split:
                                    unzipped_tile_exists= True

                if unzipped_tile_exists or options.no_download:
                    print unzipped_tile_exists, options.no_download
                    print "tile already exists or option -n is set, skipping this download"
                else:
                    #find URL of header file
                    url_file_dir=link.replace(value,"Nodes('%s')/Nodes"%(filename))
                    commande_wget='%s %s %s%s "%s"'%(wg,auth,wg_opt,'file_dir.xml',url_file_dir)
                    os.system(commande_wget)
                    while os.path.getsize('file_dir.xml')==0 : #in case of "bad gateway error"
                        os.system(commande_wget)
                    urls,types,names=get_elements('file_dir.xml')
                    #search for the xml file
                    for i in range(len(urls)):
                        if names[i].find('SAFL1C')>0:
                            xml=names[i]
                            url_header=urls[i]


                    #retrieve list of granules
                    url_granule_dir=link.replace(value,"Nodes('%s')/Nodes('GRANULE')/Nodes"%(filename))
                    print url_granule_dir
                    commande_wget='%s %s %s%s "%s"'%(wg,auth,wg_opt,'granule_dir.xml',url_granule_dir)
                    os.system(commande_wget)
                    while os.path.getsize('granule_dir.xml')==0 : #in case of "bad gateway error"
                        os.system(commande_wget)
                    urls,types,names=get_elements('granule_dir.xml')
                    granule=None
                    #search for the tile
                    for i in range(len(urls)):
                        if names[i].find(options.tile)>0:
                            granule=names[i]
                    if granule==None:
                        print "========================================================================"
                        print "Tile %s is not available within product (check coordinates or tile name)"%options.tile
                        print "========================================================================"
                    else :
                        #create product directory
                        product_dir_name=("%s/%s"%(options.write_dir,filename))
                        if not(os.path.exists(product_dir_name)) :
                            os.mkdir(product_dir_name)
                        #create tile directory
                        granule_dir_name=("%s/%s"%(product_dir_name,'GRANULE'))
                        if not(os.path.exists(granule_dir_name)) :
                            os.mkdir(granule_dir_name)
                        #create tile directory

                        nom_rep_tuile=("%s/%s"%(granule_dir_name,granule))
                        if not(os.path.exists(nom_rep_tuile)) :
                            os.mkdir(nom_rep_tuile)
                        # download product header file
                        print "############################################### header"
                        url_header=url_header.replace("eu/odata","eu/apihub/odata")
                        commande_wget='%s %s %s%s "%s"'%(wg,auth,wg_opt,product_dir_name+'/'+xml,url_header+"/"+value)
                        print commande_wget
                        os.system(commande_wget)
                        while os.path.getsize(product_dir_name+'/'+xml)==0 : #in case of "bad gateway error"
                            os.system(commande_wget)
                        #download INSPIRE.xml
                        url_inspire=link.replace(value,"Nodes('%s')/Nodes('INSPIRE.xml')/"%(filename))
                        commande_wget='%s %s %s%s "%s"'%(wg,auth,wg_opt,product_dir_name+'/'+"INSPIRE.xml",url_inspire+"/"+value)

                        print commande_wget
                        os.system(commande_wget)
                        while os.path.getsize(product_dir_name+'/'+"INSPIRE.xml")==0 : #in case of "bad gateway error"
                            os.system(commande_wget)

                        #download manifest.safe
                        url_manifest=link.replace(value,"Nodes('%s')/Nodes('manifest.safe')/"%(filename))
                        commande_wget='%s %s %s%s "%s"'%(wg,auth,wg_opt,product_dir_name+'/'+"manifest.safe",url_manifest+"/"+value)
                        print commande_wget
                        os.system(commande_wget)
                        while os.path.getsize(product_dir_name+'/'+"manifest.safe")==0 : #in case of "bad gateway error"
                            os.system(commande_wget)

                        # rep_info
                        url_rep_info_dir=link.replace(value,"Nodes('%s')/Nodes('rep_info')/Nodes"%(filename))
                        get_dir('rep_info',url_rep_info_dir,product_dir_name,wg,auth,wg_opt,value)

                        # HTML
                        url_html_dir=link.replace(value,"Nodes('%s')/Nodes('HTML')/Nodes"%(filename))
                        get_dir('HTML',url_html_dir,product_dir_name,wg,auth,wg_opt,value)

                        # AUX_DATA
                        url_auxdata_dir=link.replace(value,"Nodes('%s')/Nodes('AUX_DATA')/Nodes"%(filename))
                        get_dir('AUX_DATA',url_auxdata_dir,product_dir_name,wg,auth,wg_opt,value)

                        # DATASTRIP
                        url_datastrip_dir=link.replace(value,"Nodes('%s')/Nodes('DATASTRIP')/Nodes"%(filename))
                        get_dir('DATASTRIP',url_datastrip_dir,product_dir_name,wg,auth,wg_opt,value)


                        # granule files
                        url_granule="%s('%s')/Nodes"%(url_granule_dir,granule)
                        commande_wget='%s %s %s%s "%s"'%(wg,auth,wg_opt,'granule.xml',url_granule)
                        print commande_wget
                        os.system(commande_wget)
                        while os.path.getsize("granule.xml")==0 : #in case of "bad gateway error"
                            os.system(commande_wget)
                        download_tree(nom_rep_tuile,"granule.xml",wg,auth,wg_opt,value)

