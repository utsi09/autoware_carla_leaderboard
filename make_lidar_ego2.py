#!/usr/bin/env python3
import carla
import time

def main():
    client = carla.Client('localhost', 2000)
    client.set_timeout(10.0)
    world = client.get_world()
    bp_lib = world.get_blueprint_library()

    actor_list = []

    try:
        # 1. Ego Vehicle 생성
        v_bp = bp_lib.find('vehicle.audi.etron')
        v_bp.set_attribute('role_name', 'ego_vehicle') # ROS Bridge가 이 이름을 보고 토픽 생성
        
        spawn_point = world.get_map().get_spawn_points()[0]
        vehicle = world.spawn_actor(v_bp, spawn_point)
        actor_list.append(vehicle)
        print(f'Vehicle spawned: {vehicle.id} (role_name: ego_vehicle)')

        # 2. LiDAR 센서 설정
        l_bp = bp_lib.find('sensor.lidar.ray_cast')
        l_bp.set_attribute('role_name', 'front') # 최종 토픽명에 영향 (/carla/ego_vehicle/front/...)
        l_bp.set_attribute('range', '100')
        l_bp.set_attribute('channels', '64')
        l_bp.set_attribute('points_per_second', '600000')
        l_bp.set_attribute('rotation_frequency', '10')

        # 차량 위 2m 지점에 부착
        lidar_transform = carla.Transform(carla.Location(x=0, y=0, z=2.0))
        lidar = world.spawn_actor(l_bp, lidar_transform, attach_to=vehicle)
        actor_list.append(lidar)
        
        # ROS 연동 활성화 (0.9.12+ 버전 대응)
        if hasattr(lidar, 'enable_for_ros'):
            lidar.enable_for_ros()
            print('LiDAR: enable_for_ros() called')
        
        # listen을 호출해야 데이터가 발생함 (callback은 비워둬도 무방)
        lidar.listen(lambda data: None)
        print(f'LiDAR spawned: {lidar.id} (attached to {vehicle.id})')

        print("\n[성공] 차량과 센서가 생성되었습니다.")
        print("이제 다른 터미널에서 'ros2 topic list'를 확인하세요.")
        
        while True:
            world.wait_for_tick()
            time.sleep(1)

    except KeyboardInterrupt:
        print('\n사용자에 의해 종료됨. 액터를 삭제합니다...')
    finally:
        for actor in actor_list:
            if actor.is_alive:
                actor.destroy()
        print('삭제 완료.')

if __name__ == '__main__':
    main()
