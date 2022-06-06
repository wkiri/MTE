#!/usr/bin/env python
# generate_pds4_bundle.py
# Mars Target Encyclopedia
# Generate a complete MTE PDS4 bundle.
#
# Steven Lu
# January 13, 2021

import os
import sys
import csv
import shutil
import fnmatch
import hashlib
import datetime
import numpy as np
import deliver_sqlite
import pandas as pd
from xml.etree import ElementTree
from Cheetah.Template import Template


# Constants
MTE_BUNDLE_NAME = 'mars_target_encyclopedia'
MER_COLLECTION_NAME = 'data_mer'
MPF_COLLECTION_NAME = 'data_mpf'
PHX_COLLECTION_NAME = 'data_phx'
MSL_COLLECTION_NAME = 'data_msl'
DOC_COLLECTION_NAME = 'document'
MD5_CHECKSUM_NAME = 'urn-nasa-pds-mars_target_encyclopedia.md5'
MANIFEST_NAME = 'urn-nasa-pds-mars_target_encyclopedia.manifest'


# This function sets up the MTE PDS4 bundle structure, specifically
# accomplishing the following tasks:
# 1. If the MTE bundle directory exists in out_dir, remove it.
# 2. Create MTE bundle directory
# 3. Create directories for collections (document, mer, mpf, msl, and phx) based
#    on mission DB files
# 4. Copy documents and the corresponding XML files to document collection
# 5. Create bundle xml file based on mission DB files
# 6. Copy README.txt and mte_schema.jpg to the bundle directory
def setup_bundle_structure(out_dir, bundle_template_dir, mpf_db_file,
                           phx_db_file, msl_db_file, mer2_db_file, mer1_db_file):
    # Create MTE bundle directory
    mte_bundle_dir = os.path.join(out_dir, MTE_BUNDLE_NAME)
    if os.path.exists(mte_bundle_dir):
        shutil.rmtree(mte_bundle_dir)
        print '[INFO] The bundle dir already exists. Removed.'

    os.mkdir(mte_bundle_dir)
    print '[INFO] Create bundle directory: %s' % os.path.abspath(mte_bundle_dir)

    # Create collection directories
    doc_collection_dir = os.path.join(mte_bundle_dir, DOC_COLLECTION_NAME)
    os.mkdir(doc_collection_dir)
    print '[INFO] Create %s collection at %s.' % \
          (DOC_COLLECTION_NAME, os.path.abspath(doc_collection_dir))

    include_mer2 = mer2_db_file is not None
    include_mer1 = mer1_db_file is not None
    mer_collection_dir = os.path.join(mte_bundle_dir, MER_COLLECTION_NAME)
    mer2_subdir = os.path.join(mer_collection_dir, 'mer2')
    mer1_subdir = os.path.join(mer_collection_dir, 'mer1')
    if include_mer2 or include_mer1:
        os.mkdir(mer_collection_dir)
        print '[INFO] Create %s collection at %s.' % \
              (MER_COLLECTION_NAME, os.path.abspath(mer_collection_dir))

        if include_mer2:
            os.mkdir(mer2_subdir)
            print '[INFO] Create MER-2 Spirit directory: %s' % \
                  os.path.abspath(mer2_subdir)

        if include_mer1:
            os.mkdir(mer1_subdir)
            print '[INFO] Create MER-1 Opportunity directory: %s' % \
                  os.path.abspath(mer1_subdir)

    include_mpf = mpf_db_file is not None
    mpf_collection_dir = os.path.join(mte_bundle_dir, MPF_COLLECTION_NAME)
    if include_mpf:
        os.mkdir(mpf_collection_dir)
        print '[INFO] Create %s collection at %s.' % \
              (MPF_COLLECTION_NAME, os.path.abspath(mpf_collection_dir))

    include_phx = phx_db_file is not None
    phx_collection_dir = os.path.join(mte_bundle_dir, PHX_COLLECTION_NAME)
    if include_phx:
        os.mkdir(phx_collection_dir)
        print '[INFO] Create %s collection at %s.' % \
              (PHX_COLLECTION_NAME, os.path.abspath(phx_collection_dir))

    include_msl = msl_db_file is not None
    msl_collection_dir = os.path.join(mte_bundle_dir, MSL_COLLECTION_NAME)
    if include_msl:
        os.mkdir(msl_collection_dir)
        print '[INFO] Create %s collection at %s.' % \
              (MSL_COLLECTION_NAME, os.path.abspath(msl_collection_dir))

    # Copy documents to the document collection
    doc_template_dir = os.path.join(bundle_template_dir, DOC_COLLECTION_NAME)
    create_document_collection(doc_template_dir, doc_collection_dir)

    # Create bundle xml
    create_bundle_xml(bundle_template_dir, mte_bundle_dir, include_mpf,
                      include_phx, include_msl, include_mer2, include_mer1)

    bundle_dict = {
        'mte_bundle_dir': mte_bundle_dir,
        'doc_collection_dir': doc_collection_dir,
        'mpf_collection_dir': mpf_collection_dir,
        'mer_collection_dir': mer_collection_dir,
        'phx_collection_dir': phx_collection_dir,
        'msl_collection_dir': msl_collection_dir,
        'out_dir': out_dir
    }

    return bundle_dict


