#!/usr/bin/python3
from ast import parse
import json
from unicodedata import name
from flask import Flask, request, jsonify, redirect, send_from_directory, send_file
from flask_restful import Resource, Api
from json import dumps, loads
import io
import os
import sys
import time
import shutil
from skyfield.api import load, wgs84
from skyfield.api import EarthSatellite
import sys, getopt



app = Flask(__name__)
api = Api(app)
ts = load.timescale()
stations_url = 'https://www.celestrak.com/NORAD/elements/supplemental/gps.txt'
        
class Query(Resource):  
   
    def get(self,):
        print(request.args['longitude'])
        print(request.args['latitude'])
        print(request.args['radius'])
        if int(float(request.args['longitude'])) == -117 and int(float(request.args['latitude'])) == 32:
            return_data = {'num' : 1,
                       'list' : [
                            'http://206.12.92.18:10083/3DTiles/San_Diego/tileset.json'
                            ]
                       }
        elif int(float(request.args['longitude'])) == -75 and int(float(request.args['latitude'])) == 40:
            return_data = {'num' : 1,
                       'list' : [
                            'http://206.12.92.18:10083/3DTiles/test/tileset.json'
                            ]
                       }
        elif int(float(request.args['longitude'])) == -73 and int(float(request.args['latitude'])) == 41:
            return_data = {'num' : 1,
                       'list' : [
                            'http://206.12.92.18:10083/3DTiles/Manhattan/tileset.json'
                            ]
                       }
        else:
            return_data = {'num' : 0}


        return jsonify(return_data)


    def post(self):
        print(request.json)    
        return "success"

class Satellites(Resource):  
   
    def get(self,):
        
        satellites = load.tle_file(stations_url)
        print('Loaded', len(satellites), 'satellites')
        satlist = {sat.name: sat.model.satnum for sat in satellites}

        print(satlist)

        return jsonify(satlist)

class Locate(Resource):  
   
    def get(self,):
        
        returnlist = {}
        print(request.args['satellites'])
        print(request.args['time'])
        satellites_request = request.args['satellites']
        arg = request.args['time']

        year = int(arg[0:4])
        month = int(arg[4:6])
        day = int(arg[6:8])
        hour = int(arg[8:10])
        minute = int(arg[10:12])
        second = int(arg[12:])
        print(year, month, day, hour, minute, second)
        t = ts.utc(year, month, day, hour, minute, second) 
        
        satellites = load.tle_file(stations_url)
        by_id = {sat.model.satnum: sat for sat in satellites}
        print(by_id)

        arr = satellites_request.split(',')

        for id in arr:
            satellite = by_id[int(id)]
            geocentric = satellite.at(t)
            subpoint = wgs84.subpoint(geocentric)
            print('Latitude:', subpoint.latitude.degrees)
            print('Longitude:', subpoint.longitude.degrees)
            print('Height: {:.1f} m'.format(subpoint.elevation.m))
            returnlist[int(id)] = {'Latitude' : subpoint.latitude.degrees,
                            'Longitude' : subpoint.longitude.degrees,
                            'Elevation' : subpoint.elevation.m           
            }

        return jsonify(returnlist)

    
api.add_resource(Query, '/query') 
api.add_resource(Satellites, '/satellites') 
api.add_resource(Locate, '/locate') 

if __name__ == '__main__':
    app.run(host='0.0.0.0', port = 4444, threaded=True)
    #app.run()




    
