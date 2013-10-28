import os
import re
import itertools
from functools import partial
import numpy as np

import sys

data_base = os.path.join(
    os.path.dirname(sys.modules['eco'].__file__),
    'data')


def sum_ignore_none(elems):
    """
    Sums an iterable, filtering out falsy values and returning None if all
    values are falsy
    """
    elems = filter(None, elems)
    return sum(elems) if elems else None


def sum_factor_and_conversion(*args):
    """
    Sums a list of factor and converted factor tuples
    The converted factors may be None, in which case their sum will be None
    """
    return map(sum_ignore_none, zip(*args))


class Benefits(object):
    WATTS_PER_BTU = 0.29307107
    GAL_PER_CUBIC_M = 264.172052
    LBS_PER_KG = 2.20462

    def __init__(self, factor_conversions=None):
        """
        Class for getting i-Tree eco-benfits for trees

        factor_conversions - An optional dictionary of factor to multiplier
                             Intended for converting benefits into money saved
        """
        self._species_list_cache = None
        self._factor_cache = {}
        self._regions = None
        self._factor_conversions = factor_conversions or {}

    # ALL DBH UNITS ARE CM
    def _data_files(self):
        pattern = r'output__(.*)__(.*).csv'
        matches = []
        for datafile in os.listdir(data_base):
            match = re.match(pattern, datafile)
            if match:
                matches.append(match)

        return matches

    @property
    def regions(self):
        if self._regions is None:
            self._regions = {m.group(1) for m in self._data_files()}

        return self._regions

    def factors_for_region(self, region):
        return {m.group(2) for m in self._data_files()}

    def _assert_valid_region(self, region):
        if region not in self.regions:
            raise Exception('Invalid region %s' % region)

    def _strip_trailing_empty_cells(self, alist):
        return list(itertools.takewhile(lambda a: a, alist))

    def _get_data(self, region, factor):
        self._assert_valid_region(region)

        data_file = os.path.join(data_base,
                                 'output__%s__%s.csv' % (region, factor))

        if data_file not in self._factor_cache:

            if factor not in self.factors_for_region(region):
                raise Exception('Invalid facor, %s, for region %s'
                                % (factor, region))

            alldata = [row.split(',')
                       for row in open(data_file).read().split('\n')]
            dbh_breaks_dirty = alldata[0][1:]

            def safe_float(f):
                try:
                    return float(f)
                except:
                    return 0.0

            # It is possible the dbh break set contains empty strings at the
            # end, so trim ending cells while empty
            dbh_breaks = np.array(
                map(safe_float,
                    self._strip_trailing_empty_cells(dbh_breaks_dirty)))

            datarows = alldata[1:]

            data = {}

            for row in datarows:
                if len(row[0]) > 0:
                    row_data = map(safe_float,
                                   self._strip_trailing_empty_cells(row[1:]))
                    data[row[0]] = np.array(row_data)

            self._factor_cache[data_file] = (dbh_breaks, data)

        return self._factor_cache[data_file]

    def lookup_species_code(self, region, genus, species=None, cultivar=None):

        self._assert_valid_region(region)

        if self._species_list_cache is None:
            data_file = os.path.join(data_base, 'species_master_list.csv')
            self._species_list_cache = open(data_file).read().split('\n')

        sci_name = genus

        if species:
            sci_name = '%s %s' % (sci_name, species)
            if cultivar:
                sci_name = "%s '%s'" % (sci_name, cultivar)

        sci_name = sci_name.lower()

        for datarow in self._species_list_cache:
            cols = [c.strip() for c in datarow.split(',')]

            if (len(cols) >= 3 and
               cols[1].lower() == sci_name and cols[-1] == region):
                return cols[4]

        return None

    def linear_interp(self, x1, y1, x2, y2, x):
        m = (y2 - y1) / (x2 - x1)
        b = y1 - m*x1

        return m*x + b

    def interp(self, breaks, values, dbh):
        if len(breaks) != len(values):
            raise Exception('break and values arrays should be the same'
                            'length\n%s and %s' % (breaks, values))

        if dbh < 0:
            dbh = 0.0

        # If we're before the first break assume everything
        # begins as zero
        if dbh < breaks[0]:
            return self.linear_interp(0.0, 0.0, breaks[0], values[0], dbh)

        # If we're after the last break we cap the max benefit
        # to the last value
        if dbh > breaks[-1]:
            return values[-1]

        # Determine the interval that we're in
        for i in xrange(1, len(breaks)):
            if dbh >= breaks[i-1] and \
               dbh < breaks[i]:
                return self.linear_interp(breaks[i-1], values[i-1],
                                          breaks[i], values[i], dbh)

    def get_factor_for_trees(self, *args, **kwargs):
        # Since there is legacy code that expects this to return a single value
        # only return the factor, not the converted factor
        factor, _ = self.get_factor_and_conversion_for_trees(*args, **kwargs)
        return factor

    def get_factor_and_conversion_for_trees(self, region, factor,
                                            species_codes_and_dbh):
        breaks, data = self._get_data(region, factor)

        # Group by species, only use first code
        species = {}

        for (scs, dbh) in species_codes_and_dbh:
            if scs not in species:
                species[scs] = []

            species[scs].append(dbh)

        f = 0
        for code in species:
            if code in data:
                f += np.sum(np.interp(species[code], breaks, data[code]))
            else:
                raise Exception('Could not find data for '
                                'factor %s in region %s for species %s' %
                                (factor, region, code))

        if factor in self._factor_conversions:
            converted_factor = f * self._factor_conversions[factor]
        else:
            converted_factor = None

        return f, converted_factor

    def get_energy_conserved(self, region, species_codes_and_dbh):
        """ Get kWHs of energy conserved """
        # 1000s of BTU?
        nat_gas_kbtu, nat_gas_converted =\
            self.get_factor_and_conversion_for_trees(
                region, 'natural_gas', species_codes_and_dbh)

        nat_gas_kwh = nat_gas_kbtu * Benefits.WATTS_PER_BTU

        energy_kwh, energy_converted =\
            self.get_factor_and_conversion_for_trees(
                region, 'electricity', species_codes_and_dbh)

        return (nat_gas_kwh + energy_kwh,
                sum_ignore_none([nat_gas_converted, energy_converted]))

    def get_stormwater_management(self, region, species_codes_and_dbh):
        """ Gallons of stormwater reduced """
        stormwater_cubic_m, stormwater_cubic_m_converted =\
            self.get_factor_and_conversion_for_trees(
                region, 'hydro_interception', species_codes_and_dbh)

        return (stormwater_cubic_m * Benefits.GAL_PER_CUBIC_M,
                stormwater_cubic_m_converted * Benefits.GAL_PER_CUBIC_M
                if stormwater_cubic_m_converted else None)

    def _get_lbs(self, region, species_codes_and_dbh, factor):
        factor_value_kg, converted_factor_value_kg =\
            self.get_factor_and_conversion_for_trees(
                region, factor, species_codes_and_dbh)

        return (factor_value_kg * Benefits.LBS_PER_KG,
                converted_factor_value_kg * Benefits.LBS_PER_KG
                if converted_factor_value_kg else None)

    def get_co2_stats(self, region, species_codes_and_dbh):
        """ lbs per year of co2
        provides:
           sequestered
           avoided
           stored

        and calculates:
           reduced
        """
        get_lbs = partial(self._get_lbs, region, species_codes_and_dbh)
        data = {
            'sequestered': get_lbs('co2_sequestered'),
            'avoided': get_lbs('co2_avoided'),
            'stored': get_lbs('co2_storage')
        }

        data['reduced'] = sum_factor_and_conversion(data['sequestered'],
                                                    data['avoided'])

        return data

    def get_air_quality_stats(self, region, species_code_and_dbh):
        """ lbs per year of various air quality indicators
        All 'annual' indicators (except for ozone, bvoc, and voc) include
        both 'dep' and 'avoidance' factors

        The 'improvement' factor is a synthesis of all of the other
        factors
        """
        get_lbs = partial(self._get_lbs, region, species_code_and_dbh)
        data = {
            'ozone': get_lbs('aq_ozone_dep'),
            'nox': sum_factor_and_conversion(get_lbs('aq_nox_dep'),
                                             get_lbs('aq_nox_avoided')),
            'pm10': sum_factor_and_conversion(get_lbs('aq_pm10_dep'),
                                              get_lbs('aq_pm10_avoided')),
            'sox': sum_factor_and_conversion(get_lbs('aq_sox_dep'),
                                             get_lbs('aq_sox_avoided')),
            'voc': get_lbs('aq_voc_avoided'),
            'bvoc': get_lbs('bvoc')
        }

        data['improvement'] = sum_factor_and_conversion(data['ozone'],
                                                        data['nox'],
                                                        data['pm10'],
                                                        data['sox'],
                                                        data['voc'],
                                                        data['bvoc'])

        return data

# Create baseline benefits
benefits = Benefits()
