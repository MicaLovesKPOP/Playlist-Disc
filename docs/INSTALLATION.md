# Installation and packaging

Playlist Disc is still a pre-alpha Draft 0.2 project. It is not published to PyPI yet, and permanent public disc IDs are not open.

## Requirements

- Python 3.11–3.13;
- Git only when installing directly from the repository;
- `cdrdao` only if/when you actually want to write a physical CD.

All encoding, catalog, library, bridge, compatibility, resolution, virtual-build, and static-site tooling works without `cdrdao`.

## Install from a checkout

```bash
git clone https://github.com/MicaLovesKPOP/Playlist-Disc.git
cd Playlist-Disc
python -m pip install .
pdv1 --help
```

For development:

```bash
python -m pip install -e '.[dev]'
pytest
```

## Install as a CLI with pipx

Until a packaged release channel exists, pipx can install directly from GitHub:

```bash
pipx install "git+https://github.com/MicaLovesKPOP/Playlist-Disc.git"
pdv1 --help
```

An editable/source checkout is still recommended for contributors because the public/test catalog and compatibility source data live in the repository rather than inside the Python wheel.

## Build distributable Python artifacts

```bash
python -m pip install '.[release]'
python -m build
python -m twine check dist/*
```

This creates a source distribution and wheel. The package includes the machine-readable bridge and provider-index schemas required by the installed library/CLI.

## Cross-platform package smoke tests

CI builds and installs the wheel on current Ubuntu, Windows, and macOS runners with Python 3.13. It verifies:

- the wheel can be installed into the runner Python environment;
- `pdv1 inspect 999901` starts successfully;
- packaged bridge and provider-index schemas can be loaded.

This is installability evidence only. It says nothing about optical drives, `cdrdao` device support, vehicle behavior, or physical media compatibility.

## Burning backend

Physical writing is intentionally separated from the Python package. `pdv1 build` creates a tiny mastering bundle; `pdv1 burn` invokes an external `cdrdao` executable when one is available on PATH.

Do not interpret package installation success as permission to burn permanent IDs during the Draft 0.2 phase.
