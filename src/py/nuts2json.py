from pathlib import Path
import ogr2ogr, subprocess

####
# Target structure:
# topojson:  YEAR/GEO/PROJECTION/SCALE/<NUTS_LEVEL>.json
# geojson:   YEAR/GEO/PROJECTION/SCALE/<TYPE>[_<NUTS_LEVEL>].json
# pts:       YEAR/GEO/PROJECTION/nutspt_<NUTS_LEVEL>.json
####

# The Nuts2json version number
version = "v1"

# NUTS year version and, for each year, the countrie shown as stat units
years = {
    "2010" : "'PT','ES','IE','UK','FR','IS','BE','LU','NL','CH','LI','DE','DK','IT','VA','MT','NO','SE','FI','EE','LV','LT','PL','CZ','SK','AT','SI','HU','HR','RO','BG','TR','EL','CY','MK','ME','RS','AL'",
    "2013" : "'PT','ES','IE','UK','FR','IS','BE','LU','NL','CH','LI','DE','DK','IT','VA','MT','NO','SE','FI','EE','LV','LT','PL','CZ','SK','AT','SI','HU','HR','RO','BG','TR','EL','CY','MK','ME','RS','AL'",
    "2016" : "'PT','ES','IE','UK','FR','IS','BE','LU','NL','CH','LI','DE','DK','IT','VA','MT','NO','SE','FI','EE','LV','LT','PL','CZ','SK','AT','SI','HU','HR','RO','BG','TR','EL','CY','MK','ME'",
    "2021" : "'PT','ES','IE','UK','FR','IS','BE','LU','NL','CH','LI','DE','DK','IT','VA','MT','NO','SE','FI','EE','LV','LT','PL','CZ','SK','AT','SI','HU','HR','RO','BG','TR','EL','CY','MK','ME'"
    }

# scales
scales = ["10M", "20M", "60M"]

#regions, CRSs and extends
geos = {
   "EUR" : {
      "4326" : { "xmin" : -25, "ymin" : 32.5, "xmax" : 46.5, "ymax" : 73.9},
      "4258" : { "xmin" : -25, "ymin" : 32.5, "xmax" : 46.5, "ymax" : 73.9},
      "3857" : { "xmin" : -2800000, "ymin" : 3884000, "xmax" : 5200000, "ymax" : 11690000},
      "3035" : { "xmin" : 2434560, "ymin" : 1340340, "xmax" : 7512390, "ymax" : 5664590}
   }
}


#prepare input data into tmp folder: filter, rename attributes, decompose by nuts level
def filterRenameDecompose():
   Path("tmp/").mkdir(parents=True, exist_ok=True)

   print("Graticule")
   ogr2ogr.main(["-overwrite","-f", "GPKG", "tmp/graticule.gpkg", "src/resources/shp/graticule.shp"])

   for year in years:
       for scale in scales:

           print(year + " " + scale + " CNTR RG - filter, rename attributes")
           ogr2ogr.main(["-overwrite","-f", "GPKG",
              "tmp/" + year + "_" + scale + "_CNTR_RG.gpkg",
              "src/resources/shp/" + year + "/CNTR_RG_" + scale + "_" + year + "_4326.shp",
              "-sql", "SELECT CNTR_ID as id,NAME_ENGL as na FROM CNTR_RG_" + scale + "_" + year + "_4326 WHERE CNTR_ID NOT IN (" + years[year] + ")"])

           print(year + " " + scale + " CNTR BN - filter, rename attributes")
           ogr2ogr.main(["-overwrite","-f", "GPKG",
              "tmp/" + year + "_" + scale + "_CNTR_BN.gpkg",
              "src/resources/shp/" + year + "/CNTR_BN_" + scale + "_" + year + "_4326.shp",
              "-sql", "SELECT CNTR_BN_ID as id,CC_FLAG as cc,OTHR_FLAG as oth,COAS_FLAG as co FROM CNTR_BN_" + scale + "_" + year + "_4326 WHERE EU_FLAG='F' AND EFTA_FLAG='F'"])

           #nuts: filter, rename attributes
           for level in ["0", "1", "2", "3"]:

               print(year + " " + scale + " NUTS RG " + level + " - filter, rename attributes")
               ogr2ogr.main(["-overwrite","-f", "GPKG",
                 "tmp/" + year + "_" + scale + "_" + level + "_NUTS_RG.gpkg",
                 "src/resources/shp/" + year + "/NUTS_RG_" + scale + "_" + year + "_4326.shp",
                 "-sql", "SELECT N.NUTS_ID as id,A.NAME_LATN as na FROM NUTS_RG_" + scale + "_" + year + "_4326 as N left join 'src/resources/shp/" + year + "/NUTS_AT_" + year + ".csv'.NUTS_AT_" + year + " as A on N.NUTS_ID = A.NUTS_ID WHERE N.LEVL_CODE = " + level])

               print(year + " " + scale + " NUTS BN " + level + " - filter, rename attributes")
               ogr2ogr.main(["-overwrite","-f", "GPKG",
                 "tmp/" + year + "_" + scale + "_" + level + "_NUTS_BN.gpkg",
                 "src/resources/shp/" + year + "/NUTS_BN_" + scale + "_" + year + "_4326.shp",
                 "-sql", "SELECT NUTS_BN_ID as id,LEVL_CODE as lvl,EU_FLAG as eu,EFTA_FLAG as efta,CC_FLAG as cc,OTHR_FLAG as oth,COAS_FLAG as co FROM NUTS_BN_" + scale + "_" + year + "_4326 WHERE LEVL_CODE <= " + level])