def create_bundle_xml(bundle_template_dir, mte_bundle_dir, include_mpf,
                      include_phx, include_msl, include_mer2, include_mer1):
    bundle_dict = dict()
    bundle_dict.setdefault('include_mer2', include_mer2)
    bundle_dict.setdefault('include_mer1', include_mer1)
    bundle_dict.setdefault('include_mpf', include_mpf)
    bundle_dict.setdefault('include_phx', include_phx)
    bundle_dict.setdefault('include_msl', include_msl)

    template_file = os.path.join(bundle_template_dir,
                                 'bundle_mars_target_encyclopedia.txml')
    template = Template(file=template_file, searchList=[{
        'bundle': bundle_dict,
        'today': get_current_date()
    }])

    bundle_xml_file = os.path.join(mte_bundle_dir,
                                   'bundle_mars_target_encyclopedia.xml')
    with open(bundle_xml_file, 'w+') as f:
        f.write(str(template))
    print '[INFO] Create bundle xml file: %s' % os.path.abspath(bundle_xml_file)


# One char is stored in one byte. To count the total bytes of a string, we
# simply just need to count the length of the string.
def get_string_size_in_bytes(string):
    return len(string)


# Get the size of a file in bytes.
def get_file_size_in_bytes(target_file):
    return os.stat(target_file).st_size


# Compute records. -1 to not include header.
def get_total_number_of_records(csv_lines):
    return len(csv_lines) - 1


# Compute object length (in bytes) for the header (first) line.
# Note: the CRLF ('\r\n') needs to be included when counting the bytes of
# a record. Commas need to be included as well.
def get_header_object_length(header_line):
    return get_string_size_in_bytes(header_line)


# Compute maximum_record_length (in bytes) for the table contents (excluding
# the header).
# Note: the CRLF ('\r\n') needs to be included when counting the bytes of
# a record. Commas need to be included as well.
def get_max_record_length(csv_lines):
    content_1d_array = np.array(csv_lines[1:])
    if len(content_1d_array) == 0:
        record_longest_str = ''
    else:
        record_longest_str = max(content_1d_array, key=len)

    return get_string_size_in_bytes(record_longest_str)


# Compute maximum_field_length for all columns in the csv lines.
def get_max_field_len(csv_lines, field_index):
    # content_2d_array = np.array([line.split(',') for line in csv_lines])
    content_df = pd.DataFrame(csv_lines)
    if len(content_df) == 1:
        max_len = 0
    else:
        max_len = content_df[field_index][1:].astype(bytes).str.len().max()

    return max_len


# This function returns the current date in YYYY-MM-DD format
def get_current_date():
    today = datetime.date.today()

    return str(today)


