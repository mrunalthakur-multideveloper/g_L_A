"""
Google Colab Execution Script
Runs the Two-Tier Client-Driven Scraping Pipeline directly in Google Colab.
"""

import os
import subprocess
import sys


def setup_colab_environment():
    print("🚀 Preparing Google Colab Environment for Two-Tier Scraping Pipeline...\n")

    # Install requirements
    req_file = os.path.join(os.path.dirname(__file__), "requirements.txt")
    if os.path.exists(req_file):
        print("📦 Installing required dependencies from requirements.txt...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "-r", req_file])
        print("✅ Dependencies installed successfully.\n")

    # Launch pipeline
    print("🎯 Executing Two-Tier Client Pipeline...")
    pipeline_script = os.path.join(os.path.dirname(__file__), "run_crm_pipeline.py")
    subprocess.check_call([sys.executable, pipeline_script] + sys.argv[1:])


if __name__ == "__main__":
    setup_colab_environment()
