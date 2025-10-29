# Installation

The project has been initially developed with 3.12 and tested with that version.

If you don't have Poetry installed, you can install it by following the instructions on
https://python-poetry.org/docs/#installation
or by running the following command:

```sh
pipx install poetry
```

Clone the repository and enter the project directory

```sh
git https://github.com/bio-tools/biohackathon2025.git
cd biohackathon2025
```

Create and activate the virtual environment

```sh
poetry install
```
This installs all dependencies in a virtual environment managed by Poetry.




### View docs
```bash
open docs/build/html/index.html  # On macOS
# or:
python -m http.server --directory docs/build/html
```
Then open your browser and go to `http://localhost:8000/`.