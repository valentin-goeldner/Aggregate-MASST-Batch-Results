"""
Aggregates MASST search results into a single summary file.

This script processes the output of a MASST search by grouping results for
unique compounds (defined by name and precursor mass). It computes summary
statistics, such as the number of unique public datasets and library spectra
matched.

To use this script, edit the variables in the "USER CONFIGURATION" section
below, then run the file directly from your IDE or terminal.
"""

from collections import defaultdict
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
PROJECT_DIRECTORY = Path(r"Y:\Data\goeldnerv97\Research\Spectral Library Building\Applications\MASST_Search\20260416_natural_products")

# 2. Filename of the MGF input file. This file must be located inside the
#    PROJECT_DIRECTORY defined above.
MGF_FILENAME = "20260605_natural_products_curated_parents_pos.mgf"

# 3. Name of the sub-directory containing the MASST result files.
#    This folder should also be inside your PROJECT_DIRECTORY.
OUTPUT_SUBDIR = "20260605_output"

# 4. The "Output Prefix" used when running the MASST search (e.g., "pos", "neg").
#    This prefix is part of every MASST output filename.
OUTPUT_PREFIX = "np"

# 5. Desired filename for the final summary CSV file. This file will be saved
#    in your PROJECT_DIRECTORY.
SUMMARY_FILENAME = ("20260605_dataset_summary_unique_compounds_np.csv")

# ========================================================================= #
# ---         SCRIPT LOGIC (No modifications needed below here)         --- #
# ========================================================================= #

# Automatically construct full paths from the user-defined variables
MGF_FILE_PATH = PROJECT_DIRECTORY / MGF_FILENAME
OUTPUT_FOLDER_PATH = PROJECT_DIRECTORY / OUTPUT_SUBDIR
OUTPUT_CSV_PATH = PROJECT_DIRECTORY / SUMMARY_FILENAME


def compile_masst_results(mgf_path: Path, output_folder: Path, output_prefix: str,
                          output_csv: Path):
    """
    Aggregates MASST search results for all spectra in an MGF file.
    """
    # --- Initial Validation ---
    if not mgf_path.is_file():
        print(f"Error: MGF file not found at '{mgf_path}'")
        sys.exit(1)
    if not output_folder.is_dir():
        print(f"Error: Output directory not found at '{output_folder}'")
        sys.exit(1)

    # Dictionaries to aggregate data, keyed by a unique compound identifier.
    grouped_datasets = defaultdict(list)
    grouped_html_files = defaultdict(list)
    grouped_library_matches = defaultdict(list)
    all_unique_compounds = set()

    print(f"Reading spectra from: {mgf_path}")
    print(f"Looking for output files in: {output_folder}")
    print("--- Phase 1: Collecting data from MGF and MASST outputs ---")

    with MGF(str(mgf_path)) as mgf_reader:
        for spectrum in tqdm(mgf_reader, desc="Processing MGF entries"):
            params = spectrum['params']
            compound_name = params.get('name', 'Unknown')
            pepmass_tuple = params.get('pepmass')
            scan_number = params.get('scans')

            if not pepmass_tuple or not scan_number:
                continue

            # Define a unique identifier for the compound based on its name and formula
            formula = params.get('formula')
            compound_key = (compound_name, formula)
            all_unique_compounds.add(compound_key)

            # Construct the base filename for this spectrum's output files
            spectrum_id = params.get('spectrumid')
            entry_identifier = f"{scan_number}_{spectrum_id}" if spectrum_id else str(scan_number)
            base_filename = f"{output_prefix}_{entry_identifier}"

            grouped_html_files[compound_key].append(f"{base_filename}_combined.html")

            # Parse the _datasets.tsv file for public dataset matches
            tsv_path = output_folder / f"{base_filename}_datasets.tsv"
            if tsv_path.is_file():
                try:
                    df = pd.read_csv(tsv_path, sep='\t')
                    if 'Dataset' in df.columns:
                        grouped_datasets[compound_key].extend(df['Dataset'].tolist())
                except Exception as e:
                    print(f"\nWarning: Could not process file {tsv_path}. Error: {e}")

            # Parse the _library.tsv file for library spectra matches
            library_path = output_folder / f"{base_filename}_library.tsv"
            if library_path.is_file():
                try:
                    df_lib = pd.read_csv(library_path, sep='\t')
                    if 'USI' in df_lib.columns:
                        grouped_library_matches[compound_key].extend(df_lib['USI'].tolist())
                except Exception as e:
                    print(f"\nWarning: Could not process file {library_path}. Error: {e}")

    if not all_unique_compounds:
        print("Error: No valid compounds found in the MGF file. Exiting.")
        return

    print("\n--- Phase 2: Aggregating results and generating summary ---")

    final_results = []
    # Iterate through a sorted list of compounds for reproducible output
    for name, formula in tqdm(sorted(list(all_unique_compounds)), desc="Aggregating results"):
        compound_key = (name, formula)

        # Calculate unique counts by converting lists to sets
        unique_dataset_count = len(set(grouped_datasets.get(compound_key, [])))
        unique_library_count = len(set(grouped_library_matches.get(compound_key, [])))
        html_files_string = ", ".join(sorted(set(grouped_html_files.get(compound_key, []))))

        final_results.append({
            'Compound Name': name,
            'Molecular Formula': formula,
            'Unique Matched Datasets': unique_dataset_count,
            'Unique Library Matches': unique_library_count,
            'Associated HTML Files': html_files_string
        })

    if not final_results:
        print("Warning: No results were aggregated. The output file will be empty.")
        return

    # Create and save the final summary DataFrame
    final_df = pd.DataFrame(final_results)
    final_df.sort_values(by=['Compound Name', 'Molecular Formula'], inplace=True)
    final_df.to_csv(output_csv, index=False)

    print("\n--- Compilation Complete! ---")
    print(f"Successfully created summary file at: {output_csv}")
    print(f"Total unique compounds reported: {len(final_df)}")


if __name__ == "__main__":
    # The script calls the main function using the variables defined
    # in the configuration section at the top of the file.
    compile_masst_results(
        mgf_path=MGF_FILE_PATH,
        output_folder=OUTPUT_FOLDER_PATH,
        output_prefix=OUTPUT_PREFIX,
        output_csv=OUTPUT_CSV_PATH,
    )