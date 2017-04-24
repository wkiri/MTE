import re, os
import argparse


def get_reference_id(reference):
    """
    Extract reference id ([N])
    :param reference: Any possible reference
    :return: reference id
    """
    ref_id = -1
    match = re.search('\[[0-9]+\]', reference)
    if match:
        ref_id = int(match.group(0).strip('[]'))
    return ref_id


def parse_file(path):
    """
    Parses a file at given path
    :param path: path to file
    :return: parsed content
    """
    with open(path, 'rb') as f:
        content = f.read()

    # Extract references from the parsed content
    references = extract_references(content)

    # Remove references from the parsed content
    for ref_id in references:
        content = content.replace(references[ref_id], ' ' * len(references[ref_id]))
    return content


def extract_references(content):
    """
    Extract references from text
    :param content: text
    :return: dictionary of references with reference id ([N]) as key
    """
    references = {}
    content = content.replace("\n", "\\n")
    matches = re.findall('(\[[0-9]+\][^\[]*?(?=\[|Acknowledge|Fig|Table|Conclusion|pdf))', content)
    if matches:
        for match in matches:
            ref_id = get_reference_id(match)
            # No reference id exist -- skip it
            if ref_id != -1:
                value = match.replace('\\n', '\n')
                references[ref_id] = value
    return references


def process_docs(in_path, out_path):
    for in_file in os.listdir(in_path):
        if in_file.endswith(".txt"):
            print("Processing: " + os.path.join(in_path, in_file))
            content = parse_file(os.path.join(in_path, in_file))
            with open(os.path.join(out_path, in_file), 'wb') as out:
                out.write(content)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', help='Directory path to documents containing content')
    parser.add_argument('-o', '--output', help='Directory path where processed documents to be placed')
    args = parser.parse_args()
    process_docs(args.input, args.output)