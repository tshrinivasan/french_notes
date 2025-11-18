import os
import re
from gtts import gTTS
import logging
import shutil # For copying files

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def simple_slugify(text):
    """
    Converts a string into a URL-friendly slug.
    This is a simplified version, suitable for basic word slugging.
    """
    text = text.lower()
    # Replace non-alphanumeric characters (except spaces and hyphens) with nothing
    text = re.sub(r'[^\w\s-]', '', text)
    # Replace one or more spaces/underscores/hyphens with a single hyphen
    text = re.sub(r'[\s_-]+', '-', text)
    # Remove leading/trailing hyphens
    text = text.strip('-')
    return text

def generate_audio_and_process_markdown(input_md_dir, output_md_dir, audio_output_dir):
    """
    Scans Markdown files from input_md_dir for French words marked with
    [[word]] syntax, generates audio for each unique word, saves audio
    to audio_output_dir, and then writes processed Markdown (with HTML for audio)
    to output_md_dir.
    """
    if not os.path.exists(input_md_dir):
        logging.error(f"Input Markdown directory not found: {input_md_dir}")
        return

    os.makedirs(output_md_dir, exist_ok=True)
    os.makedirs(audio_output_dir, exist_ok=True)
    logging.info(f"Audio files will be saved to: {os.path.abspath(audio_output_dir)}")
    logging.info(f"Processed Markdown files will be written to: {os.path.abspath(output_md_dir)}")

    # Regex to find [[word]] or [[phrase with spaces]]
    # This pattern now specifically looks for [[...]] NOT preceded by a backslash.
    custom_syntax_pattern = re.compile(r'(?<!\\)\[\[([^\]]+)\]\]')

    # Regex to find escaped [[word]] patterns for later unescaping
    escaped_syntax_pattern = re.compile(r'\\\[\[([^\]]+)\]\]')

    unique_french_words = set()
    input_markdown_files = []

    logging.info(f"Scanning Markdown files in: {os.path.abspath(input_md_dir)}")
    for root, _, files in os.walk(input_md_dir):
        for file_name in files:
            if file_name.endswith(('.md', '.markdown')):
                file_path = os.path.join(root, file_name)
                input_markdown_files.append(file_path)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # Find words from custom [[ syntax (non-escaped)
                        found_custom_words = custom_syntax_pattern.findall(content)
                        for word in found_custom_words:
                            unique_french_words.add(word.strip())

                except Exception as e:
                    logging.error(f"Error reading file {file_path}: {e}")

    if not unique_french_words:
        logging.info("No French words marked with [[word]] found in input Markdown files.")
        # Still copy files even if no words found, to keep content in sync
        logging.info("Copying Markdown files without audio conversion...")
        for input_file_path in input_markdown_files:
            relative_path = os.path.relpath(input_file_path, input_md_dir)
            output_file_name = os.path.basename(input_file_path)

            if relative_path == "_index.md":
                output_full_path = os.path.join(output_md_dir, output_file_name)
            else:
                output_posts_dir = os.path.join(output_md_dir, 'posts')
                os.makedirs(output_posts_dir, exist_ok=True)
                output_full_path = os.path.join(output_posts_dir, output_file_name)

            os.makedirs(os.path.dirname(output_full_path), exist_ok=True)
            shutil.copy2(input_file_path, output_full_path)
            logging.info(f"Copied: {input_file_path} to {output_full_path}")
        return


    logging.info(f"Found {len(unique_french_words)} unique French words to convert to audio.")

    generated_count = 0
    for word in sorted(list(unique_french_words)):
        slug = simple_slugify(word)
        audio_file_name = f"{slug}.mp3"
        audio_file_path = os.path.join(audio_output_dir, audio_file_name)

        if os.path.exists(audio_file_path):
            logging.info(f"Skipping '{word}' (audio already exists): {audio_file_name}")
            continue

        try:
            logging.info(f"Generating audio for: '{word}' -> {audio_file_name}")
            tts = gTTS(text=word, lang='fr')
            tts.save(audio_file_path)
            generated_count += 1
        except Exception as e:
            logging.error(f"Failed to generate audio for '{word}': {e}")

    logging.info(f"Finished audio generation. Successfully generated {generated_count} new audio files.")
    logging.info(f"Total unique French words processed: {len(unique_french_words)}")

    # --- Now, process and write Markdown files with HTML ---
    logging.info("Processing and writing Markdown files with HTML for audio...")
    for input_file_path in input_markdown_files:
        relative_path = os.path.relpath(input_file_path, input_md_dir)
        output_file_name = os.path.basename(input_file_path) # Just the filename

        if relative_path == "_index.md":
            # If it's the root _index.md, place it directly in the output_md_dir
            output_full_path = os.path.join(output_md_dir, output_file_name)
        else:
            # For all other Markdown files, place them in the 'posts' subdirectory
            # This assumes all other content should go into the 'posts' section.
            output_posts_dir = os.path.join(output_md_dir, 'posts')
            os.makedirs(output_posts_dir, exist_ok=True) # Ensure 'posts' directory exists
            output_full_path = os.path.join(output_posts_dir, output_file_name)

        # Ensure the full path to the output file's directory exists
        os.makedirs(os.path.dirname(output_full_path), exist_ok=True)


        try:
            with open(input_file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Function to replace custom syntax with HTML
            def replace_custom_syntax(match):
                word = match.group(1).strip()
                slug = simple_slugify(word)
                html_snippet = (
                    f'<span class="french-word-container">'
                    f'<span class="french-word">{word}</span>'
                    f'<i class="fas fa-volume-up audio-icon" onclick="playFrenchAudio(\'{slug}\')"></i>'
                    f'<audio id="audio-{slug}" src="/audio/{slug}.mp3" preload="auto"></audio>'
                    f'</span>'
                )
                return html_snippet

            # Perform replacement only on the non-escaped custom syntax.
            new_content = custom_syntax_pattern.sub(replace_custom_syntax, content)

            # Unescape any literally intended [[word]] patterns
            def unescape_syntax(match):
                return f'[[{match.group(1)}]]' # Remove the backslash

            new_content = escaped_syntax_pattern.sub(unescape_syntax, new_content)

            with open(output_full_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            logging.info(f"Processed: {input_file_path} to {output_full_path}")

        except Exception as e:
            logging.error(f"Error processing and writing file {input_file_path}: {e}")

    logging.info("Finished processing Markdown files.")


if __name__ == "__main__":
    # Define your Hugo content directory and the desired audio output directory
    # Assuming this script is run from the root of your Hugo project.
    INPUT_MD_DIR = 'french_notes_src' # New input directory for your raw Markdown files
    OUTPUT_MD_DIR = 'content'        # Your Hugo content directory
    HUGO_STATIC_AUDIO_DIR = 'static/audio' # This path is relative to your Hugo root

    print("\n--- Starting French Audio Generator and Markdown Processor ---")
    print("This script will read Markdown files from '{INPUT_MD_DIR}'.")
    print("It will generate audio files for words marked with [[word]] syntax in '{HUGO_STATIC_AUDIO_DIR}'.")
    print("It will then write processed Markdown files (with HTML for audio) to '{OUTPUT_MD_DIR}'.")
    print("Specifically, '_index.md' will go to '{OUTPUT_MD_DIR}/_index.md', and all other Markdown files will go to '{OUTPUT_MD_DIR}/posts/'.")
    print("To display [[word]] literally without conversion, use \\[[word]].")
    print("Make sure you have 'gtts' installed: pip install gtts")
    print("-----------------------------------------------------------\n")

    generate_audio_and_process_markdown(INPUT_MD_DIR, OUTPUT_MD_DIR, HUGO_STATIC_AUDIO_DIR)

    print("\n--- Processing Complete ---")
    print("Remember to run 'hugo server' or 'hugo' to build your site from the 'content' directory.")
    print("---------------------------\n")

