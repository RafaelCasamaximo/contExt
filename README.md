<p align="center">
  <img src="https://i.ibb.co/4SkhSKG/cont-Ext-Cover.png" alt="ContExt Banner">
</p>

<h1 align="center">ContExt</h1>

<p align="center">
  <strong>Contour extraction and rectangular mesh generation for numerical analysis of medical and scientific images</strong>
</p>

<p align="center">
  <a href="https://doi.org/10.1016/j.compbiomed.2025.110591"><img alt="DOI" src="https://img.shields.io/badge/DOI-10.1016%2Fj.compbiomed.2025.110591-blue"></a>
  <a href="./LICENSE"><img alt="License" src="https://img.shields.io/badge/license-GPL--3.0-green"></a>
  <img alt="Python" src="https://img.shields.io/badge/python-3.x-blue">
  <img alt="Platforms" src="https://img.shields.io/badge/platforms-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey">
</p>

<p align="center">
  <a href="https://github.com/RafaelCasamaximo/contExt/issues/new/choose">Report a Bug</a> •
  <a href="https://github.com/RafaelCasamaximo/contExt/issues/new/choose">Request a Feature</a> •
  <a href="https://github.com/RafaelCasamaximo/contExt/releases">Download</a> •
  <a href="#citing-context">Cite this work</a>
</p>

---

## Table of Contents

