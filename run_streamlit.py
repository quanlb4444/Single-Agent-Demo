#!/usr/bin/env python3
"""
Script to run Streamlit app for Single Agent Demo
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    print("🚀 Starting Single Agent Demo Streamlit App...")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("app.py").exists():
        print("❌ Please run this script from the single_agent_demo directory")
        sys.exit(1)
    
    # Check if virtual environment exists
    if not Path(".venv").exists():
        print("❌ Virtual environment not found. Please run setup.py first:")
        print("   python setup.py")
        sys.exit(1)
    
    # Determine pip command based on OS
    if os.name == 'nt':  # Windows
        pip_cmd = ".venv\\Scripts\\pip"
        python_cmd = ".venv\\Scripts\\python"
    else:  # Unix/Linux/macOS
        pip_cmd = ".venv/bin/pip"
        python_cmd = ".venv/bin/python"
    
    # Install streamlit if not already installed
    print("📦 Checking dependencies...")
    try:
        result = subprocess.run([pip_cmd, "show", "streamlit"], 
                              capture_output=True, text=True, check=True)
        print("✅ Streamlit already installed")
    except subprocess.CalledProcessError:
        print("📦 Installing Streamlit...")
        subprocess.run([pip_cmd, "install", "streamlit>=1.28.0"], check=True)
        print("✅ Streamlit installed")
    
    # Run streamlit app
    print("\n🌐 Starting Streamlit app...")
    print("📍 The app will open in your browser at: http://localhost:8501")
    print("🛑 Press Ctrl+C to stop the app")
    print("=" * 50)
    
    try:
        subprocess.run([python_cmd, "-m", "streamlit", "run", "app.py"], check=True)
    except KeyboardInterrupt:
        print("\n👋 App stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running Streamlit: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
