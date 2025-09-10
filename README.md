# SimCity 4 Maxis RCI Blockers - LotConfigurations Extractor

## Overview
A robust parser for extracting LotConfigurations data from SimCity 4 DBPF files, specifically designed to extract ExemplarName strings and zone/wealth/purpose type arrays for RCI blocker analysis.

## Mission Accomplished
Successfully extracted **1,908 LotConfigurations entries** from SimCity_1.dat with accurate property parsing.

## Custom Building Pack Support

The parser now supports **dual-track processing** for both Maxis base game data and custom building packs with enhanced property handling:

### Key Improvements
- **Rep=0 Property Handling**: Correctly processes properties with zero repetitions as empty arrays `[]` instead of `None`
- **Dual-Track Logic**: Handles both Maxis data (rep≥1) and custom data (rep=0) property encodings
- **Custom ZIP Processing**: Extracts and processes custom building packs from ZIP archives
- **Property Validation**: Enhanced validation logic that accommodates different property encoding patterns

### Supported Custom Formats
- **Building Pack ZIP files** containing `.dat`, `.SC4Lot`, `.SC4Desc` files
- **Multiple DBPF files** in single archive (recursive scanning)
- **QFS compressed exemplars** with automatic decompression
- **Various property encodings** including rep=0 empty arrays

### Technical Achievement
Custom building packs often use **different property encoding** than Maxis data:
- **Maxis encoding**: Properties typically have rep≥1 with actual values
- **Custom encoding**: Properties may have rep=0 indicating empty arrays rather than missing properties
- **Our solution**: Implemented dual-track parsing that correctly handles both encoding patterns

## Features
- Complete DBPF file parsing with QFS decompression support
- EQZB container parsing with correct header handling  
- Property structure parsing with dual-track rep handling
- **Custom Building Pack Support** - Process user-provided building collections with rep=0 property handling
- Dynamic property search (handles missing properties gracefully)
- Comprehensive validation and regression testing framework
- **Zone/Wealth filtering** - Generate patches for specific RCI combinations
- **Datpack functionality** - Combine multiple .dat files into single DBPF for easier installation
- **Dual-track rep handling** - Correctly processes both rep≥1 (arrays with values) and rep=0 (empty arrays) properties
- Support for key LotConfiguration properties:
  - ExemplarName (0x88EDC790) - String
  - ZoneTypes (0x88EDC793) - UINT8 array (supports rep=0 and rep≥1)
  - ZoneWealth (0x88EDC795) - UINT8 array (supports rep=0 and rep≥1)
  - ZonePurpose (0x88EDC796) - UINT8 array (supports rep=0 and rep≥1)
  - GrowthStage (0x27812837) - UINT8, Rep=0
  - RoadCornerIndicator (0x4A4A88F0) - UINT8, Rep=0

## Technical Approach

This project used a systematic, expert-level approach with dual-track support:

### Core Implementation
1. DBPF File Structure + LotConfiguration Filtering ✅
2. EQZB Container Parsing + Property Location ✅  
3. Property Structure Parsing ✅
4. Property Value Interpretation ✅
5. Complete Extraction ✅
6. Validation & Regression Testing ✅

### Custom Building Pack Extensions
7. **Custom DBPF Processing** ✅ - ZIP archive extraction and multi-file scanning
8. **Dual-Track Rep Handling** ✅ - Enhanced property parsing for rep=0 vs rep≥1 encodings
9. **Property Validation Enhancement** ✅ - Adaptive validation for different encoding patterns
10. **Cross-Format Compatibility** ✅ - Unified processing pipeline for both Maxis and custom data

Each layer was validated before proceeding, with regression tests preventing breakage of working components. The dual-track implementation ensures compatibility with both official Maxis content and community-created building packs.

## References

