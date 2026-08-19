#!/usr/bin/env python3                                                                                                                          
import carla                                                                                                                                    
import time                                                                                                                                     
                                                                                                                                                  
client = carla.Client('localhost', 2000)                                                                                                        
client.set_timeout(10.0)                                                                                                                        
world = client.get_world()
                                                                                                                                                  
bp = world.get_blueprint_library().find('vehicle.audi.etron')
bp.set_attribute('role_name', 'ego_vehicle')                                                                                                    
                                              
spawn = world.get_map().get_spawn_points()[0]                                                                                                   
vehicle = world.spawn_actor(bp, spawn)
print(f'Spawned id={vehicle.id} at {spawn.location}')                                                                                           
                                          
try:                                                                                                                                            
    while True:                                                                                                                                 
        time.sleep(1)
except KeyboardInterrupt:                                                                                                                       
      vehicle.destroy()                   
      print('Destroyed')
