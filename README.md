![ContExt Banner](https://i.ibb.co/4SkhSKG/cont-Ext-Cover.png)
<p align="center">
  <a href="https://github.com/RafaelCasamaximo/contExt/issues/new/choose">Report a Bug</a> •
  <a href="https://github.com/RafaelCasamaximo/contExt/issues/new/choose">Request a Feature</a>
</p>

## About the Project
ContExt is a desktop application for image processing, contour extraction, interpolation, and sparse or adaptive mesh generation for numerical analysis workflows.

## Getting Started
This project uses `Python`, a local `.venv` virtual environment, and dependencies defined in `pyproject.toml`.

### Graphical User Interface
The graphical interface is implemented with [DearPyGUI](https://github.com/hoffstadt/DearPyGui), which uses platform graphics APIs (`DirectX 11` on Windows, `Metal` on macOS, `OpenGL 3` on Linux, and `OpenGL ES` on Raspberry Pi 4). Make sure the required graphics drivers are available on the target machine.

### Create the Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
```

On Windows:

```powershell
.venv\Scripts\Activate.ps1
```

### Install Dependencies
```bash
python3 -m pip install --upgrade pip
python3 -m pip install -e .
```

If you prefer a compatibility file instead of editable installation:

```bash
python3 -m pip install -r requirements.txt
```

### How to generate the binaries
Use the platform-specific build scripts in the project root. Each script creates a distributable artifact in `release/`.

#### macOS

    bash ./build-macos.sh

Creates:

    release/ContExt-macos-<arch>.app.zip

By default the macOS build uses the current machine architecture (`arm64` or `x64`). You can override it with:

    CONTEXT_TARGET_ARCH=arm64 bash ./build-macos.sh

or, if you have a universal2-compatible Python environment and dependencies:

    CONTEXT_TARGET_ARCH=universal2 bash ./build-macos.sh

#### Windows

    .\build.cmd

Creates:

    release\ContExt-windows-x64.zip

#### Linux

    bash ./build.sh

Creates:

    release/ContExt-linux-x64.tar.gz

These first-step builds are unsigned. macOS and Windows may show security warnings when opening the application.

## How to Use

To execute the software run either command below:

    python3 -m context

or

    python3 main.py

### Features

 - Import a large range of image formats
 - Apply multiple image processing filters
 - Extract contours with configurable approximation options
 - Interpolate contours before export or meshing
 - Generate sparse or adaptive meshes

### Screenshots
![Processing Tab](https://i.ibb.co/YbB9Td1/image.png)
![Filtering Tab](https://i.ibb.co/Svt0bjb/1.png)
![Thresholding Tab](https://i.ibb.co/dbPHGX8/2.png)
![Contour Extraction Tab](https://i.ibb.co/WkBhxfB/3.png)
![Mesh Generation Tab](https://i.ibb.co/fYpFPRM/4.png)

## Download
You can download the binaries for each operating system on the [Releases tab](https://github.com/RafaelCasamaximo/contExt/releases).
Tagged releases publish the following artifacts:

 - `ContExt-macos-<arch>.app.zip`
 - `ContExt-windows-x64.zip`
 - `ContExt-linux-x64.tar.gz`

## Contributing
You can [open a new issue or request a feature here](https://github.com/RafaelCasamaximo/contExt/issues/new/choose).
If you want to contribute to the project, see our [contribution guideline](https://github.com/RafaelCasamaximo/contExt/blob/main/CONTRIBUTING.md).

## Code of Conduct
Read our [Code of Conduct](https://github.com/RafaelCasamaximo/contExt/blob/main/CODE_OF_CONDUCT.md).

## License
This project is distributed under the [GNU GENERAL PUBLIC LICENSE V3.0](https://github.com/RafaelCasamaximo/contExt/blob/main/LICENSE) and is registered with [INPI (National Institute of Industrial Property)](https://www.gov.br/inpi/pt-br).

## Credits

 - [Pedro Zaffalon da Silva](https://github.com/PedroZaffalon)
 - [Rafael Furlanetto Casamaximo](https://github.com/RafaelCasamaximo)
## Acknowledgments
Special thanks to professor Neyva Romeiro and the other professors at [LabSan](http://www.uel.br/laboratorios/labsan/index.html) and [Universidade Estadual de Londrina](https://portal.uel.br/home/).