### Primary Sources
- **[TiepiNL/sc4-reader](https://github.com/TiepiNL/sc4-reader)** - ilive's Reader 0.9.3: Reference implementation for DBPF parsing logic
- **[SC4Mapper-2013 by Denis Auroux](https://github.com/wouanagaine/SC4Mapper-2013)** - QFS decompression C reference implementation
- **[memo33/JDatPacker](https://github.com/memo33/JDatPacker)** - DBPF datpacking logic and TGI handling reference for combining multiple .dat files

### Technical Documentation
- **DBPF File Format**: Based on ilive's Reader 0.9.3 DBPF structure parsing
- **QFS Compression**: RefPack algorithm implementation from SC4Mapper-2013
- **Property Structure**: Reverse-engineered through systematic hex analysis and validation

## License
This project builds upon open-source SC4 community tools and follows their respective licenses.

## Technical Implementation

### Scripts Overview

- **`scripts/extract_maxis_lots.py`**: Main extraction script implementing the complete DBPF parsing pipeline for Maxis base game data
- **`scripts/process_custom_dbpf.py`**: Processes custom building packs from zip archives containing SC4 files (.SC4Lot, .SC4Desc, .dat) with dual-track rep=0 property handling
- **`scripts/qfs.py`**: QFS (RefPack) decompression implementation for compressed exemplars  
- **`scripts/create_patches_from_json.py`**: Patch creation utility with automatic data source detection, zone/wealth filtering and datpack support
- **`scripts/datpack_patches.py`**: Combines multiple .dat files into a single DBPF file for easier installation

### Key Technical Features

- **Dual-Track Property Parsing**: Handles both Maxis (rep≥1) and custom (rep=0) property encodings
- **Adaptive Validation**: Enhanced property validation that accommodates different encoding patterns  
- **Rep=0 Handling**: Correctly processes properties with zero repetitions as empty arrays `[]`
- **Cross-Format Compatibility**: Unified processing pipeline for official and community content


### Data Source Support

The system now supports two data sources with automatic detection:

1. **Maxis Base Game Data** - Extracts from SimCity_1.dat
2. **Custom Building Packs** - Processes user-provided building collections

**Priority:** Custom data takes precedence when both are available.

### Running the Scripts

```bash
# === MAXIS BASE GAME DATA ===
# Parse SimCity_1.dat (output: data/lot_configurations.json)
python scripts/extract_maxis_lots.py data/SimCity_1.dat

# === CUSTOM BUILDING PACKS ===
# Process custom building packs (requires data/custom.zip)
python scripts/process_custom_dbpf.py

# === PATCH GENERATION (AUTO-DETECTS DATA SOURCE) ===
# Create exemplar patches (all zone/wealth combinations)
python scripts/create_patches_from_json.py

# Create patches for specific zone/wealth combinations
python scripts/create_patches_from_json.py --filter-r-low --filter-cs-med --filter-i-high-tech

# Create patches and combine into single datpacked file
python scripts/create_patches_from_json.py --datpack

# Create datpacked file with custom name
python scripts/create_patches_from_json.py --datpack --datpack-output my_blockers.dat

# === DATPACK UTILITIES ===
# Combine existing .dat files into datpacked file
python scripts/datpack_patches.py --input output_patches --output combined_blockers.dat
```

**Data Requirements:**
- **Maxis data:** `SimCity_1.dat` in the `data/` directory (140MB+ file not included in repo)
- **Custom data:** `custom.zip` containing building pack files in the `data/` directory

## Datpack Functionality

The datpack feature combines multiple individual .dat patch files into a single DBPF file, making installation and management easier:

### Benefits
- **Single file installation**: Copy one .dat file instead of multiple files
- **Reduced file count**: Keeps Plugins folder organized  
- **Identical functionality**: Combined file works exactly like individual patches
- **Automatic cleanup**: Source .dat files can be automatically removed after datpacking

### Zone/Wealth Filtering

Create patches for specific RCI combinations using filter arguments:

- **Residential**: `--filter-r-low`, `--filter-r-med`, `--filter-r-high` (R$, R$$, R$$$)
- **Commercial Service**: `--filter-cs-low`, `--filter-cs-med`, `--filter-cs-high` (CS$, CS$$, CS$$$) 
- **Commercial Office**: `--filter-co-med`, `--filter-co-high` (CO$$, CO$$$)
- **Industrial**: `--filter-i-resource`, `--filter-i-dirty`, `--filter-i-manufacturing`, `--filter-i-high-tech` (I-r$, I-d$$, I-m$$, I-ht$$$)

If no filters are specified, all zone/wealth combinations are included.

## GitHub Actions Workflow

The repository includes an automated GitHub Actions workflow that generates and releases patch files:

### Workflow Features

- **Automated patch generation** from GitHub web interface
- **Data source selection**: Choose between Maxis base game or custom building packs  
- **Custom Google Drive integration**: Upload your own SimCity_1.dat or building pack archives
- **Zone/wealth filtering**: Select specific RCI combinations using comma-separated values
- **Automatic datpack creation**: Combines patches into single file for easy installation
- **Release artifacts**: Downloads available immediately after workflow completion

### Workflow Inputs

1. **Data Source** (choice): 
   - `maxis` - Use SimCity_1.dat base game data
   - `custom` - Use custom building pack archive

2. **Custom File ID** (string): Google Drive file ID when using custom data source

3. **Selection Mode** (choice):
   - `all` - Generate patches for all available zone/wealth combinations
   - `specific` - Filter using zone/wealth combinations input

4. **Zone/Wealth Combinations** (string): Comma-separated values like `R$$$,CO$$,I-ht$$$`

5. **Enable Datpack** (boolean): Combine all patches into single file

### Usage Example

1. Go to **Actions** tab in GitHub repository
2. Select **Generate SimCity 4 Exemplar Patches** workflow  
3. Click **Run workflow**
4. Configure inputs:
   - Data Source: `custom`
   - Custom File ID: `1ABC...XYZ` (your Google Drive file ID)
   - Selection Mode: `specific`
   - Zone/Wealth Combinations: `CO$$,R$$$,I-ht$$$`
   - Enable Datpack: `true`
5. Download generated files from workflow artifacts

**Supported Zone/Wealth Values**: `R$`, `R$$`, `R$$$`, `CS$`, `CS$$`, `CS$$$`, `CO$$`, `CO$$$`, `I-r$`, `I-d$$`, `I-m$$`, `I-ht$$$`

## Documentation

- **[Technical Reference 1](scripts/extract_maxis_lots.md)**: Complete DBPF format documentation
- **[Technical Reference 2](scripts/create_patches_from_json.md)**: Complete exemplar patch file generation documentation
- **[Generated Data](data/lot_configurations.json)**: Complete JSON output with all 341 lots
