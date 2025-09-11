# GitHub Actions Workflow - Complete Technical Guide

## Overview

The GitHub Actions workflow provides a comprehensive automation system for generating RCI (Residential, Commercial, Industrial) blocker patches for SimCity 4. The workflow supports multiple data sources, flexible zone/wealth selection, and various output formats.

## Workflow Architecture

### Trigger Mechanism

- **Manual Dispatch Only** (`workflow_dispatch`)
- Provides interactive UI with dropdown menus and checkboxes
- No automatic triggers to prevent accidental resource consumption

### Key Features

1. **Dual Data Sources**: Maxis base game data or custom building packs
2. **Flexible Selection**: All combinations or user-specified zone/wealth filtering
3. **Intelligent Caching**: Google Drive files cached by content hash
4. **Multiple Output Formats**: Individual .dat files or single datpacked file
5. **Dynamic Artifact Naming**: Descriptive names based on configuration

## Input Parameters

### Data Source Configuration

```yaml
data_source:
  type: choice
  options: ['SimCity_1.dat', 'custom']
  default: 'SimCity_1.dat'
  
custom_file_id:
  type: string
  description: 'Google Drive File ID for custom building packs'
  required: false
```

### Zone/Wealth Selection

```yaml
selection_mode:
  type: choice
  options: ['all', 'specific']
  default: 'all'
  
zone_wealth_combinations:
  type: string
  default: 'R$,R$$,R$$$,CO$$,CO$$$,CS$,CS$$,CS$$$,I-d,I-m,I-ht,I-r'
  description: 'Comma-separated combinations for specific mode'
```

### Output Format

```yaml
enable_datpack:
  type: boolean
  default: false
  description: 'Combine all .dat files into single archive'
```

## Technical Implementation

### Environment Variables

- **GDRIVE_FILE_ID**: Repository variable for Maxis SimCity_1.dat
- **CUSTOM_FILE_ID**: Runtime variable from user input  
- **STARTING_MAXIS_IID**: Instance ID seed for cohort generation
- **DATA_SOURCE**: Determines processing pipeline

### Processing Pipeline

#### Stage 1: Data Acquisition

```bash
# Maxis Data Path
gdown --id $GDRIVE_FILE_ID --fuzzy -O "data/SimCity_1.dat.zip"
unzip "data/SimCity_1.dat.zip" -d data/

# Custom Data Path  
gdown --id $CUSTOM_FILE_ID --fuzzy -O "data/custom.zip"
```

#### Stage 2: Data Processing

```bash
# Maxis Processing
python3 scripts/extract_maxis_lots.py data/SimCity_1.dat data/lot_configurations.json

# Custom Processing
python3 scripts/process_custom_dbpf.py
```

#### Stage 3: Patch Generation

```bash
# Dynamic argument building based on selection mode
if [ "$SELECTION_MODE" = "specific" ]; then
  # Parse zone_wealth_combinations and build filter arguments
  # Convert: "R$,CS$$,I-ht" -> "--filter-r-low --filter-cs-med --filter-i-high-tech"
fi

python3 scripts/create_patches_from_json.py $ARGS
```

### Caching Strategy

```yaml
cache:
  path: data/${{ env.DAT_FILENAME }}
  key: ${{ runner.os }}-simcity-dat-${{ env.DATA_SOURCE == 'custom' && env.CUSTOM_FILE_ID || env.GDRIVE_FILE_ID }}
```

**Benefits:**

- **Content-based keys**: Different file IDs = different cache entries
- **Source-aware**: Maxis vs custom data cached separately  
- **Cross-run persistence**: Identical file IDs reuse cached data

## Zone/Wealth Mapping

### Available Combinations

