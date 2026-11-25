import os
from glob import glob
from setuptools import setup

package_name = 'pentographe_description'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],

    data_files=[
        ('share/ament_index/resource_index/packages',
         ['resource/' + package_name]),

        ('share/' + package_name,
         ['package.xml']),

        (os.path.join('share', package_name, 'urdf'),
         glob('urdf/*.urdf')),

        (os.path.join('share', package_name, 'meshes'),
         glob('meshes/*.dae')),

        (os.path.join('share', package_name, 'launch'),
         glob('launch/*.launch.py')),

        (os.path.join('share', package_name, 'config'),
         glob('config/*')),

        (os.path.join('share', package_name, 'sdf'),
         glob('sdf/*.sdf')),

        (os.path.join('share', package_name, 'worlds'),
         glob('worlds/*.sdf')),
    ],

    install_requires=['setuptools'],
    zip_safe=True,

    maintainer='zilan',
    maintainer_email='zilan.duman@insa-strasbourg.fr',

    description='Description, visualisation et simulation du pantographe à cinq barres',

    license='Apache-2.0',
    tests_require=['pytest'],

    entry_points={
        'console_scripts': [
            'joint_bridge = pentographe_description.joint_bridge:main',
        ],
    },
)
