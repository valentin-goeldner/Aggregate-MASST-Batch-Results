# -*- coding: utf-8 -*-
"""
Splits a summary CSV file into two separate files based on a search string.

This script is intended to be run after 'aggregate_results.py'. It takes a
CSV file and separates its rows into two new files: one containing rows where
a specific column includes a given search string (e.g., "_ETP_"), and another
with the remaining rows.

To use this script, edit the variables in the "USER CONFIGURATION" section
below, then run the file.
"""

from pathlib import Path
import sys
import pandas as pd

# ========================================================================= #
# ---                          USER CONFIGURATION                         --- #
# ---                  EDIT THE VARIABLES IN THIS SECTION                 --- #
# ========================================================================= #

# 1. Set the main project directory. This should be the same directory used
#    in the first script.
PROJECT_DIRECTORY = Path(r"Y:\Data\goeldnerv97\Research\Spectral Library Building\Applications\MASST_Search\20260416_natural_products")

# 2. Filename of the input CSV file you want to separate. This should be
#    one of the summary files created by 'aggregate_results.py'.
INPUT_CSV_FILENAME = "dataset_summary_unique_compounds.csv"

# 3. The column to check for the search string.
#    For this workflow, this will typically be 'Compound Name'.
COLUMN_TO_CHECK = 'Compound Name'

# 4. The string to search for (e.g., a tag for transformation products).
SEARCH_STRING = "_ETP_"


# ========================================================================= #
# ---         SCRIPT LOGIC (No modifications needed below here)         --- #
# ========================================================================= #

# Automatically construct the full input path from the configuration
INPUT_CSV_PATH = PROJECT_DIRECTORY / INPUT_CSV_FILENAME


def separate_csv_by_string(input_path: Path, column_name: str, search_str: str):
    """
    Reads a CSV and splits it into two files based on a string in a column.
    """
    # --- 1. Verify input file exists ---
    if not input_path.is_file():
        print(f"Error: Input file not found at '{input_path}'")
        sys.exit(1)

    print(f"Reading input file: {input_path.name}")

    try:
        # --- 2. Read the entire CSV into a pandas DataFrame ---
        df = pd.read_csv(input_path)
    except Exception as e:
        print(f"Error: Failed to read the CSV file. Reason: {e}")
        sys.exit(1)

    # Verify the specified column exists
    if column_name not in df.columns:
        print(f"Error: Column '{column_name}' not found in the CSV file.")
        print(f"Available columns are: {list(df.columns)}")
        sys.exit(1)

    # --- 3. Create a boolean mask for rows containing the search string ---
    # The 'na=False' ensures that any empty cells are treated as not containing the string.
    mask = df[column_name].str.contains(search_str, na=False)

    # --- 4. Separate the DataFrame into two parts using the mask ---
    df_with_string = df[mask]
    df_without_string = df[~mask]  # The '~' inverts the mask (selects remaining rows)

    # --- 5. Define the output filenames ---
    # The new files will be saved in the same directory as the input file.
    file_stem = input_path.stem
    # The first output file is named after the search string (e.g., "..._ETPs.csv")
    output_with_string_path = input_path.with_name(f"{file_stem}_{search_str.strip('_')}.csv")
    output_without_string_path = input_path.with_name(f"{file_stem}_parents.csv")

    # --- 6. Save the two new DataFrames to their respective CSV files ---
    df_with_string.to_csv(output_with_string_path, index=False)
    df_without_string.to_csv(output_without_string_path, index=False)

    print("\n--- Separation Complete! ---")
    print(f"{len(df_with_string)} rows containing '{search_str}' saved to: {output_with_string_path.name}")
    print(f"{len(df_without_string)} other rows saved to: {output_without_string_path.name}")


if __name__ == "__main__":
    separate_csv_by_string(INPUT_CSV_PATH, COLUMN_TO_CHECK, SEARCH_STRING)