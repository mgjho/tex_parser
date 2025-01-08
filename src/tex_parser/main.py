import os
import re
import threading
import time

# Flags to prevent callback loops
tex_file_modified_by_script = False
out_file_modified_by_script = False


def extract_first_sentence_from_paragraphs(tex_file):
    with open(tex_file) as file:
        content = file.read()

    # Find the position of \maketitle and process content from there
    maketitle_pos = content.find(r"\maketitle")
    if maketitle_pos != -1:
        content = content[maketitle_pos + len(r"\maketitle") :]

    # Remove figure objects
    content = re.sub(r"\\begin{figure}.*?\\end{figure}", "", content, flags=re.DOTALL)
    content = re.sub(
        r"\\begin{figure\*}.*?\\end{figure\*}", "", content, flags=re.DOTALL
    )
    # Split the content into paragraphs by identifying empty lines between them
    paragraphs = re.split(r"\\par\n", content.strip())
    paragraphs = paragraphs[:-1]  # Skip the last paragraph
    first_sentences = []
    comments = []
    for paragraph in paragraphs:
        # Extract comments preceding the paragraph
        comment_match = re.search(r"%\s*(.*?)\n", paragraph)
        comment = comment_match.group(1) if comment_match else ""
        comments.append(comment)
        # Split the paragraph into sentences (using common punctuation marks)
        sentences = re.split(r"(?<=[.!?]) +", paragraph)
        if sentences:
            first_sentence = sentences[0]
            last_newline_pos = first_sentence.rfind("\n")
            # If the first sentence contains a newline character, consider the text after the last newline
            if last_newline_pos != -1:
                first_sentence = first_sentence[last_newline_pos + 1 :]
            first_sentences.append(first_sentence)
    return first_sentences, comments


def monitor_file(file_path, callback, interval=1):
    last_modified = os.path.getmtime(file_path)

    while True:
        new_last_modified = os.path.getmtime(file_path)

        if new_last_modified != last_modified:
            last_modified = new_last_modified
            callback(file_path)
        time.sleep(interval)


def process_out_file(tex_file, out_file):
    global out_file_modified_by_script
    first_sentences, comments = extract_first_sentence_from_paragraphs(tex_file)

    with open(out_file, "w") as out_file_obj:
        out_file_obj.write(f"Summary of {tex_file}\n ---")
        for idx, sentence in enumerate(first_sentences):
            comment = comments[idx] if idx < len(comments) else ""
            if not comment:
                comment = "[Empty comment]"
            # Not having a \n after summary is intentional
            out_file_obj.write(f"\n__{idx+1}. {comment}__: _{sentence}_\n")
    print("Changes detected, processing out file.")
    out_file_modified_by_script = True


def update_tex_file_from_out(tex_file, out_file):
    global tex_file_modified_by_script
    with open(out_file) as file:
        lines = file.readlines()

    updated_sentences = []
    updated_comments = []
    for line in lines:
        if ": _" in line:
            parts = line.split(": _")
            # Extract the comment part using regular expression
            match = re.search(r"__\d+\.\s*(.*?)__", parts[0])
            updated_comment = match.group(1).strip() if match else ""
            if updated_comment == "[Empty comment]":
                updated_comment = ""
            updated_comments.append(updated_comment)
            updated_sentence = parts[1].strip().rstrip("_")
            updated_sentences.append(updated_sentence)

    first_sentences, comments = extract_first_sentence_from_paragraphs(tex_file)

    with open(tex_file) as file:
        content = file.read()

    # Search for the original sentences and comments, and replace them with the updated sentences and comments
    for idx, original_sentence in enumerate(first_sentences):
        if idx < len(updated_sentences):
            updated_sentence = updated_sentences[idx]
            content = content.replace(original_sentence, updated_sentence, 1)

    for idx, original_comment in enumerate(comments):
        if original_comment and idx < len(updated_comments):
            updated_comment = updated_comments[idx]
            # content = content.replace(original_comment, updated_comment, 1)
            content = content.replace(
                f"% {original_comment}", f"% {updated_comment}", 1
            )

    with open(tex_file, "w") as file:
        file.write(content)
    print("Changes detected, processing tex file.")
    tex_file_modified_by_script = True


if __name__ == "__main__":
    # Your tex file name goes here
    tex_file = "main.tex"
    # Output file name here
    out_file = "first_sentences.md"

    process_out_file(tex_file, out_file)

    def tex_callback(file_path):
        global tex_file_modified_by_script
        if not tex_file_modified_by_script:
            process_out_file(tex_file, out_file)
        tex_file_modified_by_script = False

    def out_callback(file_path):
        global out_file_modified_by_script
        if not out_file_modified_by_script:
            update_tex_file_from_out(tex_file, out_file)
        out_file_modified_by_script = False

    # Monitor all files
    tex_thread = threading.Thread(target=monitor_file, args=(tex_file, tex_callback))
    out_thread = threading.Thread(target=monitor_file, args=(out_file, out_callback))

    tex_thread.start()
    out_thread.start()

    tex_thread.join()
    out_thread.join()
