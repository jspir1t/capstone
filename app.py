from flask import Flask, request
import psycopg2

app = Flask(__name__)

conn = psycopg2.connect(host='206.12.92.18', dbname='propdb', user='propval', password='BCParks')
cur = conn.cursor()
table_name = 'lidar_north_va'


@app.route('/', methods=['POST'])
def hello_world():

    if not request.json:
        return {}
    paras = request.json
    try:
        polygon = f"({paras['p1'][0]} {paras['p1'][1]},{paras['p2'][0]} {paras['p2'][1]},{paras['p3'][0]} {paras['p3'][1]},{paras['p4'][0]} {paras['p4'][1]},{paras['p5'][0]} {paras['p5'][1]})"
        assert paras['p1'] == paras['p5']
    except:
        raise SyntaxError

    try:
        print(f"SELECT * FROM {table_name} WHERE ST_Intersects(geo_polygon, 'POLYGON({polygon})');")
        cur.execute(f"SELECT * FROM {table_name} WHERE ST_Intersects(geo_polygon, 'POLYGON({polygon})');")
    except:
        print("SQL error")

    render_result = ''
    result = cur.fetchall()
    for row in result:
        # for column in row[:-1]:
        #     render_result += str(column)
        render_result += row[1]
        render_result += '\n'

    return render_result


@app.route('/file_path')
def file_path():
    return '/data/test/San_Diego/tileset.json'