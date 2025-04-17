# ImageScan: Automatic Image Tagger & Renamer

[![GitHub Repo](https://img.shields.io/badge/GitHub-ImageScan-blue?logo=github)](https://github.com/rogu3bear/ImageScan)

**Version:** v0.2.0

---

## Overview

**ImageScan** is a command-line tool that scans directories for images, sends them to an OpenAI-compatible vision model API (e.g., LMStudio), generates concise descriptive keywords, and renames the image files accordingly. This streamlines image organization, searchability, and dataset preparation.

---

## Features

- **Recursive Directory Scanning:** Processes all images in a target directory and its subdirectories.
- **Flexible Image Format Support:** Handles PNG, JPG, JPEG, WEBP, and GIF files.
- **OpenAI-Compatible API Integration:** Works with local or remote vision models (e.g., LMStudio, OpenAI API).
- **Configurable Prompts & Naming Schemes:** Choose how files are renamed and how keywords are generated.
- **Dry-Run & Verbose Modes:** Preview changes and get detailed logs before making modifications.
- **Progress Bar:** Visual feedback for large batches.
- **Robust Error Handling:** Skips problematic files, avoids overwrites, and provides clear error messages.
- **Interactive or Scriptable:** Use interactively (with path completion) or fully via CLI arguments.

---

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/rogu3bear/ImageScan.git
cd ImageScan
```

### 2. Create & Activate a Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate  # Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Start Your API Server
- Launch your OpenAI-compatible vision model server (e.g., LMStudio).
- Ensure the model is loaded and the API is accessible (default: `http://127.0.0.1:1234/v1`).

---

## Usage

Run the script from your terminal:

```bash
python image_processor.py [OPTIONS] [-d <path_to_image_directory>]
```

### Common Examples

- **Interactive directory selection:**
  ```bash
  python image_processor.py
  ```
- **Specify directory, dry run, verbose:**
  ```bash
  python image_processor.py -d ~/Pictures/Products --dry-run -v
  ```
- **Skip confirmation prompt:**
  ```bash
  python image_processor.py -d ./images -y
  ```

### Key Options

- `-d`, `--target-directory DIR`  
  Directory to scan (prompts interactively if omitted).
- `--api-base-url URL`  
  API server base URL (default: `http://127.0.0.1:1234/v1`).
- `--model MODEL_NAME`  
  Model identifier (default: `llama-3.2-11b-vision-instruct`).
- `--temperature FLOAT`  
  LLM temperature (default: 0.3).
- `--max-tokens INT`  
  Max tokens for LLM response (default: 50).
- `--prefix PREFIX`  
  Prefix for renamed files (default: `IMGSCAN`).
- `--naming-scheme {original_prefix_desc|prefix_desc|desc_only}`  
  File naming style.
- `--skip-processed/--no-skip-processed`  
  Skip files already processed (default: True).
- `--dry-run`  
  Preview changes without renaming files.
- `-y`, `--yes`  
  Skip confirmation prompt.
- `-v`, `--verbose`  
  Enable detailed logging.
- `-h`, `--help`  
  Show help and exit.

---

## Configuration & Customization

- **API Server:**
  - Must be OpenAI-compatible (e.g., LMStudio, OpenAI API).
  - Ensure the model supports vision/image input.
- **Prompt Customization:**
  - The internal prompt is optimized for concise, underscored keywords.
  - For advanced use, modify the prompt in `image_processor.py`.
- **Naming Schemes:**
  - `original_prefix_desc`: `{orig}_{prefix}_{desc}.ext` (default)
  - `prefix_desc`: `{prefix}_{desc}.ext`
  - `desc_only`: `{desc}.ext` (cannot skip processed files reliably)

---

## Troubleshooting

- **API Errors:**
  - Ensure your API server is running and accessible.
  - Check model compatibility and logs for errors (404, 500, timeouts).
- **File Not Renamed:**
  - Check for invalid characters in generated keywords.
  - Use `--dry-run` and `-v` to debug.
- **Processed Files Repeated:**
  - Ensure prefix and naming scheme are set correctly.

---

## Contributing

Contributions are welcome! Please open issues or pull requests on [GitHub](https://github.com/rogu3bear/ImageScan).

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

## Links

- **GitHub Repository:** [https://github.com/rogu3bear/ImageScan](https://github.com/rogu3bear/ImageScan)
- **LMStudio:** [https://lmstudio.ai/](https://lmstudio.ai/)
- **OpenAI API Docs:** [https://platform.openai.com/docs/api-reference](https://platform.openai.com/docs/api-reference)

---

## Acknowledgements

- Built with [requests](https://docs.python-requests.org/), [Pillow](https://python-pillow.org/), [tqdm](https://tqdm.github.io/), and [prompt_toolkit](https://python-prompt-toolkit.readthedocs.io/). 