# Note that in this function we need to read csv file twice. The first time we
# read the csv file as a text file because in order to count the bytes of some
# fields (e.g. object_length and maximum_record_length), we need to keep
# punctuations (e.g., comma, \r\n). The second time we read the csv file using
# a standard csv reader to count the maximum field length.
def compute_single_table_stats(csv_file):
    with open(csv_file, 'r') as f:
        lines = f.readlines()

    # Compute file size
    file_size = get_file_size_in_bytes(csv_file)

    # Compute total number of records (or rows, with header lines excluded)
    records = get_total_number_of_records(lines)

    # Compute object length (in bytes) for the header (first) line.
    header_line = lines[0]
    object_len = get_header_object_length(header_line)

    # The offset (in bytes) of the table content equals the length of the header
    offset = object_len

    # Compute maximum_record_length (in bytes) for the table contents.
    max_record_len = get_max_record_length(lines)

    # Store these values in a dictionary and return
    table_stats = {
        'file_size': file_size,
        'records': records,
        'object_len': object_len,
        'offset': offset,
        'max_record_len': max_record_len
    }

    # Compute maximum_field_length for all columns in the table csv
    columns = header_line.split(',')
    lines = list(csv.reader(open(csv_file, 'r')))
    for index, column in enumerate(columns):
        table_stats['max_field_len_%d' % (index+1)] = get_max_field_len(
            lines, field_index=index
        )

    return table_stats


def create_single_xml_label(template_file, label_file, table_stats):
    template = Template(file=template_file, searchList=[{
        'table': table_stats,
        'today': get_current_date()
    }])

    with open(label_file, 'w+') as f:
        f.write(str(template))


# Generate xml labels for the csv files. If a csv file is empty (meaning
# contains only the header but no actual content), the csv file will be removed
# from the collection and no xml label file will be generated.
def create_xml_labels(collection_dir, bundle_template_dir, mission_name):
    # Create label XML files for the corresponding table CSV files
    for table_name in ['targets', 'components', 'contains', 'documents',
                       'sentences', 'mentions', 'properties', 'has_property',
                       'aliases']:
        csv_file = os.path.join(collection_dir, '%s.csv' % table_name)

        with open(csv_file, 'r') as f:
            lines = f.readlines()

        if len(lines) == 1:
            os.remove(csv_file)
            print '[INFO] Remove %s file because it contains only header.' % \
                  os.path.abspath(csv_file)
            continue

        template_file = os.path.join(bundle_template_dir,
                                     '%s_%s.txml' % (mission_name, table_name))
        label_file = os.path.join(collection_dir, '%s.xml' % table_name)

        table_stats = compute_single_table_stats(csv_file)
        create_single_xml_label(template_file, label_file, table_stats)
        print '[INFO] Create %s mission %s.xml label file: %s' % \
              (mission_name, table_name, label_file)


# Generate inventory csv and xml files.
# This function must be executed after create_xml_labels function.
def create_inventory_files(collection_dir, bundle_template_dir,
                           collection_name):
    # Create inventory csv file
    inventory_csv_name = 'collection_%s_inventory.csv' % collection_name
    inventory_csv_path = os.path.join(collection_dir, inventory_csv_name)
    inventory_csv_file = open(inventory_csv_path, 'w+')

    xml_file_counter = 0
    for root, _, file_names in os.walk(collection_dir):
        for file_name in fnmatch.filter(file_names, '*.xml'):
            xml_file_counter += 1
            file_path = os.path.join(root, file_name)

            lid_vid = get_lidvid(file_path)
            inventory_csv_file.write('P,%s\r\n' % lid_vid)

    inventory_csv_file.close()
    print '[INFO] Create inventory csv file for %s mission: %s' % \
          (collection_name, os.path.abspath(inventory_csv_path))

    # Create collection xml file
    template_file = os.path.join(bundle_template_dir,
                                 'collection_%s_inventory.txml' % collection_name)
    template = Template(file=template_file, searchList=[{
        'inventory_records': xml_file_counter,
        'today': get_current_date()
    }])

    collection_xml_name = 'collection_%s_inventory.xml' % collection_name
    collection_xml_path = os.path.join(collection_dir, collection_xml_name)
    with open(collection_xml_path, 'w+') as f:
        f.write(str(template))
    print '[INFO] Create collection xml file for %s mission: %s' % \
          (collection_name, os.path.abspath(collection_xml_path))


