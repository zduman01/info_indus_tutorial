import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import IncludeLaunchDescription
from launch.actions import ExecuteProcess, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource


def generate_launch_description():

    description_dir = get_package_share_directory(
        'pentographe_description'
    )

    kinematics_dir = get_package_share_directory(
        'pentographe_kinematics'
    )

    urdf_file = os.path.join(
        description_dir,
        'urdf',
        'pentographe.urdf'
    )

    with open(urdf_file, 'r') as fichier:
        robot_description = fichier.read()

    # Cinematique avec les dimensions Creo
    kinematics = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                kinematics_dir,
                'launch',
                'rviz_joint_state.launch.py'
            )
        )
    )

    # Conversion des angles pour l'URDF
    joint_bridge = Node(
        package='pentographe_description',
        executable='joint_bridge',
        output='screen'
    )

    # Publication des transformations TF
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{
            'robot_description': robot_description
        }],
        output='screen'
    )

    # Configuration RViz
    rviz_config = os.path.join(
        description_dir,
        'config',
        'pentographe.rviz'
    )

    # Lancement de RViz
    rviz = Node(
        package='rviz2',
        executable='rviz2',
        arguments=['-d', rviz_config]
        if os.path.isfile(rviz_config) else [],
        output='screen'
    )

    # Configuration RQT
    rqt_config = os.path.join(
        description_dir,
        'config',
        'pentographe.perspective'
    )

    # Lancement de RQT
    rqt = ExecuteProcess(
        cmd=['rqt', '--perspective-file', rqt_config]
        if os.path.isfile(rqt_config) else ['rqt'],
        output='screen'
    )

    # Initialisation de la position du stylo
    initialisation = TimerAction(
        period=5.0,
        actions=[
            ExecuteProcess(
                cmd=[
                    'ros2', 'topic', 'pub',
                    '--once',
                    '/pen_target',
                    'geometry_msgs/msg/Point',
                    '{x: 0.07, y: 0.15, z: 0.0}'
                ],
                output='screen'
            )
        ]
    )

    return LaunchDescription([
        kinematics,
        joint_bridge,
        robot_state_publisher,
        rviz,
        rqt,
        initialisation
    ])
