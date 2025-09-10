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
- **`scripts/create_patches_from_json.py`**: Patch creation utility


### Running the Extraction

```bash
# Parse SimCity_1.dat (output: json)
python scripts/extract_maxis_lots.py data/SimCity_1.dat
# Create exemplar patches
python scripts/create_patches_from_json.py
```

Requires `SimCity_1.dat` in the `data/` directory (140MB+ file not included in repo).

## Documentation

- **[Technical Reference 1](scripts/extract_maxis_lots.md)**: Complete DBPF format documentation
- **[Technical Reference 2](scripts/create_patches_from_json.md)**: Complete exemplar patch file generation documentation
- **[Generated Data](data/lot_configurations.json)**: Complete JSON output with all 341 lots
