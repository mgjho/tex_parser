Python based Tex parser
---
## Installation

Clone the repository and install the package in editable mode:

```bash
cd /path/to/file
pip install -e . --config-settings editable_mode=compat --no-deps
```
___

## Run

```bash
python -m tex_parser.main
```

## Features

1. Get first sentence of tex file and parse them into markdown file. (_first_sentences.md_)
2. If there is %comment on top of your paragraph, it will also be parsed.
3. If there are changes made in _first_sentences_, it will be reflected on your tex file.
