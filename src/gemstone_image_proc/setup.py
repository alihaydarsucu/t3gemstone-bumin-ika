from setuptools import find_packages, setup

package_name = 'gemstone_image_proc'

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
    description='Goruntu isleme node iskeleti.',
    license='Apache-2.0',
    extras_require={
        'test': ['pytest'],
    },
    entry_points={
        'console_scripts': [
            'image_processing_node = gemstone_image_proc.image_processing_node:main',
        ],
    },
)
