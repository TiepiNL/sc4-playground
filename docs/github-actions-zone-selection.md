# GitHub Actions Workflow - Zone/Wealth Selection Guide

## Overview

The GitHub Actions workflow now supports two modes for generating RCI blocker patches:

1. **All Combinations** (default) - Generates patches for all valid zone/wealth combinations
2. **Specific Selection** - Generates patches only for user-selected zone/wealth combinations

## Usage

### Running with All Combinations

1. Go to the **Actions** tab in your GitHub repository
2. Select the **Generate Blocker Patch Files** workflow
3. Click **Run workflow**
4. Set **Zone/Wealth Selection Mode** to `all` (default)
5. Click **Run workflow**

This will generate all 12 possible patch files (R$, R$$, R$$$, CS$, CS$$, CS$$$, CO$$, CO$$$, I-d$$, I-m$$, I-ht$$$, I-r$).

### Running with Specific Selections

1. Go to the **Actions** tab in your GitHub repository
2. Select the **Generate Blocker Patch Files** workflow
3. Click **Run workflow**
4. Set **Zone/Wealth Selection Mode** to `specific`
5. Check the checkboxes for the zone/wealth combinations you want:

#### Available Options:
- **R$** - Residential Low Wealth
- **R$$** - Residential Medium Wealth  
- **R$$$** - Residential High Wealth
- **CO$$** - Commercial Office Medium Wealth
- **CO$$$** - Commercial Office High Wealth
- **CS$** - Commercial Service Low Wealth
- **CS$$** - Commercial Service Medium Wealth
- **CS$$$** - Commercial Service High Wealth
- **I-D** - Industrial Dirty
- **I-M** - Industrial Manufacturing
- **I-HT** - Industrial High Tech
- **I-R** - Industrial Resource/Raw Materials

6. Click **Run workflow**

## Examples

### Blocking Only Residential Growth
Select: R$, R$$, R$$$

### Blocking Only Commercial Growth  
Select: CS$, CS$$, CS$$$, CO$$, CO$$$

### Blocking Only Industrial Growth
Select: I-D, I-M, I-HT, I-R

### Blocking High Wealth Only
Select: R$$$, CS$$$, CO$$$, I-HT

## Artifacts

The workflow generates artifacts with descriptive names:
- `maxis-blocker-dat-files-all-combinations` - When using "all" mode
- `maxis-blocker-dat-files-specific-selection` - When using "specific" mode

## Command Line Usage

The script supports command-line filtering for local development:

```bash
# Generate all combinations
python scripts/create_patches_from_json.py

# Generate specific combinations
python scripts/create_patches_from_json.py --filter-r-low --filter-cs-med --filter-i-high-tech
```

The script generates individual .dat files in the `output_patches/` directory. When run via GitHub Actions, these files are automatically packaged as workflow artifacts for download.

## Notes

- When using "specific" mode, at least one checkbox must be selected
- The checkboxes are ignored when "all" mode is selected
- Each generated patch file targets only the lots matching that specific zone/wealth combination
- The script automatically excludes special buildings (Military, Airport, Seaport, Spaceport, Landmark, Civic zones)
