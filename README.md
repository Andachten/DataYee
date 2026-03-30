# DataYee

Single-Molecule Force Spectroscopy (SMFS) Data Analysis Tool

[English](README.md) | [中文](README_zh.md)

## Overview

DataYee is a Python-based desktop application for analyzing Single-Molecule Force Spectroscopy (SMFS) data, commonly acquired using Atomic Force Microscopy (AFM). It provides tools for force curve processing, WLC (Worm-Like Chain) fitting, energy landscape analysis, and data clustering.

## Features

- **Force Curve Processing**: Load, process, and visualize force-distance curves from JPK, TXT, and custom DataYee formats
- **Peak Detection**: Automatic and manual detection of unfolding peaks
- **WLC Fitting**: Worm-Like Chain model fitting for contour length and persistence length estimation
- **Energy Landscape Analysis**: Bell-Evans and Friddle models for unfolding energy calculations
- **Data Clustering**: K-Means clustering and DTW-based similarity sorting
- **Batch Processing**: Process multiple force curves simultaneously
- **Export Options**: Export results to Excel, TXT, and image formats

## Installation

### Prerequisites

- Python 3.11+
- Conda or pip package manager

### Quick Install

```bash
# Clone the repository
git clone https://github.com/Andachten/DataYee.git
cd DataYee

# Create conda environment
conda create -n datayee python=3.11 -y
conda activate datayee

# Install dependencies
pip install numpy pandas scipy matplotlib scikit-learn PyQt5 openpyxl xlwt

# Run the application
python -m src
```

### Or install via pip (if available on PyPI)

```bash
pip install datayee
datayee
```

## Usage

### Starting the Application

```bash
# From source
python -m src

# Or with a specific file
python -m src path/to/force_curve.jpk-force
```

### Basic Workflow

1. **Load Force Curve**: File → Open Force Curve (or drag & drop)
2. **Process Data**: Use auto-step or manually adjust parameters
3. **Detect Peaks**: Click on peaks or use automatic detection
4. **Fit WLC**: Adjust lc, lp parameters and fit curves
5. **Analyze Energy**: Calculate unfolding forces and energy landscapes
6. **Export Results**: Export to Excel, TXT, or images

### Command Line Options

```bash
python -m src --help
```

```
usage: datayee [-h] [--batch DIRECTORY] [--version] [--theme {light,dark}]
               [file]

positional arguments:
  file                  Force curve file to open (.jpk-force, .txt, .spm, .DataYee-force)

options:
  --batch DIRECTORY, -b  Process all force curves in directory
  --version, -v          Show program version
  --theme {light,dark}  Set GUI theme
```

## Project Structure

```
DataYee/
├── src/
│   ├── __main__.py          # Entry point
│   ├── cli.py               # Command-line interface
│   ├── main.py              # Core program logic
│   ├── update.py             # Auto-update checker
│   ├── designer.py           # Qt UI definitions
│   ├── core/                 # Core algorithms
│   │   ├── data_processing.py
│   │   ├── fitting.py
│   │   ├── clustering.py
│   │   └── file_io.py
│   ├── models/               # Data models
│   │   └── force_curve.py
│   └── ui/                   # UI components
│       ├── main_window.py
│       ├── dialogs/
│       └── widgets/
├── tests/                    # Test suite
├── scripts/                  # User scripts
├── testdata/                 # Test data files
└── pyproject.toml           # Project configuration
```

## Development

### Running Tests

```bash
pytest tests/ -v
```

### Code Quality

```bash
# Lint with ruff
ruff check src/

# Type check with mypy
mypy src/
```

## Dependencies

- **numpy**: Numerical computing
- **pandas**: Data manipulation
- **scipy**: Scientific computing
- **matplotlib**: Plotting and visualization
- **scikit-learn**: Machine learning and clustering
- **PyQt5**: GUI framework
- **openpyxl/xlwt**: Excel file support

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## License

MIT License

## Citation

If you use DataYee in your research, please cite:

```
DataYee: Single-Molecule Force Spectroscopy Data Analysis Tool
https://github.com/Andachten/DataYee
```

## Support

- **Issues**: https://github.com/Andachten/DataYee/issues
- **Email**: [Contact the author]

## Acknowledgments

Developed for Single-Molecule Force Spectroscopy research.
