# -*- coding: utf-8 -*-
"""
Summarizes MASST results by mapping them against the Pan-ReDu metadata database.

This script processes MASST search results by first collecting all unique matched
public spectra (from '_matches.tsv' files). It then reduces these matches to unique
datafiles and looks up their 'SampleType' in a comprehensive Pan-ReDu database file.

The final output is a CSV summarizing, for each compound, the total number of unique
datafiles it matched and a count for each sample type of interest (e.g., 'plant',
'animal', 'bacteria').

To use this script, edit the variables in the "USER CONFIGURATION" section below.
"""

from collections import defaultdict, Counter
from pathlib import Path
import sys
import pandas as pd
from pyteomics.mgf import MGF
from tqdm import tqdm

# ========================================================================= #
# ---                          USER CONFIGURATION                         --- #
# ---                  EDIT THE VARIABLES IN THIS SECTION                 --- #
# ========================================================================= #

# 1. Set the main project directory.
PROJECT_DIRECTORY = Path(
  r"Y:\Data\goeldnerv97\Research\Spectral Library Building\Applications\MASST_Search\20260416_Contaminants")

# 2. Filename of the MGF input file, located inside the PROJECT_DIRECTORY.
MGF_FILENAME = "20250917+18_EC_library_merged_neg_20260605.mgf"

# 3. Name of the sub-directory containing the MASST result files.
OUTPUT_SUBDIR = "20260605_output"

# 4. The full, absolute path to the comprehensive Pan-ReDu database file.
#    This file can be located anywhere on your system.
PAN_REDU_DB_PATH = Path(
  r"Y:\Data\goeldnerv97\Research\Spectral Library Building\Applications\MASST_Search\ReDu\all_sampleinformation.tsv")

# 5. The "Output Prefix" used when running the MASST search.
OUTPUT_PREFIX = "neg"

# 6. Desired filename for the final summary CSV file.
SUMMARY_FILENAME = "Pan_ReDU_metadata_summary_neg.csv"

# 8. List of sample types to create columns for in the final output.
SAMPLE_TYPES_OF_INTEREST = [
  'algae', 'animal', 'archaea', 'bacteria', 'beverage', 'blank_QC',
  'blank_analysis', 'blank_culturemedia', 'blank_extraction',
  'built_environment', 'combinatorial_synthesis', 'culture_bacterial',
  'culture_fungal', 'culture_mammalian', 'culture_multiplespecies',
  'environmental', 'food', 'fungi', 'inanimate_object', 'microalgae',
  'molecular_standards', 'plant', 'pool_QC', 'reference material', 'Unknown'
]

# ========================================================================= #
# ---         SCRIPT LOGIC (No modifications needed below here)         --- #
# ========================================================================= #

# Automatically construct full paths from the user-defined variables
MGF_FILE_PATH = PROJECT_DIRECTORY / MGF_FILENAME
OUTPUT_FOLDER_PATH = PROJECT_DIRECTORY / OUTPUT_SUBDIR
OUTPUT_CSV_PATH = PROJECT_DIRECTORY / SUMMARY_FILENAME


def create_metadata_lookup(db_path: Path) -> pd.Series:
  """Loads the Pan-ReDu database and creates an efficient lookup map."""
  print(f"Loading Pan-ReDu database from: {db_path}...")
  if not db_path.is_file():
    print(f"FATAL ERROR: Pan-ReDu database file not found at '{db_path}'")
    sys.exit(1)
  try:
    # Load only necessary columns to conserve memory
    df_db = pd.read_csv(db_path, sep='\t', usecols=['USI', 'SampleType'],
                        low_memory=False)
    # Create a mapping from USI to SampleType for fast lookups
    lookup_map = df_db.set_index('USI')['SampleType']
    print("Database loaded and lookup map created successfully.")
    return lookup_map
  except Exception as e:
    print(
      f"FATAL ERROR: Could not load or process the Pan-ReDu database. Error: {e}")
    sys.exit(1)


