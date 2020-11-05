from pathlib import Path
import ogr2ogr, subprocess, json

################
# Target structure:
# topojson:  YEAR/GEO/PROJECTION/SCALE/<NUTS_LEVEL>.json
# geojson:   YEAR/GEO/PROJECTION/SCALE/<TYPE>[_<NUTS_LEVEL>].json
# pts:       YEAR/GEO/PROJECTION/nutspt_<NUTS_LEVEL>.json
################

# TODO: quick check, possibly with observable ?
# TODO: use new clean input data, new branch: GPKG. buffer 0. Add Kosovo ?
# automated download - https://gisco-services.ec.europa.eu/distribution/v2/nuts/geojson/NUTS_BN_03M_2021_3857_LEVL_0.geojson
# TODO: brasil, LI-AT issue: use buffer(0) cleaning after reprojection?
# TODO: use more detailled data for map insets - scales should be more detailled for map insets: ["1M", "3M", "10M"]


# The Nuts2json version number
version = "v1"

# NUTS year version and, for each year, the countrie shown as stat units
nutsData = {
   "years" : {
      "2010" : "'PT','ES','IE','UK','FR','IS','BE','LU','NL','CH','LI','DE','DK','IT','VA','MT','NO','SE','FI','EE','LV','LT','PL','CZ','SK','AT','SI','HU','HR','RO','BG','TR','EL','CY','MK','ME','RS','AL'",
      "2013" : "'PT','ES','IE','UK','FR','IS','BE','LU','NL','CH','LI','DE','DK','IT','VA','MT','NO','SE','FI','EE','LV','LT','PL','CZ','SK','AT','SI','HU','HR','RO','BG','TR','EL','CY','MK','ME','RS','AL'",
      "2016" : "'PT','ES','IE','UK','FR','IS','BE','LU','NL','CH','LI','DE','DK','IT','VA','MT','NO','SE','FI','EE','LV','LT','PL','CZ','SK','AT','SI','HU','HR','RO','BG','TR','EL','CY','MK','ME'",
      "2021" : "'PT','ES','IE','UK','FR','IS','BE','LU','NL','CH','LI','DE','DK','IT','VA','MT','NO','SE','FI','EE','LV','LT','PL','CZ','SK','AT','SI','HU','HR','RO','BG','TR','EL','CY','MK','ME'"
   },
   "scales" : ["10M", "20M", "60M"]
}

