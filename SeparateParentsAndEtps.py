import os
from pathlib import Path
import pandas as pd

# ========================== #
# --- USER CONFIGURATION --- #
# ========================== #

# 1. Path to the input CSV file you want to separate.
#    This should be one of the summary files we created earlier.
INPUT_CSV_PATH = r"Y:\Data\goeldnerv97\Research\Spectral Library Building\Applications\MASST_Search\20260416_natural_products\dataset_summary_unique_compounds.csv"

# 2. The column to check for the "_ETP_" string.
#    This should almost always be 'Compound Name'.
COLUMN_TO_CHECK = 'Compound Name'

# 3. The string to search for.
SEARCH_STRING = "_ETP_"


# ========================== #
# ------ SCRIPT LOGIC ------ #
# ========================== #

def separate_csv_by_string(input_path, column_name, search_str):
    """
    Reads a CSV file and separates it into two new CSVs based on whether
    a specific string is present in a given column.
    """
    input_path = Path(input_path)

    # --- 1. Verify input file exists ---
    if not input_path.is_file():
        print(f"Error: Input file not found at '{input_path}'")
        return

    print(f"Reading input file: {input_path.name}")

    try:
        # --- 2. Read the entire CSV into a pandas DataFrame ---
        df = pd.read_csv(input_path)
    except Exception as e:
        print(f"Error: Failed to read the CSV file. Reason: {e}")
        return

    # Verify the specified column exists in the DataFrame
    if column_name not in df.columns:
        print(f"Error: Column '{column_name}' not found in the CSV file.")
        print(f"Available columns are: {list(df.columns)}")
        return

    # --- 3. Create a filter (a "mask") for rows containing the search string ---
    # The 'na=False' ensures that any empty cells don't cause an error.
    etp_mask = df[column_name].str.contains(search_str, na=False)

    # --- 4. Separate the DataFrame into two parts using the mask ---
    df_etps = df[etp_mask]
    df_parents = df[~etp_mask]  # The '~' symbol inverts the mask (selects non-ETPs)

    # --- 5. Define the output filenames ---
    # Get the base name of the input file without the extension
    file_stem = input_path.stem
    output_etps_path = input_path.with_name(f"{file_stem}_ETPs.csv")
    output_parents_path = input_path.with_name(f"{file_stem}_parents.csv")

    # --- 6. Save the two new DataFrames to their respective CSV files ---
    # The 'index=False' prevents pandas from writing an extra index column.
    df_etps.to_csv(output_etps_path, index=False)
    df_parents.to_csv(output_parents_path, index=False)

    print("\n--- Separation Complete! ---")
    print(f"{len(df_etps)} rows saved to: {output_etps_path.name}")
    print(f"{len(df_parents)} rows saved to: {output_parents_path.name}")


if __name__ == "__main__":
    separate_csv_by_string(INPUT_CSV_PATH, COLUMN_TO_CHECK, SEARCH_STRING)