![ContExt Banner](https://i.ibb.co/4SkhSKG/cont-Ext-Cover.png)
<p align="center">
  <a href="https://github.com/RafaelCasamaximo/contExt/issues/new/choose">Report a Bug</a> •
  <a href="https://github.com/RafaelCasamaximo/contExt/issues/new/choose">Request a Feature</a>
</p>

## About the Project
This application performs treatment and contour extraction from an image, and the generation of sparse or adaptive meshes intended for the application of numerical methods, especially finite differences.

## Getting Started
This software uses `Python` and libraries managed by `PIP`.

### Graphical User Interface
The graphical interface was implemented using the [DearPyGUI](https://github.com/hoffstadt/DearPyGui) library, which makes use of graphical APIs (`DirectX 11` on Windows, `Metal` on macOS, `OpenGL 3` on Linux and `OpenGL` ES on Raspberry Pi 4), therefore, you must have the necessary drivers and software to run this software.

### Installing Libraries
To install all the requirements run the command:
```python
pip install -r requirements.txt
```
### Complete List of Libraries
| Library | Version |
|--|--|
| dearpygui | 1.8.0 |
| numpy| 1.24.1 |
| opencv_python| 4.7.0.68 |
| shapely| 2.0.1 |
| pyinstaller| 5.7.0 |

### How to generate the binary
To generate the binary it is possible to use one of the existing build scripts in the project files.

#### Windows

    .\build.cmd
#### Linux

    bash ./build.sh

## How to Use

To execute the software run the command:

    python main.py

### Features

 - Importing a large range of image formats;
 - Various filters for image processing;
 - Selection of contour extraction method;
 - Parameterization of the generated contour;
 - Generation of sparse or adaptive meshes;

### Screenshots
![Processing Tab](https://i.ibb.co/YbB9Td1/image.png)
![Filtering Tab](https://i.ibb.co/Svt0bjb/1.png)
![Thresholding Tab](https://i.ibb.co/dbPHGX8/2.png)
![Contour Extraction Tab](https://i.ibb.co/WkBhxfB/3.png)
![Mesh Generation Tab](https://i.ibb.co/fYpFPRM/4.png)

## Download
You can download the binaries for each operating system on the [Releases tab](https://github.com/RafaelCasamaximo/contExt/releases).

## Contributing
You can [open a new issue or request a feature here](https://github.com/RafaelCasamaximo/contExt/issues/new/choose).

## Code of Conduct
Access our [Code of Conduct](https://github.com/RafaelCasamaximo/contExt/blob/main/CODE_OF_CONDUCT.md)

## License
We are under the [GNU GENERAL PUBLIC LICENSE V3.0](https://github.com/RafaelCasamaximo/contExt/blob/main/LICENSE) and this software is patented on [INPI (National Institute of Industrial Property)](https://www.gov.br/inpi/pt-br).

## Credits

 - [Pedro Zaffalon da Silva](https://github.com/PedroZaffalon)
 - [Rafael Furlanetto Casamaximo](https://github.com/RafaelCasamaximo)
## Acknowledgments
Special thanks to professor Neyva Romeiro and the other professors at [LabSan](http://www.uel.br/laboratorios/labsan/index.html) and [Universidade Estadual de Londrina](https://portal.uel.br/home/).