# Geographical territories for map insets, CRSs and extends
geos = {
   "EUR" : {
      "name" : "Europe",
      "crs" : {
      "4326" : { "xmin" : -25, "ymin" : 32.5, "xmax" : 46.5, "ymax" : 73.9},
      "4258" : { "xmin" : -25, "ymin" : 32.5, "xmax" : 46.5, "ymax" : 73.9},
      "3857" : { "xmin" : -2800000, "ymin" : 3884000, "xmax" : 5200000, "ymax" : 11690000},
      "3035" : { "xmin" : 2434560, "ymin" : 1340340, "xmax" : 7512390, "ymax" : 5664590}
      },
      "scales" : ["10M", "20M", "60M"]
   },
   "PT20" : {
      "name" : "Azores",
      "crs" : {
      "4326" : { "xmin" : -32.67, "ymin" : 35.92, "xmax" : -23.89, "ymax" : 40.53},
      "4258" : { "xmin" : -32.67, "ymin" : 35.92, "xmax" : -23.89, "ymax" : 40.53},
      "3857" : { "xmin" : -3692767, "ymin" : 4238065, "xmax" : -2526564, "ymax" : 4972707},
      "32626" : { "xmin" : 16784, "ymin" : 4002891, "xmax" : 788999, "ymax" : 4458221}
      },
      "scales" : ["10M", "20M", "60M"]
   },
    "PT30" : {
      "name" : "Madeira",
      "crs" : {
      "4326" : { "xmin" : -18.18, "ymin" : 29.73, "xmax" : -15.46, "ymax" : 33.52},
      "4258" : { "xmin" : -18.18, "ymin" : 29.73, "xmax" : -15.46, "ymax" : 33.52},
      "3857" : { "xmin" : -1987937, "ymin" : 3483657, "xmax" : -1698033, "ymax" : 3938279},
      "32628" : { "xmin" : 189150, "ymin" : 3262646, "xmax" : 525471, "ymax" : 3697671}
      },
      "scales" : ["10M", "20M", "60M"]
   },
   "IC" : {
      "name" : "Canary islands",
      "crs" : {
      "4326" : { "xmin" : -18.599, "ymin" : 27.131, "xmax" : -12.82, "ymax" : 29.77},
      "4258" : { "xmin" : -18.599, "ymin" : 27.131, "xmax" : -12.82, "ymax" : 29.77},
      "3857" : { "xmin" : -2093768, "ymin" : 3148045, "xmax" : -1438191, "ymax" : 3480775},
      "32628" : { "xmin" : 79480, "ymin" : 2951914, "xmax" : 755779, "ymax" : 3306514}
      },
      "scales" : ["10M", "20M", "60M"]
    },
   "GF" : {
      "name" : "French Guiana",
      "crs" : {
      "4326" : { "xmin" : -55, "ymin" : 1.9, "xmax" : -51.5, "ymax" : 6},
      "4258" : { "xmin" : -55, "ymin" : 1.9, "xmax" : -51.5, "ymax" : 6},
      "3857" : { "xmin" : -6103000, "ymin" : 214000, "xmax" : -5722000, "ymax" : 660000},
      "32622" : { "xmin" : 90000, "ymin" : 224000, "xmax" : 436000, "ymax" : 647000}
      },
      "scales" : ["10M", "20M", "60M"]
   },
   "GP" : {
      "name" : "Guadeloupe",
      "crs" : {
      "4326" : { "xmin" : -63.519, "ymin" : 15.391, "xmax" : -60.196, "ymax" : 18.515},
      "4258" : { "xmin" : -63.519, "ymin" : 15.391, "xmax" : -60.196, "ymax" : 18.515},
      "3857" : { "xmin" : -7101130, "ymin" : 1734899, "xmax" : -6747739, "ymax" : 2095527},
      "32620" : { "xmin" : 413686, "ymin" : 1696392, "xmax" : 1109654, "ymax" : 2043231}
     },
      "scales" : ["10M", "20M", "60M"]
   },
   "MQ" : {
      "name" : "Martinique",
      "crs" : {
      "4326" : { "xmin" : -61.398, "ymin" : 14.293, "xmax" : -60.618, "ymax" : 15.059},
      "4258" : { "xmin" : -61.398, "ymin" : 14.293, "xmax" : -60.618, "ymax" : 15.059},
      "3857" : { "xmin" : -6843610, "ymin" : 1596556, "xmax" : -6743775, "ymax" : 1692156},
      "32620" : { "xmin" : 658362, "ymin" : 1580492, "xmax" : 760525, "ymax" : 1660906}
     },
      "scales" : ["10M", "20M", "60M"]
   },
   "CARIB" : {
      "name" : "Caribbean islands",
      "crs" : {
      "4326" : { "xmin" : -64.074, "ymin" : 12.816, "xmax" : -60.257, "ymax" : 18.350},
      "4258" : { "xmin" : -64.074, "ymin" : 12.816, "xmax" : -60.257, "ymax" : 18.350},
      "3857" : { "xmin" : -7114435, "ymin" : 1438782, "xmax" : -6701775, "ymax" : 2080865},
      "32620" : { "xmin" : 390901, "ymin" : 1412066, "xmax" : 803644, "ymax" : 2038195}
     },
     "scales" : ["10M", "20M", "60M"]
   },
   "RE" : {
      "name" : "Reunion",
      "crs" : {
      "4326" : { "xmin" : 55.087, "ymin" : -21.521, "xmax" : 55.981, "ymax" : -20.752},
      "4258" : { "xmin" : 55.087, "ymin" : -21.521, "xmax" : 55.981, "ymax" : -20.752},
      "3857" : { "xmin" : 6118552, "ymin" : -2456745, "xmax" : 6240595, "ymax" : -2355898},
      "32740" : { "xmin" : 301152, "ymin" : 7625194, "xmax" : 397346, "ymax" : 7708036}
     },
     "scales" : ["10M", "20M", "60M"]
   },
   "YT" : {
      "name" : "Mayotte",
      "crs" : {
      "4326" : { "xmin" : 44.854, "ymin" : -13.112, "xmax" : 45.454, "ymax" : -12.532},
      "4258" : { "xmin" : 44.854, "ymin" : -13.112, "xmax" : 45.454, "ymax" : -12.532},
      "3857" : { "xmin" : 4990911, "ymin" : -1475429, "xmax" : 5056930, "ymax" : -1411884},
      "32738" : { "xmin" : 484128, "ymin" : 8548691, "xmax" : 546084, "ymax" : 8611393}
     },
     "scales" : ["10M", "20M", "60M"]
   },
   "MT" : {
      "name" : "Malta",
      "crs" : {
      "4326" : { "xmin" : 14.1, "ymin" : 35.7, "xmax" : 14.6, "ymax" : 36.1},
      "4258" : { "xmin" : 14.1, "ymin" : 35.7, "xmax" : 14.6, "ymax" : 36.1},
      "3857" : { "xmin" : 1573000, "ymin" : 4270000, "xmax" : 1632000, "ymax" : 4320000},
      "3035" : { "xmin" : 4692000, "ymin" : 1420000, "xmax" : 4750000, "ymax" : 1466000}
      },
      "scales" : ["10M", "20M", "60M"]
   },
   "LI" : {
      "name" : "Liechtenstein",
      "crs" : {
      "4326" : { "xmin" : 9.4, "ymin" : 47, "xmax" : 9.7, "ymax" : 47.4},
      "4258" : { "xmin" : 9.4, "ymin" : 47, "xmax" : 9.7, "ymax" : 47.4},
      "3857" : { "xmin" : 1046000, "ymin" : 5945000, "xmax" : 1079000, "ymax" : 5992000},
      "3035" : { "xmin" : 4276797, "ymin" : 2655615, "xmax" : 4300880, "ymax" : 2686748}
      },
      "scales" : ["10M", "20M", "60M"]
   },
   "IS" : {
      "name" : "Iceland",
      "crs" : {
      "4326" : { "xmin" : -25, "ymin" : 62.6, "xmax" : -12, "ymax" : 67.7},
      "4258" : { "xmin" : -25, "ymin" : 62.6, "xmax" : -12, "ymax" : 67.7},
      "3857" : { "xmin" : -2800000, "ymin" : 9000000, "xmax" : -1360000, "ymax" : 1020000},
      "3035" : { "xmin" : 2717398, "ymin" : 4722894, "xmax" : 3301249, "ymax" : 5171386}
      },
      "scales" : ["10M", "20M", "60M"]
   }
}


