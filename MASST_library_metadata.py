import os
from pathlib import Path
import pandas as pd
from pyteomics.mgf import MGF
from tqdm import tqdm
from collections import defaultdict

# ========================== #
# --- USER CONFIGURATION --- #
# ========================== #

# 1. Path to your original MGF input file.
MGF_FILE_PATH = r"Y:/Data/goeldnerv97/Research/Spectral Library Building/Applications/MASST_Search/20260416_natural_products/20260520_natural_products_curated_parents_pos.mgf"

# 2. Path to the folder where all your output files were saved.
OUTPUT_FOLDER_PATH = r"Y:/Data/goeldnerv97/Research/Spectral Library Building/Applications/MASST_Search/20260416_natural_products/output"

# 3. The "Output Prefix" string you used in jobs.py.
OUTPUT_PREFIX = ""

# 4. Name of the final summary CSV file to be created.
OUTPUT_CSV_PATH = r"Y:/Data/goeldnerv97/Research/Spectral Library Building/Applications/MASST_Search/20260416_natural_products/dataset_summary_unique_compounds.csv"

# 5. Precision for rounding the exact mass to group similar compounds.
MASS_PRECISION = 3


# ========================== #
# ------ SCRIPT LOGIC ------ #
# ========================== #

def compile_unique_dataset_counts(mgf_path, output_folder, output_prefix,
    output_csv):
  """
  Groups compounds, counts unique datasets and library matches, and lists HTML files.
  """
  # Dictionaries to group data by unique compound
  grouped_datasets = defaultdict(list)
  grouped_html_files = defaultdict(list)
  grouped_library_matches = defaultdict(list)

  # Set to store all unique compounds found in the MGF
  all_unique_compounds = set()

  mgf_path = Path(mgf_path)
  output_folder = Path(output_folder)

  print(f"Reading spectra from: {mgf_path}")
  print(f"Looking for output files in: {output_folder}")
  print("--- Phase 1: Identifying all compounds and collecting their data ---")

  with MGF(str(mgf_path)) as mgf_reader:
    for spectrum in tqdm(mgf_reader, desc="Processing MGF entries"):
      params = spectrum['params']

      # --- 1. Create a unique key for the compound ---
      compound_name = params.get('name', 'Unknown')
      pepmass_tuple = params.get('pepmass')
      if not pepmass_tuple:
        continue

      exact_mass = float(pepmass_tuple[0])
      rounded_mass = round(exact_mass, MASS_PRECISION)
      compound_key = (compound_name, rounded_mass)
      all_unique_compounds.add(compound_key)

      # --- 2. Construct the filenames for this specific MGF entry ---
      scan_number = params.get('scans')
      if not scan_number:
        continue

      spectrum_id = params.get('spectrumid')
      entry_identifier = f"{scan_number}_{spectrum_id}" if spectrum_id else str(
        scan_number)

      base_filename = f"{output_prefix}_{entry_identifier}"

      # --- 3. Collect data from all relevant files ---

      # Add HTML filename to its group
      html_filename = f"{base_filename}_combined.html"
      grouped_html_files[compound_key].append(html_filename)

      # Add dataset IDs to their group
      tsv_path = output_folder / f"{base_filename}_datasets.tsv"
      if tsv_path.is_file():
        try:
          df = pd.read_csv(tsv_path, sep='\t')
          if 'Dataset' in df.columns:
            grouped_datasets[compound_key].extend(df['Dataset'].tolist())
        except Exception as e:
          print(f"\nWarning: Could not read file {tsv_path}. Error: {e}")

      # Add library match IDs to their group
      library_path = output_folder / f"{base_filename}_library.tsv"
      if library_path.is_file():
        try:
          df_lib = pd.read_csv(library_path, sep='\t')
          if 'USI' in df_lib.columns:
            grouped_library_matches[compound_key].extend(
              df_lib['USI'].tolist())
        except Exception as e:
          print(f"\nWarning: Could not read file {library_path}. Error: {e}")

  if not all_unique_compounds:
    print("No compounds found in MGF file. Exiting.")
    return

  print("\n--- Phase 2: Aggregating results for ALL unique compounds ---")

  final_results = []
  for name, mass in tqdm(sorted(list(all_unique_compounds)),
                         desc="Aggregating groups"):
    compound_key = (name, mass)

    # Get the unique dataset count
    unique_dataset_count = len(set(grouped_datasets.get(compound_key, [])))

    # **NEW**: Get the unique library match count
    unique_library_count = len(
      set(grouped_library_matches.get(compound_key, [])))

    # Get the list of all associated HTML files
    html_files_string = ", ".join(grouped_html_files.get(compound_key, []))

    final_results.append({
      'Compound Name': name,
      'Exact Mass': mass,
      'Unique Matched Datasets': unique_dataset_count,
      'Unique Library Matches': unique_library_count,  # The new column
      'Associated HTML Files': html_files_string
    })

  # --- 6. Create and save the final summary CSV ---
  final_df = pd.DataFrame(final_results)
  final_df.sort_values(by=['Compound Name', 'Exact Mass'], inplace=True)

  final_df.to_csv(output_csv, index=False)

  print("\n--- Compilation Complete! ---")
  print(f"Successfully created summary file at: {output_csv}")
  print(f"Total unique compounds reported: {len(final_df)}")


if __name__ == "__main__":
  compile_unique_dataset_counts(MGF_FILE_PATH, OUTPUT_FOLDER_PATH,
                                OUTPUT_PREFIX, OUTPUT_CSV_PATH)