import os
from pathlib import Path
import pandas as pd
from pyteomics.mgf import MGF
from tqdm import tqdm

# ========================== #
# --- USER CONFIGURATION --- #
# ========================== #

# 1. Path to your original MGF input file.
MGF_FILE_PATH = r"Y:/Data/goeldnerv97/Research/Spectral Library Building/Applications/MASST_Search/20260416_natural_products/20260520_natural_products_curated_parents_pos.mgf"

# 2. Path to the folder where all your output files were saved.
#    This should be the folder containing all the _datasets.tsv files.
TSV_FOLDER_PATH = r"Y:/Data/goeldnerv97/Research/Spectral Library Building/Applications/MASST_Search/20260416_natural_products/output"

# 3. The "Output Prefix" string you used in jobs.py (WITHOUT the unique identifier part).
#    This is CRITICAL for finding the files correctly.
#    For example, if your jobs.py had `(..., "path/to/output/20260520_")`, this should be "20260520_".
OUTPUT_PREFIX = ""

# 4. Name of the final summary CSV file to be created.
OUTPUT_CSV_PATH = r"Y:/Data/goeldnerv97/Research/Spectral Library Building/Applications/MASST_Search/20260416_natural_products/dataset_summary.csv"


# ========================== #
# ------ SCRIPT LOGIC ------ #
# ========================== #

def compile_dataset_counts(mgf_path, tsv_folder, output_prefix, output_csv):
  """
  Compiles the number of matched datasets for each spectrum in an MGF file.
  """
  results_data = []

  # Ensure paths are handled correctly
  mgf_path = Path(mgf_path)
  tsv_folder = Path(tsv_folder)

  print(f"Reading spectra from: {mgf_path}")
  print(f"Looking for TSV files in: {tsv_folder}")

  # Open and iterate through the MGF file with a progress bar
  with MGF(str(mgf_path)) as mgf_reader:
    for spectrum in tqdm(mgf_reader, desc="Processing MGF entries"):
      # --- 1. Extract info from the MGF spectrum ---
      params = spectrum['params']

      # Get the compound name from the 'NAME' field. Default to 'Unknown' if not present.
      compound_name = params.get('name', 'Unknown')

      # Get the scan number, which is used to identify the output files.
      scan_number = params.get('scans')
      if not scan_number:
        print(f"Skipping spectrum with missing 'SCANS' field.")
        continue

      # Check for SPECTRUMID as well, just like the original script
      spectrum_id = params.get('spectrumid')
      entry_identifier = f"{scan_number}_{spectrum_id}" if spectrum_id else str(
        scan_number)

      # --- 2. Construct the corresponding TSV filename ---
      tsv_filename = f"{output_prefix}_{entry_identifier}_datasets.tsv"
      tsv_path = tsv_folder / tsv_filename

      num_datasets = 0
      # --- 3. Read the TSV and count datasets ---
      if tsv_path.is_file():
        try:
          df = pd.read_csv(tsv_path, sep='\t')
          # The number of datasets is the number of rows in the file.
          num_datasets = len(df)
        except Exception as e:
          print(f"Warning: Could not read file {tsv_path}. Error: {e}")
          num_datasets = -1  # Use -1 to indicate an error
      else:
        # If the file doesn't exist, it means there were 0 matches.
        num_datasets = 0

      # --- 4. Store the result ---
      results_data.append({
        'Compound Name': compound_name,
        'Matched Datasets': num_datasets
      })

  # --- 5. Create and save the final summary CSV ---
  if not results_data:
    print("No spectra processed. Exiting.")
    return

  final_df = pd.DataFrame(results_data)
  final_df.to_csv(output_csv, index=False)

  print("\n--- Compilation Complete! ---")
  print(f"Successfully created summary file at: {output_csv}")
  print(f"Total entries processed: {len(final_df)}")


if __name__ == "__main__":
  compile_dataset_counts(MGF_FILE_PATH, TSV_FOLDER_PATH, OUTPUT_PREFIX,
                         OUTPUT_CSV_PATH)
