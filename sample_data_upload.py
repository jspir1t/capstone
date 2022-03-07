import geojson
import psycopg2
import urllib.request as request

conn = psycopg2.connect(host='206.12.92.18', dbname='propdb', user='propval', password='BCParks')
cur = conn.cursor()

with open('lidar-2018.geojson') as file:
    gj = geojson.load(file)
    for feature in gj['features']:

        geo = feature['geometry']
        polygon_data = 'POLYGON(('
        for pair in geo['coordinates'][0]:
            polygon_data += f'{pair[0]} {pair[1]},'
        polygon_data = polygon_data[:-1] + '))'

        prop = feature['properties']
        geo_point_2d = prop['geo_point_2d']
        point_data = f'POINT({geo_point_2d[0]} {geo_point_2d[1]})'
        lidar_url = prop['lidar_url']
        name = prop['name']

        # download las files

        cur.execute(
            f'INSERT INTO public.lidar_va (name, lidar_url, geo_polygon, geo_point_2d) VALUES (\'{name}\', \'{lidar_url}\', \'{polygon_data}\', \'{point_data}\');')
    conn.commit()
    conn.close()
