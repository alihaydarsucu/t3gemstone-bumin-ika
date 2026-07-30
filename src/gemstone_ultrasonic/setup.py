from setuptools import find_packages, setup

package_name = 'gemstone_ultrasonic'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='gemstone',
    maintainer_email='gemstone@todo.todo',
    description='HC-SR04 benzeri ultrasonik mesafe sensoru (libgpiod) node.',
    license='Apache-2.0',
    extras_require={
        'test': ['pytest'],
    },
    entry_points={
        'console_scripts': [
            'ultrasonic_node = gemstone_ultrasonic.ultrasonic_node:main',
        ],
    },
)
