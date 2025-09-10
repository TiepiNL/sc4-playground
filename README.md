# SimCity 4 Maxis RCI Blockers - LotConfigurations Extractor

## Overview
A robust parser for extracting LotConfigurations data from SimCity 4 DBPF files, specifically designed to extract ExemplarName strings and zone/wealth/purpose type arrays for RCI blocker analysis.

## Mission Accomplished
Successfully extracted **1,908 LotConfigurations entries** from SimCity_1.dat with accurate property parsing.

## Features
- Complete DBPF file parsing with QFS decompression support
- EQZB container parsing with correct header handling  
- Property structure parsing
- Dynamic property search (handles missing properties gracefully)
- Comprehensive validation and regression testing framework
- **Zone/Wealth filtering** - Generate patches for specific RCI combinations
- **Datpack functionality** - Combine multiple .dat files into single DBPF for easier installation
- Support for key LotConfiguration properties:
  - ExemplarName (0x88EDC790) - String
  - ZoneTypes (0x88EDC793) - UINT8 array
  - ZoneWealth (0x88EDC795) - UINT8 array  
  - ZonePurpose (0x88EDC796) - UINT8 array
  - GrowthStage (0x27812837) - UINT8, Rep=0
  - RoadCornerIndicator (0x4A4A88F0) - UINT8, Rep=0

## Technical Approach

This project used a systematic, expert-level approach:

1. DBPF File Structure + LotConfiguration Filtering ✅
2. EQZB Container Parsing + Property Location ✅  
3. Property Structure Parsing ✅
4. Property Value Interpretation ✅
5. Complete Extraction ✅
6. Validation & Regression Testing ✅

Each layer was validated before proceeding, with regression tests preventing breakage of working components.

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

- **`scripts/extract_maxis_lots.py`**: Main extraction script implementing the complete DBPF parsing pipeline
- **`scripts/qfs.py`**: QFS (RefPack) decompression implementation for compressed exemplars  
- **`scripts/create_patches_from_json.py`**: Patch creation utility with zone/wealth filtering and datpack support
- **`scripts/datpack_patches.py`**: Combines multiple .dat files into a single DBPF file for easier installation


### Running the Extraction

```bash
# Parse SimCity_1.dat (output: json)
python scripts/extract_maxis_lots.py data/SimCity_1.dat

# Create exemplar patches (all zone/wealth combinations)
python scripts/create_patches_from_json.py

# Create patches for specific zone/wealth combinations
python scripts/create_patches_from_json.py --filter-r-low --filter-cs-med --filter-i-high-tech

# Create patches and combine into single datpacked file
python scripts/create_patches_from_json.py --datpack

# Create datpacked file with custom name
python scripts/create_patches_from_json.py --datpack --datpack-output my_blockers.dat

# Combine existing .dat files into datpacked file
python scripts/datpack_patches.py --input output_patches --output combined_blockers.dat
```

Requires `SimCity_1.dat` in the `data/` directory (140MB+ file not included in repo).

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

## Documentation

- **[Technical Reference 1](scripts/extract_maxis_lots.md)**: Complete DBPF format documentation
- **[Technical Reference 2](scripts/create_patches_from_json.md)**: Complete exemplar patch file generation documentation
- **[Generated Data](data/lot_configurations.json)**: Complete JSON output with all 341 lots
