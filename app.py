from flask import Flask, request, abort, jsonify
from werkzeug.exceptions import HTTPException
import psycopg2

app = Flask(__name__)

conn = psycopg2.connect(host='206.12.92.18', dbname='propdb', user='propval', password='BCParks')
cur = conn.cursor()
vancouver_table_name = 'lidar_north_va'


@app.errorhandler(Exception)
def handle_error(e):
    code = 500
    if isinstance(e, HTTPException):
        code = e.code
    return jsonify(error=str(e)), code


@app.route('/lidar/polygon', methods=['POST'])
def polygon_intersect():
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
def circle_intersect():
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