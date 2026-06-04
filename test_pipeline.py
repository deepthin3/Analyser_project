#!/usr/bin/env python3
"""Test script to skip sync and test analysis pipeline directly"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add python_side to path so we can import modules
sys.path.insert(0, str(Path(__file__).parent / 'python_side'))

import dep_finder
import analyser
from python_side.main import load_all_sources

load_dotenv()

def main():
    local_path = os.getenv('LOCAL_PATH', './sources')
    
    print("=" * 60)
    print("TEST: Loading sources into memory")
    print("=" * 60)
    
    all_sources, source_types = load_all_sources(local_path)
    
    if not all_sources:
        print("ERROR: No sources found!")
        sys.exit(1)
    
    program_name = 'AIRLINERP'
    
    if program_name not in all_sources:
        print(f"ERROR: {program_name} not found!")
        print(f"Available: {list(all_sources.keys())[:10]}")
        sys.exit(1)
    
    print(f"[OK] Loaded {len(all_sources)} sources")
    print(f"[OK] Found program: {program_name}")
    
    print()
    print("=" * 60)
    print("TEST: Finding dependencies (AI Call 1)")
    print("=" * 60)
    
    program_source = all_sources[program_name]
    
    try:
        dependencies = dep_finder.find_dependencies(program_name, program_source)
        print(f"[OK] Found dependencies: {dependencies}")
    except Exception as e:
        print(f"[ERROR] FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print()
    print("=" * 60)
    print("TEST: Analyzing program (AI Call 2)")
    print("=" * 60)
    
    pgm_library = os.getenv('IBMI_LIBRARY', 'VAVAN1')
    dta_library = os.getenv('IBMI_LIBRARY', 'VAVAN1')
    
    try:
        analysis = analyser.analyse(
            program_name,
            dependencies,
            all_sources,
            source_types,
            pgm_library,
            dta_library
        )
        print("[OK] Analysis complete!")
        print(f"[OK] Output file created: {program_name}_analysis.txt")
    except Exception as e:
        print(f"[ERROR] FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
