#!/usr/bin/env python3
import carla
import time

def main():
    # 1. 클라이언트 연결
    client = carla.Client('localhost', 2000)
    client.set_timeout(10.0)
    world = client.get_world()
    bp_lib = world.get_blueprint_library()
    
    actor_list = []

    try:
        # 2. 차량 생성 — role_name='ego_vehicle' 필수
        v_bp = bp_lib.find('vehicle.audi.etron')
        v_bp.set_attribute('role_name', 'ego_vehicle')
        
        spawn_point = world.get_map().get_spawn_points()[0]
        vehicle = world.spawn_actor(v_bp, spawn_point)
        actor_list.append(vehicle)
        print(f'Vehicle id={vehicle.id} (role_name=ego_vehicle)')

        # 3. LiDAR 생성 — ros_name 설정
        l_bp = bp_lib.find('sensor.lidar.ray_cast')
        l_bp.set_attribute('role_name', 'front')
        l_bp.set_attribute('ros_name', 'sensor/lidar/front') # ROS 토픽 경로 결정
        l_bp.set_attribute('channels', '128')
        l_bp.set_attribute('range', '100')
        l_bp.set_attribute('rotation_frequency', '20')
        l_bp.set_attribute('points_per_second', '1800000')
        
        l_tf = carla.Transform(carla.Location(x=0.3, z=1.70))
        lidar = world.spawn_actor(l_bp, l_tf, attach_to=vehicle)
        actor_list.append(lidar)

        # ROS 활성화 및 데이터 스트림 시작
        if hasattr(lidar, 'enable_for_ros'):
            lidar.enable_for_ros()
        lidar.listen(lambda data: None)
        print(f'LiDAR id={lidar.id} attached to vehicle')

        # 4. Camera 생성 — ros_name 설정
        c_bp = bp_lib.find('sensor.camera.rgb')
        c_bp.set_attribute('role_name', 'camera')
        c_bp.set_attribute('ros_name', 'sensor/camera')
        c_bp.set_attribute('image_size_x', '800')
        c_bp.set_attribute('image_size_y', '400')
        c_bp.set_attribute('fov', '90')
        
        c_tf = carla.Transform(carla.Location(z=2.0))
        camera = world.spawn_actor(c_bp, c_tf, attach_to=vehicle)
        actor_list.append(camera)

        if hasattr(camera, 'enable_for_ros'):
            camera.enable_for_ros()
        camera.listen(lambda data: None)
        print(f'Camera id={camera.id} attached to vehicle')

        print('\n--- 모든 센서 활성화 완료 ---')
        print('ros2 topic list 명령어로 확인하세요.')
        print('Ctrl+C를 누르면 종료 및 객체가 삭제됩니다.')

        while True:
            # 시뮬레이션 동기화 유지
            world.wait_for_tick()
            time.sleep(0.1)

    except KeyboardInterrupt:
        print('\n사용자에 의해 종료 요청됨...')
    finally:
        print('객체 삭제 중...')
        for actor in reversed(actor_list):
            if actor is not None:
                actor.destroy()
        print('삭제 완료. 프로그램을 종료합니다.')

if __name__ == '__main__':
    main()
