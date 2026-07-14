def build_terrain_mesh_data(width,length,z=0.0):
    if width<=0 or length<=0: raise ValueError("map dimensions must be positive")
    return [(-width/2,-length/2,z),(width/2,-length/2,z),(width/2,length/2,z),(-width/2,length/2,z)],[(0,1,2,3)]