print("save data")
with open("pub/" + version + "/data.json", "w") as fp:
    json.dump(geos, fp, indent=3)


# Prepare input data into tmp folder: filter, rename attributes, decompose by nuts level
def filterRenameDecompose():
   Path("tmp/").mkdir(parents=True, exist_ok=True)

   print("Graticule")
   ogr2ogr.main(["-overwrite","-f", "GPKG", "tmp/graticule.gpkg", "src/resources/shp/graticule.shp"])

   for year in nutsData["years"]:
       for scale in nutsData["scales"]:

           print(year + " " + scale + " CNTR RG - filter, rename attributes")
           ogr2ogr.main(["-overwrite","-f", "GPKG",
              "tmp/" + year + "_" + scale + "_CNTR_RG.gpkg",
              "src/resources/shp/" + year + "/CNTR_RG_" + scale + "_" + year + "_4326.shp",
              "-sql", "SELECT CNTR_ID as id,NAME_ENGL as na FROM CNTR_RG_" + scale + "_" + year + "_4326 WHERE CNTR_ID NOT IN (" + nutsData["years"][year] + ")"])

           print(year + " " + scale + " CNTR BN - filter, rename attributes")
           ogr2ogr.main(["-overwrite","-f", "GPKG",
              "tmp/" + year + "_" + scale + "_CNTR_BN.gpkg",
              "src/resources/shp/" + year + "/CNTR_BN_" + scale + "_" + year + "_4326.shp",
              "-sql", "SELECT CNTR_BN_ID as id,CC_FLAG as cc,OTHR_FLAG as oth,COAS_FLAG as co FROM CNTR_BN_" + scale + "_" + year + "_4326 WHERE EU_FLAG='F' AND EFTA_FLAG='F'"])

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




