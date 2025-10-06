#!/usr/bin/env python3
"""
Setup script for Single Agent Demo
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def main():
    print("🚀 Setting up Single Agent Demo...")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("requirements.txt").exists():
        print("❌ Please run this script from the single_agent_demo directory")
        sys.exit(1)
    
    # Create virtual environment
    if not Path(".venv").exists():
        if not run_command("python -m venv .venv", "Creating virtual environment"):
            sys.exit(1)
    else:
        print("✅ Virtual environment already exists")
    
    # Activate virtual environment and install dependencies
    if os.name == 'nt':  # Windows
        activate_cmd = ".venv\\Scripts\\activate"
        pip_cmd = ".venv\\Scripts\\pip"
    else:  # Unix/Linux/macOS
        activate_cmd = "source .venv/bin/activate"
        pip_cmd = ".venv/bin/pip"
    
    if not run_command(f"{pip_cmd} install -r requirements.txt", "Installing dependencies"):
        sys.exit(1)
    
    # Copy .env.example to .env if it doesn't exist
    if not Path(".env").exists():
        if Path(".env.example").exists():
            run_command("cp .env.example .env", "Creating .env file from template")
        else:
            print("⚠️  .env.example not found, creating basic .env file")
            with open(".env", "w") as f:
                f.write("OPENAI_API_KEY=\nOPENAI_MODEL=gpt-4o-mini\nWEATHER_API_BASE=https://api.open-meteo.com/v1/forecast\n")
    
    # Run structure test
    print("\n🧪 Testing structure...")
    if run_command(f"{pip_cmd} run python test_structure.py", "Running structure tests"):
        print("\n🎉 Setup completed successfully!")
        print("\nTo run the demo:")
        if os.name == 'nt':
            print("  .venv\\Scripts\\python main.py")
        else:
            print("  source .venv/bin/activate && python main.py")
    else:
        print("\n⚠️  Setup completed but tests failed. Check the errors above.")

if __name__ == "__main__":
    main()