- [About the Project](#about-the-project)
- [Scientific Background](#scientific-background)
- [Processing Pipeline](#processing-pipeline)
- [Features](#features)
- [Getting Started](#getting-started)
- [How to Use](#how-to-use)
- [Building the Binaries](#building-the-binaries)
- [Download](#download)
- [Screenshots](#screenshots)
- [Citing ContExt](#citing-context)
- [Publications](#publications)
- [Software Registration](#software-registration)
- [Contributing](#contributing)
- [Code of Conduct](#code-of-conduct)
- [License](#license)
- [Credits](#credits)
- [Acknowledgments](#acknowledgments)

---

## About the Project

**ContExt** is a cross-platform desktop application that turns raster images into geometry ready for
numerical simulation. It takes an image, applies a configurable chain of image-processing filters,
extracts the contours of the regions of interest, optionally interpolates and refines those contours,
and finally generates a **rectangular (structured) mesh** whose boundary approximates the irregular
geometry found in the image.

The output is a finite set of coordinates and mesh nodes that can be fed directly into
**finite difference method (FDM)** solvers and computational fluid dynamics workflows — closing the gap
between *laboratory imaging* and *numerical analysis*.

Although the software is domain-agnostic, its main validated application is **breast cancer imaging**:
mammography and other laboratory images are processed to extract lesion and tissue contours, which are
then meshed for numerical simulation of tumor dynamics
([Silva et al., 2025 — *Computers in Biology and Medicine*](https://doi.org/10.1016/j.compbiomed.2025.110591)).

### Why it exists

Discretizing an irregular physical domain by hand is slow, error-prone, and hard to reproduce.
Classical structured-mesh solvers require the boundary to be described over mesh nodes, which is
straightforward for canonical geometries and painful for anything extracted from a real image.
ContExt automates the full path — **image → contour → interpolation → mesh → exportable node set** —
in a single reproducible tool with a graphical interface.

---

## Scientific Background

ContExt is not a standalone utility: it is the software materialization of a research line developed at
the **Universidade Estadual de Londrina (UEL)**, within the Graduate Program in Applied and Computational
Mathematics (PGMAC) and the Sanitation Laboratory (LabSan). Each major capability of the software maps
to a peer-reviewed contribution:

| Capability | Origin |
|---|---|
| Point extraction from images with irregular contours | Casamaximo et al. (2021) |
| Mesh generation over irregularly contoured regions for PDE simulation by finite differences | da Silva et al. (2020) |
| Contour approximation of the physical domain by mesh segments (rectangular meshes) | da Silva et al. (2022), arXiv:2205.06670 |
| Mesh generation and manipulation for finite difference method usage | da Silva et al. (2022), CILAMCE XLIII |
| Integrated application to breast cancer laboratory imaging | Silva et al. (2025), *Computers in Biology and Medicine* |
| Interpolation methods for resolution reduction and contour enlargement | Tokairin et al. (2025), *Semina: Ciências Exatas e Tecnológicas* |

### Contour approximation algorithm

The boundary of the physical domain is approximated by **mesh segments** using the known coordinates of
the extracted contour. The algorithm iterates over the known irregular-contour coordinates, computes the
slope of the line defined by each contour point and its neighboring vertices, evaluates the points along
that line and their distance to the nearest mesh nodes, and selects the nodes that best approximate the
boundary. The process repeats until the full approximate contour is described over the mesh, producing a
discretization suitable for finite difference calculations.

### Interpolation and computational efficiency

Processing full-resolution medical images is expensive. ContExt implements a **downscale → extract →
interpolate back** strategy: the image resolution is reduced, contours are extracted on the smaller image,
and the resulting contour is enlarged back to the original scale using interpolation.

Available interpolation methods: **bilinear**, **bicubic**, **biquadratic** and **cubic spline**, plus
refinement techniques such as **node removal** and the **Ramer–Douglas–Peucker** algorithm.

Reported results (Tokairin et al., 2025):

- Reducing the image to **1/2** of the original resolution cut processing time by **more than 95%** while
  keeping contour quality satisfactory.
- Reducing to **1/4** compromised the fidelity of the extracted structures.
- **Bilinear** achieved the highest overlap rate; **cubic spline** was the most accurate.

---

## Processing Pipeline

```
┌──────────────┐   ┌────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────┐
│  Image Input │ → │ Processing │ → │ Thresholding │ → │   Contour    │ → │Interpolation │ → │   Mesh   │
│  (raster)    │   │  & Filters │   │              │   │  Extraction  │   │  & Refine    │   │Generation│
└──────────────┘   └────────────┘   └──────────────┘   └──────────────┘   └──────────────┘   └──────────┘
                                                                                                   │
                                                                                                   ▼
                                                                                      Node set for FDM / CFD
```

Each stage corresponds to a tab in the graphical interface, and the intermediate result is previewed
before moving to the next step.

---

## Features

- **Broad image format support** — import a large range of raster image formats.
- **Image processing filters** — apply and chain multiple filters to enhance the regions of interest.
- **Thresholding** — segment regions (e.g. tumor, tissue, background) with adjustable parameters.
- **Contour extraction** — extract contours with configurable approximation options for irregular geometries.
- **Interpolation** — bilinear, bicubic, biquadratic and cubic spline enlargement of contours after
  resolution reduction, with node removal and Ramer–Douglas–Peucker refinement.
- **Mesh generation** — build sparse or adaptive rectangular meshes whose boundary approximates the
  extracted contour over mesh nodes.
- **Export** — obtain the finite set of points/nodes for use in finite difference and CFD solvers.
- **Cross-platform GUI** — Windows, macOS and Linux, with distributable binaries.

---

## Getting Started

This project uses `Python`, a local `.venv` virtual environment, and dependencies defined in `pyproject.toml`.

### Graphical User Interface

The graphical interface is implemented with [DearPyGui](https://github.com/hoffstadt/DearPyGui), which uses
platform graphics APIs (`DirectX 11` on Windows, `Metal` on macOS, `OpenGL 3` on Linux, and `OpenGL ES` on
Raspberry Pi 4). Make sure the required graphics drivers are available on the target machine.

### Create the environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

On Windows:

```powershell
.venv\Scripts\Activate.ps1
```

### Install dependencies

```bash
python3 -m pip install --upgrade pip
python3 -m pip install -e .
```

If you prefer a compatibility file instead of an editable installation:

```bash
python3 -m pip install -r requirements.txt
```

---

## How to Use

Run either command below:

```bash
python3 -m context
```

or

```bash
python3 main.py
```

Then follow the tabs in order: **Processing → Filtering → Thresholding → Contour Extraction → Mesh Generation**.

---

## Building the Binaries

Use the platform-specific build scripts in the project root. Each script creates a distributable artifact in `release/`.

### macOS

```bash
bash ./build-macos.sh
```

Creates `release/ContExt-macos-<arch>.app.zip`.

By default the macOS build uses the current machine architecture (`arm64` or `x64`). Override it with:

```bash
CONTEXT_TARGET_ARCH=arm64 bash ./build-macos.sh
```

or, with a universal2-compatible Python environment and dependencies:

```bash
CONTEXT_TARGET_ARCH=universal2 bash ./build-macos.sh
```

### Windows

```cmd
.\build.cmd
```

Creates `release\ContExt-windows-x64.zip`.

### Linux

```bash
bash ./build.sh
```

Creates `release/ContExt-linux-x64.tar.gz`.

> These first-step builds are unsigned. macOS and Windows may show security warnings when opening the application.

---

## Download

Binaries for each operating system are available on the [Releases tab](https://github.com/RafaelCasamaximo/contExt/releases).
Tagged releases publish the following artifacts:

- `ContExt-macos-<arch>.app.zip`
- `ContExt-windows-x64.zip`
- `ContExt-linux-x64.tar.gz`

---

## Screenshots

| Processing | Filtering | Thresholding |
|---|---|---|
| ![Processing Tab](https://i.ibb.co/YbB9Td1/image.png) | ![Filtering Tab](https://i.ibb.co/Svt0bjb/1.png) | ![Thresholding Tab](https://i.ibb.co/dbPHGX8/2.png) |

| Contour Extraction | Mesh Generation |
|---|---|
| ![Contour Extraction Tab](https://i.ibb.co/WkBhxfB/3.png) | ![Mesh Generation Tab](https://i.ibb.co/fYpFPRM/4.png) |

---

## Citing ContExt

If ContExt is useful in your research, please cite the reference article:

> Silva, P. Z., Casamaximo, R. F., Romeiro, N. M. L., Izidoro, G. P., Tokairin, R. P., & Natti, P. L. (2025).
> Integrating breast cancer laboratory imaging with numerical analysis: ContExt software for contour
> extraction and mesh generation. *Computers in Biology and Medicine*, 196, 110591.
> https://doi.org/10.1016/j.compbiomed.2025.110591

<details>
<summary><strong>BibTeX</strong></summary>

```bibtex
@article{silva2025context,
  title   = {Integrating breast cancer laboratory imaging with numerical analysis:
             ContExt software for contour extraction and mesh generation},
  author  = {Silva, Pedro Zaffalon da and Casamaximo, Rafael Furlanetto and
             Romeiro, Neyva Maria Lopes and Izidoro, Gabriel Pietsiaki and
             Tokairin, Rafael Palheta and Natti, Paulo Laerte},
  journal = {Computers in Biology and Medicine},
  volume  = {196},
  pages   = {110591},
  year    = {2025},
  doi     = {10.1016/j.compbiomed.2025.110591}
}
```
</details>

If you use the **interpolation features**, please also cite:

> Tokairin, R., Casamaximo, R. F., Romeiro, N. M. L., Silva, P. Z. da, & Cirilo, E. R. (2025).
> Interpolation Features in ContExt Software for Mammography Processing.
> *Semina: Ciências Exatas e Tecnológicas*, 46, e53582.
> https://doi.org/10.5433/1679-0375.2025.v46.53582

<details>
<summary><strong>BibTeX</strong></summary>

```bibtex
@article{tokairin2025interpolation,
  title   = {Interpolation Features in ContExt Software for Mammography Processing},
  author  = {Tokairin, Rafael and Casamaximo, Rafael Furlanetto and
             Romeiro, Neyva Maria Lopes and Silva, Pedro Zaffalon da and
             Cirilo, Eliandro Rodrigues},
  journal = {Semina: Ci{\^e}ncias Exatas e Tecnol{\'o}gicas},
  volume  = {46},
  pages   = {e53582},
  year    = {2025},
  doi     = {10.5433/1679-0375.2025.v46.53582}
}
```
</details>

---

## Publications

Works that originated from or make use of the ContExt software and its underlying algorithms:

### Journal articles

1. **Silva, P. Z.**, Casamaximo, R. F., Romeiro, N. M. L., Izidoro, G. P., Tokairin, R. P., & Natti, P. L. (2025).
   *Integrating breast cancer laboratory imaging with numerical analysis: ContExt software for contour extraction and mesh generation.*
   **Computers in Biology and Medicine**, 196, 110591.
   [DOI: 10.1016/j.compbiomed.2025.110591](https://doi.org/10.1016/j.compbiomed.2025.110591)
   *(Preprint: [SSRN 4824613](https://doi.org/10.2139/ssrn.4824613))*

2. **Tokairin, R.**, Casamaximo, R. F., Romeiro, N. M. L., Silva, P. Z. da, & Cirilo, E. R. (2025).
   *Interpolation Features in ContExt Software for Mammography Processing* / *Funcionalidades de Interpolação no Software ContExt para Processamento de Mamografias.*
   **Semina: Ciências Exatas e Tecnológicas**, 46, e53582.
   [DOI: 10.5433/1679-0375.2025.v46.53582](https://doi.org/10.5433/1679-0375.2025.v46.53582)

### Conference papers

3. **da Silva, P. Z.**, Romeiro, N. M. L., Casamaximo, R. F., de Souza, I. P., & Natti, P. L. (2022).
   *Mesh generation and manipulation for finite difference method usage.*
   **XLIII Ibero-Latin American Congress on Computational Methods in Engineering (CILAMCE)**, 4(04).

4. **Casamaximo, R. F.**, Romeiro, N. M. L., da Silva, P. Z., de Souza, I. P., da Silva, J. T. A., Natti, P. L., & Cirilo, E. R. (2021).
   *Algorithm for extracting points from images: irregular contours.*
   **XLII Ibero-Latin American Congress on Computational Methods in Engineering (CILAMCE)**, 3(03).

5. **da Silva, P. Z.**, Romeiro, N. M. L., Casamaximo, R. F., de Souza, I. P., Natti, P. L., & Cirilo, E. R. (2020).
   *Mesh generation algorithm involving irregularly contoured regions for numerical simulations of partial differential equations by finite differences.*
   **XLI Ibero-Latin American Congress on Computational Methods in Engineering (CILAMCE)**, 2(02).

### Preprints and book chapters

6. **da Silva, P. Z.**, Romeiro, N. M. L., de Souza, I. P., Natti, P. L., & Cirilo, E. R. (2022).
   *Rectangular mesh contour generation algorithm for finite differences calculus.*
   **arXiv preprint** [arXiv:2205.06670](https://arxiv.org/abs/2205.06670).

7. **da Silva, P. Z.**, Romeiro, N. M. L., Casamaximo, R. F., de Souza, I. P., Natti, P. L., & Cirilo, E. R.
   *Algoritmo para geração de contorno de malhas retangulares para cálculo de diferenças finitas.*
   In: **Coleção Desafios das Engenharias: Engenharia de Computação** (Atena Editora).

---

## Software Registration

Beyond the publications above, ContExt is registered as a computer program with the Brazilian
**INPI — Instituto Nacional da Propriedade Industrial**
([National Institute of Industrial Property](https://www.gov.br/inpi/pt-br)).

> ℹ️ *Registration number: `<add the INPI process/registration number here>`.*

---

## Contributing

You can [open a new issue or request a feature here](https://github.com/RafaelCasamaximo/contExt/issues/new/choose).
If you want to contribute to the project, see our [contribution guideline](./CONTRIBUTING.md).

## Code of Conduct

Read our [Code of Conduct](./CODE_OF_CONDUCT.md).

## License

This project is distributed under the [GNU General Public License v3.0](./LICENSE) and is registered with
[INPI (National Institute of Industrial Property)](https://www.gov.br/inpi/pt-br).

## Credits

**Development**

- [Pedro Zaffalon da Silva](https://github.com/PedroZaffalon) — [ORCID 0009-0004-8160-8882](https://orcid.org/0009-0004-8160-8882)
- [Rafael Furlanetto Casamaximo](https://github.com/RafaelCasamaximo) — [ORCID 0009-0009-6404-206X](https://orcid.org/0009-0009-6404-206X)
- Rafael Palheta Tokairin — [ORCID 0009-0004-8369-2192](https://orcid.org/0009-0004-8369-2192)
- Gabriel Pietsiaki Izidoro
- Iury Pereira de Souza

**Scientific supervision**

- Prof. Dra. Neyva Maria Lopes Romeiro — [ORCID 0000-0002-3249-3490](https://orcid.org/0000-0002-3249-3490)
- Prof. Dr. Paulo Laerte Natti — [ORCID 0000-0002-5988-2621](https://orcid.org/0000-0002-5988-2621)
- Prof. Dr. Eliandro Rodrigues Cirilo — [ORCID 0000-0001-7530-1770](https://orcid.org/0000-0001-7530-1770)

## Acknowledgments

Special thanks to Professor Neyva Romeiro and the other professors and researchers at
[LabSan](http://www.uel.br/laboratorios/labsan/index.html), the Graduate Program in Applied and
Computational Mathematics (PGMAC), and the Department of Mathematics of the
[Universidade Estadual de Londrina](https://portal.uel.br/home/).
