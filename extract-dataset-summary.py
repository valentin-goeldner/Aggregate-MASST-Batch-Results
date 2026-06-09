"""
Summarizes MASST search dataset hits from a results folder.

This script scans a MASST output directory for all '_datasets.tsv' files.
It counts the number of input spectra (referred to as ETPs in the prompt)
that were found within each unique public dataset.

It includes an OPTIONAL filter to analyze only results corresponding to
spectra named with '_ETP_' in the input MGF file.

The final output is a CSV file containing two columns:
1. 'Dataset': The unique dataset identifier (e.g., a MassIVE ID).
2. 'Annotated ETPs Count': The number of input spectra that had a match
   in that specific dataset.

To use this script, edit the variables in the "USER CONFIGURATION" section
below, then run the file directly from your IDE or terminal.
"""

from collections import Counter
from pathlib import Path
import sys
import pandas as pd
from pyteomics.mgf import MGF
from tqdm import tqdm

# ========================================================================= #
# ---                          USER CONFIGURATION                         --- #
# ---                  EDIT THE VARIABLES IN THIS SECTION                 --- #
# ========================================================================= #

# 1. Set the main project directory. All other paths will be built from this.
#    Use an 'r' before the string (e.g., r"C:\...") to handle Windows paths correctly.
PROJECT_DIRECTORY = Path(r"Y:\Data\goeldnerv97\Research\Spectral Library Building\Applications\MASST_Search\20260416_Contaminants")

# 2. Name of the sub-directory containing the MASST result files.
#    This is where the script will look for '_datasets.tsv' files.
OUTPUT_SUBDIR = "20260605_output"

# 3. Desired filename for the final summary CSV file. This file will be saved
#    in your PROJECT_DIRECTORY.
SUMMARY_FILENAME = "20260605_masst_dataset_summary_ETP_only_pos.csv"

# 4. --- OPTIONAL FILTER ---
#    Set to True to analyze ONLY spectra named with '_ETP_' in the MGF file.
#    If set to True, you MUST also provide the MGF_FILENAME and OUTPUT_PREFIX below.
FILTER_FOR_ETP_ONLY = True

# 5. Filename of the MGF input file (REQUIRED if FILTER_FOR_ETP_ONLY is True).
MGF_FILENAME = "20250917+18_EC_library_merged_pos_20260605.mgf"

# 6. The "Output Prefix" used for the MASST search (REQUIRED if FILTER_FOR_ETP_ONLY is True).
OUTPUT_PREFIX = "pos"


# ========================================================================= #
# ---         SCRIPT LOGIC (No modifications needed below here)         --- #
# ========================================================================= #

def get_etp_filenames(mgf_path: Path, output_prefix: str) -> set:
    """Reads an MGF file and returns a set of expected _datasets.tsv filenames
    for spectra containing '_ETP_' in their name."""
    if not mgf_path.is_file():
        print(f"Error: MGF file for filtering not found at '{mgf_path}'")
        sys.exit(1)

    print(f"Reading MGF to identify ETP spectra: {mgf_path.name}")
    etp_tsv_filenames = set()

    with MGF(str(mgf_path)) as mgf_reader:
        for spectrum in tqdm(mgf_reader, desc="Scanning MGF for ETPs"):
            params = spectrum['params']
            compound_name = params.get('name', '')

            # Check if the compound name indicates it's an ETP
            if '_ETP_' in compound_name:
                scan_number = params.get('scans')
                if not scan_number:
                    continue  # Skip if essential info is missing

                spectrum_id = params.get('spectrumid')
                entry_identifier = f"{scan_number}_{spectrum_id}" if spectrum_id else str(scan_number)
                base_filename = f"{output_prefix}_{entry_identifier}_datasets.tsv"
                etp_tsv_filenames.add(base_filename)

    print(f"Found {len(etp_tsv_filenames)} spectra matching the ETP filter.")
    return etp_tsv_filenames


def summarize_dataset_hits(output_folder: Path, output_csv: Path, filter_etp: bool,
                           mgf_path: Path = None, output_prefix: str = None):
    """
    Finds all _datasets.tsv files, counts occurrences of each unique dataset,
    and saves the results to a summary CSV. Optionally filters for ETPs.
    """
    # --- Initial Validation ---
    if not output_folder.is_dir():
        print(f"Error: Output directory not found at '{output_folder}'")
        sys.exit(1)

    if filter_etp and (mgf_path is None or output_prefix is None):
        print("Error: To filter for ETPs, MGF_FILENAME and OUTPUT_PREFIX must be provided.")
        sys.exit(1)

    print(f"Scanning for '_datasets.tsv' files in: {output_folder}")

    # --- File Discovery and Filtering ---
    # First, find all potentially relevant files
    all_tsv_files = list(output_folder.glob('*_datasets.tsv'))

    if not all_tsv_files:
        print("Error: No '_datasets.tsv' files found in the specified directory. Exiting.")
        return

    # If filtering is enabled, determine the subset of files to process
    if filter_etp:
        etp_filenames = get_etp_filenames(mgf_path, output_prefix)
        files_to_process = [
            f for f in all_tsv_files if f.name in etp_filenames
        ]
        if not files_to_process:
            print("Warning: Filtering for ETPs resulted in 0 files to process. Exiting.")
            return
    else:
        files_to_process = all_tsv_files

    print(f"Found {len(files_to_process)} files to process after applying filters.")

    # --- Data Processing ---
    # Use collections.Counter for an efficient way to count hashable objects.
    dataset_counter = Counter()

    for file_path in tqdm(files_to_process, desc="Analyzing dataset files"):
        try:
            df = pd.read_csv(file_path, sep='\t')
            if 'Dataset' in df.columns:
                unique_datasets_in_file = df['Dataset'].unique()
                dataset_counter.update(unique_datasets_in_file)
        except pd.errors.EmptyDataError:
            pass # Silently skip empty files, as they are expected for no-hit searches
        except Exception as e:
            print(f"\nWarning: Could not process file {file_path.name}. Error: {e}")

    # --- Aggregating and Saving Results ---
    if not dataset_counter:
        print("\nWarning: No dataset matches were found. Output file will not be created.")
        return

    print("\nAggregation complete. Preparing summary file...")

    summary_data = [{'Dataset': name, 'Annotated ETPs Count': count}
                    for name, count in dataset_counter.items()]

    final_df = pd.DataFrame(summary_data)
    final_df.sort_values(
        by=['Annotated ETPs Count', 'Dataset'],
        ascending=[False, True],
        inplace=True
    )
    final_df.to_csv(output_csv, index=False)

    print("\n--- Summary Complete! ---")
    print(f"Successfully created dataset summary at: {output_csv}")
    print(f"Total unique public datasets found: {len(final_df)}")


if __name__ == "__main__":
    # Automatically construct full paths from the user-defined variables
    OUTPUT_FOLDER_PATH = PROJECT_DIRECTORY / OUTPUT_SUBDIR
    OUTPUT_CSV_PATH = PROJECT_DIRECTORY / SUMMARY_FILENAME
    MGF_FILE_PATH = PROJECT_DIRECTORY / MGF_FILENAME if MGF_FILENAME else None

    # Run the main function with all necessary parameters
    summarize_dataset_hits(
        output_folder=OUTPUT_FOLDER_PATH,
        output_csv=OUTPUT_CSV_PATH,
        filter_etp=FILTER_FOR_ETP_ONLY,
        mgf_path=MGF_FILE_PATH,
        output_prefix=OUTPUT_PREFIX
    )