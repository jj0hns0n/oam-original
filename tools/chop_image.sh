#!/bin/sh

if [ ! $3 ]; then
 echo "Usage: $0 filename.tiff rows cols";
 exit
fi 


INPUT=$1
OUTPUT=`echo $INPUT | sed -e 's/.tiff/_/'` 

`~/FWTools-1.3.9/bin_safe/gdalinfo $INPUT | grep "Size is" | sed -e 's/Size is \(.*\),.*/export IMAGE_WIDTH=\1/'`
`~/FWTools-1.3.9/bin_safe/gdalinfo $INPUT | grep "Size is" | sed -e 's/Size is .*, \(.*\)/export IMAGE_HEIGHT=\1/'`


X_WIDTH=$((IMAGE_WIDTH/$2))
Y_HEIGHT=$((IMAGE_HEIGHT/$3))

END_WIDTH=$((IMAGE_WIDTH-X_WIDTH))
END_HEIGHT=$((IMAGE_HEIGHT-Y_HEIGHT))

I=0
for x in `seq 0 $X_WIDTH $END_WIDTH`; do 
  J=0
  for y in `seq 0 $Y_HEIGHT $END_HEIGHT`; do
    if [[ ! -e "${OUTPUT}c${I}_r${J}.tiff" ]]; then
      touch "${OUTPUT}c${I}_r${J}.tiff"
      nice -n 10 ~/FWTools-1.3.9/bin_safe/gdal_translate --config GDAL_CACHEMAX 500  -co TILED=yes -co BLOCKXSIZE=512 -co BLOCKYSIZE=512 -of GTiff -srcwin $x $y $X_WIDTH $Y_HEIGHT $INPUT ~/${OUTPUT}c${I}_r${J}.tiff
      nice -n 10 gdaladdo --config GDAL_CACHEMAX 500 -r average ~/${OUTPUT}c${I}_r${J}.tiff 2 4 8 16 32 64 128
      cp ~/${OUTPUT}c${I}_r${J}.tiff ${OUTPUT}c${I}_r${J}.tiff
      rm ~/${OUTPUT}c${I}_r${J}.tiff
    fi
    J=$(($J+1))
  done  
 I=$(($I+1))
done 
