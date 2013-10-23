from unittest import TestCase, main

from .context import benefits, Benefits


class TestEco(TestCase):

    def test_simple_interp(self):
        self.assertEqual(benefits.linear_interp(1, 4, 3, 6, 2), 5)

    def test_regions(self):
        regions = benefits.regions
        self.assertIn('NoEastXXX', regions)
        self.assertTrue(len(regions) > 1)

    def test_factors(self):
        regions = benefits.regions
        factors_set = {frozenset(benefits.factors_for_region(region))
                       for region in regions}

        factors_we_use = set(['electricity',
                              'natural_gas',
                              'hydro_interception',
                              'co2_sequestered',
                              'co2_avoided',
                              'co2_storage',
                              'aq_ozone_dep',
                              'aq_nox_dep',
                              'aq_nox_avoided',
                              'aq_pm10_dep',
                              'aq_pm10_avoided',
                              'aq_sox_dep',
                              'aq_sox_avoided',
                              'aq_voc_avoided',
                              'bvoc'])

        self.assertEqual(len(factors_set), 1)
        factors = factors_set.pop()

        self.assertTrue(factors_we_use.issubset(factors))

    def test_species_lookup(self):
        # Lookup a species that doesn't exist in any region
        for region in benefits.regions:
            self.assertIsNone(benefits.lookup_species_code(
                region, genus='Ecoputius'))

        expected = {
            'PiedmtCLT': 'BDS OTHER',
            'NoEastXXX': 'BDS OTHER',
            'CaNCCoJBK': 'BDS OTHER',
            'InlValMOD': 'MAGR',
            'SoCalCSMA': 'BDS OTHER',
            'GulfCoCHS': 'BDS OTHER',
            'CenFlaXXX': 'BDS OTHER',
            'PacfNWLOG': 'BDS OTHER',
            'InlEmpCLM': 'MAGR',
        }

        for region in benefits.regions:
            codes = benefits.lookup_species_code(
                region, genus='Magnolia', species='x soulangiana')

            if region in expected:
                self.assertEqual(expected[region], codes)
            else:
                self.assertIsNone(codes)

    def test_get_factor_for_trees(self):
        region = 'NoEastXXX'
        species_codes = benefits.lookup_species_code(
            region, 'cedrus', 'atlantica')

        bvoc = benefits.get_factor_for_trees(region, 'bvoc',
                                             [(species_codes, 1630.0)])
        self.assertEqual(int(bvoc * 100), -7)

    def test_get_factor_and_conversion_for_trees(self):
        region = 'NoEastXXX'
        species_codes = benefits.lookup_species_code(
            region, 'cedrus', 'atlantica')

        bvoc = benefits.get_factor_and_conversion_for_trees(
            region, 'bvoc', [(species_codes, 1630.0)])
        self.assertEqual(len(bvoc), 2)
        self.assertEqual(int(bvoc[0] * 100), -7)
        self.assertEqual(bvoc[1], None)

    def test_benefit_calc_wo_conversions(self):
        # Since there isn't really a canonical benefits
        # library to test against, we're just going to
        # use a couple of existing OTM instances
        #
        # These test are pretty data dependent but the
        # whole purpose of the library is to provide access to
        # that data

        # Using NoEastXXX
        region = 'NoEastXXX'
        species_codes = benefits.lookup_species_code(
            region, 'cedrus', 'atlantica')

        kwh = benefits.get_energy_conserved(region, [(species_codes, 1630.0)])
        self.assertEqual(int(kwh[0]), 1896)

        gal = benefits.get_stormwater_management(region,
                                                 [(species_codes, 1630.0)])
        self.assertEqual(int(gal[0]), 3185)

        co2 = benefits.get_co2_stats(region, [(species_codes, 1630.0)])
        self.assertEqual(int(co2['reduced'][0]), 563)

        aq = benefits.get_air_quality_stats(region, [(species_codes, 1630.0)])
        self.assertEqual(int(aq['improvement'][0]*10), 63)

        # The default Benefits instance there should have no conversions
        self.assertEqual(kwh[1], None)
        self.assertEqual(gal[1], None)
        self.assertEqual(co2['reduced'][1], None)
        self.assertEqual(aq['improvement'][1], None)

    def test_benefit_calc_w_conversions(self):
        # Since there isn't really a canonical benefits
        # library to test against, we're just going to
        # use a couple of existing OTM instances
        #
        # These test are pretty data dependent but the
        # whole purpose of the library is to provide access to
        # that data

        # Using NoEastXXX
        region = 'NoEastXXX'
        benefits = Benefits({
            'electricity': 2,
            'natural_gas': 2 * Benefits.WATTS_PER_BTU,
            'hydro_interception': 2,
            'co2_sequestered': 2,
            'co2_avoided': 2,
            'co2_storage': 2,
            'aq_ozone_dep': 2,
            'aq_nox_dep': 2,
            'aq_nox_avoided': 2,
            'aq_pm10_dep': 2,
            'aq_pm10_avoided': 2,
            'aq_sox_dep': 2,
            'aq_sox_avoided': 2,
            'aq_voc_avoided': 2,
            'bvoc': 2
        })
        species_codes = benefits.lookup_species_code(
            region, 'cedrus', 'atlantica')

        kwh = benefits.get_energy_conserved(region, [(species_codes, 1630.0)])
        self.assertEqual(int(kwh[0]), 1896)
        self.assertEqual(int(kwh[1]), 3793)

        gal = benefits.get_stormwater_management(region,
                                                 [(species_codes, 1630.0)])
        self.assertEqual(int(gal[0]), 3185)
        self.assertEqual(int(gal[1]), 6371)

        co2 = benefits.get_co2_stats(region, [(species_codes, 1630.0)])
        self.assertEqual(int(co2['reduced'][0]), 563)
        self.assertEqual(int(co2['reduced'][1]), 1126)

        aq = benefits.get_air_quality_stats(region, [(species_codes, 1630.0)])
        self.assertEqual(int(aq['improvement'][0]*10), 63)
        self.assertEqual(int(aq['improvement'][1]*10), 127)


if __name__ == '__main__':
    main()
