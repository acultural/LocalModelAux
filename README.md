# Local Model Aux Projects

Auxillary gadgets for local model interactions

## Venv
`.\localModelAux\Scripts\Activate.ps1`

## Build
`pyinstaller --onedir -w --add-data "assets:assets" --add-data "external:external" --add-data "config.toml:." --icon=assets\icon.ico translator.py`

## Below are some reference materials
### Simple SVG visual editor
    https://www.svgviewer.dev/
### Color picler
    https://htmlcolorcodes.com/color-picker/
### About SVG gradient
    https://developer.mozilla.org/en-US/docs/Web/SVG/Tutorials/SVG_from_scratch/Gradients
### The SVG path guide I always use
    https://www.joshwcomeau.com/svg/interactive-guide-to-paths/