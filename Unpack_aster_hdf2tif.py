# -*- coding: utf-8 -*-
#developed by Shevyrev Sergey (http://lefa.geologov.net)
#This software was brought to ya 'as is' with no warranty or promised results based on MIT licence.
#Have a nice day!
"""
https://gis.stackexchange.com/questions/162892/opening-hdf5-satellite-images-in-gdal-with-python

https://lpdaac.usgs.gov/products/ast_l1tv003/

SDS Name	Description	Units	Data Type	Fill Value	No Data Value	Valid Range	Scale Factor
VNIR_Band1	15 meter resolution VNIR Band 1(0.52 to 0.60 µm)	W/m²/sr/μm	8-bit unsigned integer	N/A	N/A	0 to 255	N/A
VNIR_Band2	15 meter resolution VNIR Band 2 (0.63 to 0.69 µm)	W/m²/sr/μm	8-bit unsigned integer	N/A	N/A	0 to 255	N/A
VNIR_Band3N	15 meter resolution VNIR Band 3N (0.78 to 0.86 µm)	W/m²/sr/μm	8-bit unsigned integer	N/A	N/A	0 to 255	N/A
SWIR_Band4	30 meter resolution SWIR Band 4 (1.600 to 1.700 µm)	W/m²/sr/μm	8-bit unsigned integer	N/A	N/A	0 to 255	N/A
SWIR_Band5	30 meter resolution SWIR Band 5 (2.145 to 2.185 µm)	W/m²/sr/μm	8-bit unsigned integer	N/A	N/A	0 to 255	N/A
SWIR_Band6	30 meter resolution SWIR Band 6 (2.185 to 2.225 µm)	W/m²/sr/μm	8-bit unsigned integer	N/A	N/A	0 to 255	N/A
SWIR_Band7	30 meter resolution SWIR Band 7 (2.235 to 2.285 µm)	W/m²/sr/μm	8-bit unsigned integer	N/A	N/A	0 to 255	N/A
SWIR_Band8	30 meter resolution SWIR Band 8 (2.295 to 2.365 µm)	W/m²/sr/μm	8-bit unsigned integer	N/A	N/A	0 to 255	N/A
SWIR_Band9	30 meter resolution SWIR Band 9 (2.360 to 2.430 µm)	W/m²/sr/μm	8-bit unsigned integer	N/A	N/A	0 to 255	N/A
TIR_Band10	90 meter resolution TIR Band 10 (8.125 to 8.475 µm)	W/m²/sr/μm	16-bit unsigned integer	N/A	N/A	0 to 65535	N/A
TIR_Band11	90 meter resolution TIR Band 11 (8.475 to 8.825 µm)	W/m²/sr/μm	16-bit unsigned integer	N/A	N/A	0 to 65535	N/A
TIR_Band12	90 meter resolution TIR Band 12 (8.925 to 9.275 µm)	W/m²/sr/μm	16-bit unsigned integer	N/A	N/A	0 to 65535	N/A
TIR_Band13	90 meter resolution TIR Band 13 (10.25 to 10.95 µm)	W/m²/sr/μm	16-bit unsigned integer	N/A	N/A	0 to 65535	N/A
TIR_Band14	90 meter resolution TIR Band 14 (10.95 to 11.65 µm)	W/m²/sr/μm	16-bit unsigned integer	N/A	N/A	0 to 65535	N/A


https://lpdaac.usgs.gov/resources/e-learning/working-aster-l1t-visible-and-near-infrared-vnir-data-r/
 
meta:
'GAIN.1': '01, HGH',
 'GAIN.10': '09, NOR',
 'GAIN.2': '02, HGH',
 'GAIN.3': '3N, NOR',
 'GAIN.4': '3B, NOR',
 'GAIN.5': '04, NOR',
 'GAIN.6': '05, NOR',
 'GAIN.7': '06, NOR',
 'GAIN.8': '07, NOR',
 'GAIN.9': '08, NOR',
 
 HGH = High
NOR = Normal
LOW = Low

Disclaimer:
    ASTER SWIR detectors are no longer functioning due 
    to anomalously high SWIR detector temperatures. 
    ASTER SWIR data acquired since !!!April 2008!!!

"""


