# HidroMap
A tool for irrigation monitoring and management using free satellite imagery.

This is an open source tool organized in two different modules, desktop-GIS and web-GIS, with complementary roles and functionalities and based on a PostgreSQL/PostGIS database. Through an effective combination of algorithms and methodologies for downloading, storing and processing satellite images within field data provided by the River Surveillance Agency (RSA) and complex databases from the Hydrological Planning Office (HPO), HidroMap allows managing unregulated irrigation, temporally monitoring irrigated plots and optimizing available fluvial surveillance resources in the Duero river basin.

The tool was developed with Python programming language for QGIS (PyQGIS). It allows to automatically perform three different processes: (i) detecting those agricultural plots with non-regulated irrigation activity, (ii) prioritizing them based on different parameters, prevailing larger areas and longer distance to wells with rights and (iii) estimating the total irrigated area and agricultural plots involved for an area of interest.

# eo_download_processing
Python scripts for automatic download and preprocessing of Earth observation images from both Landsat-8 and Sentinel-2 platforms.
Scripts based on [olivierhagolle](https://github.com/olivierhagolle) [LANDSAT-Download](https://github.com/olivierhagolle/LANDSAT-Download) and [Sentinel-download](https://github.com/olivierhagolle/Sentinel-download).

# Hidromap_data_model.sql
PostgreSQL/PostGIS database consumed and fed by HidroMap model. Database here consists of the main structure (fields, relations of tables and triggers for cases prioritization). Data not included.

# quick_process.py
This process developed with PyQGIS presents the main algorithm of the tool. It took advantage of all the available geo-processing tools in QGIS (gdal and SAGA) since they made spatial intersections between several layers and surface calculations. Either an area of interest defined in a shapefile or a municipality selected from 2067 in the database was the input for starting the algorithm process within the NDVI image. It also allowed taking specific request from the user such as the NDVI and plots surface thresholds. First, the total irrigated surface and number of plots involved could be obtained. Then, SAGA spatial difference was the main step; processing intersections with several layers provided by the Duero Hydrographic Basin and kept in the database up-to-date. Moreover, this process step was enhanced in order to make geospatial differences one by one, taking out all the invalid and incorrect geometries per intersection. Final cases shapefile is obtained after geometric validation, loading all the data from SIGPAC and fluvial guard sectors, filtering forest or non-agricultural areas (if requested) and prioritizing the plots. Outputs from every sub-process may be added to QGIS map canvas with a settled style so the user was able to analyse every result.

# AutomaticIrrigatedArea
This processing model estimates total irrigated area and agricultural plots involved in an area of interest during a period of time by selecting HidroMap results from different dates.
