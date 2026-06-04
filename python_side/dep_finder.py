# AI call 1 - Find all the dependencies of the input program
# Sends program source to OpenAI and gets back a structured JSON
# with called programs, used files, submitted jobs and copybooks

import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
#Create the OpenAI client using the API key from the .env file
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def find_dependencies(program_name, source_code):
    print(f'AI Call 1: Identifying dependencies of {program_name}...')
    print(f'AI Call 1: Identifying dependencies of {program_name}...')
 
    prompt = f"""You are an expert IBM i developer with 20 years of experience
in RPG III, RPG IV fixed format, free-format RPGLE, CL, and CLLE.

Analyse this IBM i source code and identify its dependencies.

Return ONLY a JSON object. No explanation. No markdown. No code fences.

{{
  "called_programs": [],
  "used_files": [],
  "display_files": [],
  "printer_files": [],
  "submitted_jobs": [],
  "copybooks": []
}}

════════════════════════════════════════
FIXED FORMAT F SPEC FILE IDENTIFICATION
════════════════════════════════════════
Fixed format F spec lines start with the letter F followed immediately
by the filename. To extract the filename from any fixed format F spec line:
  Step 1: WITHOUT FAIL Remove the very first character (it is always F — the spec indicator)
  Step 2: Take the next 10 characters
  Step 3: Strip spaces — the result is the filename

Example: FAIRLINEDSPCF   E             WORKSTN
  Remove first char F → AIRLINEDSPCF   E             WORKSTN
  Take 10 chars       → AIRLINEDSP
  Filename            = AIRLINEDSP → goes in display_files (WORKSTN present)

Example: FAIRMASTER UF A E           K DISK
  Remove first char F → AIRMASTER UF A E           K DISK
  Take 10 chars       → AIRMASTER 
  Filename            = AIRMASTER → goes in used_files (DISK present)

Example: FAIRMASL1  IF   E           K DISK
  Remove first char F → AIRMASL1  IF   E           K DISK
  Take 10 chars       → AIRMASL1
  Filename            = AIRMASL1 → goes in used_files (DISK present)

Example: FLEAVERPT  O    E             PRINTER OFLIND(*INOF)
  Remove first char F → LEAVERPT  O    E             PRINTER OFLIND(*INOF)
  Take 10 chars       → LEAVERPT
  Filename            = LEAVERPT → goes in printer_files (PRINTER present)

Classify the extracted filename based on device keyword on the same line:
  WORKSTN present → display_files
  PRINTER present → printer_files
  DISK present    → used_files

Continuation F spec lines have F followed by spaces — no filename after F.
These are continuations of the previous file declaration — ignore them.
Example: F                                     infds(dinfds)
  Remove F → all spaces → no filename → ignore this line completely

════════════════════════════════════════
FREE FORMAT FILE IDENTIFICATION
════════════════════════════════════════
For free format RPGLE DCL-F declarations:
Use your expert IBM i knowledge to identify files naturally.
You understand free format RPGLE. Identify the filename and classify
as database, display, or printer based on the keywords present.

════════════════════════════════════════
OTHER DEPENDENCIES
════════════════════════════════════════
- called_programs:
  CALL, CALLP, CALLB targets — extract the program name only.
  QCMDEXC containing CALL — extract the called program name.
  declared as prototypes using PR in D specs or DCL-PR — extract the program name from the prototype.
  If a variable is used instead of a literal name add DYNAMIC_CALL_VAR.

- submitted_jobs:
  Program name from SBMJOB CMD(CALL PROGNAME) or
  SBMJOB CMD(CALL PGM(PROGNAME)) — return program name only.

- copybooks:
  /COPY SOURCEFILE,MEMBERNAME — return MEMBERNAME only (after last comma).
  /COPY MEMBERNAME — return MEMBERNAME only.
  NEVER return QRPGLESRC, QCLLESRC, QLLESRC or any source file name.
  NEVER return library names.
  ALWAYS return only the final token after the last comma.

════════════════════════════════════════
WHAT NOT TO INCLUDE — EVER
════════════════════════════════════════
- Record format names accessed via EXFMT, WRITE, READ, READC, READP
- Subfile format names from sfile() parameter
- Data structure names from LIKEREC() or EXTNAME()
- Key field names from CHAIN or READ (first operand is key, second is file)
- System programs: QCMDEXC, QSYS, QSYS2, QUSRWRK
- SQL system tables: QSYS2.SYSPARTITIONSTAT etc
- Any name longer than 10 characters (all IBM i names are max 10 chars)
- Continuation F spec lines (F followed by spaces — no filename)

If a section has no items return empty list [].

Program name: {program_name}

Source code:
{source_code}"""
    
    # Make the API call to OpenAI
    # model = which AI model to use — gpt-4o-mini is cheap and capable
    # temperature = 0.1 means very consistent answers, little variation
    # max_tokens = maximum length of AI response — JSON is short so 1000 is enough

    try:
        response = client.chat.completions.create(
            model='gpt-4o-mini',
            messages=[{'role': 'user', 'content': prompt}],
            temperature=0.1,
            max_tokens=1000,
            timeout=60  # 60 second timeout to catch hanging requests
        )
    except Exception as e:
        print(f'  ERROR: OpenAI API call failed: {str(e)}')
        raise

    # Extract the text response from the API result
    # response.choices[0] = first (and only) answer
    # .message.content = the actual text
    raw_text = response.choices[0].message.content.strip()

    # Parse the JSON text into a Python dictionary
    try:
        # json.loads converts JSON text string into a Python dictionary
        deps = json.loads(raw_text)

    except json.JSONDecodeError:
        # If AI returned something that is not valid JSON, use empty defaults
        # This should be rare with temperature=0.1 and clear instructions
        print('  WARNING: AI returned non-JSON response. Using empty dependencies.')
        print(f'  Raw response: {raw_text[:200]}')
        deps = {
            'called_programs': [],
            'used_files': [],
            'display_files': [],
            'printer_files': [],
            'submitted_jobs': [],
            'copybooks': []
        }

    # Print what was found so the developer can see progress
    print(f'  Called programs : {deps.get("called_programs", [])}')
    print(f'  Used files      : {deps.get("used_files", [])}')
    print(f'  Display files   : {deps.get("display_files", [])}')
    print(f'  Printer files   : {deps.get("printer_files", [])}')
    print(f'  Submitted jobs  : {deps.get("submitted_jobs", [])}')
    print(f'  Copybooks       : {deps.get("copybooks", [])}')

    # Save to a JSON file on disk for debugging and audit trail
    # This lets you open the file and see exactly what AI found
    output_dir = 'output'
    os.makedirs(output_dir, exist_ok=True)
    json_file = os.path.join(output_dir, f'{program_name}_deps.json')

    try:
        with open(json_file, 'w') as f:
            # json.dump writes Python dictionary to a file as JSON text
            # indent=2 makes it human-readable with indentation
            json.dump(deps, f, indent=2)
        print(f'  Dependencies saved to {json_file}')
    except IOError as e:
        print(f'  WARNING: Could not save dependencies to {json_file}: {str(e)}')
        print('  Continuing without saving to file...')
 
    return deps

