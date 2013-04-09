from unittest import TestCase, main

from .context import benefits

class TestEco(TestCase):

    def test_simple_interp(self):
        self.assertEqual(benefits.linear_interp(1,4,3,6,2), 5)

    def test_regions(self):
        regions = benefits.regions
        self.assertIn('NoEastXXX', regions)
        self.assertTrue(len(regions) > 1)

    def test_factors(self):
        regions = benefits.regions
        factors_set = { frozenset(benefits.factors_for_region(region))
                        for region in regions }

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
                region, species='Ecoputius'))

        expected = {
            'PiedmtCLT': ('MASO', 'BDS OTHER'),
            'NoEastXXX': ('MASO', 'BDS OTHER'),
            'CaNCCoJBK': ('MASO', 'BDS OTHER'),
            'InlValMOD': ('MASO', 'MAGR'),
            'SoCalCSMA': ('MASO', 'BDS OTHER'),
            'GulfCoCHS': ('MASO', 'BDS OTHER'),
            'CenFlaXXX': ('MASO', 'BDS OTHER'),
            'PacfNWLOG': ('MASO', 'BDS OTHER'),
            'InlEmpCLM': ('MASO', 'MAGR'),
        }

        for region in benefits.regions:
            codes = benefits.lookup_species_code(
                region, species='Magnolia', genus='x soulangiana')

            if region in expected:
                self.assertEqual(expected[region], codes)
            else:
                self.assertIsNone(codes)

    def test_benefit_calc(self):
        # Since there isn't really a canonical benefits
        # library to test against, we're just going to
        # use a couple of exsiting OTM instances
        #
        # These test are pretty data dependent but the
        # whole purpose of the library is to provide access to
        # that data

        # Using NoEastXXX
        region = 'NoEastXXX'
        species_codes = benefits.lookup_species_code(
            region, 'cedrus', 'atlantica')

        kwh = benefits.get_energy_conserved(region, species_codes, 1630.0)
        self.assertEqual(int(kwh), 1896)

        gal = benefits.get_stormwater_management(region, species_codes, 1630.0)
        self.assertEqual(int(gal), 3185)

        co2 = benefits.get_co2_stats(region, species_codes, 1630.0)
        self.assertEqual(int(co2['reduced']), 563)

        aq = benefits.get_air_quality_stats(region, species_codes, 1630.0)
        self.assertEqual(int(aq['improvement']*10), 63)


if __name__ == '__main__':
    main()
