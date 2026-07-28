from setuptools import find_packages, setup


package_name = "gemstone_bringup"


setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(exclude=("test",)),
    data_files=[
        ("share/ament_index/resource_index/packages", [f"resource/{package_name}"]),
        (f"share/{package_name}", ["package.xml"]),
        (f"share/{package_name}/launch", ["launch/bringup.launch.py"]),
        (f"share/{package_name}/config", ["config/bringup.yaml"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Ali",
    maintainer_email="ali@localhost",
    description="Linux-first ROS 2 bringup package for T3 Gemstone.",
    license="Apache-2.0",
    entry_points={
        "console_scripts": [
            "imu_node = gemstone_bringup.imu_node:main",
        ],
    },
)
