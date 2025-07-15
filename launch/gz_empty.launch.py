from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, SetEnvironmentVariable
from launch.substitutions import Command, PathJoinSubstitution, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.parameter_descriptions import ParameterValue
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():


# ================== ENVIRONMENT SETUP =================== #

    robot_description_path = get_package_share_directory('camlidarbot_description')  # -----> Change me!

    parent_of_share_path = os.path.dirname(robot_description_path)

    # --- Set GZ_SIM_RESOURCE_PATH / GAZEBO_MODEL_PATH ---
    set_gz_sim_resource_path = SetEnvironmentVariable(
        name='GZ_SIM_RESOURCE_PATH', 
        value=[
            os.environ.get('GZ_SIM_RESOURCE_PATH', ''), # Keep existing paths
            os.path.pathsep, # Separator for paths
            parent_of_share_path # Add the path containing your package's share directory
        ]
    )

    # --- Launch Arguments (Optional but good practice) ---
    use_sim_time = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use simulation (Gazebo) clock if true'
    )
    

# ========================================================= #



# ======================== RVIZ ========================== #

    # Declare arguments
    urdf_path_arg = DeclareLaunchArgument(
        'urdf_path',
        default_value=PathJoinSubstitution([
            FindPackageShare('camlidarbot_description'), # -----> Change me!
            'urdf',
            'robot.urdf.xacro'  # -----> Change me!
        ]),
        description='Path to the URDF file for the robot description.'
    )

    rviz_config_path_arg = DeclareLaunchArgument(
        'rviz_config_path',
        default_value=PathJoinSubstitution([
            FindPackageShare('camlidarbot_description'),  # -----> Change me!
            'rviz',
            'camlidarbot_config.rviz'  # -----> Change me!
        ]),
        description='Path to the RViz configuration file.'
    )

    # Get the robot description from the URDF file
    robot_description_content = ParameterValue(
        Command(['xacro ', LaunchConfiguration('urdf_path')]),
        value_type=str
    )

    # Robot State Publisher node
    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{
            'robot_description': robot_description_content,
            'use_sim_time': LaunchConfiguration('use_sim_time')
        }]
    )

    # RViz2 node
    rviz2_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', LaunchConfiguration('rviz_config_path')]
    )

    # Joint State Publisher GUI node - ONLY UNCOMMENT IF NOT RUNNING ANY ROS/GAZEBO BRIDGE!!!
    #joint_state_publisher_gui_node = Node(
    #    package='joint_state_publisher_gui',
    #    executable='joint_state_publisher_gui',
    #    name='joint_state_publisher_gui'
    #)

# ========================================================= #


# ======================== GAZEBO ========================== #


    # Include the Gazebo Sim launch file (using gz_sim.launch.py)
    gz_sim_launch_file = PathJoinSubstitution([
        FindPackageShare('ros_gz_sim'),
        'launch',
        'gz_sim.launch.py'
    ])

    gazebo_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([gz_sim_launch_file]),
        launch_arguments={'gz_args': '-r empty.sdf'}.items() # Use -r for 'run' and loads the world.
    )

    # This is the corrected way to spawn the entity using ros_gz_sim's 'create' executable
    # It reads the robot_description from the parameter server and spawns it.
    spawn_entity_node = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            '-name', 'camlidarbot',   # -----> Change me!
            '-topic', 'robot_description', # Read URDF from /robot_description topic
            '-x', '0', # Default spawn location
            '-y', '0',
            '-z', '0.5'
        ],
        output='screen'
    )

# ========================================================= #


# ================= ROS / GAZEBO BRIDGE =================== #

    bridge_config_file = os.path.join(robot_description_path, 'yaml', 'gazebo_bridge.yaml')

    ros_gz_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='ros_gz_bridge',
        parameters=[
            {'config_file': bridge_config_file}
        ],
        output='screen'
    )


# ========================================================= #

    return LaunchDescription([
        urdf_path_arg,
        rviz_config_path_arg,
        use_sim_time,
        set_gz_sim_resource_path, # This must come before any nodes that rely on it
        robot_state_publisher_node,
        #joint_state_publisher_gui_node,    # - ONLY UNCOMMENT IF NOT RUNNING ANY ROS/GAZEBO BRIDGE!!!
        gazebo_launch,
        spawn_entity_node,
        ros_gz_bridge,
        rviz2_node
    ])