#clip, reproject and convert as geojson
def reprojectClipGeojson():
   for year in years:
      for geo in geos:
         for crs in geos[geo]:
            outpath = "tmp/"+year+"/"+geo+"/"+crs+"/"
            Path(outpath).mkdir(parents=True, exist_ok=True)
            extends = geos[geo][crs]

            print(year + " " + geo + " " + crs + " - reproject graticule")
            ogr2ogr.main(["-overwrite","-f", "GPKG",
              outpath + "graticule.gpkg",
              "tmp/graticule.gpkg",
              "-t_srs", "EPSG:"+crs, "-s_srs", "EPSG:4258"
              ])

            print(year + " " + geo + " " + crs + " - clip + geojson graticule")
            ogr2ogr.main(["-overwrite","-f", "GeoJSON",
              outpath + "graticule.geojson",
              outpath + "graticule.gpkg",
              "-clipsrc", str(extends["xmin"]), str(extends["ymin"]), str(extends["xmax"]), str(extends["ymax"])
              ])

            for type in ["RG", "BN"]:
               for scale in scales:

                  print(year + " " + geo + " " + crs + " " + scale + " " + type + " - reproject CNTR")
                  ogr2ogr.main(["-overwrite","-f", "GPKG",
                    outpath + scale + "_CNTR_" + type + ".gpkg",
                    "tmp/" + year + "_" + scale + "_CNTR_" + type + ".gpkg",
                    "-t_srs", "EPSG:"+crs, "-s_srs", "EPSG:4258"
                    ])

                  print(year + " " + geo + " " + crs + " " + scale + " " + type + " - clip + geojson CNTR")
                  ogr2ogr.main(["-overwrite","-f", "GeoJSON",
                    outpath + scale + "_CNTR_" + type + ".geojson",
                    outpath + scale + "_CNTR_" + type + ".gpkg",
                    "-clipsrc", str(extends["xmin"]), str(extends["ymin"]), str(extends["xmax"]), str(extends["ymax"])
                    ])

                  for level in ["0", "1", "2", "3"]:

                     print(year + " " + geo + " " + crs + " " + scale + " " + type + " " + level + " - reproject NUTS")
                     ogr2ogr.main(["-overwrite","-f", "GPKG",
                       outpath + scale + "_" + level + "_NUTS_" + type + ".gpkg",
                       "tmp/" + year + "_" + scale + "_" + level + "_NUTS_" + type + ".gpkg",
                       "-t_srs", "EPSG:"+crs, "-s_srs", "EPSG:4258"
                       ])

                     print(year + " " + geo + " " + crs + " " + scale + " " + type + " " + level + " - clip + geojson NUTS")
                     ogr2ogr.main(["-overwrite","-f", "GeoJSON",
                       outpath + scale + "_" + level + "_NUTS_" + type + ".geojson",
                       outpath + scale + "_" + level + "_NUTS_" + type + ".gpkg",
                       "-clipsrc", str(extends["xmin"]), str(extends["ymin"]), str(extends["xmax"]), str(extends["ymax"])
                       ])



