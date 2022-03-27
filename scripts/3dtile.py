import psycopg2
import numpy as np
import json
import os

conn = psycopg2.connect(host='206.12.92.18', dbname='propdb', user='propval', password='BCParks')
cur = conn.cursor()


def convert_to_polygon(name, file_path):
    if not os.path.exists(file_path):
        print("No such json file!")
        return
    f = open(file_path)
    data = json.load(f)
    radians = list(map(np.rad2deg, data['root']['boundingVolume']['region'][0:4]))
    d = {'west': radians[0], 'south': radians[1], 'east': radians[2], 'north': radians[3]}

    polygon_data = 'POLYGON(('
    polygon_data += f'{d["west"]} {d["north"]},'
    polygon_data += f'{d["east"]} {d["north"]},'
    polygon_data += f'{d["east"]} {d["south"]},'
    polygon_data += f'{d["west"]} {d["south"]},'
    polygon_data += f'{d["west"]} {d["north"]},'
    polygon_data = polygon_data[:-1] + '))'
    cur.execute(f'INSERT INTO public.tiles_3d (name, geo_polygon) VALUES (\'{name}\', \'{polygon_data}\');')
    conn.commit()
    conn.close()


if __name__ == '__main__':
    name = 'Manhattan'
    convert_to_polygon(name, f'/mnt/data/3DTiles/{name}/tileset.json')