# Perform coarse clipping by region, to improve reprojection process
def coarseClipping():
   for year in nutsData["years"]:
      for geo in geos:

         extends = geos[geo]["crs"]["4326"]
         marginDeg = 30 if(geo == "EUR") else 5

         for type in ["RG", "BN"]:
            for scale in geos[geo]["scales"]:

               print(year + " " + geo + " " + scale + " CNTR " + type + " - coarse clipping")
               ogr2ogr.main(["-overwrite","-f", "GPKG",
                 "tmp/" + year + "_" + geo + "_" + scale + "_CNTR_" + type + ".gpkg",
                 "tmp/" + year + "_" + scale + "_CNTR_" + type + ".gpkg",
                 "-clipsrc", str(extends["xmin"]-marginDeg), str(extends["ymin"]-marginDeg), str(extends["xmax"]+marginDeg), str(extends["ymax"]+marginDeg)])

               for level in ["0", "1", "2", "3"]:

                  print(year + " " + geo + " " + scale + " NUTS " + type + " - coarse clipping")
                  ogr2ogr.main(["-overwrite","-f", "GPKG",
                    "tmp/" + year + "_" + geo + "_" + scale + "_" + level + "_NUTS_" + type + ".gpkg",
                    "tmp/" + year + "_" + scale + "_" + level + "_NUTS_" + type + ".gpkg",
                    "-clipsrc", str(extends["xmin"]-marginDeg), str(extends["ymin"]-marginDeg), str(extends["xmax"]+marginDeg), str(extends["ymax"]+marginDeg)])



# Clip, reproject and convert as geojson
def reprojectClipGeojson():
   for year in nutsData["years"]:
      for geo in geos:
         for crs in geos[geo]["crs"]:
            outpath = "tmp/"+year+"/"+geo+"/"+crs+"/"
            Path(outpath).mkdir(parents=True, exist_ok=True)
            extends = geos[geo]["crs"][crs]

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
               for scale in geos[geo]["scales"]:

                  print(year + " " + geo + " " + crs + " " + scale + " " + type + " - reproject CNTR")
                  ogr2ogr.main(["-overwrite","-f", "GPKG",
                    outpath + scale + "_CNTR_" + type + ".gpkg",
                    "tmp/" + year + "_" + geo + "_" + scale + "_CNTR_" + type + ".gpkg",
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
                       "tmp/" + year + "_" + geo + "_" + scale + "_" + level + "_NUTS_" + type + ".gpkg",
                       "-t_srs", "EPSG:"+crs, "-s_srs", "EPSG:4258"
                       ])

                     print(year + " " + geo + " " + crs + " " + scale + " " + type + " " + level + " - clip + geojson NUTS")
                     ogr2ogr.main(["-overwrite","-f", "GeoJSON",
                       outpath + scale + "_" + level + "_NUTS_" + type + ".geojson",
                       outpath + scale + "_" + level + "_NUTS_" + type + ".gpkg",
                       "-clipsrc", str(extends["xmin"]), str(extends["ymin"]), str(extends["xmax"]), str(extends["ymax"])
                       ])



