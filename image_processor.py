import os
import base64
import requests
import re
from PIL import Image
import io
import argparse
import sys
from tqdm import tqdm # Import tqdm
from pathlib import Path # Import Path
from prompt_toolkit import prompt # Import prompt
from prompt_toolkit.completion import PathCompleter # Import PathCompleter

# --- Constants ---
DEFAULT_API_BASE_URL = "http://127.0.0.1:1234/v1"
DEFAULT_MODEL = "llama3.1-11b-vision-instruct"
DEFAULT_PREFIX = "IMGSCAN"
SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}

# --- Helper Functions ---

def encode_image_to_base64(image_path):
    """Encodes an image file to base64."""
    try:
        with Image.open(image_path) as img:
            if img.mode != 'RGB':
                img = img.convert('RGB')
            buffered = io.BytesIO()
            img.save(buffered, format="JPEG")
            img_byte = buffered.getvalue()
            return base64.b64encode(img_byte).decode('utf-8')
    except Exception as e:
        tqdm.write(f"Error encoding image {image_path}: {e}", file=sys.stderr) # Use tqdm.write for progress bar compatibility
        return None

def sanitize_filename(text):
    """Removes or replaces characters that are invalid in filenames, keeping underscores."""
    # Replace common problematic separators potentially returned by LLM with underscores
    text = re.sub(r'[\s,;:-]+', '_', text)
    # Remove characters invalid in most filesystems
    text = re.sub(r'[<>:"/\\|?*]', '', text)
    # Consolidate multiple underscores
    text = re.sub(r'_+', '_', text)
    # Remove leading/trailing underscores
    text = text.strip('_')
    # Limit length
    return text[:100]

# --- API Interaction ---

def call_vision_api(image_path, api_base_url, model, temperature, max_tokens, verbose=False):
    """Calls the LMStudio Vision API to get keyword descriptions."""
    base64_image = encode_image_to_base64(image_path)
    if not base64_image:
        return None

    chat_completions_endpoint = f"{api_base_url}/chat/completions"
    headers = {"Content-Type": "application/json"}

    # Role-play prompt for concise, underscored keywords
    user_message_text = (
        "You are a filename generator. Describe the image using only 6 keywords maximum, "
        "separated by underscores. Focus on the main subject. Ignore background and surface. "
        "Example: red_mug_steam_handle_ceramic"
    )

    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}},
                    {"type": "text", "text": user_message_text}
                ]
            }
        ],
        "max_tokens": max_tokens,
        "temperature": temperature
    }

    if verbose:
         tqdm.write(f"  Calling API for {os.path.basename(image_path)} with temp={temperature}, max_tokens={max_tokens}")

    try:
        response = requests.post(chat_completions_endpoint, headers=headers, json=payload, timeout=60) # Added timeout
        response.raise_for_status()
        response_json = response.json()

        if 'choices' in response_json and len(response_json['choices']) > 0:
            message = response_json['choices'][0].get('message', {})
            content = message.get('content')
            if content:
                if verbose:
                    tqdm.write(f"  LLM Raw Response: {content.strip()[:100]}...")
                return content.strip()
            else:
                tqdm.write(f"  Warning: 'content' not found in response message for {image_path}", file=sys.stderr)
                if verbose: tqdm.write(f"  Full Response: {response_json}", file=sys.stderr)
                return None
        else:
            tqdm.write(f"  Warning: 'choices' not found or empty in response for {image_path}", file=sys.stderr)
            if verbose: tqdm.write(f"  Full Response: {response_json}", file=sys.stderr)
            return None

    except requests.exceptions.Timeout:
        tqdm.write(f"API Error: Request timed out for {image_path} to {chat_completions_endpoint}", file=sys.stderr)
        return None
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            tqdm.write(f"API Error: Endpoint {chat_completions_endpoint} not found (404). Check LM Studio server setup.", file=sys.stderr)
        else:
            tqdm.write(f"API HTTP Error for {image_path}: {e}", file=sys.stderr)
        return None
    except requests.exceptions.RequestException as e:
        tqdm.write(f"API Request Failed for {image_path}: {e}", file=sys.stderr)
        return None
    except Exception as e:
        tqdm.write(f"Error processing API response for {image_path}: {e}", file=sys.stderr)
        return None


