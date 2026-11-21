from setuptools import setup

setup(
    name="cbpi4-hx711-loadcell",
    version="0.1.3",
    description="CraftBeerPi 4 HX711 load cell plugin with a stable scale and median filter",
    author="Alexander Vollkopf",
    author_email="avollkopf@web.de",
    url="https://github.com/braubunker/cbpi4-hx711-loadcell",
    license="GPLv3",
    include_package_data=True,
    package_data={"cbpi4-hx711-loadcell": ["*.yaml", "*.py"]},
    packages=["cbpi4-hx711-loadcell"],
    install_requires=["hx711-rpi-py"],
)
