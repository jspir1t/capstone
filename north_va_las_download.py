import geojson
from urllib.request import urlopen
import os
from zipfile import ZipFile
from io import BytesIO

if __name__ == '__main__':
    las_dir = f'/mnt/data/lidar/vancouver'

    if not os.path.exists(las_dir):
        os.makedirs(las_dir)
    with open('lidar-2018.geojson') as file:
        gj = geojson.load(file)
        for feature in gj['features']:
            prop = feature['properties']
            las_url = prop['lidar_url']

            zip_file_name = las_url.split('/')[-1]

            resp = urlopen(las_url)
            zip_file = ZipFile(BytesIO(resp.read()))
            names = zip_file.namelist()
            las_file_name = ''
            for name in names:
                if name.endswith('.las'):
                    if las_file_name != '':
                        raise FileExistsError
                    else:
                        las_file_name = name
            if las_file_name == '':
                raise FileNotFoundError

            assert zip_file_name[:-3] == las_file_name[:-3]
            print(las_file_name)
            zip_file.extract(las_file_name, las_dir)