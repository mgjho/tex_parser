Python based Tex parser
---
## Installation

Clone the repository and install the package in editable mode:

```bash
cd /path/to/file
pip install -e . --config-settings editable_mode=compat --no-deps
```
___
## Features
1. Get first sentence of tex file and parse them into markdown file. (_first_sentences.md_)
2. If there is _comment.md_ file, it will structure the _first_sentences_ analogous to _comment.md_.
3. If there are changes made in _first_sentences_, it will be reflecte on your tex file.

