# SimCity 4 DBPF Parser & RCI Blocker Generator

## Project Mission

A comprehensive solution for SimCity 4 modding that extracts lot data from game files and generates exemplar patches (" blockers") to control city growth. Built through systematic reverse engineering of the DBPF format, this tool enables precise control over which buildings grow in your cities.

## What This Does

### Core Functionality

- **Extracts lot data** from SimCity 4's DBPF archives (SimCity_1.dat and custom building packs)
- **Generates blocker patches** that prevent specific building types from growing automatically
- **Provides flexible filtering** to target only desired zone/wealth combinations
- **Creates installation-ready files** for immediate use in SimCity 4

### Practical Benefits

- **Stop unwanted growth**: Prevent specific residential, commercial, or industrial buildings from appearing
- **Preserve custom content**: All custom lots and assets remain fully functional
- **Selective control**: Block only high-wealth buildings, only residential, or any combination you choose
- **Easy installation**: Single-file patches that work like any other SimCity 4 mod

### Real-World Applications

- **Historical cities**: Block modern high-rises to maintain period authenticity
- **Themed regions**: Prevent industrial buildings in pastoral agricultural areas
- **Gameplay balance**: Remove overpowered high-wealth buildings for increased challenge
- **Aesthetic control**: Eliminate specific building types that don't fit your city's vision

## Technical Achievement

Successfully reverse-engineered SimCity 4's proprietary DBPF format to extract **1,908 lot configurations** from the base game, plus support for unlimited custom building packs. The parser handles compressed data, complex property structures, and multiple encoding patterns - technical details that took months to crack.

## Supported Data Sources

### Maxis Base Game Data