def create_collection(collection_dir, db_file, mission_name,
                      bundle_template_dir):
    # Export DB file to CSV files. If the mission DB file isn't available yet,
    # we will deliver empty CSV files.
    if db_file is not None:
        # For MER, data files go in subdirectories
        if mission_name in ['mer1', 'mer2']:
            deliver_sqlite.main(db_file, os.path.join(collection_dir, mission_name), 
                                fix_double_quotes=True)
        else:
            deliver_sqlite.main(db_file, collection_dir, fix_double_quotes=True)

    # For MER, data labels go in subdirectories
    if mission_name in ['mer1', 'mer2']:
        create_xml_labels(os.path.join(collection_dir, mission_name), 
                          bundle_template_dir, mission_name)
    else:
        create_xml_labels(collection_dir, bundle_template_dir, mission_name)
    # Inventory files go at the collection level
    create_inventory_files(collection_dir, bundle_template_dir, mission_name)


def create_document_collection(doc_template_dir, doc_collection_dir):
    # Copy readme file to the document collection
    src_readme = os.path.join(doc_template_dir, 'readme.txt')
    trt_readme = os.path.join(doc_collection_dir, 'readme.txt')
    shutil.copyfile(src_readme, trt_readme)
    print '[INFO] Copied readme file %s to document collection.' % \
          os.path.abspath(trt_readme)

    # Create readme XML label
    readme_template_file = os.path.join(doc_template_dir, 'readme.txml')
    readme_template = Template(file=readme_template_file, searchList=[{
        'today': get_current_date()
    }])

    readme_xml_file = os.path.join(doc_collection_dir, 'readme.xml')
    with open(readme_xml_file, 'w+') as f:
        f.write(str(readme_template))
    print '[INFO] Created XML label file %s for readme.txt' % \
          os.path.abspath(readme_xml_file)

    # Copy MTE schema diagram to the document collection
    src_schema = os.path.join(doc_template_dir, 'mte_schema.jpg')
    trt_schema = os.path.join(doc_collection_dir, 'mte_schema.jpg')
    shutil.copyfile(src_schema, trt_schema)
    print '[INFO] Copied MTE schema file %s to document collection.' % \
          os.path.abspath(trt_schema)

    # Create MTE schema XML label
    schema_template_file = os.path.join(doc_template_dir, 'mte_schema.txml')
    schema_template = Template(file=schema_template_file, searchList=[{
        'today': get_current_date()
    }])

    schema_xml_file = os.path.join(doc_collection_dir, 'mte_schema.xml')
    with open(schema_xml_file, 'w+') as f:
        f.write(str(schema_template))
    print '[INFO] Created XML label file %s for mte_schema.jpg' % \
          os.path.abspath(schema_xml_file)
    
    # Create inventory file to the document collection
    create_inventory_files(doc_collection_dir, doc_template_dir, 'document')


def create_md5_checksum_file(out_dir):
    md5_checksum_file = open(os.path.join(out_dir, MD5_CHECKSUM_NAME), 'w+')

    for root, _, file_names in os.walk(out_dir):
        for file_name in file_names:
            if file_name == MD5_CHECKSUM_NAME:
                continue

            file_path = os.path.join(root, file_name)
            relative_path = os.path.relpath(file_path, start=out_dir)
            md5_checksum = hashlib.md5(open(file_path, 'rb').read()).hexdigest()
            md5_checksum_file.write('%s  %s\r\n' % (md5_checksum,
                                                    relative_path))

    md5_checksum_file.close()


