from skyfield.api import load, wgs84
from skyfield.api import EarthSatellite
import sys, getopt

stations_url = 'https://www.celestrak.com/NORAD/elements/supplemental/gps.txt'
satellites = load.tle_file(stations_url)
print('Loaded', len(satellites), 'satellites')
by_name = {sat.name: sat for sat in satellites}
ts = load.timescale()


def calculate(satellite_name, t):
    if satellite_name != '':
        # print("satellite")
        # for example 'GPS BIIR-2  (PRN 13)'
        satellite = by_name[satellite_name]
        print(satellite)
        geocentric = satellite.at(t)
        print(geocentric.position.km)

        subpoint = wgs84.subpoint(geocentric)
        print('Latitude:', subpoint.latitude.degrees)
        print('Longitude:', subpoint.longitude.degrees)
        print('Height: {:.1f} m'.format(subpoint.elevation.m))
        print('Height: {:.1f} km'.format(subpoint.elevation.km))

    else:
        for gps in satellites:
            print(gps.name)
            geocentric = gps.at(t)
            # print(geocentric.position.km)
            subpoint = wgs84.subpoint(geocentric)
            print('Latitude:', subpoint.latitude.degrees)
            print('Longitude:', subpoint.longitude.degrees)
            print('Height: {:.1f} m'.format(subpoint.elevation.m))
            print('Height: {:.1f} km'.format(subpoint.elevation.km))


def main(argv):
    satellite_name = ''
    # You can instead use ts.now() for the current time
    time = ts.now()
    try:
        opts, args = getopt.getopt(argv, "n:t:", ["name=", "time="])
    except getopt.GetoptError:
        # print(err)
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-n", "--name"):
            satellite_name = arg
        elif opt in ("-t", "--time"):
            print(arg[0:4])
            year = int(arg[0:4])
            month = int(arg[4:6])
            day = int(arg[6:8])
            hour = int(arg[8:10])
            minute = int(arg[10:12])
            second = int(arg[12:])
            print(year, month, day, hour, minute, second)
            time = ts.utc(year, month, day, hour, minute, second)
    calculate(satellite_name, time)


if __name__ == "__main__":
    main(sys.argv[1:])