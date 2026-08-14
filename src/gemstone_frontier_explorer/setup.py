from setuptools import find_packages, setup
import os

package_name = 'gemstone_frontier_explorer'

data_files = [
    ('share/ament_index/resource_index/packages',
     ['resource/' + package_name]),
    ('share/' + package_name, ['package.xml']),
]
params_dir = os.path.join('share', package_name, 'params')
launch_dir = os.path.join('share', package_name, 'launch')
for d in ('params', 'launch'):
    base = os.path.join(os.path.dirname(__file__), d)
    files = []
    for f in os.listdir(base):
        if f.startswith('.') or f == '__pycache__':
            continue
        if os.path.isfile(os.path.join(base, f)):
            files.append(os.path.join(d, f))
    data_files.append((os.path.join('share', package_name, d), files))

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=data_files,
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='gemstone',
    maintainer_email='gemstone@todo.todo',
    description='Frontier-tabanli otonom oda kesif node paketi (MIGHTY ilhamli).',
    license='Apache-2.0',
    extras_require={
        'test': ['pytest'],
    },
    entry_points={
        'console_scripts': [
            'frontier_explorer_node = '
            'gemstone_frontier_explorer.frontier_explorer_node:main',
        ],
    },
)
