#!/usr/bin/env python3                                                                                                                          
import carla, time                                                                                                                              
                                                                                                                                                  
client = carla.Client('localhost', 2000)                                                                                                        
client.set_timeout(10.0)                                                                                                                        
world = client.get_world()                                                                                                                      
bp_lib = world.get_blueprint_library()      
                                                                                                                                                  
# 차량          
v_bp = bp_lib.find('vehicle.audi.etron')                                                                                                        
v_bp.set_attribute('role_name', 'ego_vehicle')
spawn = world.get_map().get_spawn_points()[3]                                                                                                   
vehicle = world.spawn_actor(v_bp, spawn)    
#vehicle.enable_for_ros()                                                                                                                        
print(f'Vehicle id={vehicle.id}')
                                                                                                                                                  
# LiDAR (차량 위)                       
l_bp = bp_lib.find('sensor.lidar.ray_cast')                                                                                                     
l_bp.set_attribute('role_name', 'ego_vehicle')                                                                                                  
l_bp.set_attribute('ros_name', 'front') 
l_bp.set_attribute('channels', '128')                                                                                                           
l_bp.set_attribute('range', '100')                                                                                                              
l_bp.set_attribute('points_per_second', '2560000')
l_bp.set_attribute('rotation_frequency', '10')                                                                                                  
lidar = world.spawn_actor(l_bp, carla.Transform(carla.Location(x=0, z=2.0)), attach_to=vehicle)
lidar.enable_for_ros()                                                                                                                          
print(f'LiDAR id={lidar.id} → /carla/ego_vehicle/sensor/lidar/front/point_cloud')                                                               
                                                                                                                                                  
# Camera (전방)                                                                                                                                 
c_bp = bp_lib.find('sensor.camera.rgb')                                                                                                         
c_bp.set_attribute('role_name', 'ego_vehicle')                                                                                                  
c_bp.set_attribute('ros_name', 'camera')                                                                                                        
c_bp.set_attribute('image_size_x', '800')                                                                                                       
c_bp.set_attribute('image_size_y', '400')   
c_bp.set_attribute('fov', '90')                                                                                                                 
camera = world.spawn_actor(c_bp, carla.Transform(carla.Location(x=1.5, z=1.5)), attach_to=vehicle)
camera.enable_for_ros()                                                                                                                         
print(f'Camera id={camera.id} → /carla/ego_vehicle/sensor/camera/image')
                                                                                                                                                  
try:                                                                                                                                            
    print('\nCtrl+C to destroy')        
    while True: time.sleep(1)                                                                                                                   
except KeyboardInterrupt:                                                                                                                       
    for a in [camera, lidar, vehicle]:  
        try: a.destroy()                                                                                                                        
        except: pass                                                                                                                            
    print('Destroyed')