# --- File Processing ---

def process_and_rename_file(filepath, target_dir, api_base_url, model, temperature, max_tokens, prefix, naming_scheme, dry_run, verbose):
    """Gets description from API and renames the file based on the chosen scheme."""
    if verbose:
        tqdm.write(f"Processing file: {filepath}")

    description = call_vision_api(filepath, api_base_url, model, temperature, max_tokens, verbose)
    if not description:
        tqdm.write(f"  Skipping rename for {os.path.basename(filepath)} due to missing description.", file=sys.stderr)
        return False # Indicate failure

    sanitized_desc = sanitize_filename(description)
    if not sanitized_desc:
        tqdm.write(f"  Warning: Could not generate valid filename part from description for {filepath}. Desc: '{description}'", file=sys.stderr)
        return False # Indicate failure

    original_filename = os.path.basename(filepath)
    original_name , ext = os.path.splitext(original_filename)

    # Construct new filename based on scheme
    if naming_scheme == 'original_prefix_desc':
        base_new_filename = f"{original_name}_{prefix}_{sanitized_desc}"
    elif naming_scheme == 'prefix_desc':
        base_new_filename = f"{prefix}_{sanitized_desc}"
    elif naming_scheme == 'desc_only':
         base_new_filename = sanitized_desc
    else: # Should not happen with argparse choices
        tqdm.write(f"  Internal Error: Invalid naming scheme '{naming_scheme}'", file=sys.stderr)
        return False

    new_filename = f"{base_new_filename}{ext}"
    new_filepath = os.path.join(target_dir, new_filename)

    # Avoid overwriting files
    counter = 1
    while os.path.exists(new_filepath):
        new_filename = f"{base_new_filename}_{counter}{ext}"
        new_filepath = os.path.join(target_dir, new_filename)
        counter += 1
        if counter > 100:
             tqdm.write(f"  Error: Could not find unique filename for {original_filename} starting with '{base_new_filename}' after 100 attempts.", file=sys.stderr)
             return False # Indicate failure

    # Perform rename or dry run
    if dry_run:
        tqdm.write(f"[DRY RUN] Would rename '{original_filename}' to '{new_filename}'")
        return True # Indicate success (dry run)
    else:
        try:
            os.rename(filepath, new_filepath)
            if verbose:
                tqdm.write(f"  Renamed '{original_filename}' to '{new_filename}'")
            return True # Indicate success
        except OSError as e:
            tqdm.write(f"  Error renaming file {original_filename} to {new_filename}: {e}", file=sys.stderr)
            return False # Indicate failure

def has_processed_marker(filename, prefix, naming_scheme):
    """Checks if a filename indicates it has already been processed based on the scheme."""
    if not prefix: # If no prefix is used, skipping isn't really possible based on prefix
        return False
        
    name, _ = os.path.splitext(filename)
    marker = f"_{prefix}_" # Used in original_prefix_desc

    if naming_scheme == 'original_prefix_desc':
        # Check if _{prefix}_ exists somewhere in the name part
        return marker in name
    elif naming_scheme == 'prefix_desc':
        # Check if the filename starts with the prefix and an underscore
        return name.startswith(f"{prefix}_")
    elif naming_scheme == 'desc_only':
        # Cannot reliably determine if 'desc_only' has been processed
        return False
    return False


