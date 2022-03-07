import csv
import os
import requests
from urllib.request import urlopen
import laspy
import numpy as np
import s3fs

montreal_dir = f'/home/jingtong/montreal_files/'
las_dir = f'/home/jingtong/montreal_las/'
failed_laz = f'/home/jingtong/failure.txt'
if not os.path.exists(montreal_dir):
    os.makedirs(montreal_dir)
if not os.path.exists(las_dir):
    os.makedirs(las_dir)


def download():
    with open('indexlidar2015.csv', encoding='utf-8') as f:
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


def analysis(laz_file_name):
    las = laspy.read(laz_file_name)
    # header
    print(las.header)
    print(las.header.point_count)

    # points
    point_format = las.point_format
    print(point_format.id)
    print(list(point_format.dimension_names))


    # fs = s3fs.S3FileSystem()
    # with open(laz_file_name, 'rb') as f:
    #     if f.header.point_count < 100_000_000:
    #         las = laspy.read(f)


if __name__ == '__main__':
    # download()
    analysis('/home/jingtong/flask-server/276-5030_2015.laz')
    # convert_laz_to_las()
