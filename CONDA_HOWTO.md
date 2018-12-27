# Managing Conda environment for the project

In order to get all the dependencies in place 
for the python packages we use the `conda` environment
in this project.


[Miniconda](https://conda.io/miniconda.html) 
is a cross-platform package manager that allows managing
dependencies and creates a corresponding python *environment*. 

1) Install [miniconda](https://conda.io/miniconda.html)

2) Create the `bno055-usb-stick` environment:
`
conda env create -f environment.yml
`

3) Update the `bno055-usb-stick` environment:
`
conda-env update -n bno055-usb-stick -f environment.yml
`

4) Activate the `bno055-usb-stick` environment:
Mac and Linux:
`
source activate bno055-usb-stick
`

5) Remove the `bno055-usb-stick` environment 
(delete the corresponding python packages):
`
conda env remove --name bno055-usb-stick
`