- **Complete coverage**: All 1,908 official lot configurations extracted
- **Property extraction**: Zone types, wealth levels, purposes, names, and placement rules
- **Validated accuracy**: Regression tested against known working configurations
- **Ready-to-use blockers**: Pre-generated Maxis blockers available at [Simtropolis Exchange (STEX)](https://community.simtropolis.com/files/file/37015-block-maxis-rci-lots/) for immediate download and installation

### Custom Building Packs

- **Universal compatibility**: Processes any community-created building collection
- **Multiple formats**: Supports .dat, .SC4Lot, .SC4Desc files in ZIP archives
- **Advanced handling**: Correctly parses different property encoding patterns used by various creators
- **Automatic detection**: Seamlessly switches between Maxis and custom data sources

## Usage Examples

### Quick Start - Generate All Blockers

```powershell
# Extract base game data (requires SimCity_1.dat in data/ folder)
python scripts/extract_maxis_lots.py data/SimCity_1.dat

# Generate blocker patches for all building types
python scripts/create_patches_from_json.py

# Result: Individual .dat files in output_patches/ folder
```

### Advanced Usage - Custom Building Packs

```powershell
# Process custom building collection (requires custom.zip in data/ folder) 
python scripts/process_custom_dbpf.py

# Generate blockers for custom content
python scripts/create_patches_from_json.py
```

### Selective Blocking - Target Specific Building Types

```powershell
# Block only high-wealth buildings
python scripts/create_patches_from_json.py --filter-r-high --filter-cs-high --filter-co-high --filter-i-high-tech

# Block all residential except luxury high-rises
python scripts/create_patches_from_json.py --filter-r-low --filter-r-med

# Block industrial buildings in commercial zones
python scripts/create_patches_from_json.py --filter-i-resource --filter-i-dirty --filter-i-manufacturing --filter-i-high-tech
```

### Installation-Ready Files

```powershell
# Create single installation file containing all patches
python scripts/create_patches_from_json.py --datpack

# Custom output filename
python scripts/create_patches_from_json.py --datpack --datpack-output "MyCustomBlockers.dat"

# Result: Single .dat file ready for Plugins folder
```

## Zone & Wealth Targeting

The system supports precise control over which building types to block:

### Residential (R)

- **R$** - Low wealth houses and apartments
- **R$$** - Medium wealth condos and townhomes  
- **R$$$** - High wealth estates and luxury towers

### Commercial Services (CS)

- **CS$** - Convenience stores, fast food, gas stations
- **CS$$** - Shopping centers, restaurants, entertainment
- **CS$$$** - High-end retail, luxury services, malls

### Commercial Office (CO)

- **CO$$** - Medium density office buildings
- **CO$$$** - High-rise corporate towers and headquarters

### Industrial (I)

- **I-r$** - Resource extraction (farms, mines, oil wells)
- **I-d$$** - Dirty industry (factories, chemical plants)
- **I-m$$** - Manufacturing (assembly, processing plants)
- **I-ht$$$** - High-tech industry (electronics, biotech, aerospace)

Mix and match any combination to achieve your desired city growth patterns.

## Automated GitHub Actions Workflow

Generate patches directly from the GitHub web interface without local setup:

### Features

- **Web-based operation**: No local Python installation required
- **Data source flexibility**: Use base game data or upload custom building packs via Google Drive
- **Selective generation**: Choose specific zone/wealth combinations  
- **One-click installation**: Download ready-to-use .dat files

### How to Use

1. Navigate to the **Actions** tab in this repository
2. Select **Generate SimCity 4 Exemplar Patches**
3. Click **Run workflow** and configure:
   - **Data Source**: Choose Maxis base game or custom building pack
   - **Building Selection**: All buildings or specific zone/wealth combinations
   - **Output Format**: Individual files or combined datpack
4. Download the generated patches from workflow artifacts

**Supported combinations**: Any mix of `R$`, `R$$`, `R$$$`, `CS$`, `CS$$`, `CS$$$`, `CO$$`, `CO$$$`, `I-r$`, `I-d$$`, `I-m$$`, `I-ht$$$`

For complete workflow documentation, see **[GitHub Actions Technical Guide](docs/GITHUB_ACTIONS_WORKFLOW.md)**.

## File Structure & Scripts

### Core Processing Scripts

- **`extract_maxis_lots.py`**: Extracts lot data from SimCity_1.dat base game files  
- **`process_custom_dbpf.py`**: Processes custom building packs from ZIP archives
- **`create_patches_from_json.py`**: Generates exemplar patch files with zone/wealth filtering
- **`datpack_patches.py`**: Combines individual patches into single installation file
- **`qfs.py`**: QFS decompression engine for compressed game data

### Validation & Testing

- **`validate_patches.py`**: Verifies patch file integrity and structure
- **`debug/regression_test.py`**: Comprehensive validation suite for parser accuracy
- **`debug/validate_phase*.py`**: Step-by-step validation components

### Data Files

- **`lot_configurations.json`**: Extracted lot data in structured JSON format
- **`patch_instance_ids.csv`**: Instance ID mappings for generated patches
- **`new_properties.xml`**: Property definitions for exemplar structure

## System Architecture

### Collision-Resistant Instance ID Management

The system implements sophisticated Instance ID allocation to prevent conflicts between different building packs:

- **Allocated Range**: `0xFE700000 - 0xFE7FFFFF` (1,048,576 unique slots)
- **Hash-Based Generation**: Uses MD5 of building pack contents for deterministic, unique IID assignment  
- **Community Scale**: Supports 52,428 building packs with 20 IIDs each
- **Registry Compatible**: Positioned for integration with community Instance ID registry systems

This ensures your custom blocker patches won't conflict with other mods or future community tools.

## Technical Documentation

### Comprehensive References

- **[DBPF Format & Parsing Technical Guide](docs/TECHNICAL_REFERENCE.md)**: Complete documentation of SimCity 4's DBPF file format, QFS compression, exemplar structures, and parsing implementation
- **[GitHub Actions Workflow Technical Guide](docs/GITHUB_ACTIONS_WORKFLOW.md)**: Detailed workflow architecture, input parameters, processing pipeline, and automation systems

### Community Resources

- **[SC4Devotion DBPF Documentation](https://wiki.sc4devotion.com/index.php?title=DBPF)**: Community-maintained DBPF format reference
- **[SC4Devotion DBPF Compression (QFS)](https://wiki.sc4devotion.com/index.php?title=DBPF_Compression)**: RefPack algorithm technical details
- **[SC4Devotion Exemplar Properties](https://wiki.sc4devotion.com/index.php?title=Exemplar_properties)**: Complete property ID reference

### Implementation References

- **[TiepiNL/sc4-reader](https://github.com/TiepiNL/sc4-reader)**: ilive's Reader 0.9.3 DBPF parsing reference
- **[SC4Mapper-2013](https://github.com/wouanagaine/SC4Mapper-2013)**: QFS decompression C implementation  
- **[memo33/JDatPacker](https://github.com/memo33/JDatPacker)**: DBPF datpacking and TGI handling reference

## Requirements

### For Local Usage

- **Python 3.7+** with standard library modules
- **SimCity_1.dat** file (140MB+, not included) for base game data extraction
- **Custom building pack ZIP files** for processing community content

### For GitHub Actions (Web Usage)

- **Google Drive account** for uploading custom data files
- **Web browser** for workflow configuration and file downloads

No additional dependencies or complex installation required - the parser uses only Python standard library modules for maximum compatibility.

## License

This project builds upon open-source SimCity 4 community tools and research. The parser implementation is original work based on publicly available format documentation and community reverse engineering efforts.

---

**Ready to control your SimCity 4 growth patterns?** Start with the automated GitHub Actions workflow for instant results, or clone the repository for local customization and advanced usage.