# make topojson file from geojson files
# simplify them with topojson simplify
# produce geojson from topojson
# See: https://github.com/topojson/topojson-server/blob/master/README.md#geo2topo
# See: https://github.com/topojson/topojson-simplify/blob/master/README.md#toposimplify
# See: https://github.com/topojson/topojson-client/blob/master/README.md#topo2geo
# See: https://stackoverflow.com/questions/89228/how-to-call-an-external-command
def topogeojson():
   for year in years:
      for geo in geos:
         for crs in geos[geo]:
            for scale in scales:
               for level in ["0", "1", "2", "3"]:
                  inpath = "tmp/"+year+"/"+geo+"/"+crs+"/"
                  outpath = "pub/" + version + "/" + year + "/" + ("" if geo=="EUR" else geo) + "/" + crs + "/" + scale + "/"
                  Path(outpath).mkdir(parents=True, exist_ok=True)

                  # make topojson base files, one per nuts level
                  # quantization: q small means strong 'simplification'
                  print(year + " " + geo + " " + crs + " " + scale + " " + level + " - make topojson")
                  subprocess.run(["geo2topo", "-q", "20000",
                    "nutsrg=" + inpath + scale + "_" + level + "_NUTS_RG.geojson",
                    "nutsbn=" + inpath + scale + "_" + level + "_NUTS_BN.geojson",
                    "cntrg=" + inpath + scale + "_CNTR_RG.geojson",
                    "cntbn=" + inpath + scale + "_CNTR_BN.geojson",
                    "gra=" + inpath + "graticule.geojson",
                    "-o", inpath + level + ".json"])

                  print(year + " " + geo + " " + crs + " " + scale + " " + level + " - simplify topojson")
                  subprocess.run(["toposimplify", "-f", "-P", "0.99", "-o",
                    outpath + level + ".json",
                    inpath + level + ".json"])

                  print(year + " " + geo + " " + crs + " " + scale + " " + level + " - topojson to geojson")
                  subprocess.run(["topo2geo",
                    "nutsrg=" + outpath + "nutsrg_" + level + ".json",
                    "nutsbn=" + outpath + "nutsbn_" + level + ".json",
                    "cntrg=" + outpath + "cntrg_" + level + ".json",
                    "cntbn=" + outpath + "cntbn_" + level + ".json",
                    "gra=" + outpath + "gra_" + level + ".json",
                    "-i", outpath + level + ".json"])




# produce point representations
def pts():

   # prepare
   for year in years:

      #TODO join area/name
  #echo "9- $year NUTS LB: Join area"
  #ogr2ogr -overwrite -f "ESRI Shapefile" -lco ENCODING=UTF-8 \
  #   $dir"/NUTS_LB_.shp" \
  #   "../shp/"$year"/NUTS_LB_"$year"_4326.shp" \
  #   -sql "select LB.NUTS_ID as id, LB.LEVL_CODE as lvl, A.area as ar FROM NUTS_LB_"$year"_4326 AS LB left join '../shp/"$year"/AREA.csv'.AREA AS A ON LB.NUTS_ID = A.nuts_id"

  #echo "9- $year NUTS LB: Join latn name"
  #ogr2ogr -overwrite -f "ESRI Shapefile" -lco ENCODING=UTF-8 \
  #   $dir"/NUTS_LB.shp" \
  #   $dir"/NUTS_LB_.shp" \
  #   -sql "select LB.id as id, LB.lvl as lvl, A.NAME_LATN as na, LB.ar as ar FROM NUTS_LB_ AS LB left join '../shp/"$year"/NUTS_AT_"$year".csv'.NUTS_AT_"$year" as A on LB.id = A.NUTS_ID"

      for level in ["0", "1", "2", "3"]:
         print()
         #TODO decompose by level
      #echo "9- $year $proj $level NUTS LB: extract by level"
      #dir="../tmp/$year/LB"
      #ogr2ogr -overwrite -lco ENCODING=UTF-8 \
      #   -sql "SELECT id,na,ar FROM NUTS_LB_"$proj" WHERE lvl="$level \
      #   $dir"/NUTS_LB_"$proj"_"$level".shp" \
      #   $dir"/NUTS_LB_"$proj".shp"


   for year in years:
      for geo in geos:
         for crs in geos[geo]:
            for level in ["0", "1", "2", "3"]:
               print()
               #TODO reproject, clip, to geojson




#filterRenameDecompose()
#reprojectClipGeojson()
#topogeojson()
pts()




#run command
#https://stackoverflow.com/questions/89228/how-to-call-an-external-command

#import subprocess
#subprocess.run(["ls", "-l"])

#
#https://gis.stackexchange.com/questions/39080/using-ogr2ogr-to-convert-gml-to-shapefile-in-python
#import ogr2ogr
#https://github.com/OSGeo/gdal/tree/master/gdal/swig/python
#https://pcjericks.github.io/py-gdalogr-cookbook/
#ogr2ogr.main(["","-f", "KML", "out.kml", "data/san_andres_y_providencia_administrative.shp"])


#For TopoJSON format: /<YEAR>/<PROJECTION>/<SCALE>/<NUTS_LEVEL>.json
#For GeoJSON format: /<YEAR>/<PROJECTION>/<SCALE>/<TYPE>[_<NUTS_LEVEL>].json
#nutsrg nutsbn cntrg cntbn gra
#PTs: /<YEAR>/<PROJECTION>/nutspt_<NUTS_LEVEL>.json


#GDAL_DATA ="/usr/share/gdal/2.2"
