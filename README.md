# ImageScan - Automatic Image Tagger

Version: v0.2.0

This script scans images within a specified directory structure, sends them to a running OpenAI-compatible vision model API (like LMStudio), generates descriptive keywords, and renames the image files based on those keywords.

## Features

*   Processes images recursively within a target directory.
*   Supports common image formats (PNG, JPG, JPEG, WEBP, GIF).
*   Communicates with an OpenAI-compatible API endpoint (like LMStudio).
*   Encodes images to base64 for API transmission.
*   Uses a configurable prompt optimized for generating filename keywords.
*   Extracts and sanitizes keywords from the API response.
*   Multiple configurable file naming schemes (e.g., keeping original name, prefixing).
*   Optionally skips files already processed based on naming scheme and prefix.
*   Configurable API endpoint, model name, temperature, and max tokens.
*   Dry-run mode to preview changes without renaming.
*   Progress bar for processing large directories.
*   Verbose mode for detailed logging.
*   Handles potential filename conflicts by adding counters.

## Setup

1.  **Clone the Repository (if applicable):**
    ```bash
    # git clone <repository_url>
    # cd ImageScan
    ```

2.  **Create a Virtual Environment:**
    It is highly recommended to use a virtual environment.
    ```bash
    python -m venv .venv
    ```
    Activate it:
    *   macOS/Linux: `source .venv/bin/activate`
    *   Windows: `.venv\Scripts\activate`

3.  **Install Dependencies:**
    Requires `requests`, `Pillow`, `tqdm`, and `prompt_toolkit`.
    ```bash
    pip install -r requirements.txt
    ```

4.  **Ensure API Server (e.g., LMStudio) is Running:**
    *   Start your API server (e.g., LMStudio).
    *   Load the desired Vision model (e.g., `llama-3.2-11b-vision-instruct`).
    *   Ensure the server is running and accessible at the specified API base URL (default: `http://127.0.0.1:1234/v1`).
    *   Make sure the model identifier used by the server matches the `--model` argument (or its default).

## Usage

Run the script from your terminal. You can optionally provide the target directory using `-d` or `--target-directory`. If omitted, you will be prompted interactively to select the directory with path completion.

```bash
python image_processor.py [OPTIONS] [-d <path_to_your_image_directory>]
```

**Example:**

```bash
# Run interactively (will prompt for directory)
python image_processor.py --naming-scheme original_prefix_desc

# Specify directory via argument
python image_processor.py -d ~/Pictures/Products --dry-run -v

# Run non-interactively, skipping confirmation
python image_processor.py -d ~/Pictures/Products -y 
```

**Options:**

*   `-d`, `--target-directory DIR`: Root directory (prompts interactively if omitted).
*   `--api-base-url URL`: Base URL of the API server (default: `http://127.0.0.1:1234/v1`).
*   `--model MODEL_NAME`: Model identifier to use (default: `llama-3.2-11b-vision-instruct`).
*   `--temperature TEMP`: LLM temperature (0.0-2.0, lower is more focused; default: 0.3).
*   `--max-tokens MAX_T`: Max tokens for LLM response (default: 50).
*   `--prefix PREFIX`: Prefix for processed files (default: `IMGSCAN`). Use `""` for no prefix.
*   `--naming-scheme {original_prefix_desc|prefix_desc|desc_only}`:
    *   `original_prefix_desc`: `{orig}_{prefix}_{desc}.ext` (default)
    *   `prefix_desc`: `{prefix}_{desc}.ext`
    *   `desc_only`: `{desc}.ext` (Note: Skipping processed files is disabled with this scheme).
*   `--skip-processed` / `--no-skip-processed`: Skip already processed files? (default: True).
*   `--dry-run`: Simulate processing without renaming files.
*   `-y`, `--yes`: Skip final confirmation prompt.
*   `-v`, `--verbose`: Enable detailed logging.
*   `-h`, `--help`: Show this help message and exit.

## Important Notes

*   **Backup:** Always back up your images before running this script, especially without `--dry-run`.
*   **API Server:** Ensure your local API server (like LMStudio) is stable and the model is loaded correctly. Check its logs if you encounter API errors (404, 500, timeouts).
*   **Keyword Quality:** The quality and format of the generated keywords depend heavily on the LLM used. Experiment with different models, temperature, and the internal prompt if needed.
*   **Error Handling:** Check the console output and summary for errors during processing.

## Version History

*   v0.2.0: Added interactive directory prompt (using prompt_toolkit), confirmation step.
*   v0.1.0: Major CLI refactor, added naming schemes, dry-run, progress bar, verbose mode, improved skip logic and error handling.
*   v0.0.1: Initial version. 