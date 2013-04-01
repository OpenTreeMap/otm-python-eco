Python library for calculating eco benefit data for trees
=====

Generally you need a region code, species code, and factor type. You
can also use some convenience functions to get around factor type all
together.

Example
====

    from eco import benefits
    dbh_cm = 311 # Diameter at breast height in centimeters

    regions = benefits.regions
    region = regions.pop() # We're just going to use the first
                           # region for this demo
    factors = benefits.factors_for_region(region)

    species_codes = benefits.lookup_species_code(
                 region, species='Magnolia', genus='x soulangiana')

    # Get the amount of nox avoided:
    nox_avoided = benefits.get_factor_for_tree(
                 region, 'aq_nox_avoided', species_codes, dbh_cm)

    # Get totally energy saved
    kwh_saved = benefits.get_energy_conserved(region, species_codes, dbh_cm)