| Input Code | Zone Type | Wealth Level | Filter Argument |
|------------|-----------|--------------|-----------------|
| R$ | Residential | Low | `--filter-r-low` |
| R$$ | Residential | Medium | `--filter-r-med` |
| R$$$ | Residential | High | `--filter-r-high` |
| CO$$ | Commercial Office | Medium | `--filter-co-med` |
| CO$$$ | Commercial Office | High | `--filter-co-high` |
| CS$ | Commercial Service | Low | `--filter-cs-low` |
| CS$$ | Commercial Service | Medium | `--filter-cs-med` |
| CS$$$ | Commercial Service | High | `--filter-cs-high` |
| I-d | Industrial | Dirty | `--filter-i-dirty` |
| I-m | Industrial | Manufacturing | `--filter-i-manufacturing` |
| I-ht | Industrial | High Tech | `--filter-i-high-tech` |
| I-r | Industrial | Resource | `--filter-i-resource` |

### Automatic Exclusions

The workflow automatically excludes special building types:
- **Military** (ZoneTypes 10)
- **Airport** (ZoneTypes 11) 
- **Seaport** (ZoneTypes 12)
- **Spaceport** (ZoneTypes 13)
- **Landmark** (ZoneTypes 14)
- **Civic** (ZoneTypes 15)

## Artifact Generation

### Naming Convention

```md
{data_source}-blocker-{selection_mode}-{output_format}
```

### Examples

- `maxis-blocker-all-combinations-individual`
- `maxis-blocker-specific-selection-datpacked`
- `custom-blocker-all-combinations-individual`
- `custom-blocker-specific-selection-datpacked`

### Content Structure

```md
output_patches/
├── individual files (when datpack=false)
│   ├── maxis_blocker_R_low.dat
│   ├── maxis_blocker_CS_med.dat
│   └── ...
└── combined file (when datpack=true)
    └── maxis_blockers_[all|specific].dat
```

## Usage Examples

### All Combinations (Default)

```yaml
inputs:
  data_source: 'SimCity_1.dat'
  selection_mode: 'all'
  enable_datpack: false
```
**Result**: 12 individual .dat files for all valid zone/wealth combinations

### Residential Only

```yaml
inputs:
  data_source: 'SimCity_1.dat'
  selection_mode: 'specific'
  zone_wealth_combinations: 'R$,R$$,R$$$'
  enable_datpack: true
```

**Result**: Single datpacked file containing residential blockers only

### Custom Building Packs

```yaml
inputs:
  data_source: 'custom'
  custom_file_id: '1ABC...XYZ'
  selection_mode: 'all'
  enable_datpack: false
```

**Result**: Individual .dat files for all lots found in custom building packs

## Error Handling

### File Generation Validation

```bash
if [ -z "$(ls -A output_patches 2>/dev/null)" ]; then
  echo "No patch files were generated."
  echo "patches_exist=false" >> $GITHUB_OUTPUT
fi
```

### Common Failure Scenarios

1. **Invalid Google Drive ID**: Download fails, workflow stops
2. **Empty zone selection**: No patches generated when using 'specific' mode
3. **Corrupted DBPF data**: Parsing errors during extraction phase
4. **Missing custom data**: Custom mode selected but no valid building packs found

## Performance Characteristics

### Resource Usage

- **Runtime**: 2-5 minutes depending on data source and selection
- **Cache Size**: ~150MB for SimCity_1.dat
- **Memory Peak**: <500MB during DBPF processing
- **Output Size**: 50KB - 2MB depending on selection

### Optimization Features

- **Incremental caching**: Unchanged file IDs skip download
- **Parallel processing**: Multiple .dat files generated concurrently
- **Early termination**: Stops on first critical error
- **Selective filtering**: Only processes requested zone/wealth combinations

## Command Line Equivalents

### Local Development

```bash
# Replicate "all combinations" mode
python scripts/create_patches_from_json.py

# Replicate "specific selection" mode  
python scripts/create_patches_from_json.py --filter-r-low --filter-cs-med --filter-i-high-tech

# Replicate "datpack enabled" mode
python scripts/create_patches_from_json.py --datpack --datpack-output custom_name.dat
```

### Custom Data Processing

```bash
# Process custom building packs locally
python scripts/process_custom_dbpf.py

# Generate patches from custom data
python scripts/create_patches_from_json.py --filter-r-high --filter-co-high
```

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