import gdal,osr
from matplotlib import pyplot as plt
import numpy as np
import os
from skimage.transform import rescale, resize
import re
import pandas as pd
from datetime import datetime
import time

start_time=time.time();
print('Loading ucc coefficients...');
ucc_df=pd.read_excel('ucc.xlsx',index_col='BAND');
print(ucc_df);
print('Loading wavelength...');
wl_df=pd.read_excel('wl1.xlsx',index_col='BAND');
print(wl_df);

#coefficient for the temperature computations
C1=1.19104356e-16;
C2=1.43876869e-2;


#set irradiance values band 1-9 (Thome, 2001)
irradiance=[1848,1549,1114,225.4,86.63,81.85,74.85,66.49,59.85]

#Solar irradiance TIR bands
#https://asterweb.jpl.nasa.gov/content/03_data/01_Data_Products/RN_surface_leaving_radiance-TIR.htm

irradiance.extend([0.006882,0.006780,0.006590,0.005693,0.005225]);

foldname='ASTER_L1T_Night_Cloudless';
foldname_full=foldname;
#foldname='ASTER_Day';
#foldname_full=foldname;

fcounter=0;

for fname in os.listdir(foldname_full):
    if fname.endswith('.hdf'):
        fname_full=os.path.join(foldname_full,fname);   
        fcounter+=1;
    else:
        continue;
    try:
        hdf_ds = gdal.Open(fname_full);
    except:
        print('can not open HDF file. Exiting...')
        continue;  
        
        
       
    # replace <subdataset> with the number of the subdataset you need, starting with 0
    #band_ds = gdal.Open(hdf_ds.GetSubDatasets()[<subdataset>][0], gdal.GA_ReadOnly)
    subdatasets_list=[band[1] for band in hdf_ds.GetSubDatasets()];
    
    
    #taking adjusctment resolution from 'ImageData1'
    
    for rec in subdatasets_list:
        if 'ImageData1' in rec:
            h=int(re.sub('[^0-9]','',rec.split(' ')[0].split('x')[0]));
            w=int(re.sub('[^0-9]','',rec.split(' ')[0].split('x')[1]));
            break;
    
       
    count=0;
    for subds in hdf_ds.GetSubDatasets():
            
        
        # open the subdataset
        band_ds = gdal.Open(subds[0])
        band_array = band_ds.ReadAsArray()
        
        if  band_array.shape[0]<500 or band_array.shape[1]<500 or\
            ('Longitude' in subdatasets_list[count]) or\
                ('Latitude' in subdatasets_list[count]):
            continue;
        else:
            print(subdatasets_list[count]);
        
        
        #read metadata
        meta=band_ds.GetMetadata();
        
        #determine path and row
        path_row_vp=[s.strip() for s in meta['ASTERSCENEID'].split(',')];
        path='_p'+path_row_vp[0];
        row='_r'+path_row_vp[1];
        
        #determine time of the day(day, night) and declare variable for filename
        daytime='';
        if 'OFF' in meta['ASTEROBSERVATIONMODE.1'] and 'OFF' in meta['ASTEROBSERVATIONMODE.2'] and\
            'OFF' in meta['ASTEROBSERVATIONMODE.3'] and 'ON' in meta['ASTEROBSERVATIONMODE.4']:
            daytime='Night';
        else:
            daytime='Day';
        calendardate=meta['CALENDARDATE'];
        
        
        #retrieving output directory name
        out_dir_name='AST_L1T_'+path+row+calendardate+'_'+daytime+'_Unpacked'
        #fcounter was added to overcome repeating dates out_dir_name
        #convert from DN to spectral radiance (Table 5, Aster handbook)
        band_name=subdatasets_list[count].split(' ')[1][9:]; #str type
        
        gain_list=[];
        for key in [*meta]:
            if 'GAIN' in key:
                gain_list.append(meta[key]);
                
        
        #searching for gain
        if band_name in str(gain_list): #if gain list has band gain
            for el in gain_list:
                if band_name in el:
                    try:
                        ind=int(band_name);
                    except:
                        ind=band_name;
                    
                    if 'LOW' in el:
                        ucc_val=ucc_df['Low_gain'][ind];
                    elif 'NOR' in el:
                        ucc_val=ucc_df['Normal_gain'][ind];
                    else:
                        ucc_val=ucc_df['High_gain'][ind];
                    break;
                
            
        else:
            print('Band name is not in gain list, so it is probably TIRS')
            ind=int(band_name);
            ucc_val=ucc_df['Normal_gain'][ind]
            print('Band name {}, so UCC is {}'.format(ind,ucc_val))
                
                
        if np.isnan(ucc_val)==True:
            print('Can not get gain value for band {}, band was skipped'.format(band_name));    
            continue;
            
        #computing radiance
        band_radiance=(np.float64(band_array)-1)*ucc_val;
        
        #converting radiance to surface temperature http://www.pancroma.com/downloads/ASTER%20Temperature%20and%20Reflectance.pdf
        try:
            ind=int(band_name);
        except:
            ind=band_name;
        if ind in [10,11,12,13,14]:
            #if we deal with TIRS bands
            print('Converting TIRS band radiance to surface temperature...')
            _lambda=(wl_df['Wavelength'][ind]*1e-6);
            K1=(C1/(_lambda)**5)/1e6
            K2=C2/(_lambda)
            Brightness_Temperature=K2/(np.log((K1/band_radiance)+1))-273; #K->C
            #Surface_Temperature=Brightness_Temperature/(1+(_lambda*Brightness_Temperature/C2))
            Surface_Temperature=Brightness_Temperature;
        
        
        """
        compare coefficients
        https://semiautomaticclassificationmanual-v5.readthedocs.io/id/latest/thematic_tutorial_temperature.html#reclassification-of-land-cover-classification-to-emissivity-values
        
        http://www.pancroma.com/downloads/ASTER%20Temperature%20and%20Reflectance.pdf
        """
        
        
        #solar zenith angle
        sza=float(meta['SOLARDIRECTION'].split()[1]);
        
        #compute earth-sun distance
        date=fname[15:19]+'/'+fname[11:13]+'/'+fname[13:15];
        doy= int(datetime.strptime(date, '%Y/%m/%d').strftime('%j'));
        earth_sun_dist = (1 - 0.01672 * np.cos(np.deg2rad(0.9856 * (doy - 4))));
        
        #get irradiance for band
        band_irradiance=irradiance[int(band_name[0])-1];
        
        band_reflectance=(np.pi*band_radiance*(earth_sun_dist**2))/(band_irradiance*np.cos(np.deg2rad(sza)))
        
        del band_radiance,band_array; #remove unnecessary variables
        
    
        #check radiometric range in band array, normalize to uint16 if uint8
        """
        if 'uint8' in str(type(band_array[0,0])):
            b_a16=np.uint16((np.float64(band_array)/255)*(2**16));
            band_array=b_a16.copy(); del b_a16;
        """
        
        # get the projection
        geoTrans = band_ds.GetGeoTransform()
        proj = band_ds.GetProjection() # Well-Known Text.
        
        #srs = osr.SpatialReference()
        #srs.ImportFromEPSG(27700)
        #ds.SetProjection(srs.ExportToWkt())
        
        
        # Set file vars
        output_file = subdatasets_list[count].split(' ')[1]+\
                            '_'+subdatasets_list[count].split(' ')[2]+'_b'+\
                                subdatasets_list[count].split(' ')[1][9:]+\
                                calendardate+daytime+path+row+'.tif'
        
        out_file_name=os.path.join('..',out_dir_name,output_file);                        
        
        if ind in [10,11,12,13,14]:
            output_file_temperature = subdatasets_list[count].split(' ')[1]+\
                                '_'+subdatasets_list[count].split(' ')[2]+'_b'+\
                                    subdatasets_list[count].split(' ')[1][9:]+\
                                    calendardate+daytime+path+row+'degC.tif';
            out_file_temperature_name=os.path.join('..',out_dir_name,output_file_temperature);
        
           
        
        WIDTH=band_reflectance.shape[1];
        HEIGHT=band_reflectance.shape[0];
        
        ULX=float(meta['UPPERLEFTM'].split(',')[1])
        URX=float(meta['UPPERRIGHTM'].split(',')[1])
        LLX=float(meta['LOWERLEFTM'].split(',')[1])
        LRX=float(meta['LOWERRIGHTM'].split(',')[1])
        
        ULY=float(meta['UPPERLEFTM'].split(',')[0])
        URY=float(meta['UPPERRIGHTM'].split(',')[0])
        LLY=float(meta['LOWERLEFTM'].split(',')[0])
        LRY=float(meta['LOWERRIGHTM'].split(',')[0])
        
        resx=-(ULX-URX)/WIDTH;
        resy=-(ULY-LLY)/HEIGHT;
        
        if w!=band_reflectance.shape[1] or h!=band_reflectance.shape[0]:
            band_reflectance = resize(band_reflectance, (h, w), anti_aliasing=True,preserve_range=True)       
            WIDTH=w;
            HEIGHT=h;
            resx=-(ULX-URX)/WIDTH;
            resy=-(ULY-LLY)/HEIGHT;
        
        
        #show image
        plt.imshow(band_reflectance)
        plt.colorbar()
        plt.show()
        
        if ind in [10,11,12,13,14]:
            plt.imshow(Surface_Temperature)
            plt.title('Surface Temperature '+band_name)
            plt.colorbar()
            plt.show()
        
        # Create gtif
        driver = gdal.GetDriverByName("GTiff")
        
        
        if os.path.isdir(os.path.join('..',out_dir_name))==False:
            os.mkdir(os.path.join('..',out_dir_name));    
        """
        if ('8-bit' in subdatasets_list[count]) or ('16-bit' in subdatasets_list[count]):
            dt=gdal.GDT_UInt16;
        else:
            dt=gdal.GDT_Float64;
        """
        dt=gdal.GDT_Float64;
        
        dst_ds = driver.Create(out_file_name, WIDTH, HEIGHT, 1, dt,options=['COMPRESS=LZW'])
        
        if ind in [10,11,12,13,14]:
           dst_ds_t = driver.Create(out_file_temperature_name, WIDTH, HEIGHT, 1, dt,options=['COMPRESS=LZW'])
        
        #set the reference info 
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(32600+int(meta['UTMZONENUMBER'])) #update EPSG according to zone number
        
        dst_ds.SetProjection(srs.ExportToWkt())
        
        # top left x, w-e pixel resolution, rotation, top left y, rotation, n-s pixel resolution
        dst_ds.SetGeoTransform([ULX, resx, 0, ULY, 0, resy]);
        if ind in [10,11,12,13,14]:
            dst_ds_t.SetProjection(srs.ExportToWkt())
            dst_ds_t.SetGeoTransform([ULX, resx, 0, ULY, 0, resy]);
            dst_ds_t.GetRasterBand(1).WriteArray(Surface_Temperature)
            dst_ds_t.FlushCache() ##saves 
            dst_ds_t=None
        
        #srs = osr.SpatialReference()
        #srs.SetWellKnownGeogCS("WGS84")
        #dst_ds.SetProjection( srs.ExportToWkt() )
        
        # write the band
        #I set my nodata values in array to be 255
        
        dst_ds.GetRasterBand(1).WriteArray(band_reflectance) 
        #dst_ds.GetRasterBand(1).SetNoDataValue(-65536)
        dst_ds.FlushCache() ##saves 
        dst_ds=None #without this thing is not working
        
        count+=1;
    sec=time.time()-start_time;
    print('Directory processing is over. {} files were processed. It took {} s'.format(fcounter,sec))


