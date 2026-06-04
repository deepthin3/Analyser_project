# ================================================================
# IBM i Source Code Intelligence — Main Orchestrator
# 
# HOW TO RUN:
#   python main.py
# 
# FIRST TIME SETUP:
#   1. Run: python sync.py (downloads sources from IBM i IFS to local folder)
#   2. Run: python main.py (analyses program and generates story)
# 
# SUBSEQUENT ANALYSES:
#   - Just run: python main.py (loads cached sources from local folder)
#   - Sources stay in local folder — no re-syncing needed
# 
# TO GET FRESH SOURCES:
#   - Run: python sync.py (when you need updated code from IBM i)
# 
# This file runs the analysis pipeline:
#   1. Load sources from local folder
#   2. Prompt for program name and libraries
#   3. AI Call 1: identify dependencies
#   4. Get object descriptions via SSH
#   5. AI Call 2: generate business story
#   6. Save output to .txt file
# ================================================================

import os
import sys
from dotenv import load_dotenv

# Import our own modules — each file in python_side/ becomes importable
import dep_finder   # dep_finder.py — AI call 1
import analyser     # analyser.py — AI call 2
from pathlib import Path  # Path = easier file path handling than os.path
 
# Load .env file at the very start
load_dotenv()

def load_all_sources(local_path):
    #Load all .txt source files from local folder into memory.
    #Returns a dictionary: {PROGRAMNAME: source_text}
    #Also returns source_types: {PROGRAMNAME: RPGLE/PF/LF/etc}


    sources = {}       # Will hold: {'OIS100': '...source code...'}
    source_types = {} 
    path = Path(local_path)

    if not path.exists():
        # If sources folder does not exist, something went wrong with sync
        print(f'ERROR: Sources folder not found: {local_path}')
        return {}, {}

        # Iterate over all .txt files in the sources folder
    # sorted() puts them in alphabetical order — consistent behaviour
    for file in sorted(path.glob('*.txt')):
        # path.glob('*.txt') finds all files ending in .txt
        # file is a Path object — file.stem = filename without .txt extension
        stem  = file.stem   # e.g. 'OIS100_RPGLE'
        parts = stem.split('_')  # ['OIS100', 'RPGLE']
        
        stype = parts[-1].upper() if len(parts) >= 2 else 'UNKNOWN'
        # Extract name from stem: first part before underscore
        name = parts[0].upper() if parts else stem.upper()
 
        # Read the file content as text
        # errors='replace' replaces unreadable characters instead of crashing
        content = file.read_text(encoding='utf-8', errors='replace')
 
        # Store in dictionary — key is program name, value is source text
        sources[name] = content
        source_types[name] = stype 
    print(f'Loaded {len(sources)} source members into memory.')
    print(f'Types: {dict([(t, list(source_types.values()).count(t)) for t in set(source_types.values())])}')

    # Return BOTH dictionaries — caller needs both
    return sources, source_types

def print_welcome():
 
    print()
    print('=' * 60)
    print('  IBM i SOURCE CODE INTELLIGENCE')
    print('  AI-powered program analyser')
    print('=' * 60)
    print()
    print('This tool will:')
    print('  1. Download sources from your IBM i system')
    print('  2. Use AI to identify program dependencies')
    print('  3. Generate a detailed business story explanation')
    print('  4. Save the analysis as a .txt file')
    print()

def get_user_inputs():
    print('-' * 60)
    print('STEP 1: Enter your inputs')
    print('-' * 60)
    print()


    # Get program name
    while True:
        # while True = keep looping until we break out
        program = input('Enter the program name to analyse: ').strip().upper()
        # .strip() removes spaces from start and end
        # .upper() converts to uppercase
 
        if program:
            # If program is not empty, we have a valid input
            break   # break exits the while loop
        # If empty, the loop continues and asks again
        print('  Program name cannot be empty. Please try again.')
 
    print()
    print('Enter library names where your sources are stored.')
    print('Separate multiple libraries with commas.')
    print('Example: LEAVELIB,INVLIB,MYLIB')
    print()
 
    while True:
        pgm_library = input('Program library (where your programs are): ').strip().upper()
        dta_library = input('Data/File library (where your PF/LF files are): ').strip().upper()
 
        if pgm_library and dta_library:
            # If both libraries are provided, we have valid input
            break
        print('  At least one library is required. Please try again.')
 
    print()
    print(f'  Program : {program}')
    print(f'  Libraries: {pgm_library} (programs), {dta_library} (files)')
    print()
 
    # Ask for confirmation before starting
    confirm = input('Start analysis? (Y/N): ').strip().upper()
    if confirm != 'Y':
        print('Analysis cancelled.')
        sys.exit(0)   # sys.exit(0) ends the program cleanly
 
    return program, pgm_library, dta_library

