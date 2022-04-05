import csv
import os
import time

import requests
from urllib.request import urlopen
from pyproj import Transformer
import laspy
import numpy as np
import utm
import psycopg2

montreal_dir = f'/home/jingtong/montreal_files/'
las_dir = f'/home/jingtong/montreal_las/'
failed_laz = f'/home/jingtong/failure.txt'
laz_dir = f'/mnt/data/lidar/montreal'
if not os.path.exists(montreal_dir):
    os.makedirs(montreal_dir)
if not os.path.exists(las_dir):
    os.makedirs(las_dir)


def download():
    with open('../data/indexlidar2015.csv', encoding='utf-8') as f:
        data = csv.reader(f, delimiter=',')
        next(data, None)
        for row in data:
            url = row[2].replace('_2-5-6', '')
            resp = urlopen(url)
            file_size = int(resp.headers['Content-Length'])
            file_name = url[-17:]
            print("Downloading: %s, Bytes: %s MB" % (file_name, file_size / 1000000))
            with open(montreal_dir + file_name, 'wb') as output:
                output.write(resp.read())


def convert_laz_to_las():
    for file in os.listdir(montreal_dir):
        laz_path = os.path.join(montreal_dir, file)
        las_path = os.path.join(las_dir, file.replace('.laz', '.las'))
        command = f"laszip -i {laz_path} -o {las_path}"
        print(command)
        try:
            os.system(command)
        except:
            with open(failed_laz) as f:
                f.write(file)


class PolygonExtraction:

    def __init__(self, input_path, data_name):
        self.input_path = input_path
        self.data_name = data_name

    @staticmethod
    def utm_to_latlon(las_file):
        start = time.time()
        scaled_x = las_file.x
        scaled_y = las_file.y
        scaled_z = las_file.z
        latitudes = []
        longitudes = []
        for i in range(len(las_file.points)):
            fixed_z = scaled_z[i]
            if fixed_z < 1:
                fixed_z = 1
            if fixed_z > 60:
                fixed_z = 60
            ans = utm.to_latlon(scaled_x[i], scaled_y[i], fixed_z, northern=True)
            latitudes.append(ans[0])
            longitudes.append(ans[1])
        end = time.time()
        print(f"Time cost: {end - start} seconds for {len(las_file.points)} points")
        return latitudes, longitudes


    def process(self):
        with laspy.open(self.input_path + self.data_name) as fh:
            print('Points from Header:', fh.header.point_count)
            f = fh.read()

            # get EPSG, for different point cloud dataset, the ESPG might be different. ESPG indicates different locations.
            # in this case, Montreal data uses ESPG:2950
            # Vancouver data uses ESPG:3157
            # https://epsg.io/2950
            # https://epsg.io/transform#s_srs=2950&t_srs=4326
            # we need to convert them to an universal reference that is ESPG：4326 also called WGS84, represented by longitude and latitude.

            for (i, vlr) in enumerate(f.header.vlrs):
                print(i, vlr.user_id, vlr.record_id, vlr.description)
                if vlr.record_id != 34735:
                    continue
                for key in vlr.geo_keys:
                    if key.id != 3072:
                        continue
                    print(key.value_offset)
                    transformer = Transformer.from_crs('epsg:' + str(key.value_offset), 'epsg:4326')

            minpoint = [f.header.min[0], f.header.min[1]]
            maxpoint = [f.header.max[0], f.header.max[1]]
            print('min point: ', minpoint)
            print('max point: ', maxpoint)

            # get longitude and latitude
            print(transformer.transform(f.header.min[0], f.header.min[1]))
            print(transformer.transform(f.header.max[0], f.header.max[1]))


class Montreal:
    def __init__(self, file_path, db_name):
        self.file_path = file_path
        self.db_name = db_name
        self.conn = psycopg2.connect(host='206.12.92.18', dbname='propdb', user='propval', password='BCParks')
        self.cur = self.conn.cursor()

    def upload(self):
        files = []
        for file_name in os.listdir(self.file_path):
            files.append(self.file_path + file_name)
        for file in files:
            file_name = file.split('/')[-1][:-4]
            # if file_name != '300-5039_2015' and file_name != '300-5040_2015' and file_name != '300-5041_2015':
            #     continue
            # print(file_name)
            with laspy.open(file) as fh:
                print(f"Processing file: {file}")
                print('Points from Header:', fh.header.point_count)
                f = fh.read()

                for (i, vlr) in enumerate(f.header.vlrs):
                    print(i, vlr.user_id, vlr.record_id, vlr.description)
                    if vlr.record_id == 34735:
                        for key in vlr.geo_keys:
                            if key.id == 3072:
                                value_offset = key.value_offset

                    if vlr.record_id == 34737:
                        print(vlr.strings[0].split('|')[0])
                        if vlr.strings[0].split('|')[0] == 'GCS_NAD83_CSRS_QUEBEC' and value_offset == 32767:
                            value_offset = 6622

                print(f"value offset = {value_offset}")
                transformer = Transformer.from_crs('epsg:' + str(value_offset), 'epsg:4326')

                # for those three laz files: 300-5039_2015，300-5040_2015，300-5041_2015, simply use the hardcoded epsg
                # transformer = Transformer.from_crs('epsg:2950', 'epsg:4326')


                x_min, y_min = f.header.min[0], f.header.min[1]
                x_max, y_max = f.header.max[0], f.header.max[1]
                left_bottom = transformer.transform(x_min, y_min)
                left_upper = transformer.transform(x_min, y_max)
                right_bottom = transformer.transform(x_max, y_min)
                right_upper = transformer.transform(x_max, y_max)

                polygon_data = 'POLYGON(('
                polygon_data += f'{left_bottom[1]} {left_bottom[0]},'
                polygon_data += f'{left_upper[1]} {left_upper[0]},'
                polygon_data += f'{right_upper[1]} {right_upper[0]},'
                polygon_data += f'{right_bottom[1]} {right_bottom[0]},'
                polygon_data += f'{left_bottom[1]} {left_bottom[0]},'
                polygon_data = polygon_data[:-1] + '))'

                self.cur.execute(
                    f'INSERT INTO public.{self.db_name} (name, geo_polygon) VALUES (\'{file_name}\', \'{polygon_data}\');')
                print(f'INSERT INTO public.{self.db_name} (name, geo_polygon) VALUES (\'{file_name}\', \'{polygon_data}\');')
                self.conn.commit()
        self.conn.close()


if __name__ == '__main__':
    # download()
    # convert_laz_to_las()

    # input_path = "/mnt/data/lidar/montreal/"
    # data_name = "307-5062_2015.laz"

    # extractor = PolygonExtraction("/mnt/data/lidar/montreal/", "300-5041_2015.laz")
    # extractor.process()

    # model = Montreal('/mnt/data/lidar/montreal/', 'lidar_montreal')
    model = Montreal('/mnt/data/lidar/northvancouver/', 'lidar_north_va')
    model.upload()