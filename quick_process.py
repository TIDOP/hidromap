# -*- coding: utf-8 -*-
"""
/******************************************************************************
    Script escrito en lenguaje PyQGIS para la explotación de datos de Observa-
    ción de la Tierra del proyecto HidroMap: generación de casos y estima-
    ción de superficies regadas
    -------------------
        begin:      20-01-2018
        authors:    Laura Piedelobo Martín
        copyright:  (C)2017
        emails:
 ******************************************************************************/

/******************************************************************************
 *   This program is free software; you can redistribute it and/or modify     *
 *   it under the terms of the GNU General Public License as published by     *
 *   the Free Software Foundation; either version 2 of the License, or        *
 *   (at your option) any later version.                                      *
  *****************************************************************************/
"""

# Import the PyQt and QGIS libraries
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import QgsMessageBar, QgsMapCanvas

# other imports
import os
import processing
import time

# import self classes
from .. progressDialogDlg.progress_dialog_dlg import * #panel progress dialog
from .. import config as c


class QuickProcess():
    """
    Clase para el procesamiento automático de detección de casos y estimación rápida de superficie regada.
    """
    def __init__(self,
                 iface,
                 pg_dialog,
                 uri,
                 plugin_dir,
                 str_path_workspace,
                 is_generacion_casos,
                 is_estimacion_sup_regada,
                 is_aoi_shapefile,
                 str_path_shapefile_aoi,
                 is_aoi_cod_municipio,
                 str_cod_municipio,
                 str_path_ndvi_image,
                 is_remove_forest_areas,
                 float_umbral_ndvi,
                 float_umbral_area,
                 num_cases_per_aoi,
                 float_umbral_area_artificios):
        """
        Constructor de la clase
        """
        self.iface = iface
        self.uri = uri
        self.plugin_dir = plugin_dir
        self.str_path_workspace = str_path_workspace
        self.is_generacion_casos = is_generacion_casos
        self.is_estimacion_sup_regada = is_estimacion_sup_regada
        self.is_aoi_shapefile = is_aoi_shapefile
        self.str_path_shapefile_aoi = str_path_shapefile_aoi
        self.is_aoi_cod_municipio = is_aoi_cod_municipio
        self.str_cod_municipio = str_cod_municipio
        self.str_path_ndvi_image = str_path_ndvi_image
        self.is_remove_forest_areas = is_remove_forest_areas
        self.float_umbral_ndvi = float_umbral_ndvi
        self.float_umbral_area = float_umbral_area
        self.num_cases_per_aoi = num_cases_per_aoi
        self.float_umbral_area_artificios = float_umbral_area_artificios
        self.pg_dialog = pg_dialog

        self.pg_dialog.setModal(True)
        self.pg_dialog.show()  # show the dialog
        self.pg_dialog.activateWindow()

        self.str_ndvi_image_filename = os.path.basename(self.str_path_ndvi_image)

    def check_normcase_path(self,
                            path_normcase):
        """
        Brief: comprueba la existencia de la una ruta y devuelve el correspondiente booleano
        :param path_normcase: ruta normalizada a comprobar
        :type path_normcase: str
        :return: Devuelve valor verdadero si la ruta existe, falso en caso contrario
        :rtype: bool
        """
        if not os.path.exists(path_normcase):
            title = c.CONST_REVELADUERO_TITLE_VERSION
            str_msg = "No existe la ruta: " + path_normcase
            QMessageBox.warning(self.iface.mainWindow(),
                                title,
                                str_msg)
            return False
        return True

    def get_recintos_sigpac_postgis_layer(self,
                                          str_cod_municipio,
                                          str_schema_sigpac,
                                          str_column_geom_name,
                                          uri,
                                          str_path_simbolgy=False,
                                          str_node_group=False):
        """
        Brief: Obtiene la capas de recintos del SIGPAC
        """
        str_cod_prov = str_cod_municipio[0:2]
        str_muni = str_cod_municipio[2:5]
        str_muni_sigpac_postgis_tablename = "tm_" + str_cod_prov + "_" + str_muni
        cartodroid_recintos_tm_sigpac_vlayer = self.load_to_qgis_postgis_layer(str_schema_sigpac,
                                                                               str_muni_sigpac_postgis_tablename,
                                                                               str_column_geom_name,
                                                                               uri,
                                                                               str_path_qml_simbology=str_path_simbolgy,
                                                                               node_group=str_node_group)
        return cartodroid_recintos_tm_sigpac_vlayer

    def improved_spatial_difference_algorithm(self,
                                              shp_name,
                                              str_path_output_workspace,
                                              regadio_probable_vlayer,
                                              mirameduero_vlayer,
                                              node_group_output_subprocess_layers):
        """
        Brief: Algoritmo de diferecia espacial SAGA mejorado
        :param shp_name:
        :param str_path_output_workspace:
        :param regadio_probable_vlayer:
        :param mirameduero_vlayer:
        :param node_group_output_subprocess_layers:
        :return:
        """
        self.pg_dialog.clear_text(1)
        self.pg_dialog.enabled_suprocess(True)
        str_secondary_process_title = u'Diferencia espacial SAGA mejorada'
        self.pg_dialog.set_title_process(1, str_secondary_process_title)
        QtCore.QCoreApplication.processEvents()

        # Diferencia SAGA **********************************************************************************************
        self.pg_dialog.insert_text(1, u'1.- Regadío probable - capa MírameDuero = Diferencia SAGA')
        self.file_report.write(u'\t1.- Regadío probable - capa MírameDuero = Diferencia SAGA' + "\n")
        QtCore.QCoreApplication.processEvents()
        process_time_start = time.time()

        str_output_diffsaga_vlayer_name = shp_name + "_01_difsaga"
        str_output_diffsaga_shapefile = str_output_diffsaga_vlayer_name + ".shp"
        str_output_diffsaga_path = os.path.normcase(os.path.join(str_path_output_workspace,
                                                                 str_output_diffsaga_shapefile))
        outputs_SAGADIFFERENCE = processing.runalg('saga:difference',
                                                   regadio_probable_vlayer,
                                                   mirameduero_vlayer,
                                                   True,
                                                   str_output_diffsaga_path)
        vlayer_difsaga = QgsVectorLayer(str_output_diffsaga_path,
                                        str_output_diffsaga_vlayer_name,
                                        "ogr")
        if not self.load_to_qgis_vlayer(vlayer_difsaga, node_group=node_group_output_subprocess_layers):
            return False

        process_time_end = time.time()
        process_time_total = process_time_end - process_time_start
        self.pg_dialog.insert_text(1, u'  - Tiempo ejecución: ' + str(round(process_time_total)) + " s.")
        self.file_report.write(u'\t  - Tiempo ejecución: ' + str(round(process_time_total)) + " s." + "\n")
        QtCore.QCoreApplication.processEvents()
        # Cálculo del gid **********************************************************************************************
        str_gid_fieldname = "gid_delet"
        self.pg_dialog.insert_text(1, u'2.- Cálculo de identificador unívoco [' + str_gid_fieldname + ']')
        self.file_report.write(u'\t2.- Cálculo de identificador unívoco [' + str_gid_fieldname + ']'+ "\n")
        QtCore.QCoreApplication.processEvents()
        process_time_start = time.time()

        str_output_diffsaga_gid_vlayer_name = shp_name + "_02_difsaga_gid"
        str_output_diffsaga_gid_shapefile = str_output_diffsaga_gid_vlayer_name + ".shp"
        str_output_diffsaga_gid_path = os.path.normcase(os.path.join(str_path_output_workspace,
                                                                     str_output_diffsaga_gid_shapefile))
        outputs_QGISFIELDCALCULATOR_1 = processing.runalg('qgis:fieldcalculator',
                                                          vlayer_difsaga,
                                                          str_gid_fieldname,
                                                          1,
                                                          20.0,
                                                          3.0,
                                                          True,
                                                          '$id',
                                                          str_output_diffsaga_gid_path)
        vlayer_diffsaga_gid = QgsVectorLayer(str_output_diffsaga_gid_path,
                                             str_output_diffsaga_gid_vlayer_name,
                                             "ogr")
        if not self.load_to_qgis_vlayer(vlayer_diffsaga_gid, node_group=node_group_output_subprocess_layers):
            return False

        process_time_end = time.time()
        process_time_total = process_time_end - process_time_start
        self.pg_dialog.insert_text(1, u'  - Tiempo ejecución: ' + str(round(process_time_total)) + " s.")
        self.file_report.write(u'\t  - Tiempo ejecución: ' + str(round(process_time_total)) + " s." + "\n")
        QtCore.QCoreApplication.processEvents()
        # Cálculo del área *********************************************************************************************
        str_area_dif_fieldname = "area_dif"
        self.pg_dialog.insert_text(1, u'3.- Cálculo de área [' + str_area_dif_fieldname + ']')
        self.file_report.write(u'\t3.- Cálculo de área [' + str_area_dif_fieldname + ']' + "\n")
        QtCore.QCoreApplication.processEvents()
        process_time_start = time.time()

        str_output_diffsaga_area_vlayer_name = shp_name + "_03_difsaga_area"
        str_output_diffsaga_area_shapefile = str_output_diffsaga_area_vlayer_name + ".shp"
        str_output_diffsaga_area_path = os.path.normcase(os.path.join(str_path_output_workspace,
                                                                      str_output_diffsaga_area_shapefile))
        outputs_QGISFIELDCALCULATOR_2 = processing.runalg('qgis:fieldcalculator',
                                                          vlayer_diffsaga_gid,
                                                          str_area_dif_fieldname,
                                                          0,
                                                          20.0,
                                                          4.0,
                                                          True,
                                                          '$area/10000',
                                                          str_output_diffsaga_area_path)
        vlayer_diffsaga_area = QgsVectorLayer(str_output_diffsaga_area_path,
                                              str_output_diffsaga_area_vlayer_name,
                                              "ogr")
        if not self.load_to_qgis_vlayer(vlayer_diffsaga_area, node_group=node_group_output_subprocess_layers):
            return False

        process_time_end = time.time()
        process_time_total = process_time_end - process_time_start
        self.pg_dialog.insert_text(1, u'  - Tiempo ejecución: ' + str(round(process_time_total)) + " s.")
        self.file_report.write(u'\t  - Tiempo ejecución: ' + str(round(process_time_total)) + " s." + "\n")
        QtCore.QCoreApplication.processEvents()
        # Intersección resultado ***************************************************************************************
        self.pg_dialog.insert_text(1, u'4.- Intersección diferencia SAGA x capa MírameDuero')
        self.file_report.write(u'\t4.- Intersección diferencia SAGA x capa MírameDuero' + "\n")
        QtCore.QCoreApplication.processEvents()

        process_time_start = time.time()
        str_output_intersect_vlayer_name = shp_name + "_04_interseccion"
        str_output_intersect_shapefile = str_output_intersect_vlayer_name + ".shp"
        str_output_intersect_area_path = os.path.normcase(os.path.join(str_path_output_workspace,
                                                                       str_output_intersect_shapefile))
        outputs_SAGAINTERSECT = processing.runalg('saga:intersect',
                                                  vlayer_diffsaga_area,
                                                  mirameduero_vlayer,
                                                  True,
                                                  str_output_intersect_area_path)
        vlayer_intersect = QgsVectorLayer(str_output_intersect_area_path,
                                          str_output_intersect_vlayer_name,
                                          "ogr")
        if not self.load_to_qgis_vlayer(vlayer_intersect, node_group=node_group_output_subprocess_layers):
            return False

        str_msg_num_features = u'  - Diferencia SAGA [' + str(vlayer_diffsaga_area.featureCount()) + "] x "
        str_msg_num_features += u'capa MírameDuero [' + str(mirameduero_vlayer.featureCount()) + "] = "
        str_msg_num_features += u'Intersección [' + str(vlayer_intersect.featureCount()) + "]"
        self.pg_dialog.insert_text(1, str_msg_num_features)
        self.file_report.write("\t" + str_msg_num_features + "\n")

        process_time_end = time.time()
        process_time_total = process_time_end - process_time_start
        self.pg_dialog.insert_text(1, u'  - Tiempo ejecución: ' + str(round(process_time_total)) + " s.")
        self.file_report.write(u'\t  - Tiempo ejecución: ' + str(round(process_time_total)) + " s." + "\n")
        QtCore.QCoreApplication.processEvents()
        # Cálculo del área interser*************************************************************************************
        str_area_interseccion_fieldname = "area_inte"
        self.pg_dialog.insert_text(1, u'5.- Cálculo de área intersección [' + str_area_interseccion_fieldname + ']')
        self.file_report.write(u'\t5.- Cálculo de área intersección [' + str_area_interseccion_fieldname + ']' + "\n")
        QtCore.QCoreApplication.processEvents()
        process_time_start = time.time()

        str_output_interseccion_area_vlayer_name = shp_name + "_05_interseccion_area"
        str_output_interseccion_area_shapefile = str_output_interseccion_area_vlayer_name + ".shp"
        str_output_interseccion_area_path = os.path.normcase(os.path.join(str_path_output_workspace,
                                                                      str_output_interseccion_area_shapefile))
        outputs_QGISFIELDCALCULATOR_2 = processing.runalg('qgis:fieldcalculator',
                                                          vlayer_intersect,
                                                          str_area_interseccion_fieldname,
                                                          0,
                                                          20.0,
                                                          4.0,
                                                          True,
                                                          '$area/10000',
                                                          str_output_interseccion_area_path)
        vlayer_interseccion_area = QgsVectorLayer(str_output_interseccion_area_path,
                                                  str_output_interseccion_area_vlayer_name,
                                                  "ogr")
        if not self.load_to_qgis_vlayer(vlayer_interseccion_area, node_group=node_group_output_subprocess_layers):
            return False


        process_time_end = time.time()
        process_time_total = process_time_end - process_time_start
        self.pg_dialog.insert_text(1, u'  - Tiempo ejecución: ' + str(round(process_time_total)) + " s.")
        self.file_report.write(u'\t  - Tiempo ejecución: ' + str(round(process_time_total)) + " s." + "\n")
        QtCore.QCoreApplication.processEvents()
        # Creación de lista de features a eliminar *********************************************************************
        self.pg_dialog.insert_text(1, u'5.- Creando lista de features a eliminar')
        self.file_report.write(u'\t5.- Creando lista de features a eliminar' + "\n")
        QtCore.QCoreApplication.processEvents()
        process_time_start = time.time()

        list_gids_to_delete = [] # inicializa lista de features a eliminar
        iter_vlayer_intersect_area = vlayer_interseccion_area.getFeatures()
        for feature in iter_vlayer_intersect_area:
            area_interseccion = feature[str_area_interseccion_fieldname]
            if area_interseccion > self.float_umbral_area_artificios:
                list_gids_to_delete.append(feature[str_gid_fieldname])
        #print list_gids_to_delete

        process_time_end = time.time()
        process_time_total = process_time_end - process_time_start
        self.pg_dialog.insert_text(1, u'  - Tiempo ejecución: ' + str(round(process_time_total)) + " s.")
        self.file_report.write(u'\t  - Tiempo ejecución: ' + str(round(process_time_total)) + " s." + "\n")
        QtCore.QCoreApplication.processEvents()
        # Eliminación de features enteramente contenidas ***************************************************************
        self.pg_dialog.insert_text(1, u'6.- Eliminando features enteramente contenidas en capa MírameDuero')
        self.file_report.write( u'\t6.- Eliminando features enteramente contenidas en capa MírameDuero' + "\n")
        QtCore.QCoreApplication.processEvents()
        process_time_start = time.time()

        vlayer_diffsaga_area.startEditing()
        iter_vlayer_diffsaga_area = vlayer_diffsaga_area.getFeatures()
        for feature in iter_vlayer_diffsaga_area:
            current_gid = feature[str_gid_fieldname]
            if current_gid in list_gids_to_delete:
                vlayer_diffsaga_area.deleteFeature(current_gid)
        vlayer_diffsaga_area.commitChanges()

        process_time_end = time.time()
        process_time_total = process_time_end - process_time_start
        self.pg_dialog.insert_text(1, u'  - Tiempo ejecución: ' + str(round(process_time_total)) + " s.")
        self.file_report.write(u'\t  - Tiempo ejecución: ' + str(round(process_time_total)) + " s." + "\n")
        QtCore.QCoreApplication.processEvents()
        # Eliminación de campos auxiliares *****************************************************************************
        self.pg_dialog.insert_text(1, u'7.- Eliminando campos auxiliares de cálculo')
        self.file_report.write(u'\t7.- Eliminando campos auxiliares de cálculo' + "\n")
        QtCore.QCoreApplication.processEvents()

        idx_gid = vlayer_diffsaga_area.fieldNameIndex(str_gid_fieldname)
        idx_area = vlayer_diffsaga_area.fieldNameIndex(str_area_dif_fieldname)
        vlayer_diffsaga_area.dataProvider().deleteAttributes([idx_gid, idx_area])
        vlayer_diffsaga_area.updateFields()

        self.pg_dialog.enabled_suprocess(False)
        return vlayer_diffsaga_area

    def load_to_qgis_and_get_rlayer(self,
                                    str_rlayer_path,
                                    str_path_qml_simbology=False,
                                    node_group=False):
        """
        Brief: carga en QGIS capas raster
        :param str_rlayer_path: ruta del fichero raster
        :type str_rlayer_path: str
        :param load_to_qgis: parámetro opcional. ¿cargar la capa en el ToC?
        :type load_to_qgis: bool
        :param str_path_qml_simbology: ruta del fichero formato qml de simbología de QGIS
        :type str_path_qml_simbology: str
        :param node_group:
        :return:
        """
        # get rlayer
        file_info = QFileInfo(str_rlayer_path)  # class provides system-independent file information
        base_name = file_info.baseName()
        rlayer = QgsRasterLayer(str_rlayer_path,
                                base_name)
        if not rlayer.isValid():
            print "Raster layer " + str_rlayer_path + " failed to load"
            print "load_to_qgis_and_get_rlayer"
            return False

        if node_group:
            QgsMapLayerRegistry.instance().addMapLayer(rlayer,
                                                       False)
            node_layer = node_group.insertLayer(0, rlayer)
        else:
            QgsMapLayerRegistry.instance().addMapLayer(rlayer,
                                                       True)

        if str_path_qml_simbology:
            rlayer.loadNamedStyle(str_path_qml_simbology)
            self.iface.legendInterface().refreshLayerSymbology(rlayer)
            self.iface.mapCanvas().refresh()

        return rlayer

    def load_to_qgis_vlayer(self,
                            qgs_vlayer,
                            str_path_qml_simbology=False,
                            node_group=False):
        """
        Brief: carga en QGIS capas vectoriales
        """
        if not qgs_vlayer.isValid():
            print "Vector layer failed to load "
            print "load_to_qgis_vlayer"
            return False

        if node_group:
            QgsMapLayerRegistry.instance().addMapLayer(qgs_vlayer,
                                                       False)
            node_layer = node_group.insertLayer(0,
                                                qgs_vlayer)
        else:
            QgsMapLayerRegistry.instance().addMapLayer(qgs_vlayer,
                                                       True)

        if str_path_qml_simbology:
            qgs_vlayer.loadNamedStyle(str_path_qml_simbology)
            qgs_vlayer.updateExtents()
            self.iface.legendInterface().refreshLayerSymbology(qgs_vlayer)
            self.iface.mapCanvas().refresh()
        return True

    def load_to_qgis_postgis_layer(self,
                                   str_schema,
                                   str_tablename,
                                   str_column_geometry_name,
                                   uri,
                                   str_path_qml_simbology=False,
                                   node_group=False):
        """
        Brief: carga en QGIS capas PostGIS
        """
        uri.setDataSource(str_schema,
                          str_tablename,
                          str_column_geometry_name)

        postgis_vlayer = QgsVectorLayer(uri.uri(False),
                                        str_tablename,
                                        "postgres")

        self.load_to_qgis_vlayer(postgis_vlayer,
                                 str_path_qml_simbology=str_path_qml_simbology,
                                 node_group=node_group)

        return postgis_vlayer

    def remove_group_gis_layers(self,
                                str_name_group):
        """
        Brief: elimina un grupo de capas de la TOC
        :param str_name_group: nombre del grupo
        :type str_name_group: str
        """
        # Return pointer to the root (invisible) node of the project's layer tree
        root = QgsProject.instance().layerTreeRoot()

        # Find group node with specified name. Searches recursively the whole sub-tree. Devuelve un QgsLayerTreeGroup
        qgs_layer_tree_group_to_remove = root.findGroup(str_name_group)

        if qgs_layer_tree_group_to_remove is not None:
            # Remove a child node from this group. The node will be deleted.
            root.removeChildNode(qgs_layer_tree_group_to_remove)

    def process(self):
        """
        Método para control del procesamiento automático
        """
        total_process_time_start = time.time()
        process_number = 0  # inicializa contador de procesos

        # Título del main process
        self.pg_dialog.enabled_suprocess(False)
        QtCore.QCoreApplication.processEvents()

        # Verificación de la información de partida ********************************************************************
        process_name = str(process_number) + u'.- Verificando la información de partida'
        print process_name
        self.pg_dialog.insert_text(0, process_name)
        QtCore.QCoreApplication.processEvents()
        process_time_start = time.time()

        str_simbology_mirameduero_dirname = os.path.normcase(os.path.join(self.plugin_dir + "/templates/simbologia/" + c.CONST_STR_MIRAMEDUERO_SIMBOLOGY_DIRNAME))
        str_simbology_raster_dirname = os.path.normcase(os.path.join(self.plugin_dir + "/templates/simbologia/" + c.CONST_STR_RASTER_SIMBOLOGY_DIRNAME))
        str_simbology_reveladuero_dirname = os.path.normcase(os.path.join(self.plugin_dir + "/templates/simbologia/" + c.CONST_STR_REVELADUERO_SIMBOLOGY_DIRNAME))
        str_simbology_sigpac_dirname = os.path.normcase(os.path.join(self.plugin_dir + "/templates/simbologia/" + c.CONST_STR_SIGPAC_SIMBOLOGY_DIRNAME))

        # create directorio de salida subproductos generados if not exists
        str_path_output_workspace = os.path.normcase(os.path.join(self.str_path_workspace,
                                                                  c.CONST_STR_OUTPUT_DIRNAME))
        if not os.path.exists(str_path_output_workspace):
            os.mkdir(str_path_output_workspace)

        str_path_output_result_dirname = os.path.normcase(os.path.join(str_path_output_workspace,
                                                                       c.CONST_STR_RESULT_DIRNAME))
        if not os.path.exists(str_path_output_result_dirname):
            os.mkdir(str_path_output_result_dirname)

        if self.is_aoi_shapefile:
            if not self.check_normcase_path(self.str_path_shapefile_aoi):
                return False

        str_umbral_ndvi = "(A>" + str(self.float_umbral_ndvi) + ")"
        str_umbral_area_ha = str(self.float_umbral_area)
        str_umbral_area_artificios_ha = str(self.float_umbral_area_artificios)

        if not self.check_normcase_path(self.str_path_ndvi_image):
            return False

        # borra los grupos del TOC de QGIS de procesamientos anteriores
        self.remove_group_gis_layers(c.CONST_STR_INPUT_LAYERS_GROUPNAME)
        self.remove_group_gis_layers(c.CONST_STR_ALBERCA_LAYERS_GROUPNAME)
        self.remove_group_gis_layers(c.CONST_STR_SUBPROCESS_LAYERS_GROUPNAME)
        self.remove_group_gis_layers(c.CONST_STR_SIGPAC_LAYERS_GROUPNAME)
        self.remove_group_gis_layers(c.CONST_STR_RESULT_LAYERS_GROUPNAME)

        # creación grupos de capas
        root = QgsProject.instance().layerTreeRoot()
        node_group_input_layers = root.insertGroup(0, c.CONST_STR_INPUT_LAYERS_GROUPNAME)
        node_group_output_sigpac_layers = root.insertGroup(0, c.CONST_STR_SIGPAC_LAYERS_GROUPNAME)
        node_group_output_subprocess_layers = root.insertGroup(0, c.CONST_STR_SUBPROCESS_LAYERS_GROUPNAME)
        if self.is_generacion_casos:
            node_group_output_alberca_layers = root.insertGroup(0, c.CONST_STR_ALBERCA_LAYERS_GROUPNAME)
        node_group_result_layers = root.insertGroup(0, c.CONST_STR_RESULT_LAYERS_GROUPNAME)

        # borra contenido integro directorio output
        for file in os.listdir(str_path_output_workspace):
            if os.path.isfile(os.path.join(str_path_output_workspace, file)):
                os.remove(str_path_output_workspace + "/" + file)

        # fichero para informe de resultados
        str_filename_results = "report.txt"
        str_path_results = os.path.normcase(os.path.join(str_path_output_workspace,
                                                         str_filename_results))
        # borra el fichero de resultados si existe
        if (os.path.exists(str_path_results)):
            os.remove(str_path_results)

        # escribe cabecera del informe
        self.file_report = open(str_path_results, "w")
        str_msg_input_data = c.CONST_REVELADUERO_TITLE_VERSION + "\n\n"
        str_msg_input_data += "Datos de entrada" + "\n"
        if self.is_estimacion_sup_regada:
            str_msg_input_data += u'  + Tipo procesamiento: \t\tEstimación rápida área regada' + "\n"
            str_main_process_title = u'Estimación rápida área regada'
            self.pg_dialog.set_title_process(0, str_main_process_title)
            QtCore.QCoreApplication.processEvents()

        if self.is_generacion_casos:
            str_msg_input_data += u'  + Tipo procesamiento: \t\tGeneración automática de casos' + "\n"
            str_main_process_title = u'Generación automática de casos'
            self.pg_dialog.set_title_process(0, str_main_process_title)
            QtCore.QCoreApplication.processEvents()

        if self.is_aoi_shapefile:
            str_msg_input_data += u'  + Ámbito geográfico: AOI shapefile' + "\n"
            str_msg_input_data += "    - Ruta shapefile AOI:\t\t" + self.str_path_shapefile_aoi + "\n"
        if self.is_aoi_cod_municipio:
            str_msg_input_data += u'  + Ámbito geográfico: \t\tCódigo muninipio (' + self.str_cod_municipio + ")\n"
        str_msg_input_data += "  + Imagen de referencia: \t\t" + self.str_path_ndvi_image + "\n"
        str_msg_input_data += "  + Umbral NDVI:\t\t\t\t" + str(self.float_umbral_ndvi) + "\n"
        str_msg_input_data += "  + Umbral superficie (ha.): \t" + str(self.float_umbral_area) + "\n"
        str_msg_input_data += "  + Ruta workspace: \t\t\t" + str_path_output_workspace + "\n"

        if self.is_remove_forest_areas:
            str_lista_usos_sigpac_to_filtered = ""
            for uso_sigpac_to_filtered in c.CONST_LIST_USOS_SIGPAC_TO_FILTERED:
                str_lista_usos_sigpac_to_filtered += "'" + uso_sigpac_to_filtered + "'" + ", "
            str_lista_usos_sigpac_to_filtered_formateada = str_lista_usos_sigpac_to_filtered[:-2]
            str_msg_input_data += "  + Usos SIGPAC a filtrar:\t\t" + str_lista_usos_sigpac_to_filtered_formateada + "\n"

        self.pg_dialog.insert_text(0, str_msg_input_data)
        QtCore.QCoreApplication.processEvents()
        self.file_report.write(str_msg_input_data)

        # imagen de NDVI de entrada
        ndvi_rlayer = self.load_to_qgis_and_get_rlayer(self.str_path_ndvi_image,
                                                       node_group=node_group_input_layers)

        if not ndvi_rlayer:
            return False

        # sigpac_ttmm_vlayer
        str_path_simbology_qml_filename = os.path.normcase(os.path.join(str_simbology_sigpac_dirname,
                                                                        c.CONST_STR_TTMM_SIGPAC_QML))
        cartodroid_ttmm_sigpac_vlayer = self.load_to_qgis_postgis_layer(c.CONST_STR_SCHEMA_CONTROL,
                                                                        c.CONST_STR_CARTODROID_MUNICIPIOS_SIGPAC,
                                                                        c.CONST_STR_COLUMN_GEOMETRY_NAME,
                                                                        self.uri,
                                                                        str_path_qml_simbology=str_path_simbology_qml_filename,
                                                                        node_group=node_group_output_sigpac_layers)

        process_time_end = time.time()
        process_time_total = process_time_end - process_time_start
        self.pg_dialog.insert_text(0, u'  - Tiempo ejecución: ' + str(round(process_time_total)) + " s.")
        QtCore.QCoreApplication.processEvents()
        process_number += 1
        # Tipo AOI a partir de municipio SIGPAC ************************************************************************
        if self.is_aoi_cod_municipio:
            self.pg_dialog.clear_text(1)
            self.str_aoi_part_filename = "aoi_tm" + self.str_cod_municipio
            # extracción del término municipal de estudio **************************************************************
            process_name = str(process_number) + u'.- Extrae municipio estudio'
            shp_name = str(process_number) + "_tm_" + self.str_cod_municipio
            print process_name
            self.pg_dialog.insert_text(0, process_name)
            self.file_report.write(process_name + "\n")
            QtCore.QCoreApplication.processEvents()
            process_time_start = time.time()

            str_output_tm_filename = shp_name + ".shp"
            str_output_tm_path = os.path.normcase(os.path.join(str_path_output_workspace,
                                                               str_output_tm_filename))

            output_qgis_extract_by_attribute_01 = processing.runalg('qgis:extractbyattribute',
                                                                    cartodroid_ttmm_sigpac_vlayer,
                                                                    c.CONST_STR_COD_PROVMUN_SIGPAC,
                                                                    0,
                                                                    self.str_cod_municipio,
                                                                    str_output_tm_path)
            vlayer_output_01_tm_path = QgsVectorLayer(str_output_tm_path,
                                                      shp_name,
                                                      "ogr")
            str_path_simbology_qml_filename = os.path.normcase(os.path.join(str_simbology_reveladuero_dirname,
                                                                            c.CONST_STR_CASO_AOI_QML))
            if not self.load_to_qgis_vlayer(vlayer_output_01_tm_path,
                                            str_path_qml_simbology=str_path_simbology_qml_filename,
                                            node_group=node_group_input_layers):
                return False

            process_time_end = time.time()
            process_time_total = process_time_end - process_time_start
            self.pg_dialog.insert_text(0, u'  - Tiempo ejecución: ' + str(round(process_time_total)) + " s.")
            self.file_report.write(u'  - Tiempo ejecución: ' + str(round(process_time_total)) + " s." + "\n")
            QtCore.QCoreApplication.processEvents()
            process_number += 1

            # recorte imagen NDVI raster x término municipal ***********************************************************
            process_name = str(process_number) + u'.- Recorte imagen NDVI raster x término municipal'
            print process_name
            self.pg_dialog.insert_text(0, process_name)
            self.file_report.write(process_name + "\n")
            QtCore.QCoreApplication.processEvents()
            process_time_start = time.time()

            #Comprueba si el AOI intersecta la imagen de NDVI
            qgsrect_aoi_vlayer = vlayer_output_01_tm_path.extent()
            qgsrect_rlayer = ndvi_rlayer.extent()
            if not qgsrect_aoi_vlayer.intersects(qgsrect_rlayer):
                str_msg = "El AOI seleccionado no intersecta con la huella de la imagen NDVI"
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Critical)
                msg.setText(str_msg)
                msg.setWindowTitle(c.CONST_REVELADUERO_TITLE_VERSION)
                msg.exec_()
                return False

            if not qgsrect_rlayer.contains(qgsrect_aoi_vlayer):
                qmessagebox = QMessageBox()
                str_msg_question = u'La huella de la imagen NDVI no contiene enteramente el AOI seleccionada por el usuario. ¿Desea continuar con el procesamiento?'
                qmessagebox.setIcon(QMessageBox.Information)
                qmessagebox.setText(str_msg_question)
                qmessagebox.setWindowTitle(c.CONST_REVELADUERO_TITLE_VERSION)
                qmessagebox.setStandardButtons(QMessageBox.Yes)
                qmessagebox.addButton(QMessageBox.Cancel)
                qmessagebox.setDefaultButton(QMessageBox.Yes)
                if qmessagebox.exec_() == QMessageBox.Cancel:
                    return False

            str_output_raster_clip_filename = str(process_number) + "_clip_tm_" + self.str_cod_municipio + ".tif"
            str_output_raster_clip_path = os.path.normcase(os.path.join(str_path_output_workspace,
                                                                        str_output_raster_clip_filename))
            outputs_GDALOGRCLIPRASTERBYMASKLAYER_1 = processing.runalg('gdalogr:cliprasterbymasklayer',
                                                                       ndvi_rlayer,
                                                                       vlayer_output_01_tm_path,
                                                                       None,
                                                                       False,
                                                                       False,
                                                                       False,
                                                                       5,
                                                                       4,
                                                                       75.0,
                                                                       6.0,
                                                                       1.0,
                                                                       False,
                                                                       0,
                                                                       False,
                                                                       None,
                                                                       str_output_raster_clip_path)

            str_path_simbology_qml_filename = os.path.normcase(os.path.join(str_simbology_raster_dirname,
                                                                            c.CONST_STR_RASTERNDVI_QML))
            rlayer_raster_clip_path_ndvi = self.load_to_qgis_and_get_rlayer(str_output_raster_clip_path,
                                                                            str_path_qml_simbology=str_path_simbology_qml_filename,
                                                                            node_group=node_group_output_subprocess_layers)
            if not rlayer_raster_clip_path_ndvi:
                return False

            process_time_end = time.time()
            process_time_total = process_time_end - process_time_start
            self.pg_dialog.insert_text(0, u'  - Tiempo ejecución: ' + str(round(process_time_total)) + " s.")
            self.file_report.write(u'  - Tiempo ejecución: ' + str(round(process_time_total)) + " s." + "\n")
            QtCore.QCoreApplication.processEvents()
            process_number += 1

        # Tipo AOI a partir de shapefile *******************************************************************************
        if self.is_aoi_shapefile:
            # Obtiene el nombre de fichero sin extension
            filename_w_ext = os.path.basename(self.str_path_shapefile_aoi)
            filename, file_extension = os.path.splitext(filename_w_ext)
            self.str_aoi_part_filename = filename

            vlayer_aoi_shapefile = QgsVectorLayer(self.str_path_shapefile_aoi,
                                                  self.str_path_shapefile_aoi,
                                                  "ogr")
            str_path_simbology_qml_filename = os.path.normcase(os.path.join(str_simbology_reveladuero_dirname,
                                                                            c.CONST_STR_CASO_AOI_QML))


            if not self.load_to_qgis_vlayer(vlayer_aoi_shapefile,
                                            str_path_qml_simbology=str_path_simbology_qml_filename,
                                            node_group=node_group_input_layers):
                return False

            # Comprueba si el AOI intersecta la imagen de NDVI
            qgsrect_aoi_vlayer = vlayer_aoi_shapefile.extent()
            qgsrect_rlayer = ndvi_rlayer.extent()
            if not qgsrect_aoi_vlayer.intersects(qgsrect_rlayer):
                str_msg = "El AOI seleccionado no intersecta con la huella de la imagen NDVI"
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Critical)
                msg.setText(str_msg)
                msg.setWindowTitle(c.CONST_REVELADUERO_TITLE_VERSION)
                msg.exec_()
                return False

            if not qgsrect_rlayer.contains(qgsrect_aoi_vlayer):
                qmessagebox = QMessageBox()
                str_msg_question = u'La huella de la imagen NDVI no contiene enteramente el AOI seleccionada por el usuario. ¿Desea continuar con el procesamiento?'
                qmessagebox.setIcon(QMessageBox.Information)
                qmessagebox.setText(str_msg_question)
                qmessagebox.setWindowTitle(c.CONST_REVELADUERO_TITLE_VERSION)
                qmessagebox.setStandardButtons(QMessageBox.Yes)
                qmessagebox.addButton(QMessageBox.Cancel)
                qmessagebox.setDefaultButton(QMessageBox.Yes)
                if qmessagebox.exec_() == QMessageBox.Cancel:
                    return False

            # Recorte de la imagen de NDVI raster x AOI shapefile
            process_name = str(process_number) + u'.- Recorta imagen NDVI raster x AOI shapefile'
            print process_name
            self.pg_dialog.insert_text(0, process_name)
            self.file_report.write(process_name + "\n")
            QtCore.QCoreApplication.processEvents()
            process_time_start = time.time()

            str_output_raster_clip_filename = str(process_number) + "_clip_aoi_shapefile.tif"
            str_output_raster_clip_path = os.path.normcase(os.path.join(str_path_output_workspace,
                                                                        str_output_raster_clip_filename))

            outputs_GDALOGRCLIPRASTERBYMASKLAYER_1 = processing.runalg('gdalogr:cliprasterbymasklayer',
                                                                       ndvi_rlayer,
                                                                       vlayer_aoi_shapefile,
                                                                       None,
                                                                       False,
                                                                       False,
                                                                       False,
                                                                       5,
                                                                       4,
                                                                       75.0,
                                                                       6.0,
                                                                       1.0,
                                                                       False,
                                                                       0,
                                                                       False,
                                                                       None,
                                                                       str_output_raster_clip_path)
            str_path_simbology_qml_filename = os.path.normcase(os.path.join(str_simbology_raster_dirname,
                                                                            c.CONST_STR_RASTERNDVI_QML))
            rlayer_raster_clip_path_ndvi = self.load_to_qgis_and_get_rlayer(str_output_raster_clip_path,
                                                                            str_path_qml_simbology=str_path_simbology_qml_filename,
                                                                            node_group=node_group_output_subprocess_layers)
            if not rlayer_raster_clip_path_ndvi:
                return False

            process_time_end = time.time()
            process_time_total = process_time_end - process_time_start
            self.pg_dialog.insert_text(0, u'  - Tiempo ejecución: ' + str(round(process_time_total)) + " s.")
            self.file_report.write(u'  - Tiempo ejecución: ' + str(round(process_time_total)) + " s." + "\n")
            QtCore.QCoreApplication.processEvents()
            process_number += 1

        # obtención de recintos por encima de umbral de NDVI ***********************************************************
        process_name = str(process_number) + u'.- Obtención recintos por encima umbral NDVI ' + str(self.float_umbral_ndvi)
        print process_name
        self.pg_dialog.insert_text(0, process_name)
        self.file_report.write(process_name + "\n")
        QtCore.QCoreApplication.processEvents()
        process_time_start = time.time()

        str_output_raster_umbral_ndvi_filename = str(process_number) + "_umbral_ndvi.tif"
        str_output_raster_umbral_ndvi_path = os.path.normcase(os.path.join(str_path_output_workspace,
                                                                           str_output_raster_umbral_ndvi_filename))
        outputs_GDALOGRRASTERCALCULATOR_1 = processing.runalg('gdalogr:rastercalculator',
                                                              rlayer_raster_clip_path_ndvi,
                                                              '1',
                                                              None,
                                                              '1',
                                                              None,
                                                              '1',
                                                              None,
                                                              '1',
                                                              None,
                                                              '1',
                                                              None,
                                                              '1',
                                                              str_umbral_ndvi,
                                                              '0',
                                                              1,
                                                              None,
                                                              str_output_raster_umbral_ndvi_path)
        rlayer_raster_umbral_ndvi = self.load_to_qgis_and_get_rlayer(str_output_raster_umbral_ndvi_path,
                                                                     node_group=node_group_output_subprocess_layers)
        if not rlayer_raster_umbral_ndvi:
            return False

        process_time_end = time.time()
        process_time_total = process_time_end - process_time_start
        self.pg_dialog.insert_text(0, u'  - Tiempo ejecución: ' + str(round(process_time_total)) + " s.")
        self.file_report.write(u'  - Tiempo ejecución: ' + str(round(process_time_total)) + " s." + "\n")
        QtCore.QCoreApplication.processEvents()
        process_number += 1

        # vectorización regadío probable umbral de NDVI ****************************************************************
        process_name = str(process_number) + u'.- Vectorización regadío probable umbral NDVI ' + str(self.float_umbral_ndvi)
        shp_name = str(process_number) + u'_umbral_ndvi_vectorizado'
        print process_name
        self.pg_dialog.insert_text(0, process_name)
        self.file_report.write(process_name + "\n")
        QtCore.QCoreApplication.processEvents()
        process_time_start = time.time()

        str_output_vector_polygonize_filename = shp_name + ".shp"
        str_output_vector_polygonize_path = os.path.normcase(os.path.join(str_path_output_workspace,
                                                                          str_output_vector_polygonize_filename))
        outputs_GDALOGRPOLYGONIZE_1 = processing.runalg('gdalogr:polygonize',
                                                        rlayer_raster_umbral_ndvi,
                                                        'DN',
                                                        str_output_vector_polygonize_path)
        vlayer_polygonize = QgsVectorLayer(str_output_vector_polygonize_path,
                                           shp_name,
                                           "ogr")
        qgs_crs_25830 = QgsCoordinateReferenceSystem("EPSG:25830")
        vlayer_polygonize.setCrs(qgs_crs_25830)
        if not self.load_to_qgis_vlayer(vlayer_polygonize,
                                        node_group=node_group_output_subprocess_layers):
            return False

        process_time_end = time.time()
        process_time_total = process_time_end - process_time_start
        self.pg_dialog.insert_text(0, u'  - Tiempo ejecución: ' + str(round(process_time_total)) + " s.")
        self.file_report.write(u'  - Tiempo ejecución: ' + str(round(process_time_total)) + " s." + "\n")
        QtCore.QCoreApplication.processEvents()
        process_number += 1

        # vectorización regadío probable umbral de NDVI ****************************************************************
        process_name = str(process_number) + u'.- Cálculo área de vectorización regadío probable umbral NDVI ' + str(self.float_umbral_ndvi)
        shp_name = str(process_number) + "_umbral_ndvi_vectorizado_area"
        print process_name
        self.pg_dialog.insert_text(0, process_name)
        self.file_report.write(process_name + "\n")
        QtCore.QCoreApplication.processEvents()
        process_time_start = time.time()

        str_output_vector_polygonize_area_filename = shp_name + ".shp"
        str_output_vector_polygonize_area_path = os.path.normcase(os.path.join(str_path_output_workspace,
                                                                               str_output_vector_polygonize_area_filename))
        outputs_QGISFIELDCALCULATOR_1 = processing.runalg('qgis:fieldcalculator',
                                                          vlayer_polygonize,
                                                          c.CONST_AREA_NDVI_FIELDNAME,
                                                          0,
                                                          20.0,
                                                          4.0,
                                                          True,
                                                          '$area/10000', str_output_vector_polygonize_area_path)
        vlayer_polygonize_area = QgsVectorLayer(str_output_vector_polygonize_area_path,
                                                shp_name,
                                                "ogr")

        if not self.load_to_qgis_vlayer(vlayer_polygonize_area,
                                        node_group=node_group_output_subprocess_layers):
            return False

        process_time_end = time.time()
        process_time_total = process_time_end - process_time_start
        self.pg_dialog.insert_text(0, u'  - Tiempo ejecución: ' + str(round(process_time_total)) + " s.")
        self.file_report.write(u'  - Tiempo ejecución: ' + str(round(process_time_total)) + " s." + "\n")
        QtCore.QCoreApplication.processEvents()
        process_number += 1

        # selección de recintos por encima de umbral de NDVI y de area *************************************************
        process_name = str(process_number) + u'.- Regadío probable umbral NDVI ' + str(self.float_umbral_ndvi) + u' umbral área > ' + str_umbral_area_ha
        print process_name
        self.pg_dialog.insert_text(0, process_name)
        self.file_report.write(process_name + "\n")
        QtCore.QCoreApplication.processEvents()
        process_time_start = time.time()

        if self.is_estimacion_sup_regada:
            shp_name = "SuperficieRegadaProbable_"
            shp_name += self.str_aoi_part_filename + "_"
            shp_name += self.str_ndvi_image_filename[:-4] + "_"
            shp_name += str(self.float_umbral_ndvi) + "_"
            shp_name += "area_" + str(self.float_umbral_area)

            str_output_vector_umbral_area_filename = shp_name + ".shp"
            str_output_vector_umbral_area_path = os.path.normcase(os.path.join(str_path_output_result_dirname,
                                                                               str_output_vector_umbral_area_filename))
        if self.is_generacion_casos:
            shp_name = str(process_number) + "_umbral_ndvi_umbral_area"
            str_output_vector_umbral_area_filename = shp_name + ".shp"
            str_output_vector_umbral_area_path = os.path.normcase(os.path.join(str_path_output_workspace,
                                                                               str_output_vector_umbral_area_filename))

        outputs_QGISEXTRACTBYATTRIBUTE_1=processing.runalg('qgis:extractbyattribute',
                                                           vlayer_polygonize_area,
                                                           c.CONST_AREA_NDVI_FIELDNAME,
                                                           2,
                                                           str_umbral_area_ha,
                                                           str_output_vector_umbral_area_path)
        vlayer_umbral_area = QgsVectorLayer(str_output_vector_umbral_area_path,
                                            shp_name,
                                            "ogr")
        process_time_end = time.time()
        process_time_total = process_time_end - process_time_start
        self.pg_dialog.insert_text(0, u'  - Tiempo ejecución: ' + str(round(process_time_total)) + " s.")
        self.file_report.write(u'  - Tiempo ejecución: ' + str(round(process_time_total)) + " s." + "\n")
        QtCore.QCoreApplication.processEvents()
        process_number += 1

        # creación de campos image - imagen de referencia, prioridad - prioridad del caso, ndvi_ref - ndvi de referencia
        process_name = str(process_number) + u'.- Añadiendo nuevos campos imagen de referencia, prioridad y ndvi referencia'
        print process_name
        self.pg_dialog.insert_text(0, process_name)
        self.file_report.write(process_name + "\n")
        QtCore.QCoreApplication.processEvents()
        process_time_start = time.time()

        caps = vlayer_umbral_area.dataProvider().capabilities()
        if caps & QgsVectorDataProvider.AddAttributes:
            res = vlayer_umbral_area.dataProvider().addAttributes([QgsField(c.CONST_IMAGE_REF_FIELDNAME, QVariant.String),
                                                                   QgsField(c.CONST_NDVI_REF_FIELDNAME, QVariant.Double),
                                                                   QgsField(c.CONST_PRIORITY_FIELDNAME, QVariant.Int),
                                                                   QgsField(c.CONST_ZONA_NO_AUTORIZADA_FIELDNAME,QVariant.String)])
            vlayer_umbral_area.updateFields()

        iter = vlayer_umbral_area.getFeatures()
        vlayer_umbral_area.startEditing()
        for feature in iter:
            vlayer_umbral_area.changeAttributeValue(feature.id(),
                                                    c.CONST_ORDER_IMAGE_REF_FIELDNAME,
                                                    self.str_ndvi_image_filename)
            vlayer_umbral_area.changeAttributeValue(feature.id(),
                                                    c.CONST_ORDER_NDVI_REF_FIELDNAME,
                                                    self.float_umbral_ndvi)
        vlayer_umbral_area.commitChanges()
        if self.is_estimacion_sup_regada:
            str_path_simbology_qml_filename = os.path.normcase(os.path.join(str_simbology_reveladuero_dirname,
                                                                            c.CONST_STR_CASOS_SUPREGPROB_QML))
            if not self.load_to_qgis_vlayer(vlayer_umbral_area,
                                            str_path_qml_simbology=str_path_simbology_qml_filename,
                                            node_group=node_group_result_layers):
                return False

            extent = vlayer_umbral_area.extent()
            self.iface.mapCanvas().setExtent(extent)

        process_time_end = time.time()
        process_time_total = process_time_end - process_time_start
        self.pg_dialog.insert_text(0, u'  - Tiempo ejecución: ' + str(round(process_time_total)) + " s.")
        self.file_report.write(u'  - Tiempo ejecución: ' + str(round(process_time_total)) + " s." + "\n")
        QtCore.QCoreApplication.processEvents()
        process_number += 1

        if self.is_generacion_casos:
            if not self.load_to_qgis_vlayer(vlayer_umbral_area,
                                            node_group=node_group_output_subprocess_layers):
                return False

            # Diferencia regadío probable - alberca regadíos ***********************************************************
            process_name = str(process_number) + u'.- Regadío probable - Regadío ALBERCA'
            shp_name = str(process_number) + u'_regadio_probable_x_reg_alberca'
            print process_name
            self.pg_dialog.insert_text(0, process_name)
            self.file_report.write(process_name + "\n")
            QtCore.QCoreApplication.processEvents()
            process_time_start = time.time()
            # carga capa ALBERCA
            str_path_simbology_qml_filename = os.path.normcase(os.path.join(str_simbology_mirameduero_dirname,
                                                                            c.CONST_STR_REGADIOS_QML))
            md_regadios_vlayer = self.load_to_qgis_postgis_layer(c.CONST_STR_SCHEMA_CONTROL,
                                                                 c.CONST_STR_REGADIOS_POSTGIS_TABLENAME,
                                                                 c.CONST_STR_COLUMN_GEOM_NAME,
                                                                 self.uri,
                                                                 str_path_qml_simbology=str_path_simbology_qml_filename,
                                                                 node_group=node_group_output_alberca_layers)
            # algoritmo diferencia mejorado
            vlayer_dif_regadio_probable_x_regadio_alberca = self.improved_spatial_difference_algorithm(shp_name,
                                                                                                       str_path_output_workspace,
                                                                                                       vlayer_umbral_area,
                                                                                                       md_regadios_vlayer,
                                                                                                       node_group_output_subprocess_layers)
            # carga en QGIS del resultado
            if not self.load_to_qgis_vlayer(vlayer_dif_regadio_probable_x_regadio_alberca,
                                            node_group=node_group_output_subprocess_layers):
                return False

            str_msg_num_features = u'  - Regadío probable [' + str(vlayer_umbral_area.featureCount()) + "] - "
            str_msg_num_features += u'Regadío ALBERCA [' + str(md_regadios_vlayer.featureCount()) + "] = "
            str_msg_num_features += u'Diferencia [' + str(vlayer_dif_regadio_probable_x_regadio_alberca.featureCount()) + "]"
            self.pg_dialog.insert_text(0, str_msg_num_features)
            self.file_report.write(str_msg_num_features + "\n")

            process_time_end = time.time()
            process_time_total = process_time_end - process_time_start
            self.pg_dialog.insert_text(0, u'  - Tiempo ejecución: ' + str(round(process_time_total)) + " s.")
            self.file_report.write(u'  - Tiempo ejecución: ' + str(round(process_time_total)) + " s." + "\n")
            QtCore.QCoreApplication.processEvents()
            process_number += 1

            # Diferencia regadío probable - alberca regadíos en tramitación ********************************************
            process_name = str(process_number) + u'.- Regadío probable - Regadío en tramitación ALBERCA'
            shp_name = str(process_number) + u'_regadio_probable_x_reg_tramita_alberca'
            print process_name
            self.pg_dialog.insert_text(0, process_name)
            self.file_report.write(process_name + "\n")
            QtCore.QCoreApplication.processEvents()
            process_time_start = time.time()
            # carga capa ALBERCA
            str_path_simbology_qml_filename = os.path.normcase(os.path.join(str_simbology_mirameduero_dirname,
                                                                            c.CONST_STR_REGADIOS_TRAMITACION_QML))
            md_regadios_tramitacion_vlayer = self.load_to_qgis_postgis_layer(c.CONST_STR_SCHEMA_CONTROL,
                                                                             c.CONST_STR_REGADIOS_TRAMITACION_POSTGIS_TABLENAME,
                                                                             c.CONST_STR_COLUMN_GEOM_NAME,
                                                                             self.uri,
                                                                             str_path_qml_simbology=str_path_simbology_qml_filename,
                                                                             node_group=node_group_output_alberca_layers)
            # algoritmo diferencia mejorado
            vlayer_dif_regadio_probable_x_regadio_tramitacion_alberca = self.improved_spatial_difference_algorithm(shp_name,
                                                                                                                   str_path_output_workspace,
                                                                                                                   vlayer_dif_regadio_probable_x_regadio_alberca,
                                                                                                                   md_regadios_tramitacion_vlayer,
                                                                                                                   node_group_output_subprocess_layers)
            # carga en QGIS del resultado
            if not self.load_to_qgis_vlayer(vlayer_dif_regadio_probable_x_regadio_tramitacion_alberca,
                                            node_group=node_group_output_subprocess_layers):
                return False

            str_msg_num_features = u'  - Regadío probable [' + str(vlayer_dif_regadio_probable_x_regadio_alberca.featureCount()) + "] - "
            str_msg_num_features += u'Regadío en tramitación ALBERCA [' + str(md_regadios_tramitacion_vlayer.featureCount()) + "] = "
            str_msg_num_features += u'Diferencia [' + str(vlayer_dif_regadio_probable_x_regadio_tramitacion_alberca.featureCount()) + "]"
            self.pg_dialog.insert_text(0, str_msg_num_features)
            self.file_report.write(str_msg_num_features + "\n")

            process_time_end = time.time()
            process_time_total = process_time_end - process_time_start
            self.pg_dialog.insert_text(0, u'  - Tiempo ejecución: ' + str(round(process_time_total)) + " s.")
            self.file_report.write(u'  - Tiempo ejecución: ' + str(round(process_time_total)) + " s." + "\n")
            QtCore.QCoreApplication.processEvents()
            process_number += 1

            # Diferencia regadío probable - regadíos en revisión ALBERCA ***********************************************
            process_name = str(process_number) + u'.- Regadío probable - Regadío en revisión ALBERCA'
            shp_name = str(process_number) + u'_regadio_probable_x_reg_revision_alberca'
            print process_name
            self.pg_dialog.insert_text(0, process_name)
            self.file_report.write(process_name + "\n")
            QtCore.QCoreApplication.processEvents()
            process_time_start = time.time()
            # carga en QGIS de capa ALBERCA
            str_path_simbology_qml_filename = os.path.normcase(os.path.join(str_simbology_mirameduero_dirname,
                                                                            c.CONST_STR_REGADIOS_REVSION_QML))
            md_regadios_revision_vlayer = self.load_to_qgis_postgis_layer(c.CONST_STR_SCHEMA_CONTROL,
                                                                          c.CONST_STR_REGADIOS_REVISION_POSTGIS_TABLENAME,
                                                                          c.CONST_STR_COLUMN_GEOM_NAME,
                                                                          self.uri,
                                                                          str_path_qml_simbology=str_path_simbology_qml_filename,
                                                                          node_group=node_group_output_alberca_layers)
            # algoritmo diferencia mejorado
            vlayer_dif_regadio_probable_x_regadio_revision_alberca = self.improved_spatial_difference_algorithm(shp_name,
                                                                                                                str_path_output_workspace,
                                                                                                                vlayer_dif_regadio_probable_x_regadio_tramitacion_alberca,
                                                                                                                md_regadios_revision_vlayer,
                                                                                                                node_group_output_subprocess_layers)
            # carga en QGIS del resultado
            if not self.load_to_qgis_vlayer(vlayer_dif_regadio_probable_x_regadio_revision_alberca,
                                            node_group=node_group_output_subprocess_layers):
                return False

            str_msg_num_features = u'  - Regadío probable [' + str(vlayer_dif_regadio_probable_x_regadio_tramitacion_alberca.featureCount()) + "] - "
            str_msg_num_features += u'Regadío en revisión ALBERCA [' + str(md_regadios_revision_vlayer.featureCount()) + "] = "
            str_msg_num_features += u'Diferencia [' + str(vlayer_dif_regadio_probable_x_regadio_revision_alberca.featureCount()) + "]"
            self.pg_dialog.insert_text(0, str_msg_num_features)
            self.file_report.write(str_msg_num_features + "\n")

            process_time_end = time.time()
            process_time_total = process_time_end - process_time_start
            self.pg_dialog.insert_text(0, u'  - Tiempo ejecución: ' + str(round(process_time_total)) + " s.")
            self.file_report.write(u'  - Tiempo ejecución: ' + str(round(process_time_total)) + " s." + "\n")
            QtCore.QCoreApplication.processEvents()
            process_number += 1

            # Diferencia regadío probable - regadíos sin clasificar ALBERCA ********************************************
            process_name = str(process_number) + u'.- Regadío probable - Regadío sin clasificar ALBERCA'
            shp_name = str(process_number) + u'_regadio_probable_x_reg_sinclasificar_alberca'
            print process_name
            self.pg_dialog.insert_text(0, process_name)
            self.file_report.write(process_name + "\n")
            QtCore.QCoreApplication.processEvents()
            process_time_start = time.time()
            # carga en QGIS de capa ALBERCA
            str_path_simbology_qml_filename = os.path.normcase(os.path.join(str_simbology_mirameduero_dirname,
                                                                            c.CONST_STR_REGADIOS_SINCLASIFICAR_QML))
            md_regadios_sinclasificar_vlayer = self.load_to_qgis_postgis_layer(c.CONST_STR_SCHEMA_CONTROL,
                                                                               c.CONST_STR_REGADIOS_SINCLASIFICAR_POSTGIS_TABLENAME,
                                                                               c.CONST_STR_COLUMN_GEOM_NAME,
                                                                               self.uri,
                                                                               str_path_qml_simbology=str_path_simbology_qml_filename,
                                                                               node_group=node_group_output_alberca_layers)
            # algoritmo diferencia mejorado
            vlayer_dif_regadio_probable_x_regadio_sinclasificar_alberca = self.improved_spatial_difference_algorithm(shp_name,
                                                                                                                     str_path_output_workspace,
                                                                                                                     vlayer_dif_regadio_probable_x_regadio_revision_alberca,
                                                                                                                     md_regadios_sinclasificar_vlayer,
                                                                                                                     node_group_output_subprocess_layers)
            # carga en QGIS del resultado
            if not self.load_to_qgis_vlayer(vlayer_dif_regadio_probable_x_regadio_sinclasificar_alberca,
                                            node_group=node_group_output_subprocess_layers):
                return False

            str_msg_num_features = u'  - Regadío probable [' + str(vlayer_dif_regadio_probable_x_regadio_revision_alberca.featureCount()) + "] - "
            str_msg_num_features += u'Regadío sin clasificar ALBERCA [' + str(md_regadios_sinclasificar_vlayer.featureCount()) + "] = "
            str_msg_num_features += u'Diferencia [' + str(vlayer_dif_regadio_probable_x_regadio_sinclasificar_alberca.featureCount()) + "]"
            self.pg_dialog.insert_text(0, str_msg_num_features)
            self.file_report.write(str_msg_num_features + "\n")

            process_time_end = time.time()
            process_time_total = process_time_end - process_time_start
            self.pg_dialog.insert_text(0, u'  - Tiempo ejecución: ' + str(round(process_time_total)) + " s.")
            self.file_report.write(u'  - Tiempo ejecución: ' + str(round(process_time_total)) + " s." + "\n")
            QtCore.QCoreApplication.processEvents()
            process_number += 1

            # Diferencia regadío probable - UDAs superficiales 2015 MírameDuero
            process_name = str(process_number) + u'.- Regadío probable - UDAs zonas regables superficiales'
            shp_name = str(process_number) + u'_regadio_probable_x_uda_sup_2015_zr'
            print process_name
            self.pg_dialog.insert_text(0, process_name)
            self.file_report.write(process_name + "\n")
            QtCore.QCoreApplication.processEvents()
            process_time_start = time.time()
            # carga en QGIS de capa ALBERCA
            str_path_simbology_qml_filename = os.path.normcase(os.path.join(str_simbology_mirameduero_dirname,
                                                                            c.CONST_STR_UDA_SUP_2015_ZR_QML))
            md_uda_sup_2015_zr_vlayer = self.load_to_qgis_postgis_layer(c.CONST_STR_SCHEMA_CONTROL,
                                                                        c.CONST_STR_UDA_SUP_2015_ZR_POSTGIS_TABLENAME,
                                                                        c.CONST_STR_COLUMN_GEOM_NAME,
                                                                        self.uri,
                                                                        str_path_qml_simbology=str_path_simbology_qml_filename,
                                                                        node_group=node_group_output_alberca_layers)
            # algoritmo diferencia mejorado
            vlayer_dif_regadio_probable_x_md_uda_2015_zr = self.improved_spatial_difference_algorithm(shp_name,
                                                                                                      str_path_output_workspace,
                                                                                                      vlayer_dif_regadio_probable_x_regadio_sinclasificar_alberca,
                                                                                                      md_uda_sup_2015_zr_vlayer,
                                                                                                      node_group_output_subprocess_layers)
            # carga en QGIS del resultado
            if not self.load_to_qgis_vlayer(vlayer_dif_regadio_probable_x_md_uda_2015_zr,
                                            node_group=node_group_output_subprocess_layers):
                return False

            str_msg_num_features = u'  - Regadío probable [' + str(vlayer_dif_regadio_probable_x_regadio_sinclasificar_alberca.featureCount()) + "] - "
            str_msg_num_features += u'UDAs zonas regables superficiales [' + str(md_uda_sup_2015_zr_vlayer.featureCount()) + "] = "
            str_msg_num_features += u'Diferencia [' + str(vlayer_dif_regadio_probable_x_md_uda_2015_zr.featureCount()) + "]"
            self.pg_dialog.insert_text(0, str_msg_num_features)
            self.file_report.write(str_msg_num_features + "\n")

            process_time_end = time.time()
            process_time_total = process_time_end - process_time_start
            self.pg_dialog.insert_text(0, u'  - Tiempo ejecución: ' + str(round(process_time_total)) + " s.")
            self.file_report.write(u'  - Tiempo ejecución: ' + str(round(process_time_total)) + " s." + "\n")
            QtCore.QCoreApplication.processEvents()
            process_number += 1
            # Diferencia regadío probable - núcleos población MírameDuero **********************************************
            process_name = str(process_number) + u'.- Regadío probable - Núcleos de población'
            shp_name = str(process_number) + u'_regadio_probable_x_nucleos_poblacion'
            print process_name
            self.pg_dialog.insert_text(0, process_name)
            self.file_report.write(process_name + "\n")
            QtCore.QCoreApplication.processEvents()
            process_time_start = time.time()
            # carga en QGIS de capa ALBERCA
            str_path_simbology_qml_filename = os.path.normcase(os.path.join(str_simbology_mirameduero_dirname,
                                                                            c.CONST_STR_NUCLEOS_URBANOS_QML))
            md_nucleos_poblacion_vlayer = self.load_to_qgis_postgis_layer(c.CONST_STR_SCHEMA_CONTROL,
                                                                          c.CONST_STR_NUCLEOS_URBANOS_POSTGIS_TABLENAME,
                                                                          c.CONST_STR_COLUMN_GEOM_NAME,
                                                                          self.uri,
                                                                          str_path_qml_simbology=str_path_simbology_qml_filename,
                                                                          node_group=node_group_output_alberca_layers)
            # algoritmo diferencia mejorado
            vlayer_dif_regadio_probable_x_md_nucleos_poblacion = self.improved_spatial_difference_algorithm(shp_name,
                                                                                                            str_path_output_workspace,
                                                                                                            vlayer_dif_regadio_probable_x_md_uda_2015_zr,
                                                                                                            md_nucleos_poblacion_vlayer,
                                                                                                            node_group_output_subprocess_layers)
            # carga en QGIS del resultado
            if not self.load_to_qgis_vlayer(vlayer_dif_regadio_probable_x_md_nucleos_poblacion,
                                            node_group=node_group_output_subprocess_layers):
                return False
            str_msg_num_features = u'  - Regadío probable [' + str(vlayer_dif_regadio_probable_x_md_uda_2015_zr.featureCount()) + "] - "
            str_msg_num_features += u'Núcleos de población [' + str(md_nucleos_poblacion_vlayer.featureCount()) + "] = "
            str_msg_num_features += u'Diferencia [' + str(vlayer_dif_regadio_probable_x_md_nucleos_poblacion.featureCount()) + "]"
            self.pg_dialog.insert_text(0, str_msg_num_features)
            self.file_report.write(str_msg_num_features + "\n")

            process_time_end = time.time()
            process_time_total = process_time_end - process_time_start
            self.pg_dialog.insert_text(0, u'  - Tiempo ejecución: ' + str(round(process_time_total)) + " s.")
            self.file_report.write(u'  - Tiempo ejecución: ' + str(round(process_time_total)) + " s." + "\n")
            QtCore.QCoreApplication.processEvents()
            process_number += 1

            vlayer_regadio_probable_no_alberca = vlayer_dif_regadio_probable_x_md_nucleos_poblacion

            # Geometrías válidas regadío probable no alberca
            # Regadío probable no ALBERCA. Validación geométrica. ******************************************************
            process_name = str(process_number) + u'.- Verificación geométrica features regadío probable NO ALBERCA'
            shp_name = str(process_number) + u'_regadio_probable_no_alberca'
            print process_name
            self.pg_dialog.insert_text(0, process_name)
            self.file_report.write(process_name + "\n")
            QtCore.QCoreApplication.processEvents()
            process_time_start = time.time()

            str_output_regadio_probable_no_alberca_valid_geom_filename = shp_name + "_valid_geom.shp"
            str_output_regadio_probable_no_alberca_valid_geom_path = os.path.normcase(os.path.join(str_path_output_workspace,
                                                                                                   str_output_regadio_probable_no_alberca_valid_geom_filename))
            str_output_regadio_probable_no_alberca_invalid_geom_filename = shp_name + "_invalid_geom.shp"
            str_output_regadio_probable_no_alberca_invalid_geom_path = os.path.normcase(os.path.join(str_path_output_workspace,
                                                                                                     str_output_regadio_probable_no_alberca_invalid_geom_filename))
            str_output_regadio_probable_no_alberca_error_geom_filename = shp_name + "_error_geom.shp"
            str_output_regadio_probable_no_alberca_error_geom_path = os.path.normcase(os.path.join(str_path_output_workspace,
                                                                                                   str_output_regadio_probable_no_alberca_error_geom_filename))
            outputs_QGISCHECKVALIDITY_1 = processing.runalg('qgis:checkvalidity',
                                                            vlayer_regadio_probable_no_alberca,
                                                            2,
                                                            str_output_regadio_probable_no_alberca_valid_geom_path,
                                                            str_output_regadio_probable_no_alberca_invalid_geom_path,
                                                            str_output_regadio_probable_no_alberca_error_geom_path)

            vlayer_dif_regadio_probable_no_alberca_valid_geom = QgsVectorLayer(str_output_regadio_probable_no_alberca_valid_geom_path,
                                                                               shp_name + "_valid_geom",
                                                                               "ogr")
            if not self.load_to_qgis_vlayer(vlayer_dif_regadio_probable_no_alberca_valid_geom,
                                            node_group=node_group_output_subprocess_layers):
                return False
            vlayer_dif_regadio_probable_no_alberca_invalid_geom = QgsVectorLayer(str_output_regadio_probable_no_alberca_invalid_geom_path,
                                                                               shp_name + "_invalid_geom",
                                                                               "ogr")
            if not self.load_to_qgis_vlayer(vlayer_dif_regadio_probable_no_alberca_invalid_geom,
                                            node_group=node_group_output_subprocess_layers):
                return False
            vlayer_dif_regadio_probable_no_alberca_error_geom = QgsVectorLayer(str_output_regadio_probable_no_alberca_error_geom_path,
                                                                               shp_name + "_error_geom",
                                                                               "ogr")
            if not self.load_to_qgis_vlayer(vlayer_dif_regadio_probable_no_alberca_error_geom,
                                            node_group=node_group_output_subprocess_layers):
                return False

            process_time_end = time.time()
            process_time_total = process_time_end - process_time_start
            self.pg_dialog.insert_text(0, u'  - Tiempo ejecución: ' + str(round(process_time_total)) + " s.")
            self.file_report.write(u'  - Tiempo ejecución: ' + str(round(process_time_total)) + " s." + "\n")
            QtCore.QCoreApplication.processEvents()
            process_number += 1
            # Regadío probable no ALBERCA. Multiparte a parte sencilla *************************************************
            process_name = str(process_number) + u'.- Regadío probable no ALBERCA. Multiparte a parte sencilla'
            shp_name = str(process_number) + u'_regadio_prob_no_alberca_singleparts'
            print process_name
            self.pg_dialog.insert_text(0, process_name)
            self.file_report.write(process_name + "\n")
            QtCore.QCoreApplication.processEvents()
            process_time_start = time.time()

            str_output_regadio_probable_no_alberca_singleparts_filename = shp_name + ".shp"
            str_output_regadio_probable_no_alberca_singleparts_path = os.path.normcase(os.path.join(str_path_output_workspace,
                                                                                                    str_output_regadio_probable_no_alberca_singleparts_filename))
            outputs_QGISMULTIPARTTOSINGLEPARTS_1 = processing.runalg('qgis:multiparttosingleparts',
                                                                     vlayer_dif_regadio_probable_no_alberca_valid_geom,
                                                                     str_output_regadio_probable_no_alberca_singleparts_path)
            vlayer_regadio_probable_no_alberca_singleparts = QgsVectorLayer(str_output_regadio_probable_no_alberca_singleparts_path,
                                                                            shp_name,
                                                                            "ogr")
            if not self.load_to_qgis_vlayer(vlayer_regadio_probable_no_alberca_singleparts,
                                            node_group=node_group_output_subprocess_layers):
                return False
            process_time_end = time.time()
            process_time_total = process_time_end - process_time_start
            self.pg_dialog.insert_text(0, u'  - Tiempo ejecución: ' + str(round(process_time_total)) + " s.")
            self.file_report.write(u'  - Tiempo ejecución: ' + str(round(process_time_total)) + " s." + "\n")
            QtCore.QCoreApplication.processEvents()
            process_number += 1

            # Regadío probable no ALBERCA. Cálculo área ****************************************************************
            process_name = str(process_number) + u'.- Regadío probable no ALBERCA. Cálculo área tras validación geométrica'
            shp_name = str(process_number) + u'_regadio_prob_no_alberca_singleparts_area'
            print process_name
            self.pg_dialog.insert_text(0, process_name)
            self.file_report.write(process_name + "\n")
            QtCore.QCoreApplication.processEvents()
            process_time_start = time.time()

            str_output_regadio_probable_no_alberca_singleparts_area_filename = shp_name +".shp"
            str_output_regadio_probable_no_alberca_singleparts_area_path = os.path.normcase(os.path.join(str_path_output_workspace,
                                                                                                         str_output_regadio_probable_no_alberca_singleparts_area_filename))
            outputs_QGISFIELDCALCULATOR_2 = processing.runalg('qgis:fieldcalculator',
                                                              vlayer_regadio_probable_no_alberca_singleparts,
                                                              c.CONST_AREA_SINGLEPARTS_FIELDNAME,
                                                              0,
                                                              20.0,
                                                              4.0,
                                                              True,
                                                              '$area/10000',
                                                              str_output_regadio_probable_no_alberca_singleparts_area_path)
            vlayer_dif_regadio_probable_no_alberca_valid_geom_area = QgsVectorLayer(str_output_regadio_probable_no_alberca_singleparts_area_path,
                                                                                    shp_name,
                                                                                    "ogr")
            if not self.load_to_qgis_vlayer(vlayer_dif_regadio_probable_no_alberca_valid_geom_area,
                                            node_group=node_group_output_subprocess_layers):
                return False

            process_time_end = time.time()
            process_time_total = process_time_end - process_time_start
            self.pg_dialog.insert_text(0, u'  - Tiempo ejecución: ' + str(round(process_time_total)) + " s.")
            self.file_report.write(u'  - Tiempo ejecución: ' + str(round(process_time_total)) + " s." + "\n")
            QtCore.QCoreApplication.processEvents()
            process_number += 1

            # Regadío probable no ALBERCA. Selección recintos por encima umbral área ***********************************
            process_name = str(process_number) + u'.- Regadío probable no ALBERCA. Recintos por encima umbral área'
            shp_name = str(process_number) + u'_regadio_prob_no_alberca_umbral_area'
            print process_name
            self.pg_dialog.insert_text(0, process_name)
            self.file_report.write(process_name + "\n")
            QtCore.QCoreApplication.processEvents()
            process_time_start = time.time()

            str_output_regadio_probable_no_alberca_umbral_area_filename = shp_name +".shp"
            str_output_regadio_probable_no_alberca_umbral_area_path = os.path.normcase(os.path.join(str_path_output_workspace,
                                                                                                    str_output_regadio_probable_no_alberca_umbral_area_filename))
            outputs_QGISEXTRACTBYATTRIBUTE_2 = processing.runalg('qgis:extractbyattribute',
                                                                 vlayer_dif_regadio_probable_no_alberca_valid_geom_area,
                                                                 c.CONST_AREA_SINGLEPARTS_FIELDNAME,
                                                                 2,
                                                                 str_umbral_area_ha,
                                                                 str_output_regadio_probable_no_alberca_umbral_area_path)

            vlayer_regadio_probable_no_alberca_umbral_area = QgsVectorLayer(str_output_regadio_probable_no_alberca_umbral_area_path,
                                                                            shp_name,
                                                                            "ogr")
            if not self.load_to_qgis_vlayer(vlayer_regadio_probable_no_alberca_umbral_area,
                                            node_group=node_group_output_subprocess_layers):
                return False

            process_time_end = time.time()
            process_time_total = process_time_end - process_time_start
            self.pg_dialog.insert_text(0, u'  - Tiempo ejecución: ' + str(round(process_time_total)) + " s.")
            self.file_report.write(u'  - Tiempo ejecución: ' + str(round(process_time_total)) + " s." + "\n")
            QtCore.QCoreApplication.processEvents()
            process_number += 1

            # Regadío probable no ALBERCA. Cálculo del identificador unívoco gid ***************************************
            process_name = str(process_number) + u'.- Regadío probable no ALBERCA. Cálculo del identificador unívoco gid'
            if self.is_remove_forest_areas:
                shp_name = "D_casos_"
                shp_name += self.str_aoi_part_filename + "_"
                shp_name += self.str_ndvi_image_filename[:-4] + "_"
                shp_name += str(self.float_umbral_ndvi) + "_"
                shp_name += "area_" + str(self.float_umbral_area)
                shp_name += "_nf"

                current_node_group = node_group_output_subprocess_layers

                current_qml_simbology = c.CONST_STR_CASOS_D_NF_QML

            else:
                shp_name = "A_casos_"
                shp_name += self.str_aoi_part_filename + "_"
                shp_name += self.str_ndvi_image_filename[:-4] + "_"
                shp_name += str(self.float_umbral_ndvi) + "_"
                shp_name += "area_" + str(self.float_umbral_area)

                current_node_group = node_group_result_layers

                current_qml_simbology = c.CONST_STR_CASOS_A_QML

            print process_name
            self.pg_dialog.insert_text(0, process_name)
            self.file_report.write(process_name + "\n")
            QtCore.QCoreApplication.processEvents()
            process_time_start = time.time()

            str_output_regadio_probable_no_alberca_gid_filename = shp_name + ".shp"

            str_output_regadio_probable_no_alberca_gid_path = os.path.normcase(os.path.join(str_path_output_result_dirname,
                                                                                            str_output_regadio_probable_no_alberca_gid_filename))

            outputs_QGISFIELDCALCULATOR_4 = processing.runalg('qgis:fieldcalculator',
                                                              vlayer_regadio_probable_no_alberca_umbral_area,
                                                              c.CONST_GID_CASOS_FIELDNAME,
                                                              1,
                                                              20.0,
                                                              3.0,
                                                              True,
                                                              '$id+1',
                                                              str_output_regadio_probable_no_alberca_gid_path)
            vlayer_regadio_probable_no_alberca_gid = QgsVectorLayer(str_output_regadio_probable_no_alberca_gid_path,
                                                                    shp_name,
                                                                    "ogr")
            str_path_simbology_qml_filename = os.path.normcase(os.path.join(str_simbology_reveladuero_dirname,
                                                                            current_qml_simbology))


            if not self.load_to_qgis_vlayer(vlayer_regadio_probable_no_alberca_gid,
                                            str_path_qml_simbology=str_path_simbology_qml_filename,
                                            node_group=current_node_group):
                return False

            process_time_end = time.time()
            process_time_total = process_time_end - process_time_start
            self.pg_dialog.insert_text(0, u'  - Tiempo ejecución: ' + str(round(process_time_total)) + " s.")
            self.file_report.write(u'  - Tiempo ejecución: ' + str(round(process_time_total)) + " s." + "\n")
            QtCore.QCoreApplication.processEvents()
            process_number += 1

            # priorización de casos ************************************************************************************
            process_name = str(process_number) + u'.- Priorización de casos'
            print process_name
            self.pg_dialog.insert_text(0, process_name)
            self.file_report.write(process_name + "\n")
            QtCore.QCoreApplication.processEvents()
            process_time_start = time.time()

            iter = vlayer_regadio_probable_no_alberca_gid.getFeatures()
            dict_superficies = {}
            for feature in iter:
                current_gid = feature[c.CONST_GID_CASOS_FIELDNAME] - 1  # porque se le incremento en 1 en el paso anterior
                current_area = feature[c.CONST_AREA_SINGLEPARTS_FIELDNAME]
                dict_superficies[current_gid] = current_area

            list_order = sorted(dict_superficies.items(), key=lambda x: x[1], reverse=True)
            top_cases = list_order[:self.num_cases_per_aoi]
            #print top_cases

            vlayer_regadio_probable_no_alberca_gid.startEditing()
            order = 1
            for element in top_cases:
                current_gid = element[0]
                vlayer_regadio_probable_no_alberca_gid.changeAttributeValue(current_gid,
                                                                            c.CONST_ORDER_PRIORITY_FIELDNAME,
                                                                            order)
                order += 1
            vlayer_regadio_probable_no_alberca_gid.commitChanges()

            process_time_end = time.time()
            process_time_total = process_time_end - process_time_start
            self.pg_dialog.insert_text(0, u'  - Tiempo ejecución: ' + str(round(process_time_total)) + " s.")
            self.file_report.write(u'  - Tiempo ejecución: ' + str(round(process_time_total)) + " s." + "\n")
            QtCore.QCoreApplication.processEvents()
            process_number += 1

            # zona con limitaciones especiales y no autorizadas ********************************************************
            process_name = str(process_number) + u'.- Verificando caso contenido en zona con limitaciones específicas o zonas autorizadas'
            print process_name
            self.pg_dialog.insert_text(0, process_name)
            self.file_report.write(process_name + "\n")
            QtCore.QCoreApplication.processEvents()
            process_time_start = time.time()

            str_path_simbology_qml_filename = os.path.normcase(os.path.join(str_simbology_mirameduero_dirname,
                                                                            c.CONST_STR_ZONA_LIMITACIONES_ESPECIFICAS_QML))
            md_zona_limitaciones_especificas_vlayer = self.load_to_qgis_postgis_layer(c.CONST_STR_SCHEMA_CONTROL,
                                                                                      c.CONST_STR_ZONA_LIMITACIONES_ESPECIFICAS_POSTGIS_TABLENAME,
                                                                                      c.CONST_STR_COLUMN_GEOM_NAME,
                                                                                      self.uri,
                                                                                      str_path_qml_simbology=str_path_simbology_qml_filename,
                                                                                      node_group=node_group_output_alberca_layers)

            str_path_simbology_qml_filename = os.path.normcase(os.path.join(str_simbology_mirameduero_dirname,
                                                                            c.CONST_STR_ZONA_NO_AUTORIZADA_QML))
            md_zona_no_autorizada_vlayer = self.load_to_qgis_postgis_layer(c.CONST_STR_SCHEMA_CONTROL,
                                                                           c.CONST_STR_ZONA_NO_AUTORIZADA_POSTGIS_TABLENAME,
                                                                           c.CONST_STR_COLUMN_GEOM_NAME,
                                                                           self.uri,
                                                                           str_path_qml_simbology=str_path_simbology_qml_filename,
                                                                           node_group=node_group_output_alberca_layers)

            iter_regadio_probable = vlayer_regadio_probable_no_alberca_gid.getFeatures()
            vlayer_regadio_probable_no_alberca_gid.startEditing()
            for feature_regadio_probable in iter_regadio_probable:
                current_gid = feature_regadio_probable.id()
                geom_regadio_probable = feature_regadio_probable.geometry()
                iter_limitaciones = md_zona_limitaciones_especificas_vlayer.getFeatures()
                is_intersects_zona_con_limitaciones = False
                for feature_limitacion in iter_limitaciones:
                    geom_limitaciones = feature_limitacion.geometry()
                    if geom_limitaciones.intersects(geom_regadio_probable):
                        is_intersects_zona_con_limitaciones = True
                        break

                iter_no_autorizada = md_zona_no_autorizada_vlayer.getFeatures()
                is_intersects_zona_no_autorizable = False
                for feature_no_autorizada in iter_no_autorizada:
                    geom_no_autorizada = feature_no_autorizada.geometry()
                    if geom_no_autorizada.intersects(geom_regadio_probable):
                        is_intersects_zona_no_autorizable = True
                        break

                if is_intersects_zona_no_autorizable:
                    str_zona_no_autorizable = "Zona no autorizada"
                else:
                    if is_intersects_zona_con_limitaciones:
                        str_zona_no_autorizable = "Zona con limitaciones"
                    else:
                        str_zona_no_autorizable = "No"

                vlayer_regadio_probable_no_alberca_gid.changeAttributeValue(current_gid,
                                                                            c.CONST_ORDER_ZONA_NO_AUTORIZADA_FIELDNAME,
                                                                            str_zona_no_autorizable)
            vlayer_regadio_probable_no_alberca_gid.commitChanges()

            process_time_end = time.time()
            process_time_total = process_time_end - process_time_start
            self.pg_dialog.insert_text(0, u'  - Tiempo ejecución: ' + str(round(process_time_total)) + " s.")
            self.file_report.write(u'  - Tiempo ejecución: ' + str(round(process_time_total)) + " s." + "\n")
            QtCore.QCoreApplication.processEvents()
            process_number += 1

        if self.is_estimacion_sup_regada:
            process_name = str(process_number) + u'.- Calculando la superficie estimada'
            print process_name
            self.pg_dialog.insert_text(0, process_name)
            self.file_report.write(process_name + "\n")
            QtCore.QCoreApplication.processEvents()
            process_time_start = time.time()

            iter = vlayer_umbral_area.getFeatures()
            area_regada = 0.0
            casos_regadio_probable_number = 0
            for feature in iter:
                # retrieve every feature with its geometry and attributes
                geom = feature.geometry()  # fetch geometry
                current_area = geom.area()
                area_regada += current_area / 10000
                casos_regadio_probable_number += 1

            str_title = c.CONST_REVELADUERO_TITLE_VERSION
            str_msg_text = u'Estimación área regada: ' + "%.2f" % area_regada + " ha.\n"
            str_msg_text += u'Número de recintos identificados: ' + str(casos_regadio_probable_number)
            # str_msg_informative_text = "informative text"
            str_msg_detailed_text = str_msg_input_data

            msg = QMessageBox()
            msg.setIcon(QMessageBox.Information)
            msg.setWindowTitle(str_title)
            msg.setText(str_msg_text)
            # msg.setInformativeText(str_msg_informative_text)
            msg.setToolTip(str_msg_detailed_text)
            # msg.setDetailedText(str_msg_detailed_text)
            msg.exec_()

            process_time_end = time.time()
            process_time_total = process_time_end - process_time_start
            self.pg_dialog.insert_text(0, u'  - Tiempo ejecución: ' + str(round(process_time_total)) + " s.")
            self.file_report.write(u'  - Tiempo ejecución: ' + str(round(process_time_total)) + " s." + "\n")
            QtCore.QCoreApplication.processEvents()
            process_number += 1

        if self.is_generacion_casos and self.is_aoi_shapefile:
            # Intersección cartodroid ttmm sigpac x manchurrones *******************************************************
            process_name = str(process_number) + u'.- Cruce regadío probable no ALBERCA x ttmm SIGPAC'
            shp_name = str(process_number) + u'_regadio_probable_no_alberca_x_ttmm_sigpac'
            print process_name
            self.pg_dialog.insert_text(0, process_name)
            self.file_report.write(process_name + "\n")
            QtCore.QCoreApplication.processEvents()
            process_time_start = time.time()

            str_output_regadio_probable_no_alberca_x_ttmm_sigpac_filename = shp_name + ".shp"
            str_output_regadio_probable_no_alberca_x_ttmm_sigpac_path = os.path.normcase(os.path.join(str_path_output_workspace,
                                                                                                      str_output_regadio_probable_no_alberca_x_ttmm_sigpac_filename))
            outputs_SAGAINTERSECT_1 = processing.runalg('saga:intersect',
                                                        cartodroid_ttmm_sigpac_vlayer,
                                                        vlayer_regadio_probable_no_alberca_gid,
                                                        True,
                                                        str_output_regadio_probable_no_alberca_x_ttmm_sigpac_path)
            vlayer_regadio_probable_no_alberca_x_ttmm_sigpac = QgsVectorLayer(str_output_regadio_probable_no_alberca_x_ttmm_sigpac_path,
                                                                              shp_name,
                                                                              "ogr")
            if not self.load_to_qgis_vlayer(vlayer_regadio_probable_no_alberca_x_ttmm_sigpac,
                                            node_group=node_group_output_subprocess_layers):
                return False

            process_time_end = time.time()
            process_time_total = process_time_end - process_time_start
            self.pg_dialog.insert_text(0, u'  - Tiempo ejecución: ' + str(round(process_time_total)) + " s.")
            self.file_report.write(u'  - Tiempo ejecución: ' + str(round(process_time_total)) + " s." + "\n")
            QtCore.QCoreApplication.processEvents()
            process_number += 1

            # obtención de lista de municipios incluidos en la capa de manchurrones ************************************
            process_name = str(process_number) + u'.- Obtención de lista de cod_muni de ttmm incluidos en la capa de regadío probable'
            print process_name
            self.pg_dialog.insert_text(0, process_name)
            self.file_report.write(process_name + "\n")
            QtCore.QCoreApplication.processEvents()
            process_time_start = time.time()

            iter = vlayer_regadio_probable_no_alberca_x_ttmm_sigpac.getFeatures()
            list_cod_muni = []
            for feature in iter:
                current_cod_muni = feature[c.CONST_STR_COD_PROVMUN_SIGPAC]
                if current_cod_muni not in list_cod_muni:
                    list_cod_muni.append(current_cod_muni)

            #print list_cod_muni

            process_time_end = time.time()
            process_time_total = process_time_end - process_time_start
            self.pg_dialog.insert_text(0, u'  - Tiempo ejecución: ' + str(round(process_time_total)) + " s.")
            self.file_report.write(u'  - Tiempo ejecución: ' + str(round(process_time_total)) + " s." + "\n")
            QtCore.QCoreApplication.processEvents()
            process_number += 1

            # Obtención de las vlayer del PostGIS **********************************************************************
            process_name = str(process_number) + u'.- Obtiene capa recintos SIGPAC merged'
            print process_name
            self.pg_dialog.insert_text(0, process_name)
            self.file_report.write(process_name + "\n")
            QtCore.QCoreApplication.processEvents()
            process_time_start = time.time()

            feats = []
            str_path_simbology_qml_filename = os.path.normcase(os.path.join(str_simbology_sigpac_dirname,
                                                                            c.CONST_STR_RECINTOS_SIGPAC_QML))
            for str_current_cod_muni_list in list_cod_muni:
                cartodroid_recintos_tm_sigpac_vlayer = self.get_recintos_sigpac_postgis_layer(str_current_cod_muni_list,
                                                                                              c.CONST_STR_SCHEMA_SIGPAC_2017,
                                                                                              c.CONST_STR_COLUMN_GEOM_NAME,
                                                                                              self.uri,
                                                                                              str_path_simbolgy=str_path_simbology_qml_filename,
                                                                                              str_node_group=node_group_output_sigpac_layers)
                if not cartodroid_recintos_tm_sigpac_vlayer:
                    return False

                for feat in cartodroid_recintos_tm_sigpac_vlayer.getFeatures():
                    geom = feat.geometry()
                    attrs = feat.attributes()
                    feature = QgsFeature()
                    feature.setGeometry(geom)
                    feature.setAttributes(attrs)
                    feats.append(feature)

            process_time_end = time.time()
            process_time_total = process_time_end - process_time_start
            self.pg_dialog.insert_text(0, u'  - Tiempo ejecución: ' + str(round(process_time_total)) + " s.")
            self.file_report.write(u'  - Tiempo ejecución: ' + str(round(process_time_total)) + " s." + "\n")
            QtCore.QCoreApplication.processEvents()
            process_number += 1

            # Añadiendo entidades gráficas a la capa memory fusionada **************************************************
            field_list = cartodroid_recintos_tm_sigpac_vlayer.dataProvider().fields().toList()

            process_name = str(process_number) + u'.- Añadiendo entidades gráficas a la capa fusionada'
            memory_layer_name = str(process_number) + "_recintos_SIGPAC_merged"
            print process_name
            self.pg_dialog.insert_text(0, process_name)
            self.file_report.write(process_name + "\n")
            QtCore.QCoreApplication.processEvents()
            process_time_start = time.time()

            v_merged_layer = QgsVectorLayer('Polygon?crs=EPSG:25830',
                                            memory_layer_name,
                                            "memory")
            prov = v_merged_layer.dataProvider()
            prov.addAttributes(field_list)
            v_merged_layer.updateFields()
            v_merged_layer.startEditing()
            prov.addFeatures(feats)
            v_merged_layer.commitChanges()
            process_number += 1

            str_path_simbology_qml_filename = os.path.normcase(
                os.path.join(str_simbology_sigpac_dirname, c.CONST_STR_RECINTOS_SIGPAC_QML))
            if not self.load_to_qgis_vlayer(v_merged_layer,
                                            str_path_qml_simbology=str_path_simbology_qml_filename,
                                            node_group=node_group_output_sigpac_layers):
                return False

            process_time_end = time.time()
            process_time_total = process_time_end - process_time_start
            self.pg_dialog.insert_text(0, u'  - Tiempo ejecución: ' + str(round(process_time_total)) + " s.")
            self.file_report.write(u'  - Tiempo ejecución: ' + str(round(process_time_total)) + " s." + "\n")
            QtCore.QCoreApplication.processEvents()
            process_number += 1

            # Intersectar vlayer anterior x manchurrones ***************************************************************
            process_name = str(process_number) + u'.- Regadío probable no ALBERCA x Recintos SIGPAC'
            if self.is_remove_forest_areas:
                shp_name = "A_casos_"
                shp_name += self.str_aoi_part_filename + "_"
                shp_name += self.str_ndvi_image_filename[:-4] + "_"
                shp_name += str(self.float_umbral_ndvi) + "_"
                shp_name += "area_" + str(self.float_umbral_area) + "_"
                shp_name += "sigpac_nf"

                current_qml_simbology = c.CONST_STR_CASOS_A_NF_QML

            else:
                shp_name = "B_casos_"
                shp_name += self.str_aoi_part_filename + "_"
                shp_name += self.str_ndvi_image_filename[:-4] + "_"
                shp_name += str(self.float_umbral_ndvi) + "_"
                shp_name += "area_" + str(self.float_umbral_area) + "_"
                shp_name += "sigpac"

                current_qml_simbology = c.CONST_STR_CASOS_B_QML


            print process_name
            self.pg_dialog.insert_text(0, process_name)
            self.file_report.write(process_name + "\n")
            QtCore.QCoreApplication.processEvents()
            process_time_start = time.time()

            str_output_regadio_probable_no_alberca_x_recintos_sigpac_filename = shp_name + ".shp"
            str_output_regadio_probable_no_alberca_x_recintos_sigpac_path = os.path.normcase(os.path.join(str_path_output_result_dirname,
                                                                                                          str_output_regadio_probable_no_alberca_x_recintos_sigpac_filename))
            outputs_SAGAINTERSECT_1 = processing.runalg('saga:intersect',
                                                        v_merged_layer,
                                                        vlayer_regadio_probable_no_alberca_gid,
                                                        True,
                                                        str_output_regadio_probable_no_alberca_x_recintos_sigpac_path)
            vlayer_regadio_probable_no_alberca_x_recintos_sigpac = QgsVectorLayer(str_output_regadio_probable_no_alberca_x_recintos_sigpac_path,
                                                                                  shp_name,
                                                                                  "ogr")
            str_path_simbology_qml_filename = os.path.normcase(os.path.join(str_simbology_reveladuero_dirname,
                                                                            current_qml_simbology))
            if not self.load_to_qgis_vlayer(vlayer_regadio_probable_no_alberca_x_recintos_sigpac,
                                            str_path_qml_simbology=str_path_simbology_qml_filename,
                                            node_group=node_group_result_layers):
                return False

            str_msg_num_features = u'  - Regadío probable no ALBERCA [' + str(v_merged_layer.featureCount()) + "] x "
            str_msg_num_features += u'Núcleos de población [' + str(vlayer_regadio_probable_no_alberca_gid.featureCount()) + "] = "
            str_msg_num_features += u'Intersección [' + str(vlayer_regadio_probable_no_alberca_x_recintos_sigpac.featureCount()) + "]"
            self.pg_dialog.insert_text(0, str_msg_num_features)
            self.file_report.write(str_msg_num_features + "\n")

            process_time_end = time.time()
            process_time_total = process_time_end - process_time_start
            self.pg_dialog.insert_text(0, u'  - Tiempo ejecución: ' + str(round(process_time_total)) + " s.")
            self.file_report.write(u'  - Tiempo ejecución: ' + str(round(process_time_total)) + " s." + "\n")
            QtCore.QCoreApplication.processEvents()
            process_number += 1

        if self.is_generacion_casos and self.is_aoi_cod_municipio:
            # obtención de la vlayer del PostGIS
            str_path_simbology_qml_filename = os.path.normcase(os.path.join(str_simbology_sigpac_dirname,
                                                                            c.CONST_STR_RECINTOS_SIGPAC_QML))

            cartodroid_recintos_tm_sigpac_vlayer = self.get_recintos_sigpac_postgis_layer(self.str_cod_municipio,
                                                                                          c.CONST_STR_SCHEMA_SIGPAC_2017,
                                                                                          c.CONST_STR_COLUMN_GEOM_NAME,
                                                                                          self.uri,
                                                                                          str_path_simbolgy=str_path_simbology_qml_filename,
                                                                                          str_node_group=node_group_output_sigpac_layers)
            if not cartodroid_recintos_tm_sigpac_vlayer:
                return False

            # Regadío probable no ALBERCA x Recintos SIGPAC del término municipal **************************************
            process_name = str(process_number) + u'.- Regadío probable no ALBERCA x Recintos SIGPAC del término municipal'
            if self.is_remove_forest_areas:
                shp_name = "A_casos_"
                shp_name += self.str_aoi_part_filename + "_"
                shp_name += self.str_ndvi_image_filename[:-4] + "_"
                shp_name += str(self.float_umbral_ndvi) + "_"
                shp_name += "area_" + str(self.float_umbral_area) + "_"
                shp_name += "sigpac_nf"

                current_qml_simbology = c.CONST_STR_CASOS_A_NF_QML

            else:
                shp_name = "B_casos_"
                shp_name += self.str_aoi_part_filename + "_"
                shp_name += self.str_ndvi_image_filename[:-4] + "_"
                shp_name += str(self.float_umbral_ndvi) + "_"
                shp_name += "area_" + str(self.float_umbral_area) + "_"
                shp_name += "sigpac"

                current_qml_simbology = c.CONST_STR_CASOS_B_QML

            print process_name
            self.pg_dialog.insert_text(0, process_name)
            self.file_report.write(process_name + "\n")
            QtCore.QCoreApplication.processEvents()
            process_time_start = time.time()

            str_output_regadio_probable_no_alberca_x_recintos_sigpac_filename = shp_name + ".shp"
            str_output_regadio_probable_no_alberca_x_recintos_sigpac_path = os.path.normcase(os.path.join(str_path_output_result_dirname,
                                                                                                          str_output_regadio_probable_no_alberca_x_recintos_sigpac_filename))
            outputs_SAGAINTERSECT_1 = processing.runalg('saga:intersect',
                                                        cartodroid_recintos_tm_sigpac_vlayer,
                                                        vlayer_regadio_probable_no_alberca_gid,
                                                        True,
                                                        str_output_regadio_probable_no_alberca_x_recintos_sigpac_path)
            vlayer_regadio_probable_no_alberca_x_recintos_sigpac = QgsVectorLayer(str_output_regadio_probable_no_alberca_x_recintos_sigpac_path,
                                                                                  shp_name,
                                                                                  "ogr")
            str_path_simbology_qml_filename = os.path.normcase(os.path.join(str_simbology_reveladuero_dirname,
                                                                            current_qml_simbology))
            if not self.load_to_qgis_vlayer(vlayer_regadio_probable_no_alberca_x_recintos_sigpac,
                                            str_path_qml_simbology=str_path_simbology_qml_filename,
                                            node_group=node_group_result_layers):
                return False
            process_time_end = time.time()
            process_time_total = process_time_end - process_time_start
            self.pg_dialog.insert_text(0, u'  - Tiempo ejecución: ' + str(round(process_time_total)) + " s.")
            self.file_report.write(u'  - Tiempo ejecución: ' + str(round(process_time_total)) + " s." + "\n")
            QtCore.QCoreApplication.processEvents()
            process_number += 1

        if self.is_generacion_casos:
            # Regadío probable no ALBERCA x Recintos SIGPAC. Validación geométrica *************************************
            process_name = str(process_number) + u'.- Regadío probable no ALBERCA x Recintos SIGPAC. Validación geométrica'
            shp_name = str(process_number) + "_regadio_probable_no_alberca_x_ttmm_sigpac"
            print process_name
            self.pg_dialog.insert_text(0, process_name)
            self.file_report.write(process_name + "\n")
            QtCore.QCoreApplication.processEvents()
            process_time_start = time.time()

            str_output_regadio_probable_no_alberca_x_ttmm_sigpac_valid_geom_filename = shp_name + "_valid_geom.shp"
            str_output_regadio_probable_no_alberca_x_ttmm_sigpac_valid_geom_path = os.path.normcase(os.path.join(str_path_output_workspace,
                                                                                                                 str_output_regadio_probable_no_alberca_x_ttmm_sigpac_valid_geom_filename))
            str_output_regadio_probable_no_alberca_x_ttmm_sigpac_invalid_geom_filename = shp_name + "_invalid_geom.shp"
            str_output_regadio_probable_no_alberca_x_ttmm_sigpac_invalid_geom_path = os.path.normcase(os.path.join(str_path_output_workspace,
                                                                                                                   str_output_regadio_probable_no_alberca_x_ttmm_sigpac_invalid_geom_filename))
            str_output_regadio_probable_no_alberca_x_ttmm_sigpac_error_geom_filename = shp_name + "_error_geom.shp"
            str_output_regadio_probable_no_alberca_x_ttmm_sigpac_error_geom_path = os.path.normcase(os.path.join(str_path_output_workspace,
                                                                                                                 str_output_regadio_probable_no_alberca_x_ttmm_sigpac_error_geom_filename))
            outputs_QGISCHECKVALIDITY_2 = processing.runalg('qgis:checkvalidity',
                                                            vlayer_regadio_probable_no_alberca_x_recintos_sigpac,
                                                            2,
                                                            str_output_regadio_probable_no_alberca_x_ttmm_sigpac_valid_geom_path,
                                                            str_output_regadio_probable_no_alberca_x_ttmm_sigpac_invalid_geom_path,
                                                            str_output_regadio_probable_no_alberca_x_ttmm_sigpac_error_geom_path)

            vlayer_regadio_probable_no_alberca_x_ttmm_sigpac_valid_geom = QgsVectorLayer(str_output_regadio_probable_no_alberca_x_ttmm_sigpac_valid_geom_path,
                                                                                         shp_name + "_valid_geom",
                                                                                         "ogr")

            if not self.load_to_qgis_vlayer(vlayer_regadio_probable_no_alberca_x_ttmm_sigpac_valid_geom,
                                            node_group=node_group_output_subprocess_layers):
                return False
            vlayer_regadio_probable_no_alberca_x_ttmm_sigpac_invalid_geom = QgsVectorLayer(str_output_regadio_probable_no_alberca_x_ttmm_sigpac_invalid_geom_path,
                                                                                         shp_name + "_invalid_geom",
                                                                                         "ogr")
            if not self.load_to_qgis_vlayer(vlayer_regadio_probable_no_alberca_x_ttmm_sigpac_invalid_geom,
                                            node_group=node_group_output_subprocess_layers):
                return False
            vlayer_regadio_probable_no_alberca_x_ttmm_sigpac_error_geom = QgsVectorLayer(str_output_regadio_probable_no_alberca_x_ttmm_sigpac_error_geom_path,
                                                                                         shp_name + "_error_geom",
                                                                                         "ogr")
            if not self.load_to_qgis_vlayer(vlayer_regadio_probable_no_alberca_x_ttmm_sigpac_error_geom,
                                            node_group=node_group_output_subprocess_layers):
                return False

            process_time_end = time.time()
            process_time_total = process_time_end - process_time_start
            self.pg_dialog.insert_text(0, u'  - Tiempo ejecución: ' + str(round(process_time_total)) + " s.")
            self.file_report.write(u'  - Tiempo ejecución: ' + str(round(process_time_total)) + " s." + "\n")
            QtCore.QCoreApplication.processEvents()
            process_number += 1

            # Regadío probable no ALBERCA x Recintos SIGPAC. Multiparte a parte sencilla *******************************
            process_name = str(process_number) + u'.- Regadío probable no ALBERCA x Recintos SIGPAC. Multiparte a parte sencilla'
            shp_name = str(process_number) + "_regadio_probable_no_alberca_x_ttmm_sigpac_singleparts"
            print process_name
            self.pg_dialog.insert_text(0, process_name)
            self.file_report.write(process_name + "\n")
            QtCore.QCoreApplication.processEvents()
            process_time_start = time.time()

            str_output_regadio_probable_no_alberca_x_ttmm_sigpac_singleparts_filename = shp_name + ".shp"
            str_output_regadio_probable_no_alberca_x_ttmm_sigpac_singleparts_path = os.path.normcase(os.path.join(str_path_output_workspace,
                                                                                                                  str_output_regadio_probable_no_alberca_x_ttmm_sigpac_singleparts_filename))
            outputs_QGISMULTIPARTTOSINGLEPARTS_2 = processing.runalg('qgis:multiparttosingleparts',
                                                                     vlayer_regadio_probable_no_alberca_x_ttmm_sigpac_valid_geom,
                                                                     str_output_regadio_probable_no_alberca_x_ttmm_sigpac_singleparts_path)
            vlayer_regadio_probable_no_alberca_x_ttmm_sigpac_singleparts = QgsVectorLayer(str_output_regadio_probable_no_alberca_x_ttmm_sigpac_singleparts_path,
                                                                                          shp_name,
                                                                                          "ogr")
            if not self.load_to_qgis_vlayer(vlayer_regadio_probable_no_alberca_x_ttmm_sigpac_singleparts,
                                            node_group=node_group_output_subprocess_layers):
                return False

            process_time_end = time.time()
            process_time_total = process_time_end - process_time_start
            self.pg_dialog.insert_text(0, u'  - Tiempo ejecución: ' + str(round(process_time_total)) + " s.")
            self.file_report.write(u'  - Tiempo ejecución: ' + str(round(process_time_total)) + " s." + "\n")
            QtCore.QCoreApplication.processEvents()
            process_number += 1

            # Regadío probable no ALBERCA x Recintos SIGPAC. Cálculo del área ******************************************
            process_name = str(process_number) + u'.- Regadío probable no ALBERCA x Recintos SIGPAC. Cálculo del área'
            shp_name = str(process_number) + "_regadio_probable_no_alberca_x_ttmm_sigpac_area"
            print process_name
            self.pg_dialog.insert_text(0, process_name)
            self.file_report.write(process_name + "\n")
            QtCore.QCoreApplication.processEvents()
            process_time_start = time.time()

            str_output_regadio_probable_no_alberca_x_ttmm_sigpac_singleparts_area_filename = shp_name +".shp"
            str_output_regadio_probable_no_alberca_x_ttmm_sigpac_singleparts_area_path = os.path.normcase(os.path.join(str_path_output_workspace,
                                                                                                                       str_output_regadio_probable_no_alberca_x_ttmm_sigpac_singleparts_area_filename))
            outputs_QGISFIELDCALCULATOR_3 = processing.runalg('qgis:fieldcalculator',
                                                              vlayer_regadio_probable_no_alberca_x_ttmm_sigpac_singleparts,
                                                              c.CONST_AREA_SINGLEPARTS_REGADIO_PROBABLE_NO_ALBERCA_X_TTMM_SIGPAC_FIELDNAME,
                                                              0,
                                                              20.0,
                                                              4.0,
                                                              True,
                                                              '$area/10000',
                                                              str_output_regadio_probable_no_alberca_x_ttmm_sigpac_singleparts_area_path)
            vlayer_regadio_probable_no_alberca_x_ttmm_sigpac_singleparts_area = QgsVectorLayer(str_output_regadio_probable_no_alberca_x_ttmm_sigpac_singleparts_area_path,
                                                                                               shp_name,
                                                                                               "ogr")
            if not self.load_to_qgis_vlayer(vlayer_regadio_probable_no_alberca_x_ttmm_sigpac_singleparts_area,
                                            node_group=node_group_output_subprocess_layers):
                return False
            process_time_end = time.time()
            process_time_total = process_time_end - process_time_start
            self.pg_dialog.insert_text(0, u'  - Tiempo ejecución: ' + str(round(process_time_total)) + " s.")
            self.file_report.write(u'  - Tiempo ejecución: ' + str(round(process_time_total)) + " s." + "\n")
            QtCore.QCoreApplication.processEvents()
            process_number += 1

            # Regadío probable no ALBERCA x Recintos SIGPAC. Selección recintos por encima de umbral area***************
            process_name = str(process_number) + u'.- Regadío probable no ALBERCA x Recintos SIGPAC. Recintos por encima umbral área'
            shp_name = str(process_number) + "_regadio_probable_no_alberca_x_ttmm_sigpac_umbral_area"
            print process_name
            self.pg_dialog.insert_text(0, process_name)
            self.file_report.write(process_name + "\n")
            QtCore.QCoreApplication.processEvents()
            process_time_start = time.time()

            str_output_regadio_probable_no_alberca_x_ttmm_sigpac_umbral_area_filename = shp_name + ".shp"
            str_output_regadio_probable_no_alberca_x_ttmm_sigpac_umbral_area_path = os.path.normcase(os.path.join(str_path_output_workspace,
                                                                                                                  str_output_regadio_probable_no_alberca_x_ttmm_sigpac_umbral_area_filename))
            outputs_QGISEXTRACTBYATTRIBUTE_3 = processing.runalg('qgis:extractbyattribute',
                                                                 vlayer_regadio_probable_no_alberca_x_ttmm_sigpac_singleparts_area,
                                                                 c.CONST_AREA_SINGLEPARTS_REGADIO_PROBABLE_NO_ALBERCA_X_TTMM_SIGPAC_FIELDNAME,
                                                                 2,
                                                                 str_umbral_area_artificios_ha,
                                                                 str_output_regadio_probable_no_alberca_x_ttmm_sigpac_umbral_area_path)

            vlayer_regadio_probable_no_alberca_x_ttmm_sigpac_umbral_area = QgsVectorLayer(str_output_regadio_probable_no_alberca_x_ttmm_sigpac_umbral_area_path,
                                                                                          shp_name,
                                                                                          "ogr")
            if not self.load_to_qgis_vlayer(vlayer_regadio_probable_no_alberca_x_ttmm_sigpac_umbral_area,
                                            node_group=node_group_output_subprocess_layers):
                return False
            process_time_end = time.time()
            process_time_total = process_time_end - process_time_start
            self.pg_dialog.insert_text(0, u'  - Tiempo ejecución: ' + str(round(process_time_total)) + " s.")
            self.file_report.write(u'  - Tiempo ejecución: ' + str(round(process_time_total)) + " s." + "\n")
            QtCore.QCoreApplication.processEvents()
            process_number += 1

            # porcentaje de superficie con respuesta de cada recinto SIGPAC
            str_name_vlayer_regadio_probable_no_alberca_x_recintos_sigpac_percentage = str(process_number) + u'.- Cálculo del porcentaje área resultado / área original recinto SIGPAC'
            print str_name_vlayer_regadio_probable_no_alberca_x_recintos_sigpac_percentage
            self.pg_dialog.insert_text(0, str_name_vlayer_regadio_probable_no_alberca_x_recintos_sigpac_percentage)
            QtCore.QCoreApplication.processEvents()

            str_percentage_operation = '"' + c.CONST_AREA_SINGLEPARTS_REGADIO_PROBABLE_NO_ALBERCA_X_TTMM_SIGPAC_FIELDNAME + '"'
            str_percentage_operation += '/("' + c.CONST_STR_AREA_RECINTOS_SIGPAC_FIELDNAME + '"/10000)'

            str_output_regadio_probable_no_alberca_x_ttmm_sigpac_percentage_filename = str(process_number) + "_regadio_probable_no_alberca_x_ttmm_sigpac_percentage.shp"
            str_output_regadio_probable_no_alberca_x_ttmm_sigpac_percentage_path = os.path.normcase(os.path.join(str_path_output_workspace,
                                                                                                                 str_output_regadio_probable_no_alberca_x_ttmm_sigpac_percentage_filename))
            outputs_QGISFIELDCALCULATOR_5 = processing.runalg('qgis:fieldcalculator',
                                                              vlayer_regadio_probable_no_alberca_x_ttmm_sigpac_umbral_area,
                                                              c.CONST_PERCENTAGE_FIELDNAME,
                                                              0,
                                                              20.0,
                                                              3.0,
                                                              True,
                                                              str_percentage_operation,
                                                              str_output_regadio_probable_no_alberca_x_ttmm_sigpac_percentage_path)
            process_number += 1

            vlayer_regadio_probable_no_alberca_x_ttmm_sigpac_percentage = QgsVectorLayer(str_output_regadio_probable_no_alberca_x_ttmm_sigpac_percentage_path,
                                                                                         str_name_vlayer_regadio_probable_no_alberca_x_recintos_sigpac_percentage,
                                                                                         "ogr")
            if not self.load_to_qgis_vlayer(vlayer_regadio_probable_no_alberca_x_ttmm_sigpac_percentage,
                                            node_group=node_group_output_subprocess_layers):
                return False

            # cruce con los sectores de GF
            process_name = str(process_number) + u'.- Regadío probable no ALBERCA x Recintos SIGPAC. Cruce con Sectores GF'
            print process_name
            self.pg_dialog.insert_text(0, process_name)
            self.file_report.write(process_name + "\n")
            QtCore.QCoreApplication.processEvents()
            process_time_start = time.time()

            str_path_simbology_qml_filename = os.path.normcase(os.path.join(str_simbology_mirameduero_dirname,
                                                                            c.CONST_STR_SECTORES_GF))
            md_sector_gf = self.load_to_qgis_postgis_layer(c.CONST_STR_SCHEMA_CONTROL,
                                                           c.CONST_STR_SECTORES_GUARDERIA_FLUVIAL_POSTGIS_TABLENAME,
                                                           c.CONST_STR_COLUMN_GEOM_NAME,
                                                           self.uri,
                                                           str_path_qml_simbology=str_path_simbology_qml_filename,
                                                           node_group=node_group_output_alberca_layers)


            if self.is_remove_forest_areas:
                shp_name = str(process_number) + "_regadio_probable_no_alberca_x_ttmm_sigpac_x_sectoresgf"

                current_path_output = str_path_output_workspace

                current_node_group = node_group_output_subprocess_layers

            else:
                shp_name = "C_casos_"
                shp_name += self.str_aoi_part_filename + "_"
                shp_name += self.str_ndvi_image_filename[:-4] + "_"
                shp_name += str(self.float_umbral_ndvi) + "_"
                shp_name += "area_" + str(self.float_umbral_area) + "_"
                shp_name += "sigpac_gf"


                current_path_output = str_path_output_result_dirname

                current_node_group = node_group_result_layers

            str_output_regadio_probable_no_alberca_x_recintos_sigpac_x_sectores_gf_filename = shp_name + ".shp"


            str_output_regadio_probable_no_alberca_x_recintos_sigpac_x_sectores_gf_path = os.path.normcase(os.path.join(current_path_output,
                                                                                                                        str_output_regadio_probable_no_alberca_x_recintos_sigpac_x_sectores_gf_filename))

            outputs_SAGAINTERSECT_2 = processing.runalg('saga:intersect',
                                                        vlayer_regadio_probable_no_alberca_x_ttmm_sigpac_percentage,
                                                        md_sector_gf,
                                                        True,
                                                        str_output_regadio_probable_no_alberca_x_recintos_sigpac_x_sectores_gf_path)
            vlayer_regadio_probable_no_alberca_x_recintos_sigpac_sectores_gf = QgsVectorLayer(str_output_regadio_probable_no_alberca_x_recintos_sigpac_x_sectores_gf_path,
                                                                                              shp_name,
                                                                                              "ogr")
            str_path_simbology_qml_filename = os.path.normcase(os.path.join(str_simbology_reveladuero_dirname,
                                                                            c.CONST_STR_CASOS_C_QML))

            str_msg_num_features = u'  - Regadío probable no ALBERCA x Recintos SIGPAC [' + str(vlayer_regadio_probable_no_alberca_x_ttmm_sigpac_percentage.featureCount()) + "] x "
            str_msg_num_features += u'Cruce con Sectores GF [' + str(md_sector_gf.featureCount()) + "] = "
            str_msg_num_features += u'Intersección [' + str(vlayer_regadio_probable_no_alberca_x_recintos_sigpac_sectores_gf.featureCount()) + "]"
            self.pg_dialog.insert_text(0, str_msg_num_features)
            self.file_report.write(str_msg_num_features + "\n")

            if not self.load_to_qgis_vlayer(vlayer_regadio_probable_no_alberca_x_recintos_sigpac_sectores_gf,
                                            str_path_qml_simbology=str_path_simbology_qml_filename,
                                            node_group=current_node_group):
                return False

            extent = vlayer_regadio_probable_no_alberca_x_recintos_sigpac_sectores_gf.extent()
            self.iface.mapCanvas().setExtent(extent)

            process_time_end = time.time()
            process_time_total = process_time_end - process_time_start
            self.pg_dialog.insert_text(0, u'  - Tiempo ejecución: ' + str(round(process_time_total)) + " s.")
            self.file_report.write(u'  - Tiempo ejecución: ' + str(round(process_time_total)) + " s." + "\n")
            QtCore.QCoreApplication.processEvents()
            process_number += 1

            if self.is_remove_forest_areas:
                process_name = str(process_number) + u'.- Regadío probable no ALBERCA x Recintos SIGPAC x Sectores GF filtrado no forestal'
                shp_name = "B_casos_"
                shp_name += self.str_aoi_part_filename + "_"
                shp_name += self.str_ndvi_image_filename[:-4] + "_"
                shp_name += str(self.float_umbral_ndvi) + "_"
                shp_name += "area_" + str(self.float_umbral_area) + "_"
                shp_name += "sigpac_gf_nf"

                print process_name
                self.pg_dialog.insert_text(0, process_name)
                self.file_report.write(process_name + "\n")
                QtCore.QCoreApplication.processEvents()
                process_time_start = time.time()

                str_sql_where_clausule_filtered = ""
                for uso_sigpac_to_filtered in c.CONST_LIST_USOS_SIGPAC_TO_FILTERED:
                    str_sql_where_clausule_filtered += "\"C_USO_SIGP\" != '" + uso_sigpac_to_filtered + "'" + " AND "
                str_sql_where_clausule_filtered_formateada = str_sql_where_clausule_filtered[:-4]

                str_output_regadio_probable_no_alberca_x_recintos_sigpac_x_sectores_gf_not_forest_filename = shp_name + ".shp"
                str_output_regadio_probable_no_alberca_x_recintos_sigpac_x_sectores_gf_no_forest_path = os.path.normcase(os.path.join(str_path_output_result_dirname,
                                                                                                                                      str_output_regadio_probable_no_alberca_x_recintos_sigpac_x_sectores_gf_not_forest_filename))
                outputs_QGISEXTRACTBYEXPRESSION_1 = processing.runalg('qgis:extractbyexpression',
                                                                      vlayer_regadio_probable_no_alberca_x_recintos_sigpac_sectores_gf,
                                                                      str_sql_where_clausule_filtered_formateada,
                                                                      str_output_regadio_probable_no_alberca_x_recintos_sigpac_x_sectores_gf_no_forest_path)
                process_number += 1

                vlayer_regadio_probable_no_alberca_x_recintos_sigpac_sectores_gf_no_forest = QgsVectorLayer(str_output_regadio_probable_no_alberca_x_recintos_sigpac_x_sectores_gf_no_forest_path,
                                                                                                            shp_name,
                                                                                                            "ogr")
                str_path_simbology_qml_filename = os.path.normcase(os.path.join(str_simbology_reveladuero_dirname,
                                                                                c.CONST_STR_CASOS_B_NF_QML))
                if not self.load_to_qgis_vlayer(vlayer_regadio_probable_no_alberca_x_recintos_sigpac_sectores_gf_no_forest,
                                                str_path_qml_simbology=str_path_simbology_qml_filename,
                                                node_group=node_group_result_layers):
                    return False

                process_time_end = time.time()
                process_time_total = process_time_end - process_time_start
                self.pg_dialog.insert_text(0, u'  - Tiempo ejecución: ' + str(round(process_time_total)) + " s.")
                self.file_report.write(u'  - Tiempo ejecución: ' + str(round(process_time_total)) + " s." + "\n")
                QtCore.QCoreApplication.processEvents()
                process_number += 1

                # Regadío probable no ALBERCA original - casos uso forestales y otros **********************************
                process_name = str(process_number) + u'.- Regadío probable no ALBERCA original - casos uso forestales y otros'
                shp_name = str(process_number) + "_regadio_probable_no_forestal"
                print process_name
                self.pg_dialog.insert_text(0, process_name)
                self.file_report.write(process_name + "\n")
                QtCore.QCoreApplication.processEvents()
                process_time_start = time.time()

                str_output_diffsaga_shapefile = shp_name + ".shp"
                str_output_diffsaga_path = os.path.normcase(os.path.join(str_path_output_workspace,
                                                                         str_output_diffsaga_shapefile))
                outputs_SAGADIFFERENCE = processing.runalg('saga:difference',
                                                           vlayer_regadio_probable_no_alberca_gid,
                                                           vlayer_regadio_probable_no_alberca_x_recintos_sigpac_sectores_gf_no_forest,
                                                           True,
                                                           str_output_diffsaga_path)
                vlayer_difsaga = QgsVectorLayer(str_output_diffsaga_path,
                                                shp_name,
                                                "ogr")
                if not self.load_to_qgis_vlayer(vlayer_difsaga,
                                                node_group=node_group_output_subprocess_layers):
                    return False

                process_time_end = time.time()
                process_time_total = process_time_end - process_time_start
                self.pg_dialog.insert_text(0, u'  - Tiempo ejecución: ' + str(round(process_time_total)) + " s.")
                self.file_report.write(u'  - Tiempo ejecución: ' + str(round(process_time_total)) + " s." + "\n")
                QtCore.QCoreApplication.processEvents()
                process_number += 1

                # Regadío probable no ALBERCA original - diferencia anterior *******************************************
                process_name = str(process_number) + u'.- Regadío probable no ALBERCA original - diferencia anterior'
                shp_name = str(process_number) + "_nf_casos_ndvi_sigpac_" + str(self.float_umbral_ndvi) + "_area_" + str(self.float_umbral_area) + "_" + self.str_ndvi_image_filename[:-4] + "_no_forestal"
                print process_name
                self.pg_dialog.insert_text(0, process_name)
                self.file_report.write(process_name + "\n")
                QtCore.QCoreApplication.processEvents()
                process_time_start = time.time()

                # algoritmo diferencia mejorado
                vlayer_dif_regadio_probable_x_diferencia = self.improved_spatial_difference_algorithm(shp_name,
                                                                                                      str_path_output_workspace,
                                                                                                      vlayer_regadio_probable_no_alberca_gid,
                                                                                                      vlayer_difsaga,
                                                                                                      node_group_output_subprocess_layers)
                # carga en QGIS del resultado
                if not self.load_to_qgis_vlayer(vlayer_dif_regadio_probable_x_diferencia,
                                                node_group=node_group_output_subprocess_layers):
                    return False

                process_time_end = time.time()
                process_time_total = process_time_end - process_time_start
                self.pg_dialog.insert_text(0, u'  - Tiempo ejecución: ' + str(round(process_time_total)) + " s.")
                self.file_report.write(u'  - Tiempo ejecución: ' + str(round(process_time_total)) + " s." + "\n")
                QtCore.QCoreApplication.processEvents()
                process_number += 1

                # Regadío probable no ALBERCA original - diferencia anterior. Cálculo del área**************************
                process_name = str(process_number) + u'.- Regadío probable no ALBERCA original - diferencia anterior. Cálculo del área'
                shp_name = "C_casos_"
                shp_name += self.str_aoi_part_filename + "_"
                shp_name += self.str_ndvi_image_filename[:-4] + "_"
                shp_name += str(self.float_umbral_ndvi) + "_"
                shp_name += "area_" + str(self.float_umbral_area) + "_"
                shp_name += "sigpac_gf_area_nf"

                print process_name
                self.pg_dialog.insert_text(0, process_name)
                self.file_report.write(process_name + "\n")
                QtCore.QCoreApplication.processEvents()
                process_time_start = time.time()

                str_output_diffsaga_area_shapefile = shp_name + ".shp"
                str_output_diffsaga_area_path = os.path.normcase(os.path.join(str_path_output_result_dirname,
                                                                              str_output_diffsaga_area_shapefile))
                outputs_QGISFIELDCALCULATOR_2 = processing.runalg('qgis:fieldcalculator',
                                                                  vlayer_dif_regadio_probable_x_diferencia,
                                                                  c.CONST_AREA_CASO_NO_FORESTAL,
                                                                  0,
                                                                  20.0,
                                                                  4.0,
                                                                  True,
                                                                  '$area/10000',
                                                                  str_output_diffsaga_area_path)
                vlayer_diffsaga_area = QgsVectorLayer(str_output_diffsaga_area_path,
                                                      shp_name,
                                                      "ogr")

                str_path_simbology_qml_filename = os.path.normcase(os.path.join(str_simbology_reveladuero_dirname,
                                                                                c.CONST_STR_CASOS_C_NF_QML))
                if not self.load_to_qgis_vlayer(vlayer_diffsaga_area,
                                                str_path_qml_simbology=str_path_simbology_qml_filename,
                                                node_group=node_group_result_layers):
                    return False

                process_time_end = time.time()
                process_time_total = process_time_end - process_time_start
                self.pg_dialog.insert_text(0, u'  - Tiempo ejecución: ' + str(round(process_time_total)) + " s.")
                self.file_report.write(u'  - Tiempo ejecución: ' + str(round(process_time_total)) + " s." + "\n")
                QtCore.QCoreApplication.processEvents()
                process_number += 1

        node_group_input_layers.setVisible(Qt.Unchecked)
        node_group_output_subprocess_layers.setVisible(Qt.Unchecked)
        node_group_output_sigpac_layers.setVisible(Qt.Unchecked)
        if self.is_generacion_casos:
            node_group_output_alberca_layers.setVisible(Qt.Unchecked)
        node_group_output_sigpac_layers.setExpanded(False)


        total_process_time_end = time.time()
        total_process_time_total = total_process_time_end - total_process_time_start
        print total_process_time_total
        self.pg_dialog.insert_text(0, u'\nTIEMPO TOTAL EJECUCIÓN: ' + str(round(total_process_time_total)) + " s.")
        self.file_report.write(u'\nTIEMPO TOTAL EJECUCIÓN: ' + str(round(total_process_time_total)) + "\n")

        self.file_report.close()
        return True