# Make topojson file from geojson files
# Simplify them with topojson simplify
# Produce geojson from topojson
# See: https://github.com/topojson/topojson-server/blob/master/README.md#geo2topo
# See: https://github.com/topojson/topojson-simplify/blob/master/README.md#toposimplify
# See: https://github.com/topojson/topojson-client/blob/master/README.md#topo2geo
# See: https://stackoverflow.com/questions/89228/how-to-call-an-external-command
def topogeojson():
   for year in nutsData["years"]:
      for geo in geos:
         for crs in geos[geo]["crs"]:
            for scale in geos[geo]["scales"]:
               for level in ["0", "1", "2", "3"]:
                  inpath = "tmp/"+year+"/"+geo+"/"+crs+"/"
                  outpath = "pub/" + version + "/" + year + "/" + ("" if geo=="EUR" else geo + "/") + crs + "/" + scale + "/"
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
                    "cntrg=" + outpath + "cntrg.json",
                    "cntbn=" + outpath + "cntbn.json",
                    "gra=" + outpath + "gra.json",
                    "-i", outpath + level + ".json"])




# Produce point representations
def makePoints():

   # prepare
   for year in nutsData["years"]:

      Path("tmp/pts/" + year + "/").mkdir(parents=True, exist_ok=True)

      print(year + " PTS join areas")
      ogr2ogr.main(["-overwrite","-f", "ESRI Shapefile",
        "tmp/pts/" + year + "/NUTS_LB.shp",
        "src/resources/shp/" + year + "/NUTS_LB_" + year + "_4326.shp",
        "-sql", "select LB.NUTS_ID as id, LB.LEVL_CODE as lvl, A.area as ar FROM NUTS_LB_" + year + "_4326 AS LB left join 'src/resources/shp/" + year + "/AREA.csv'.AREA AS A ON LB.NUTS_ID = A.nuts_id"
        ])

      print(year + " PTS join latn names")
      ogr2ogr.main(["-overwrite","-f", "GPKG",
        "tmp/pts/" + year + "/NUTS_LB.gpkg",
        "tmp/pts/" + year + "/NUTS_LB.shp",
        "-sql", "select LB.id as id, LB.lvl as lvl, A.NAME_LATN as na, LB.ar as ar FROM NUTS_LB AS LB left join 'src/resources/shp/" + year + "/NUTS_AT_" + year + ".csv'.NUTS_AT_" + year + " as A on LB.id = A.NUTS_ID"
        ])

      for level in ["0", "1", "2", "3"]:

         print(year + " " + level + " - PTS decompose by NUTS level")
         ogr2ogr.main(["-overwrite","-f", "GPKG",
           "tmp/pts/" + year + "/NUTS_LB_" + level + ".gpkg",
           "tmp/pts/" + year + "/NUTS_LB.gpkg",
           "-sql", "SELECT geom,id,na,ar FROM LB AS LB WHERE lvl=" + level
           ])

   for year in nutsData["years"]:
      for geo in geos:
         for crs in geos[geo]["crs"]:
            extends = geos[geo]["crs"][crs]

            outpath = "pub/" + version + "/" + year + "/" + ("" if geo=="EUR" else geo + "/") + crs + "/"
            Path(outpath).mkdir(parents=True, exist_ok=True)

            for level in ["0", "1", "2", "3"]:

               print(year + " " + geo + " " + crs + " " + level + " - reproject PTS")
               ogr2ogr.main(["-overwrite","-f", "GPKG",
                 "tmp/pts/" + year + "/" + geo + "_" + crs + "NUTS_LB_" + level + ".gpkg",
                 "tmp/pts/" + year + "/NUTS_LB_" + level + ".gpkg",
                 "-t_srs", "EPSG:"+crs, "-s_srs", "EPSG:4258"
                 ])

               print(year + " " + geo + " " + crs + " " + level + " - clip + geojson PTS")
               ogr2ogr.main(["-overwrite","-f", "GeoJSON",
                 outpath + "nutspt_" + level + ".json",
                 "tmp/pts/" + year + "/" + geo + "_" + crs + "NUTS_LB_" + level + ".gpkg",
                 "-nln", "nutspt_" + level,
                 "-clipsrc", str(extends["xmin"]), str(extends["ymin"]), str(extends["xmax"]), str(extends["ymax"])
                 ])



######## Full process #########
filterRenameDecompose()
coarseClipping()
reprojectClipGeojson()
topogeojson()
makePoints()
##############################



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