def process_directory(directory_path, api_base_url, model, temperature, max_tokens, prefix, naming_scheme, skip_processed, dry_run, verbose):
    """Walks through a directory and processes all supported image files."""
    
    # --- Collect files first ---
    files_to_process = []
    files_skipped_type = 0
    files_skipped_hidden = 0
    files_skipped_processed = 0

    if verbose: print("Scanning directories to collect image files...")
    for root, dirs, files in os.walk(directory_path):
         # Skip hidden directories (like .venv, .git)
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        
        for filename in files:
            if filename.startswith('.'):
                files_skipped_hidden += 1
                continue

            _, ext = os.path.splitext(filename)
            if ext.lower() not in SUPPORTED_EXTENSIONS:
                files_skipped_type += 1
                continue

            if skip_processed and has_processed_marker(filename, prefix, naming_scheme):
                 if verbose: tqdm.write(f"  Skipping already processed file: {os.path.join(root, filename)}")
                 files_skipped_processed += 1
                 continue

            files_to_process.append((os.path.join(root, filename), root))

    total_files = len(files_to_process)
    if total_files == 0:
        print("No processable image files found.")
        print(f"Skipped {files_skipped_processed} processed, {files_skipped_type} non-image, {files_skipped_hidden} hidden files.")
        return

    print(f"Found {total_files} image files to process.")
    if files_skipped_processed > 0: print(f"(Skipped {files_skipped_processed} previously processed files)")
    if files_skipped_type > 0: print(f"(Skipped {files_skipped_type} non-image files)")
    if files_skipped_hidden > 0: print(f"(Skipped {files_skipped_hidden} hidden files)")

    # --- Process files with progress bar ---
    processed_success_count = 0
    processed_fail_count = 0

    print(f"Starting processing... (Dry Run: {dry_run})")
    with tqdm(total=total_files, unit="file", desc="Processing Images") as pbar:
        for filepath, root_dir in files_to_process:
            try:
                success = process_and_rename_file(
                    filepath, root_dir, api_base_url, model, temperature, max_tokens,
                    prefix, naming_scheme, dry_run, verbose
                )
                if success:
                    processed_success_count += 1
                else:
                    processed_fail_count += 1
            except Exception as e:
                 # Catch unexpected errors during the processing of a single file
                 tqdm.write(f"!! Unhandled error processing file {filepath}: {e}", file=sys.stderr)
                 processed_fail_count += 1
            finally:
                 pbar.update(1) # Update progress bar regardless of success/failure

    # --- Final Summary ---
    print() # Print newline separately
    print("--- Processing Summary ---")
    if dry_run:
         print(f"Dry run complete. Would have attempted to process {total_files} files.")
         print(f"  Simulated Successes: {processed_success_count}")
         print(f"  Simulated Failures (API errors, bad descriptions, etc.): {processed_fail_count}")
    else:
        print(f"Processed {processed_success_count} files successfully.")
        print(f"Failed to process {processed_fail_count} files (API errors, bad descriptions, rename errors, etc.).")
    print("--------------------------")


# --- Main Execution ---

