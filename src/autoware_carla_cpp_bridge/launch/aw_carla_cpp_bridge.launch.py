from launch import LaunchDescription
from launch_ros.actions import Node

SIM_TIME = {'use_sim_time': True}

def generate_launch_description():
    return LaunchDescription([
        # Launch the central aw_carla_bridge_node
        Node(
            package='autoware_carla_cpp_bridge',
            executable='aw_carla_bridge_node',
            name='aw_carla_bridge',
            parameters=[{
                'nodes_to_wait_for': ['autoware_e2e_node', 'lidar_bridge_1',
                                      'lidar_bridge_2', 'camera_bridge_1']
            }, SIM_TIME],
            remappings=[
                ('/control/trajectory_follower/control_cmd', '/control/command/control_cmd'),
            ],
            arguments=['--ros-args', '--log-level', 'info']
        ),

        # Launch lidar_bridge_node instances
        Node(
            package='autoware_carla_cpp_bridge',
            executable='lidar_bridge_node',
            name='lidar_bridge_1',
            parameters=[SIM_TIME],
            arguments=[
                '/carla/ego_vehicle/sensor/lidar/front/point_cloud',
                '/sensor/lidar/front',
                'lidar_front',
                '128'
            ]
        ),
        Node(
            package='autoware_carla_cpp_bridge',
            executable='lidar_bridge_node',
            name='lidar_bridge_2',
            parameters=[SIM_TIME],
            arguments=[
                '/carla/ego_vehicle/sensor/lidar/back/point_cloud',
                '/sensor/lidar/rear',
                'lidar_rear',
                '64'
            ]
        ),
        # Launch camera_bridge_node instances
        Node(
            package='autoware_carla_cpp_bridge',
            executable='camera_bridge_node',
            name='camera_bridge_1',
            parameters=[SIM_TIME],
            arguments=[
                '/carla/ego_vehicle/sensor/camera/image',
                '/sensing/camera/traffic_light/image_raw',
                'camera_front_optical_link',
                '90', '400', '800'
            ]
        )
    ])