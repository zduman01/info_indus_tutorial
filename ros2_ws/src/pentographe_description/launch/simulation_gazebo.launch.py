import os

from launch import LaunchDescription
from launch.actions import (
    ExecuteProcess,
    IncludeLaunchDescription,
    TimerAction,
    RegisterEventHandler,
    EmitEvent
)
from launch.event_handlers import OnProcessExit
from launch.events import Shutdown
from launch.launch_description_sources import PythonLaunchDescriptionSource

from launch_ros.actions import Node

from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    # ==========================================
    # CHEMINS DES PACKAGES
    # ==========================================

    description_dir = get_package_share_directory(
        'pentographe_description'
    )

    kinematics_dir = get_package_share_directory(
        'pentographe_kinematics'
    )

    world_file = os.path.join(
        description_dir,
        'worlds',
        'pentographe_world.sdf'
    )

    sdf_file = os.path.join(
        description_dir,
        'sdf',
        'pentographe.sdf'
    )

    perspective_file = os.path.join(
        description_dir,
        'config',
        'pentographe.perspective'
    )

    # ==========================================
    # LANCEMENT DE GAZEBO
    # ==========================================

    gazebo = ExecuteProcess(
        cmd=[
            'ign', 'gazebo',
            world_file,
            '--physics-engine',
            'ignition-physics-bullet-plugin',
            '-r',
            '-v', '3'
        ],
        additional_env={
            'LIBGL_ALWAYS_SOFTWARE': '1',

            'IGN_GAZEBO_RESOURCE_PATH': os.pathsep.join(
                filter(None, [
                    description_dir,
                    os.environ.get('IGN_GAZEBO_RESOURCE_PATH', '')
                ])
            )
        },
        output='screen'
    )

    # ==========================================
    # IMPORTATION DU PENTOGRAPHE
    # ==========================================

    spawn_robot = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            '-world', 'pentographe_world',
            '-name', 'pentographe',
            '-file', sdf_file,
            '-x', '0',
            '-y', '0',
            '-z', '0.1',
            '-R', '1.5707963',
            '-P', '0',
            '-Y', '0'
        ],
        output='screen'
    )

    # Attendre le demarrage de Gazebo
    delayed_spawn = TimerAction(
        period=5.0,
        actions=[spawn_robot]
    )

    # ==========================================
    # BRIDGE ROS2 / GAZEBO
    # ==========================================

    ros_gazebo_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='parameter_bridge',
        arguments=[
            '/pentographe/moteur_gauche/cmd_pos'
            '@std_msgs/msg/Float64]ignition.msgs.Double',

            '/pentographe/moteur_droit/cmd_pos'
            '@std_msgs/msg/Float64]ignition.msgs.Double'
        ],
        output='screen'
    )

    # ==========================================
    # CINEMATIQUE INVERSE D'ANDREEA
    # ==========================================

    kinematics = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                kinematics_dir,
                'launch',
                'rviz_joint_state.launch.py'
            )
        )
    )

    # ==========================================
    # CONVERSION DES ANGLES MOTEURS
    # ==========================================

    gazebo_joint_bridge = Node(
    package='pentographe_description',
    executable='joint_bridge',
    name='gazebo_joint_bridge',
    parameters=[{'mode': 'gazebo'}],
    output='screen'
    )

    # ==========================================
    # INTERFACE RQT
    # ==========================================

    rqt = ExecuteProcess(
        cmd=[
            'rqt',
            '--perspective-file',
            perspective_file
        ],
        output='screen'
    )

    # ==========================================
    # DEMARRAGE APRES IMPORTATION DU ROBOT
    # ==========================================

    def after_spawn(event, context):

        if event.returncode != 0:
            return [
                EmitEvent(
                    event=Shutdown(
                        reason='Echec importation du pentographe'
                    )
                )
            ]

        return [
            ros_gazebo_bridge,
            kinematics,
            gazebo_joint_bridge,
            TimerAction(
                period=3.0,
                actions=[rqt]
            )
        ]

    start_control = RegisterEventHandler(
        OnProcessExit(
            target_action=spawn_robot,
            on_exit=after_spawn
        )
    )

    # ==========================================
    # ARRET GLOBAL SI GAZEBO EST FERME
    # ==========================================

    shutdown_gazebo = RegisterEventHandler(
        OnProcessExit(
            target_action=gazebo,
            on_exit=[
                EmitEvent(
                    event=Shutdown(
                        reason='Gazebo ferme'
                    )
                )
            ]
        )
    )

    # ==========================================
    # LANCEMENT GLOBAL
    # ==========================================

    return LaunchDescription([
        start_control,
        shutdown_gazebo,
        gazebo,
        delayed_spawn
    ])
