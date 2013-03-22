import os
import re

WATTS_PER_BTU = 0.29307107

def _data_files():
    pattern = r'output__(.*)__(.*).csv'
    matches = []
    for datafile in os.listdir('output'):
        match = re.match(pattern, datafile)
        if match:
            matches.append(match)

    return matches

def _regions():
    return { m.group(1) for m in _data_files() }

regions = _regions()

def factors_for_region(region):
    return { m.group(2) for m in _data_files() }


def _assert_valid_region(region):
    if region not in regions:
        raise Exception('Invalid region %s' % region)


def get_data(region, factor):
    _assert_valid_region(region)

    data = 'output/output__%s__%s.csv' % (region, factor)

    if factor not in factors_for_region(region):
        raise Exception('Invalid facor, %s, for region %s' % (factor, region))

    alldata = [row.split(',') for row in open(data).read().split('\n')]
    dbh_breaks = map(float, alldata[0][1:])
    datarows = alldata[1:]

    data = {}

    for row in datarows:
        if len(row[0]) > 0:
            data[row[0]] = map(float, row[1:])

    return (dbh_breaks, data)

def lookup_species_code(region, species, genus=None, cultivar=None):
    _assert_valid_region(region)

    data_file = 'output/species_master_list.csv'
    sci_name = species

    if genus:
        sci_name = '%s %s' % (sci_name, genus)
    if cultivar:
        sci_name = "%s '%s'" % (sci_name, cultivar)

    sci_name = sci_name.lower()

    print "Looking for '%s'" % sci_name

    for datarow in open(data_file).read().split('\n'):
        cols = [c.strip() for c in datarow.split(',')]

        if (len(cols) >= 3 and
            cols[1].lower() == sci_name
            and cols[-1] == region):
            return (cols[0], cols[4])

    return None

def linear_interp(x1,y1,x2,y2,x):
    m = (y2 - y1) / (x2 - x1)
    b = y1 - m*x1

    return m*x + b

def interp(breaks, values, dbh):
    if len(breaks) != len(values):
        raise Exception('break and values arrays should be the same length\n'\
                        '%s and %s' % (breaks, values))

    if dbh < 0:
        dbh = 0.0

    # If we're before the first break assume everything
    # begins as zero
    if dbh < breaks[0]:
        return linear_interp(0.0, 0.0, breaks[0], values[0], dbh)

    # If we're after the last break we cap the max benefit
    # to the last value
    if dbh > breaks[-1]:
        return values[-1]

    # Determine the interval that we're in
    for i in xrange(1,len(breaks)):
        if dbh >= breaks[i-1] and \
           dbh <  breaks[i]:
            return linear_interp(breaks[i-1], values[i-1],
                                 breaks[i], values[i], dbh)

def get_factor_for_tree(region, factor, species_codes, dbh):
    breaks, data = get_data(region, factor)

    for code in species_codes:
        if code in data:
            return interp(breaks, data[code], float(dbh))

    raise Exception('Could not find data for '\
                    'factor %s in region %s for species %s' %
                    (factor, region, species_codes))



def get_energy_conserved(region, species_codes, dbh):
    # 1000s of BTU?
    nat_gas_kbtu = get_factor_for_tree(region, 'natural_gas', species_codes, dbh)
    nat_gas_kwh = nat_gas_btu * WATTS_PER_BTU

    energy_kwh = get_factor_for_tree(region, 'electricity', species_codes, dbh)

    return nat_gas_watt + energy_watt
