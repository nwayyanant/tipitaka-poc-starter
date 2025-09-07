import argparse

def clean_file(input_path, output_path):
    with open(input_path, 'r', encoding='utf-8-sig') as infile:
        lines = infile.readlines()

    cleaned_lines = []
    for line in lines:
        # Strip leading/trailing whitespace and skip empty lines
        cleaned = line.strip()
        if cleaned:
            cleaned_lines.append(cleaned)

    with open(output_path, 'w', encoding='utf-8') as outfile:
        for line in cleaned_lines:
            outfile.write(line + '\n')

    print(f"[✓] BOM + whitespace cleaned. Output saved to: {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clean BOM and whitespace from text file")
    parser.add_argument("-i", "--input", required=True, help="Path to input text file")
    parser.add_argument("-o", "--output", required=True, help="Path to cleaned output file")
    args = parser.parse_args()

    clean_file(args.input, args.output)
