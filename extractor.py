#!/usr/bin/python
#
# This is a script to parse resource unit files
# from iTree streets to extract useful info
#

import argparse
import os
import csv
import subprocess
from bs4 import BeautifulSoup

XLS2CSV_EXEC = 'xls2csv'

def _assert_has_xls_converter():
    try:
        subprocess.check_call(['which',XLS2CSV_EXEC])
    except subprocess.CalledProcesError, e:
        print 'You need to have a supported version of "xls2csv" installed\n'\
            'Install it on ubuntu with "apt-get install catdoc"'
        exit(1)

def is_valid_code(code):
    return (code and
            len(code.strip()) and
            code.strip() != '"SpeciesCode"')

def is_valid_name(name):
    """ This is used for excel conversion weirdness """
    try:
        float(name)
        return False
    except:
        return True

def extract_data_csvs(output_dir, xls_path):
    _assert_has_xls_converter()

    sheets = ['hydro','property_value','aq_ozone_dep','aq_nox_dep',
              'aq_pm10_dep','aq_sox_dep','aq_nox_avoided',
              'aq_pm10_avoided','aq_sox_avoided','aq_voc_avoided',
              'bvoc','net_vocs','co2_seq','co2_decomp','co2_maint',
              'net_co2_seq','co2_avoided','natual_gas',
              'electricity','lsa','cpa','dbh_by_age_class',
              'species_codes','numbers','interp_range',
              'co2_storage', 't', 'u']

    devnull = open('/dev/null','w')
    p = subprocess.Popen([XLS2CSV_EXEC, '-b#', xls_path],
                         stdout=subprocess.PIPE,
                         stderr=devnull)

    csvdata, err = p.communicate()

    sheetdata = csvdata.split('#')
    if len(sheetdata) != len(sheets):
        print "Expected %s sheets, but got %s sheets for %s"\
            % (len(sheets), len(sheetdata), xls_path)
        print sheetdata[-2]
        exit(3)

def parse_path(soup, path):
    ids = {}
    for tag in soup.find('p').find_all('a'):
        ids[tag['href'][1:]] = tag.get_text().lower().replace(' ','_')

    last_ref = None
    for table in soup.find_all('table'):
        ref_link = table.find_previous_sibling('a')
        category = ids[ref_link['name']]
        file_to_write = "%s__%s.csv" % (path, category)

        writer = file(file_to_write,'w')

        for row in table.find_all('tr'):
            cells = [cell.get_text().replace(',','') for cell in row.find_all('td')]
            writer.write(','.join(cells) + "\n")

def extract_data(output_dir, resource_dir):
    for root, dirs, files in os.walk(resource_dir):
        if 'ResourceUnit.html' in files:
            html_path = os.path.join(root, 'ResourceUnit.html')
            soup = BeautifulSoup(file(html_path).read())
            parse_path(soup,
                       os.path.join(output_dir,
                                    'output__%s' % os.path.split(root)[1]))


def extract_species(output_dir, resource_dir):
    _assert_has_xls_converter()

    header = ['SpeciesCode','ScientificName','CommonName','Tree Type',
              'SppValueAssignment','Species Rating (%)',
              'Basic Price ($/sq in)','Palm Trunk Cost($/ft)',
              'Replacement Cost ($)','TAr (sq Inches)','region']

    file_path = os.path.join(output_dir, 'species_master_list.csv')
    output_file = file(file_path, 'w')

    writer = csv.DictWriter(output_file, header)
    writer.writeheader()

    devnull = open('/dev/null','w')

    for root, dirs, files in os.walk(resource_dir):
        if 'SpeciesCode.xls' in files:
            region_code = os.path.split(root)[1]

            species_path = os.path.join(root, 'SpeciesCode.xls')
            p = subprocess.Popen([XLS2CSV_EXEC, species_path],
                                 stdout=subprocess.PIPE,
                                 stderr=devnull)
            csvdata, err = p.communicate()

            reader = csv.DictReader(csvdata.split('\n'))

            for row_dict in reader:
                code = row_dict['SpeciesCode']
                name = row_dict['ScientificName']

                if is_valid_code(code) and is_valid_name(name):
                    row_dict['region'] = region_code
                    writer.writerow(row_dict)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action',help='Action should be "extract_species" or'\
                        '"extract_values"')
    parser.add_argument('-r','--resource-dir', help='resource unit directory')
    parser.add_argument('-d','--output-dir', help='output directory')
    args = parser.parse_args()

    action = args.action
    output_dir = args.output_dir or ''
    resource_dir = args.resource_dir or 'ResourceUnit'

    if action != 'extract_species' and action != 'extract_values':
        parser.print_help()
        exit(1)

    if not os.path.exists(resource_dir):
        print 'Error: Could not find a valid resource directory at {}. \n'\
            'Specify one with "-r"'.format(resource_dir)
        exit(1)


    if action == 'extract_species':
        extract_species(output_dir, resource_dir)
    elif action == 'extract_values':
        extract_data(output_dir, resource_dir)

if __name__ == '__main__':
    main()
