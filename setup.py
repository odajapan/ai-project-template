from setuptools import find_packages, setup


setup(
	name="your_project_name",
	package_dir={"": "src"},
	packages=find_packages("src"),
	version="0.1.0",
	description="Python data science project template.",
	author="Hideto Oda",
	license="MIT",
)
