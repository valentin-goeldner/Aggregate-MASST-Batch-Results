# MASST Results Post-Processing Suite

This project contains a suite of Python scripts for processing and analyzing results from a [MASST](https://github.com/mwang87/MASST) search.

1.  **`aggregate_results.py`**: A basic aggregator that counts the number of unique datasets and library spectra matched for each compound.
2.  **`separate_by_string.py`**: A general utility to split any of the generated summary CSV files based on a string in a column (e.g., separating parent compounds from transformation products).

## Requirements

-   Python 3.10
-   Required Python packages: `pandas`, `pyteomics`, `tqdm`

You can install all dependencies using the provided `requirements.txt` file:

```bash
pip install -r requirements.txt
```

## Recommended Directory Structure

A consistent project structure is recommended for the scripts to work seamlessly.

```
/path/to/your/project_folder/
├── library_pos_mode.mgf          <-- Your MGF file
├── output/                       <-- Folder with all MASST output files
│   ├── pos_1_..._datasets.tsv
│   ├── pos_1_..._matches.tsv
│   └── ...
├── aggregate_results.py          <-- Script 1
├── separate_by_string.py         <-- Script 2
└── requirements.txt
```

## Usage Workflow

The scripts are designed to be run after editing their respective `USER CONFIGURATION` sections.

### Tool 1: Basic Aggregation (`aggregate_results.py`)

This script provides a high-level summary of MASST hits. It parses `_datasets.tsv` and `_library.tsv` files.

#### Configuration
Open `aggregate_results.py` and edit its configuration section.
```python
# --- USER CONFIGURATION --- #
PROJECT_DIRECTORY = r"C:\path\to\your\project_folder"
MGF_FILENAME = "input_filename.mgf"
# ... and other settings ...
```
#### Run
Run the script from your IDE or terminal: `python aggregate_results.py`

---

### Tool 2: Splitting CSV by String (`separate_by_string.py`)

This is a general utility script that can be run on the output CSV from **either** of the tools above. It is useful for separating entries based on tags in their names, like `_ETP_` for transformation products.

#### Configuration
Open `separate_by_string.py` and edit its configuration. **Ensure `INPUT_CSV_FILENAME` matches the output file you want to split.**
```python
# --- USER CONFIGURATION --- #
PROJECT_DIRECTORY = r"C:\path\to\your\project_folder"
INPUT_CSV_FILENAME = "summary_masst_pos.csv" # Or "Pan_ReDU_metadata_summary_pos.csv"
COLUMN_TO_CHECK = 'Compound Name'
SEARCH_STRING = "_ETP_"
```
#### Run
Run the script from your IDE or terminal: `python separate_by_string.py`

This will create two new files (e.g., `..._ETP.csv` and `..._parents.csv`) in your project folder.