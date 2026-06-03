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
#    4 decimal places is usually sufficient for high-resolution data.
MASS_PRECISION = 3

# ========================== #
# ------ SCRIPT LOGIC ------ #
# ========================== #

def compile_unique_dataset_counts(mgf_path, output_folder, output_prefix,
    output_csv):
  """
  Groups compounds by name and exact mass, counts unique matched datasets,
  and lists all associated _combined.html files. Includes all compounds
  from the MGF, even those with zero matches.
  """
  # Dictionary to group dataset IDs by unique compound
  grouped_datasets = defaultdict(list)
  # **NEW**: Dictionary to group HTML filenames by unique compound
  grouped_html_files = defaultdict(list)
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
      tsv_path = output_folder / f"{base_filename}_datasets.tsv"
      html_filename = f"{base_filename}_combined.html"

      # --- 3. Add the HTML filename to its group ---
      grouped_html_files[compound_key].append(html_filename)

      # --- 4. If a match file exists, add its datasets to the group ---
      if tsv_path.is_file():
        try:
          df = pd.read_csv(tsv_path, sep='\t')
          if 'Dataset' in df.columns:
            datasets_for_this_entry = df['Dataset'].tolist()
            grouped_datasets[compound_key].extend(datasets_for_this_entry)
        except Exception as e:
          print(f"\nWarning: Could not read file {tsv_path}. Error: {e}")

  if not all_unique_compounds:
    print("No compounds found in MGF file. Exiting.")
    return

  print("\n--- Phase 2: Aggregating results for ALL unique compounds ---")

  final_results = []
  # --- 5. Iterate over ALL unique compounds to build the final table ---
  for name, mass in tqdm(sorted(list(all_unique_compounds)),
                         desc="Aggregating groups"):
    compound_key = (name, mass)

    # Get the unique dataset count
    all_datasets_for_compound = grouped_datasets.get(compound_key, [])
    unique_count = len(set(all_datasets_for_compound))

    # **NEW**: Get the list of all associated HTML files
    html_files_list = grouped_html_files.get(compound_key, [])
    # Join them into a single string for the CSV cell
    html_files_string = ", ".join(html_files_list)

    final_results.append({
      'Compound Name': name,
      'Exact Mass': mass,
      'Unique Matched Datasets': unique_count,
      'Associated HTML Files': html_files_string  # The new column
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