def validate_environment():
    """Validate that all required environment variables are set."""
    required_vars = [
        'OPENAI_API_KEY',
        'IBMI_HOST',
        'IBMI_USER',
        'IBMI_PASS',
        'IFS_PATH',
        'LOCAL_PATH'
    ]
    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        print('ERROR: Missing required environment variables:')
        for var in missing:
            print(f'  - {var}')
        print('\nCheck your .env file and try again.')
        sys.exit(1)

def main():
    """Main function — runs the complete pipeline"""
    
    # Validate environment before starting
    validate_environment()
 
    print_welcome()
 
    # Get program name and library list from user
    program_name, pgm_library, dta_library = get_user_inputs()
 
    local_path = os.getenv('LOCAL_PATH', './sources')
 
    print()
    print('=' * 60)
    print('STEP 2: Loading sources from local folder')
    print('=' * 60)
    
    # Check if sources folder exists and has files
    source_path = Path(local_path)
    if not source_path.exists() or len(list(source_path.glob('*.txt'))) == 0:
        print(f'ERROR: No sources found in {local_path}')
        print()
        print('Sources must be synced from IBM i first.')
        print('Run this command to download sources:')
        print('  python sync.py')
        print()
        print('Then run main.py again to analyse programs.')
        sys.exit(1)
 
    # Load all downloaded source files into Python memory
    all_sources, source_types = load_all_sources(local_path)

     
    if not all_sources:
        print('ERROR: No sources found. Check that sources folder is not empty.')
        sys.exit(1)
 
    # Check that the requested program actually exists
    if program_name not in all_sources:
        print(f'ERROR: Program {program_name} not found in loaded sources.')
        print(f'Available programs (first 20): {list(all_sources.keys())[:20]}')
        sys.exit(1)
 
    print()
    print('=' * 60)
    print('STEP 3: AI identifying dependencies')
    print('=' * 60)
 
    # Get the source of the requested program
    program_source = all_sources[program_name]
 
    # Call dep_finder to make the first AI call
    try:
        dependencies = dep_finder.find_dependencies(program_name, program_source)
    except Exception as e:
        print(f'ERROR: AI dependency analysis failed: {str(e)}')
        print('This may be due to API rate limits, network issues, or invalid API key.')
        sys.exit(1)
 
    print()
    print('=' * 60)
    print('STEP 4: Generating business story analysis')
    print('=' * 60)

    # Get the library from our list — use first library as primary
     
 
    # Call analyser to make the second AI call and save output
    try:
        analysis = analyser.analyse(
            program_name,
            dependencies,
            all_sources,
            source_types,
            pgm_library,
            dta_library
        )
    except Exception as e:
        print(f'ERROR: Business story analysis failed: {str(e)}')
        print('This may be due to API rate limits, network issues, or file write permissions.')
        sys.exit(1)
 
    print()
    print('=' * 60)
    print('ANALYSIS COMPLETE')

    print('=' * 60)
    print()
    print(f'Output file: {program_name}_analysis.txt')
    print()
    print('NEXT STEPS:')
    print()
    print('To analyse another program:')
    print('  python main.py')
    print('  (Sources stay in local folder — no need to re-sync)')
    print()
    print('To get fresh sources from IBM i (new libraries or updated code):')
    print('  python sync.py')
    print('  Then run python main.py to analyse')
    print()
    print('To analyse a program that was identified as a dependency:')
    print('  Run python main.py and enter the dependency program name')
    print()
 
 
# This ensures main() only runs when you execute 'python main.py' directly
# If another file imports main.py, main() does not auto-run
if __name__ == '__main__':
    main()







