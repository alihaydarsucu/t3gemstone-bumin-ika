from setuptools import find_packages, setup

package_name = 'gemstone_exploration_demo'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/params',
            ['params/exploration_demo_params.yaml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='gemstone',
    maintainer_email='gemstone@todo.todo',
    description='LiDAR tabanli exploration/demo planner node u.',
    license='Apache-2.0',
    extras_require={
        'test': ['pytest'],
    },
    entry_points={
        'console_scripts': [
            'gemstone_exploration_demo_node = '
            'gemstone_exploration_demo.exploration_demo_node:main',
        ],
    },
)