def process_usi_to_datafile(usi: str) -> str:
  """Reduces a full USI (e.g., mzspec:PXD000001:file.mzML:scan:123) to its datafile component."""
  parts = usi.split(':')
  # A datafile USI typically does not have 'scan' or 'index' as the second-to-last part
  if len(parts) > 3 and parts[-2] in ['scan', 'index']:
    return ':'.join(parts[:-2])
  return usi


def compile_metadata_from_matches(mgf_path, output_folder, db_lookup,
    output_prefix, output_csv):
  """Main function to aggregate unique USIs, retrieve metadata, and count sample types."""
  grouped_usis = defaultdict(set)
  all_unique_compounds = set()

  print("\n--- Phase 1: Collecting unique USIs for all compounds ---")
  with MGF(str(mgf_path)) as mgf_reader:
    for spectrum in tqdm(mgf_reader, desc="Processing MGF entries"):
      params = spectrum['params']
      compound_name = params.get('name', 'Unknown')
      pepmass_tuple = params.get('pepmass')
      scan_number = params.get('scans')
      if not pepmass_tuple or not scan_number:
        continue

      formula = params.get('formula')
      compound_key = (compound_name, formula)
      all_unique_compounds.add(compound_key)

      spectrum_id = params.get('spectrumid')
      entry_identifier = f"{scan_number}_{spectrum_id}" if spectrum_id else str(
        scan_number)
      base_filename = f"{output_prefix}_{entry_identifier}"

      # This script specifically uses the '_matches.tsv' file
      matches_path = output_folder / f"{base_filename}_matches.tsv"

      if matches_path.is_file():
        try:
          df_matches = pd.read_csv(matches_path, sep='\t')
          if 'USI' in df_matches.columns:
            grouped_usis[compound_key].update(df_matches['USI'].tolist())
        except Exception as e:
          print(f"\nWarning: Could not read file {matches_path}. Error: {e}")

  print("\n--- Phase 2: Aggregating metadata for unique compounds ---")
  final_results = []
  for name, formula in tqdm(sorted(list(all_unique_compounds)),
                         desc="Aggregating metadata"):
    compound_key = (name, formula)
    raw_usis = grouped_usis.get(compound_key, set())
    unique_datafiles = {process_usi_to_datafile(usi) for usi in raw_usis}

    # Count the occurrences of each sample type for the unique datafiles
    sample_type_counts = Counter(
        db_lookup.get(datafile, 'Unknown') for datafile in unique_datafiles
    )

    # Initialize a dictionary for the row with base info and all sample types set to 0
    row_data = {
      'Compound Name': name,
      'Molecular Formula': formula,
      'Total Unique Datafiles': len(unique_datafiles)
    }
    row_data.update({stype: 0 for stype in SAMPLE_TYPES_OF_INTEREST})

    # Update the row with the actual counts found for this compound
    row_data.update(sample_type_counts)
    final_results.append(row_data)

  print("\n--- Phase 3: Creating final summary table ---")
  final_df = pd.DataFrame(final_results)

  # Reorder columns for clarity: base info first, then sorted sample types
  first_cols = ['Compound Name', 'Molecular Formula', 'Total Unique Datafiles']
  # Ensure all desired sample type columns are present, even if none were found
  all_cols = first_cols + sorted(SAMPLE_TYPES_OF_INTEREST)
  final_df = final_df[all_cols]

  final_df.sort_values(by=['Compound Name', 'Molecular Formula'], inplace=True)
  final_df.to_csv(output_csv, index=False)

  print(f"\n--- Compilation Complete! ---")
  print(f"Successfully created summary file at: {output_csv}")


if __name__ == "__main__":
  db_map = create_metadata_lookup(PAN_REDU_DB_PATH)
  compile_metadata_from_matches(
      MGF_FILE_PATH,
      OUTPUT_FOLDER_PATH,
      db_map,
      OUTPUT_PREFIX,
      OUTPUT_CSV_PATH,
  )