"""Command-line interface for DataYee.

Usage:
    python -m datayee              # Launch GUI
    python -m datayee --help      # Show help
    python -m datayee file.jpk    # Open file directly
"""
from __future__ import annotations

import sys
import argparse
from pathlib import Path
from typing import Optional

import matplotlib as mpl
import matplotlib.style as mplstyle

mplstyle.use('fast')
mpl.rcParams['path.simplify_threshold'] = 1.0
mpl.rcParams['font.family'] = 'Arial'
mpl.rcParams['axes.labelsize'] = 16
mpl.rcParams['axes.labelweight'] = 'normal'
mpl.rcParams['axes.linewidth'] = 1.5
mpl.rcParams['font.size'] = 12
mpl.rcParams['axes.spines.right'] = False
mpl.rcParams['axes.spines.top'] = False
mpl.rcParams['figure.subplot.left'] = 0.05
mpl.rcParams['figure.subplot.right'] = 1
mpl.rcParams['figure.subplot.top'] = 1
mpl.rcParams['figure.subplot.bottom'] = 0.05


def setup_gui(file_path: Optional[str] = None) -> None:
    """Launch the DataYee GUI application.

    Args:
        file_path: Optional file to open on startup
    """
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtCore import Qt
    
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    app = QApplication(sys.argv)
    app.setApplicationName("DataYee")
    app.setOrganizationName("SMFS")
    app.setAttribute(Qt.AA_EnableHighDpiScaling)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps)
    from src.ui.main_window import MyMainWindow
    from src.ui.dialogs.windows import (
        ParaWindow,
        DLCRangeWindow,
        ShowImageWindow,
        StatisticsWindow,
        ScriptWindow,
    )

    app = QApplication(sys.argv)
    app.setApplicationName("DataYee")
    app.setOrganizationName("SMFS")

    myWin = MyMainWindow()

    if file_path:
        myWin.fname = file_path
        myWin.pb.creattask(file_path)

    child_window0 = ParaWindow(myWin.pb, myWin)
    child_window1 = DLCRangeWindow(myWin)
    child_window2 = StatisticsWindow(myWin)
    child_window3 = ScriptWindow(myWin)
    _connect_child_windows(myWin, [child_window0, child_window1, child_window2, child_window3])

    myWin.show()
    sys.exit(app.exec_())


def _connect_child_windows(main_win: 'MyMainWindow', dialog: list) -> None:
    """Connect child window signals to main window actions."""
    main_win.actionparameters_setting.triggered.connect(dialog[0].show)
    main_win.actionmark_base_on_dlc.triggered.connect(dialog[1].show)
    main_win.actionHistogram_scatter.triggered.connect(dialog[2].show)
    main_win.actionScript.triggered.connect(dialog[3].show)


def main() -> None:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        prog="datayee",
        description="DataYee - Single-Molecule Force Spectroscopy Data Analysis Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  datayee                           Launch GUI
  datayee file.jpk-force            Open JPK force file
  datayee --batch directory/        Batch process directory
        """
    )

    parser.add_argument(
        "file",
        nargs="?",
        help="Force curve file to open (.jpk-force, .txt, .spm, .DataYee-force)"
    )

    parser.add_argument(
        "--batch", "-b",
        metavar="DIRECTORY",
        help="Process all force curves in directory"
    )

    parser.add_argument(
        "--version", "-v",
        action="version",
        version="%(prog)s 0.1.0"
    )

    parser.add_argument(
        "--theme",
        choices=["light", "dark"],
        default="light",
        help="Set GUI theme (default: light)"
    )

    args = parser.parse_args()

    if args.batch:
        print(f"Batch processing: {args.batch}")
        print("Note: Batch processing not yet implemented, launching GUI...")
        setup_gui()

    if args.file:
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"Error: File not found: {file_path}", file=sys.stderr)
            sys.exit(1)
        setup_gui(str(file_path))
    else:
        setup_gui()


if __name__ == "__main__":
    main()
