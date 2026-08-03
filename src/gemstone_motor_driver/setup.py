from setuptools import find_packages, setup

package_name = 'gemstone_motor_driver'

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
    description='Diferansiyel surus GPIO (libgpiod) motor surucu + enkoder odometrisi node.',
    license='Apache-2.0',
    extras_require={
        'test': ['pytest'],
    },
    entry_points={
        'console_scripts': [
            'motor_driver_node = gemstone_motor_driver.motor_driver_node:main',
            'motion_state_node = gemstone_motor_driver.motion_state_node:main',
        ],
    },
)
