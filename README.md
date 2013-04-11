Python library for calculating eco benefit data for trees
=====

Generally you need a region code, species code, and factor type. You
can also use some convenience functions to get around factor type all
together.

Install
====

eco.py isn't up on pypi yet so get it with git:

```bash
pip install git+git://github.com/azavea/eco.py.git
```

Example
====

```python
from eco import benefits dbh_cm = 311 # Diameter at breast height in
                                      # centimeters

regions = benefits.regions
region = 'NoEastXXX'

factors = benefits.factors_for_region(region)

species_codes = benefits.lookup_species_code(region,
                       genus='Cedrus', species='atlantica')

# Get the amount of nox avoided:
nox_avoided =
     benefits.get_factor_for_tree(region,
                  'aq_nox_avoided', species_codes, dbh_cm)

# Get totally energy saved
kwh_saved =
    benefits.get_energy_conserved(region, species_codes, dbh_cm)
```
