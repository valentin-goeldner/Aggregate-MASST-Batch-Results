# MASST Results Aggregator and Post-Processor

This project contains a two-step Python workflow for processing results from a [MASST](https://github.com/mwang87/MASST) search.

1.  **`aggregate_MASST_batch_results.py`**: Aggregates the many individual MASST output files into a single summary CSV file.
2.  **`separate_by_string.py`**: (Optional) Takes the summary CSV and splits it into two files based on a specific string in a column (e.g., separating parent compounds from transformation products).

## Requirements

-   Python 3.10
-   Required Python packages: `pandas`, `pyteomics`, `tqdm`

You can install all dependencies using the provided `requirements.txt` file:

```bash
pip install -r requirements.txt
```

## Recommended Directory Structure

For the scripts to work seamlessly, a consistent directory structure is recommended:

```
/path/to/your/project_folder/
├── library_pos_mode.mgf          <-- Your MGF file
├── output/                       <-- Folder with all MASST output files
│   ├── pos_1_..._datasets.tsv
│   └── ...
├── aggregate_results.py          <-- Script 1
├── separate_by_string.py         <-- Script 2
└── requirements.txt
```

## Usage Workflow

Follow these steps to process your MASST results.

### Step 1: Aggregate MASST Results

First, use `aggregate_MASST_batch_results.py` to create a master summary of your search.

#### Configuration

Open `aggregate_MASST_batch_results.py` and edit the `USER CONFIGURATION` section at the top to match your project details.

```python
# --- USER CONFIGURATION --- #
PROJECT_DIRECTORY = r"C:\path\to\your\project_folder"
MGF_FILENAME = "library_pos_mode.mgf"
OUTPUT_SUBDIR = "output"
OUTPUT_PREFIX = "pos"
SUMMARY_FILENAME = "summary_masst_pos.csv"
MASS_PRECISION = 3
```

#### Run the Script

After saving your configuration, run the script from your IDE (e.g., PyCharm's "Run" button) or from the terminal:

```bash
python aggregate_MASST_batch_results.py
```

This will produce a summary file (e.g., `summary_masst_pos.csv`) in your project directory.

### Step 2: Separate Compounds (Optional)

If your compound names contain tags (e.g., `_ETP_` for Expected Transformation Products) and you wish to separate them from parent compounds, use `separate_by_string.py`.

#### Configuration

Open `separate_by_string.py` and edit its `USER CONFIGURATION` section. **Ensure `INPUT_CSV_FILENAME` matches the `SUMMARY_FILENAME` from Step 1.**

```python
# --- USER CONFIGURATION --- #
PROJECT_DIRECTORY = r"C:\path\to\your\project_folder"
INPUT_CSV_FILENAME = "summary_masst_pos.csv"
COLUMN_TO_CHECK = 'Compound Name'
SEARCH_STRING = "_ETP_"
```

#### Run the Script

Run the second script in the same way you ran the first one:

```bash
python separate_by_string.py
```

#### Output

This will create two new files in your project directory:
1.  `summary_masst_pos_ETP.csv`: Contains only the rows where the `Compound Name` included `_ETP_`.
2.  `summary_masst_pos_parents.csv`: Contains all other rows (the parent compounds).
