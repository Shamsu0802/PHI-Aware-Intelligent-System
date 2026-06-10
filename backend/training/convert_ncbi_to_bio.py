import os

DATA_DIR = "data/disease_ner"
OUTPUT_FILE = "data/disease_ner/train.bio"

def read_ncbi_file(filepath):
    texts = {}
    annotations = {}

    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if "|a|" in line or "|t|" in line:
                pmid, _, text = line.split("|", 2)
                texts.setdefault(pmid, "")
                texts[pmid] += text + " "

            elif line and line[0].isdigit():
                parts = line.split("\t")
                pmid = parts[0]
                start = int(parts[1])
                end = int(parts[2])
                disease = parts[3]

                annotations.setdefault(pmid, []).append((start, end, disease))

    return texts, annotations


def convert_to_bio(texts, annotations, output_path):
    with open(output_path, "w", encoding="utf-8") as out:
        for pmid, text in texts.items():
            char_labels = ["O"] * len(text)

            for start, end, _ in annotations.get(pmid, []):
                char_labels[start] = "B-DISEASE"
                for i in range(start + 1, end):
                    char_labels[i] = "I-DISEASE"

            tokens = text.split()
            idx = 0

            for token in tokens:
                tag = "O"
                for i in range(len(token)):
                    if idx + i < len(char_labels) and char_labels[idx + i] != "O":
                        tag = char_labels[idx + i]
                        break

                out.write(f"{token} {tag}\n")
                idx += len(token) + 1

            out.write("\n")


if __name__ == "__main__":
    train_file = os.path.join(DATA_DIR, "NCBItrainset_corpus.txt")
    texts, annotations = read_ncbi_file(train_file)
    convert_to_bio(texts, annotations, OUTPUT_FILE)

    print("✅ BIO format file created:", OUTPUT_FILE)
