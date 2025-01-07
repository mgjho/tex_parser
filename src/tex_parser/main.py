import os
import re
import threading
import time

# Flags to prevent callback loops
tex_file_modified_by_script = False
md_file_modified_by_script = False
out_file_modified_by_script = False


def extract_first_sentence_from_paragraphs(tex_file):
    with open(tex_file) as file:
        content = file.read()

    # Find the position of \maketitle and process content from there
    maketitle_pos = content.find(r"\maketitle")
    if maketitle_pos != -1:
        content = content[maketitle_pos + len(r"\maketitle") :]

    # Split the content into paragraphs by identifying empty lines between them
    paragraphs = re.split(r"\\par\n", content.strip())
    paragraphs = paragraphs[:-1]  # Skip the last paragraph
    first_sentences = []
    for paragraph in paragraphs:
        # Split the paragraph into sentences (using common punctuation marks)
        sentences = re.split(r"(?<=[.!?]) +", paragraph)
        if sentences:
            first_sentence = sentences[0]
            last_newline_pos = first_sentence.rfind("\n")
            # If the first sentence contains a newline character, consider the text after the last newline
            if last_newline_pos != -1:
                first_sentence = first_sentence[last_newline_pos + 1 :]
            first_sentences.append(first_sentence)
    return first_sentences, paragraphs


def monitor_file(file_path, callback, interval=1):
    last_modified = os.path.getmtime(file_path)

    while True:
        new_last_modified = os.path.getmtime(file_path)

        if new_last_modified != last_modified:
            last_modified = new_last_modified
            callback(file_path)
        time.sleep(interval)


def process_out_file(tex_file, md_file, out_file):
    global out_file_modified_by_script
    first_sentences, _ = extract_first_sentence_from_paragraphs(tex_file)
    with open(md_file) as file:
        summaries = file.readlines()
    with open(out_file, "w") as out_file_obj:
        out_file_obj.write(f"Summary of {tex_file}\n ---")
        for idx, sentence in enumerate(first_sentences):
            summary = summaries[idx] if idx < len(summaries) else ""
            summary = summary.strip()
            # Not having a \n after summary is intentional
            out_file_obj.write(f"\n{summary}: _{sentence}_\n")
    print("Changes detected, processing out file.")
    out_file_modified_by_script = True


def update_md_file_from_out(md_file, out_file):
    global md_file_modified_by_script
    with open(out_file) as file:
        lines = file.readlines()

    updated_summaries = []
    for line in lines:
        if ": _" in line:
            summary = line.split(": _")[0].strip()
            updated_summaries.append(summary)
    with open(md_file, "w") as file:
        for summary in updated_summaries:
            file.write(f"{summary}\n")
    print("Changes detected, processing md file.")
    md_file_modified_by_script = True


def update_tex_file_from_out(tex_file, out_file):
    global tex_file_modified_by_script
    with open(out_file) as file:
        lines = file.readlines()

    updated_sentences = []
    for line in lines:
        if ": _" in line:
            updated_sentence = line.split(": _")[1].strip().rstrip("_")
            updated_sentences.append(updated_sentence)

    first_sentences, paragraphs = extract_first_sentence_from_paragraphs(tex_file)

    with open(tex_file) as file:
        content = file.read()

    # Search for the original sentences and replace them with the updated sentences
    for idx, original_sentence in enumerate(first_sentences):
        if idx < len(updated_sentences):
            updated_sentence = updated_sentences[idx]
            content = content.replace(original_sentence, updated_sentence, 1)

    with open(tex_file, "w") as file:
        file.write(content)
    print("Changes detected, processing tex file.")
    tex_file_modified_by_script = True


if __name__ == "__main__":
    # Your tex file name goes here
    tex_file = "main.tex"
    # Your md file name goes here, it provides that structure and user comments
    md_file = "comments.md"
    # Output file name here
    out_file = "first_sentences.md"

    process_out_file(tex_file, md_file, out_file)

    def tex_callback(file_path):
        global tex_file_modified_by_script
        if not tex_file_modified_by_script:
            process_out_file(tex_file, md_file, out_file)
        tex_file_modified_by_script = False

    def md_callback(file_path):
        global md_file_modified_by_script
        if not md_file_modified_by_script:
            process_out_file(tex_file, md_file, out_file)
        md_file_modified_by_script = False

    def out_callback(file_path):
        global out_file_modified_by_script
        if not out_file_modified_by_script:
            update_tex_file_from_out(tex_file, out_file)
            update_md_file_from_out(md_file, out_file)
        out_file_modified_by_script = False

    # Monitor all files
    tex_thread = threading.Thread(target=monitor_file, args=(tex_file, tex_callback))
    md_thread = threading.Thread(target=monitor_file, args=(md_file, md_callback))
    out_thread = threading.Thread(target=monitor_file, args=(out_file, out_callback))

    tex_thread.start()
    md_thread.start()
    out_thread.start()

    tex_thread.join()
    md_thread.join()
    out_thread.join()
