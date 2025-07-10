# Utility Scripts

## generate_qa.py

Queries the Databricks catalog for site information based on parameters in the ingest configs to generate question and answer pairs to use for evaluation.

Usage:
```
python generate_qa.py generate --config_dir <config_dir> --configs <list of configs> --site_list_file <file with site list> --output_file <output file>
```

- config_dir is the directory where the configs are stored.
- configs is a comma separated list of config names to use.  They should be JSON files but do not include the .json in the list.  There can be any number of configs and the total number of generated questions is number of configs times number of sites.
- site_list_file is a file with a list of site numbers, one per line.  Should be in src/scripts/assets directory.
- output_file is the file where the results will be output to.  Output will be in .jsonl format.

Configs are JSON files that indicate which subset of fields in the catalog to use as inputs when generating questions.  Having different configs allows us to target different aspects of the data.  There are examples in evaluation/ingest_configs but more can be created.

This script can also be invoked from the VSCode Run and Debug menu under "Python: Generate Q&A".