def get_lidvid(xml_path):
    xml_tree = ElementTree.parse(xml_path)
    xml_root = xml_tree.getroot()
    for child in xml_root:
        if 'Identification_Area' in child.tag:
            for sub_child in child:
                if 'logical_identifier' in sub_child.tag:
                    lid = sub_child.text
                if 'version_id' in sub_child.tag:
                    vid = sub_child.text

    lid_vid = '%s::%s' % (lid, vid)

    return lid_vid


def create_manifest_file(out_dir):
    manifest_file = open(os.path.join(out_dir, MANIFEST_NAME), 'w+')

    for root, _, file_names in os.walk(out_dir):
        for file_name in fnmatch.filter(file_names, '*.xml'):
            file_path = os.path.join(root, file_name)
            relative_path = os.path.relpath(file_path, start=out_dir)

            lid_vid = get_lidvid(file_path)
            manifest_file.write('%s  %s\r\n' % (lid_vid, relative_path))

    manifest_file.close()


def main(out_dir, mpf_db_file, phx_db_file, msl_db_file,
         mer2_db_file, mer1_db_file, bundle_template_dir):
    if mpf_db_file is None and phx_db_file is None and msl_db_file is None and \
            mer2_db_file is None and mer1_db_file is None:
        print '[ERROR] At least one DB file should be provided. Exit.'
        sys.exit(1)

    # Setup the bundle directories, and copy static files to the bundle
    bundle_dict = setup_bundle_structure(
        out_dir, bundle_template_dir, mpf_db_file, phx_db_file, msl_db_file,
        mer2_db_file, mer1_db_file
    )

    # Create MPF collection
    if mpf_db_file is not None:
        create_collection(bundle_dict['mpf_collection_dir'], mpf_db_file,
                          'mpf', bundle_template_dir)

    # Create PHX collection
    if phx_db_file is not None:
        create_collection(bundle_dict['phx_collection_dir'], phx_db_file, 'phx',
                          bundle_template_dir)

    # Create MER-2 Spirit sub-collection.
    if mer2_db_file is not None:
        create_collection(bundle_dict['mer_collection_dir'], mer2_db_file,
                          'mer2', bundle_template_dir)

    # Create MER-1 Opportunity sub-collection.
    if mer1_db_file is not None:
        create_collection(bundle_dict['mer_collection_dir'], mer1_db_file,
                          'mer1', bundle_template_dir)

    # Create MSL collection.
    if msl_db_file is not None:
        create_collection(bundle_dict['msl_collection_dir'], msl_db_file, 'msl',
                          bundle_template_dir)

    # Create md5 checksum file
    create_md5_checksum_file(bundle_dict['mte_bundle_dir'])

    # Create delivery manifest file
    create_manifest_file(bundle_dict['mte_bundle_dir'])

    print '[INFO] Done.'


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Generate a complete MTE PDS4 '
                                                 'bundle')
    parser.add_argument('out_dir', type=str, help='Output directory contains '
                                                  'the MTE PDS4 bundle.')
    parser.add_argument('--mpf_db_file', type=str,
                        help='Path to the MPF sqlite DB file')
    parser.add_argument('--phx_db_file', type=str,
                        help='Path to the PHX sqlite DB file')
    parser.add_argument('--msl_db_file', type=str,
                        help='Path to the MSL sqlite DB file')
    parser.add_argument('--mer2_db_file', type=str,
                        help='Path to the MER Spirit rover (MER-A or MER-2) '
                             'sqlite DB file')
    parser.add_argument('--mer1_db_file', type=str,
                        help='Path to the MER Opportunity rover (MER-B or '
                             'MER-1) sqlite DB file')
    parser.add_argument('--bundle_template_dir', type=str,
                        default='pds4_bundle_template',
                        help='Path to the MTE PDS4 bundle template directory.')

    args = parser.parse_args()
    main(**vars(args))
