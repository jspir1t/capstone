# For geodetic coordinates (X, Y), X is longitude and Y is latitude
import functools
from flask import Flask, request, abort, jsonify
from werkzeug.exceptions import HTTPException
import psycopg2
from skyfield.api import load, wgs84
import utils

app = Flask(__name__)

conn = psycopg2.connect(host='206.12.92.18', dbname='propdb', user='propval', password='BCParks')
cur = conn.cursor()

lidar_table_name = 'lidar'
tiles_3d_table_name = 'tiles_3d'

stations_url = 'https://www.celestrak.com/NORAD/elements/supplemental/gps.txt'
satellites = load.tle_file(stations_url)
print('Loaded', len(satellites), 'satellites')
ts = load.timescale()


def db_conn_refresh_decorator(func):
    @functools.wraps(func)
    def wrap_func():
        global conn, cur
        if conn.closed:
            print("Postgres connection refreshing...")
            conn = psycopg2.connect(host='206.12.92.18', dbname='propdb', user='propval', password='BCParks')
            cur = conn.cursor()
            print("Postgres connection refreshed!")
        return func()

    return wrap_func


@app.errorhandler(Exception)
def handle_error(e):
    code = 500
    if isinstance(e, HTTPException):
        code = e.code
    return jsonify(error=str(e)), code


@app.route('/lidar/polygon', methods=['POST'])
@db_conn_refresh_decorator
def lidar_polygon_intersect():
    content_type = request.headers.get('Content-Type')
    if content_type != 'application/json':
        abort(415)
    else:
        body = request.get_json()
        try:
            vertices = body['vertices']
            if len(vertices) < 4 and vertices[0] != vertices[-1]:
                abort(422)
            polygon = "("
            for i in range(len(vertices)):
                polygon += f"{vertices[i][0]} {vertices[i][1]},"
            polygon = polygon[:-1] + ")"

        except Exception as e:
            abort(400)

        try:
            cur.execute(f"SELECT * FROM {lidar_table_name} WHERE ST_Intersects(geo_polygon, 'POLYGON({polygon})');")
            render_result = []
            result = cur.fetchall()
            for row in result:
                render_result.append(f'http://206.12.92.18:10083/lidar/{row[1]}/{row[0]}.laz')

            return {'total_num': len(render_result), 'regions': render_result}

        except Exception as e:
            conn.rollback()
            abort(500)


@app.route('/lidar/circle', methods=['GET'])
@db_conn_refresh_decorator
def lidar_circle_intersect():
    args = request.args
    longitude = args.get('longitude', type=float)
    latitude = args.get('latitude', type=float)
    radius = args.get('radius', type=float)
    if longitude is None or latitude is None or radius is None:
        abort(422)

    try:
        cur.execute(
            f"SELECT * from {lidar_table_name} where ST_Intersects(geo_polygon, ST_Buffer(ST_MakePoint({longitude}, {latitude})::geography, {radius}));")
        render_result = []
        result = cur.fetchall()
        for row in result:
            render_result.append(f'http://206.12.92.18:10083/lidar/{row[1]}/{row[0]}.laz')
        return {'total_num': len(render_result), 'regions': render_result}

    except Exception as e:
        conn.rollback()
        abort(500)


@app.route('/3dtiles/polygon', methods=['POST'])
@db_conn_refresh_decorator
def tile_3d_polygon_intersect():
    content_type = request.headers.get('Content-Type')
    if content_type != 'application/json':
        abort(415)
    else:
        body = request.get_json()
        try:
            vertices = body['vertices']
            if len(vertices) < 4 and vertices[0] != vertices[-1]:
                abort(422)
            polygon = "("
            for i in range(len(vertices)):
                polygon += f"{vertices[i][0]} {vertices[i][1]},"
            polygon = polygon[:-1] + ")"

        except Exception as e:
            abort(400)

        try:
            cur.execute(f"SELECT * FROM {tiles_3d_table_name} WHERE ST_Intersects(geo_polygon, 'POLYGON({polygon})');")
            render_result = []
            result = cur.fetchall()
            for row in result:
                render_result.append(f'http://206.12.92.18:10083/3DTiles/{row[0]}/tileset.json')

            return {'total_num': len(render_result), 'regions': render_result}

        except Exception as e:
            conn.rollback()
            abort(500)


@app.route('/3dtiles/circle', methods=['GET'])
@db_conn_refresh_decorator
def tile_3d_circle_intersect():
    args = request.args
    longitude = args.get('longitude', type=float)
    latitude = args.get('latitude', type=float)
    radius = args.get('radius', type=float)
    if longitude is None or latitude is None or radius is None:
        abort(422)

    try:
        cur.execute(
            f"SELECT * from {tiles_3d_table_name} where ST_Intersects(geo_polygon, ST_Buffer(ST_MakePoint({longitude}, {latitude})::geography, {radius}));")
        render_result = []
        result = cur.fetchall()
        for row in result:
            render_result.append(f'http://206.12.92.18:10083/3DTiles/{row[0]}/tileset.json')
        return {'total_num': len(render_result), 'regions': render_result}

    except Exception as e:
        conn.rollback()
        abort(500)


@app.route('/satellites', methods=['GET'])
def get_all_satellites():
    time = request.args.get('time', None)
    names = request.args.get('names', None)
    ids = request.args.get('ids', None)
    if time is None:
        time = ts.now()
    else:
        # UTC time with this format: 20220327130722
        try:
            year = int(time[0:4])
            month = int(time[4:6])
            day = int(time[6:8])
            hour = int(time[8:10])
            minute = int(time[10:12])
            second = int(time[12:])
            time = ts.utc(year, month, day, hour, minute, second)
        except Exception as e:
            abort(422)

    satellite_names = [sat.name for sat in satellites]
    satellite_ids = [str(sat.model.satnum) for sat in satellites]

    try:
        names = utils.split_check(names, satellite_names)
        ids = utils.split_check(ids, satellite_ids)
    except:
        abort(422)

    if len(names) != 0 and len(ids) != 0:
        abort(422)

    # if no name and id specified, return the whole satellites locations
    if len(names) == 0 and len(ids) == 0:
        response = {}
        for gps in satellites:
            geocentric = gps.at(time)
            sub_point = wgs84.subpoint(geocentric)
            response[str(gps.model.satnum)] = {
                'name': gps.name,
                'latitude': sub_point.latitude.degrees,
                'longitude': sub_point.longitude.degrees,
                'height': sub_point.elevation.m
            }
        return response

    if len(names) != 0:
        response = {}
        for gps in satellites:
            if gps.name in names:
                sub_point = wgs84.subpoint(gps.at(time))
                response[str(gps.model.satnum)] = {
                    'name': gps.name,
                    'latitude': sub_point.latitude.degrees,
                    'longitude': sub_point.longitude.degrees,
                    'height': sub_point.elevation.m
                }
        return response

    if len(ids) != 0:
        response = {}
        for gps in satellites:
            if str(gps.model.satnum) in ids:
                sub_point = wgs84.subpoint(gps.at(time))
                response[str(gps.model.satnum)] = {
                    'name': gps.name,
                    'latitude': sub_point.latitude.degrees,
                    'longitude': sub_point.longitude.degrees,
                    'height': sub_point.elevation.m
                }
        return response
