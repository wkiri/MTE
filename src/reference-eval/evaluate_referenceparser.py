import re, os
import argparse


def get_reference_id(line):
    """
    Extracts the reference id - the number between [] brackets
    :param line: one reference
    :return: reference id; -1 if nothing found
    """
    id = -1
    match = re.search('\[[0-9]+\]', line)
    if match:
        id = int(match.group(0).strip('[]'))
    return id


def word_set(line):
    """
    Tokenize reference into words by:
        (a) Replacing all special characters with space.
        (b) Splitting the reference by space.
    :param line: one reference
    :return: a set of words
    """
    line_set = set()
    line = set(re.sub('[^0-9a-zA-Z]+', ' ', line).strip().split(' '))
    for word in line:
        if word.strip():
            line_set.add(word.strip())
    return line_set


def compare_line(ground_truth, extracted):
    """
    Compare the intersection of words between two references
    :param ground_truth: original reference
    :param extracted: extracted reference
    :return: Number of common words, Number of actual words, Number of extracted words
    """
    ground_truth_values = word_set(ground_truth)
    extracted_values = word_set(extracted)
    common = ground_truth_values.intersection(extracted_values)
    return (len(common), len(ground_truth_values), len(extracted_values))


def reference_map(filepath):
    """
    Read references from a file and convert it into a map with key as reference id and value as reference
    :param filepath: path to the file containing references
    :return: reference map
    """
    ref_map = {}
    with open(filepath, 'rb') as f:
        lines = f.readlines()
        for line in lines:
            #print("Line: ", line)
            id = get_reference_id(line)
            if id != -1:
                ref_map[id] = line
    return ref_map


def evaluate(ground_truth, extracted):
    """
    Evaluate references extracted from a set of documents
    :param ground_truth: directory path where actual references are placed
    :param extracted: directory path where extracted references are placed
    """
    recall_file_sim = 0.0
    precision_file_sim = 0.0
    file_count = 0
    for gt_file in os.listdir(ground_truth):
        if gt_file.endswith(".txt"):
            recall_line_sim = 0.0
            precision_line_sim = 0.0
            gt_map = reference_map(os.path.join(ground_truth, gt_file))
            ex_map = reference_map(os.path.join(extracted, gt_file))
            if len(gt_map.keys()) == 0:
                continue
            file_count += 1
            if len(ex_map.keys()) != 0:
                for key in gt_map:
                    if key in ex_map:
                        (common, gt_words, ex_words) = compare_line(gt_map[key], ex_map[key])
                        recall_line_sim += (common / gt_words * 1.0)
                        precision_line_sim += (common / ex_words * 1.0)
                recall_file_sim += (recall_line_sim / len(gt_map.keys()) * 1.0)
                precision_file_sim += (precision_line_sim / len(ex_map.keys()) * 1.0)
    print("Recall: ", recall_file_sim / file_count * 1.0)
    print("Precision: ", precision_file_sim / file_count * 1.0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-gt', '--groundtruth', help='Directory path to the actual references')
    parser.add_argument('-ex', '--extracted', help='Directory path to the extracted references')
    args = parser.parse_args()
    evaluate(args.groundtruth, args.extracted)