if __name__ == "__main__":
    parser_description = "Scan images, get keyword descriptions via API, and rename files."
    parser = argparse.ArgumentParser(
        description=parser_description,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    # Directory Argument (Now Optional)
    parser.add_argument("-d", "--target-directory",
                        help="(Optional) Root directory to process. If omitted, you will be prompted interactively.")

    # API Configuration
    parser.add_argument("--api-base-url", default=DEFAULT_API_BASE_URL,
                        help="Base URL of the OpenAI-compatible API (e.g., LM Studio).")
    parser.add_argument("--model", default=DEFAULT_MODEL,
                        help="Model name to use for API calls.")
    parser.add_argument("--temperature", type=float, default=0.3,
                        help="LLM temperature (creativity). Lower is more focused.")
    parser.add_argument("--max-tokens", type=int, default=50,
                        help="Max tokens for LLM response. Keep low for keywords.")

    # Renaming Configuration
    parser.add_argument("--prefix", default=DEFAULT_PREFIX,
                        help="Prefix to use for marking processed files (e.g., 'IMGSCAN'). Set to empty string '' to disable prefix in relevant schemes.")
    parser.add_argument("--naming-scheme", choices=['original_prefix_desc', 'prefix_desc', 'desc_only'],
                        default='original_prefix_desc',
                        help=("How to name renamed files: "
                              "'original_prefix_desc' ({orig}_{prefix}_{desc}.ext), "
                              "'prefix_desc' ({prefix}_{desc}.ext), "
                              "'desc_only' ({desc}.ext)"))

    # Behavior Configuration
    parser.add_argument("--skip-processed", action=argparse.BooleanOptionalAction, default=True,
                        help="Skip files that appear already processed based on prefix and naming scheme.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be renamed without actually changing files.")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Enable verbose output (show API calls, skipped files, etc.).")
    parser.add_argument("-y", "--yes", action="store_true",
                        help="Skip the final confirmation prompt before processing.") # Added -y flag

    args = parser.parse_args()

    # --- Get Target Directory --- 
    if args.target_directory:
        target_directory_path = Path(args.target_directory).expanduser()
    else:
        print("Target directory not specified. Please select interactively.")
        print("(Press Tab for path completion)")
        path_completer = PathCompleter(only_directories=True, expanduser=True)
        try:
            selected_path_str = prompt(
                "Enter target directory path: ", 
                completer=path_completer, 
                default=str(Path.home()) + '/',
                complete_while_typing=True,
                # Restoring bottom_toolbar temporarily removed before
                bottom_toolbar="Tab: Complete | Enter: Select"
            )
            target_directory_path = Path(selected_path_str).expanduser()
        except EOFError: # Handle Ctrl+D or similar
            print("\nOperation cancelled by user.", file=sys.stderr)
            sys.exit(1)
        except KeyboardInterrupt: # Handle Ctrl+C
            print("\nOperation cancelled by user.", file=sys.stderr)
            sys.exit(1)
    # else: # Require target_directory if interactive part is commented out
    #     print("Error: Target directory must be specified with -d or --target-directory when interactive prompt is disabled.", file=sys.stderr)
    #     sys.exit(1)

    # --- Validate Target Directory --- 
    if not target_directory_path or not target_directory_path.is_dir():
         print(f"Error: Target directory not found or invalid: {target_directory_path}", file=sys.stderr)
         sys.exit(1)
    else:
        # Use the validated absolute path string
        args.target_directory = str(target_directory_path.resolve())
        print(f"Using target directory: {args.target_directory}")

    # --- Validate other args --- 
    if args.naming_scheme in ['original_prefix_desc', 'prefix_desc'] and not args.prefix:
         print("Warning: Naming scheme uses a prefix, but --prefix is empty. Files might not be skippable if re-run.", file=sys.stderr)

    if args.naming_scheme == 'desc_only' and args.skip_processed:
         print("Warning: Cannot reliably skip processed files with 'desc_only' naming scheme. Disabling skip.", file=sys.stderr)
         args.skip_processed = False

    if not args.skip_processed:
        print("Warning: Running without skipping processed files (`--no-skip-processed`). Files may be processed multiple times.", file=sys.stderr)

    # --- Confirmation Prompt --- 
    if not args.yes:
        print("\n--- Review Settings ---")
        print(f"  Target Directory: {args.target_directory}")
        print(f"  API URL:          {args.api_base_url}")
        print(f"  Model:            {args.model}")
        print(f"  Naming Scheme:    {args.naming_scheme} (Prefix: '{args.prefix}')")
        print(f"  Skip Processed:   {args.skip_processed}")
        print(f"  Dry Run:          {args.dry_run}")
        print("----------------------")
        try:
            confirm = prompt("Proceed with processing? (y/N): ").lower()
            if confirm != 'y':
                print("Operation cancelled by user.")
                sys.exit(0)
        except EOFError:
            print("\nOperation cancelled by user.", file=sys.stderr)
            sys.exit(1)
        except KeyboardInterrupt:
             print("\nOperation cancelled by user.", file=sys.stderr)
             sys.exit(1)

    # --- Call the main processing function --- 
    process_directory(
        directory_path=args.target_directory,
        api_base_url=args.api_base_url,
        model=args.model,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
        prefix=args.prefix,
        naming_scheme=args.naming_scheme,
        skip_processed=args.skip_processed,
        dry_run=args.dry_run,
        verbose=args.verbose
    )

    print("Image processing complete.") 