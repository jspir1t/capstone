
import laspy

input_path="/mnt/data/lidar/montreal/"
dataname="307-5062_2015.laz"

def scaled_x_dimension(las_file):
    x_dimension = las_file.X
    scale = las_file.header.scales[0]
    offset = las_file.header.offsets[0]
    return (x_dimension * scale) + offset

def scaled_y_dimension(las_file):
    y_dimension = las_file.Y
    scale = las_file.header.scales[1]
    offset = las_file.header.offsets[1]
    return (y_dimension * scale) + offset

def scaled_z_dimension(las_file):
    z_dimension = las_file.Z
    scale = las_file.header.scales[2]
    offset = las_file.header.offsets[2]
    return (z_dimension * scale) + offset

def main():

    with laspy.open(input_path+dataname) as fh:
        print('Points from Header:', fh.header.point_count)
        f = fh.read()
        #print(f)
        print('Points from data:', len(f.points))
        print('min: ', f.header.min)  
        print('max: ', f.header.max) 

        print('scale: ', f.header.scale)  
        print('offset: ', f.header.offset)  

        print()

        

        scaled_x = scaled_x_dimension(f)
        scaled_y = scaled_y_dimension(f)
        scaled_z = scaled_z_dimension(f)

        
        print('actual x: ', scaled_x)
        print('actual y: ', scaled_y)
        print('actual z: ', scaled_z)
        

        print(' X: ', f.X)
        print(' Y: ', f.Y)
        print(' Z: ', f.Z)
        

        print(' x: ', f.x)
        print(' y: ', f.y)
        print(' z: ', f.z)



if __name__ == "__main__":
    main()