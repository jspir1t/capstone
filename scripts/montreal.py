import csv
import os
import time

import requests
from urllib.request import urlopen
import laspy
import numpy as np
import s3fs
import utm

montreal_dir = f'/home/jingtong/montreal_files/'
las_dir = f'/home/jingtong/montreal_las/'
failed_laz = f'/home/jingtong/failure.txt'
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
    def scaled_x_dimension(las_file):
        x_dimension = las_file.X
        scale = las_file.header.scales[0]
        offset = las_file.header.offsets[0]
        return (x_dimension * scale) + offset

    @staticmethod
    def scaled_y_dimension(las_file):
        y_dimension = las_file.Y
        scale = las_file.header.scales[1]
        offset = las_file.header.offsets[1]
        return (y_dimension * scale) + offset

    @staticmethod
    def scaled_z_dimension(las_file):
        z_dimension = las_file.Z
        scale = las_file.header.scales[2]
        offset = las_file.header.offsets[2]
        return (z_dimension * scale) + offset

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
            # print(f)
            print('Points from data:', len(f.points))
            print('min: ', f.header.min)
            print('max: ', f.header.max)

            print('scale: ', f.header.scale)
            print('offset: ', f.header.offset)

            print()

            scaled_x = self.scaled_x_dimension(f)
            scaled_y = self.scaled_y_dimension(f)
            scaled_z = self.scaled_z_dimension(f)

            print('actual x: ', scaled_x)
            print('actual y: ', scaled_y)
            print('actual z: ', scaled_z)

            print(' X: ', f.X)
            print(' Y: ', f.Y)
            print(' Z: ', f.Z)

            print(' x: ', f.x)
            print(' y: ', f.y)
            print(' z: ', f.z)

            lat, lon = self.utm_to_latlon(f)
            print(len(lat), len(lon))
            print('latitude:', lat[:10])
            print('longitude', lon[:10])


if __name__ == '__main__':
    # download()
    # convert_laz_to_las()

    # input_path = "/mnt/data/lidar/montreal/"
    # data_name = "307-5062_2015.laz"
    extractor = PolygonExtraction("/mnt/data/lidar/vancouver/", "4980E_54600N.las")
    extractor.process()