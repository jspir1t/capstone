# For geodetic coordinates (X, Y), X is longitude and Y is latitude
from flask import Flask, request, abort, jsonify
from werkzeug import Response
from werkzeug.exceptions import HTTPException
import psycopg2
from skyfield.api import load, wgs84
import utils

app = Flask(__name__)

conn = psycopg2.connect(host='206.12.92.18', dbname='propdb', user='propval', password='BCParks')
cur = conn.cursor()
vancouver_table_name = 'lidar_north_va'
tiles_3d_table_name = 'tiles_3d'

stations_url = 'https://www.celestrak.com/NORAD/elements/supplemental/gps.txt'
satellites = load.tle_file(stations_url)
print('Loaded', len(satellites), 'satellites')
# by_name = {sat.name: sat for sat in satellites}
# by_id = {sat.model.satnum: sat for sat in satellites}
ts = load.timescale()


@app.errorhandler(Exception)
def handle_error(e):
    code = 500
    if isinstance(e, HTTPException):
        code = e.code
    return jsonify(error=str(e)), code


@app.route('/lidar/polygon', methods=['POST'])
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
            # print(f"SELECT * FROM {vancouver_table_name} WHERE ST_Intersects(geo_polygon, 'POLYGON({polygon})');")
            cur.execute(f"SELECT * FROM {vancouver_table_name} WHERE ST_Intersects(geo_polygon, 'POLYGON({polygon})');")
            render_result = []
            result = cur.fetchall()
            for row in result:
                render_result.append('http://206.12.92.18:10083/lidar/vancouver/' + row[0] + '.las')

            return {'total_num': len(render_result), 'regions': render_result}

        except Exception as e:
            conn.rollback()
            abort(500)


@app.route('/lidar/circle', methods=['GET'])
def lidar_circle_intersect():
    args = request.args
    longitude = args.get('longitude', type=float)
    latitude = args.get('latitude', type=float)
    radius = args.get('radius', type=int)
    if longitude is None or latitude is None or radius is None:
        abort(422)

    try:
        cur.execute(
            f"SELECT * from {vancouver_table_name} where ST_Intersects(geo_polygon, ST_Buffer(ST_MakePoint({longitude}, {latitude})::geography, {radius}));")
        render_result = []
        result = cur.fetchall()
        for row in result:
            render_result.append('http://206.12.92.18:10083/lidar/vancouver/' + row[0] + '.las')
        return {'total_num': len(render_result), 'regions': render_result}

    except Exception as e:
        conn.rollback()
        abort(500)


@app.route('/3dtiles/polygon', methods=['POST'])
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
            # print(f"SELECT * FROM {vancouver_table_name} WHERE ST_Intersects(geo_polygon, 'POLYGON({polygon})');")
            cur.execute(f"SELECT * FROM {tiles_3d_table_name} WHERE ST_Intersects(geo_polygon, 'POLYGON({polygon})');")
            render_result = []
            result = cur.fetchall()
            for row in result:
                render_result.append('http://206.12.92.18:10083/3DTiles/' + row[0] + '/')

            return {'total_num': len(render_result), 'regions': render_result}

        except Exception as e:
            conn.rollback()
            abort(500)


@app.route('/3dtiles/circle', methods=['GET'])
def tile_3d_circle_intersect():
    args = request.args
    longitude = args.get('longitude', type=float)
    latitude = args.get('latitude', type=float)
    radius = args.get('radius', type=int)
    if longitude is None or latitude is None or radius is None:
        abort(422)

    try:
        cur.execute(
            f"SELECT * from {tiles_3d_table_name} where ST_Intersects(geo_polygon, ST_Buffer(ST_MakePoint({longitude}, {latitude})::geography, {radius}));")
        render_result = []
        result = cur.fetchall()
        for row in result:
            render_result.append('http://206.12.92.18:10083/3DTiles/' + row[0] + '/')
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
        # UTC time with this format: 2022-03-27T13:07:22Z
        try:
            year = int(time[0:4])
            month = int(time[5:7])
            day = int(time[8:10])
            hour = int(time[11:13])
            minute = int(time[14:16])
            second = int(time[17:19])
            time = ts.utc(year, month, day, hour, minute, second)
        except Exception as e:
            abort(400)

    satellite_names = [sat.name for sat in satellites]
    satellite_ids = [str(sat.model.satnum) for sat in satellites]

    try:
        names = utils.split_check(names, satellite_names)
        ids = utils.split_check(ids, satellite_ids)
    except:
        # abort(422)
        abort(Response('invalid name or id'))

    if len(names) != 0 and len(ids) != 0:
        abort(Response('names and ids are not supported at the same time'))

    # if no name and id specified, return the whole satellites locations
    if len(names) == 0 and len(ids) == 0:
        response = {}
        for gps in satellites:
            geocentric = gps.at(time)
            sub_point = wgs84.subpoint(geocentric)
            response[gps.name] = {
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
                response[gps.name] = {
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
                    'latitude': sub_point.latitude.degrees,
                    'longitude': sub_point.longitude.degrees,
                    'height': sub_point.elevation.m
                }
        return response

    # # if no name passed as parameter or the name is not in the name list, return the whole satellites locations
    # if name is None or name not in satellite_names:
    #     response = {}
    #     for gps in satellites:
    #         geocentric = gps.at(time)
    #         sub_point = wgs84.subpoint(geocentric)
    #         response[gps.name] = {
    #             'latitude': sub_point.latitude.degrees,
    #             'longitude': sub_point.longitude.degrees,
    #             'height': sub_point.elevation.m
    #         }
    #     return response
    # # if name is in the list, return the corresponding location
    # else:
    #     for gps in satellites:
    #         if gps.name == name:
    #             sub_point = wgs84.subpoint(gps.at(time))
    #             return {name: {
    #                 'latitude': sub_point.latitude.degrees,
    #                 'longitude': sub_point.longitude.degrees,
    #                 'height': sub_point.elevation.m
    #             }}
    #     abort(500)