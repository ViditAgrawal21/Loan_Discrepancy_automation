"""
Fasal Rin Discrepancy Management Automation — Entry Point
Run: python main.py
"""

import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.dashboard import launch

if __name__ == "__main__":
    launch()
