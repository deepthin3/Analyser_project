# AI Call 2 - Generate business story analysis.
# Assembles full context and produces explanation
# Saves output to PROGNAME_analysis.txt


import os 
import json
import datetime
from openai import OpenAI
from dotenv import load_dotenv
import obj_desc  # Import our own obj_desc module to use get_pf_from_lf

load_dotenv()   
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def analyse(program_name, dependencies, all_sources, source_types, pgm_library, dta_library):
    print(f'\nBuilding context for second AI call...')
 
    # ================================================================
    # STEP 1: Get the input program source
    # ================================================================
    input_source = all_sources.get(program_name.upper(), '')
    if not input_source:
        print(f'ERROR: Source for {program_name} not found in memory')
        return ''

    # ================================================================
    # STEP 2: Identify all LF files used by this program
    # An LF is a logical file — a view/index built on top of a PF
    # ================================================================
    # Use the `source_types` passed in by the caller (loaded by main.load_all_sources)

    lf_names = []  # List of LF names used by the program
    pf_names = []  # List of PF names — direct and base PFs of LFs
    dspf_names = []  # List of display files used (if any)
    prtf_names = []  # List of printer files used (if any)
    
    # Get display and printer files directly from dependencies
    # (AI has already identified these specifically)
    dspf_names = [f.upper() for f in dependencies.get('display_files', [])]
    prtf_names = [f.upper() for f in dependencies.get('printer_files', [])]
    
    # Process used_files to categorize PF and LF
    for fname in dependencies.get('used_files', []):
        fname_upper = fname.upper()
        src_type = source_types.get(fname_upper, 'UNKNOWN')
        if src_type == 'LF':
            lf_names.append(fname_upper)
        elif src_type == 'PF':
            pf_names.append(fname_upper)
        elif src_type == 'DSPF':
            dspf_names.append(fname_upper)
        elif src_type == 'PRTF':
            prtf_names.append(fname_upper)
 
    print(f'  LFs found: {lf_names}')
    print(f'  PFs found (direct): {pf_names}')
    print(f'  DSPFs found: {dspf_names}')
    print(f'  PRTFs found: {prtf_names}')

    # ================================================================
    # STEP 3: For each LF, find its base PF using PFILE keyword
    # ================================================================

    for lf_name in lf_names:
        lf_source = all_sources.get(lf_name, '')
        if lf_source:
            base_pf = obj_desc.get_pf_from_lf(lf_source)
            if base_pf and base_pf not in pf_names:
                # Only add if we have not already included this PF
                pf_names.append(base_pf)
                print(f'  Base PF for {lf_name}: {base_pf}')
 
    print(f'  Total PFs (including base PFs): {pf_names}')

    # ================================================================
    # STEP 4: Get object descriptions for called programs via SSH
    # ================================================================
    called_programs = dependencies.get('called_programs', [])
    # Filter out DYNAMIC_CALL_VAR — that is not a real program name
    called_programs = [p for p in called_programs if p != 'DYNAMIC_CALL_VAR']
 
    used_files = dependencies.get('used_files', [])
    display_files_dep = dependencies.get('display_files', [])
    printer_files_dep = dependencies.get('printer_files', [])
    
    # Combine all files to get descriptions
    all_files_to_describe = used_files + display_files_dep + printer_files_dep
    descriptions = obj_desc.get_descriptions(called_programs + all_files_to_describe, pgm_library, dta_library, source_types)

    # Split descriptions back for separate use in context building
    program_descriptions = {
        k: v for k, v in descriptions.items()
        if k in called_programs
    }
    file_descriptions = {
        k: v for k, v in descriptions.items()
        if k in all_files_to_describe
    }
    print(f'  Program descriptions found: '
          f'{sum(1 for v in program_descriptions.values() if v != "No description available")}')
    print(f'  File descriptions found: '
          f'{sum(1 for v in file_descriptions.values() if v != "No description available")}')

    # ================================================================
    # STEP 5: Build the context string to send to AI
    # ================================================================
    context_parts = []
 
    # Always start with the input program
    context_parts.append(f'=== INPUT PROGRAM: {program_name} ===')
    context_parts.append(input_source)
 
    # Add all LF sources
    for lf_name in lf_names:
        lf_source = all_sources.get(lf_name, '')
        if lf_source:
            context_parts.append(f'\n=== LOGICAL FILE: {lf_name} ===')
            context_parts.append(lf_source)

        # Add all PF sources — deduplicated (no duplicates)
    # set() removes duplicates, list() converts back to list
    unique_pfs = list(set(pf_names))
    for pf_name in unique_pfs:
        pf_source = all_sources.get(pf_name, '')
        if pf_source:
            context_parts.append(f'\n=== PHYSICAL FILE: {pf_name} ===')
            context_parts.append(pf_source)

    # Add all DSPF sources  
    for dspf_name in dspf_names:
        dspf_source = all_sources.get(dspf_name, '')
        if dspf_source:
            context_parts.append(f'\n=== DISPLAY FILE: {dspf_name} ===')
            context_parts.append(dspf_source)

    # Add all PRTF sources — deduplicated (no duplicates)
     
    for prtf_name in prtf_names:
        prtf_source = all_sources.get(prtf_name, '')
        if prtf_source:
            context_parts.append(f'\n=== PRINTER FILE: {prtf_name} ===')
            context_parts.append(prtf_source)

        # Build descriptions section
    # Add program descriptions to context
    if program_descriptions:
        context_parts.append('\n=== CALLED PROGRAM DESCRIPTIONS ===')
        for prog, desc in program_descriptions.items():
            context_parts.append(f'{prog}: {desc}')

    # Add file descriptions to context — NEW
    if file_descriptions:
        context_parts.append('\n=== FILE DESCRIPTIONS ===')
        for fname, fdesc in file_descriptions.items():
            ftype = source_types.get(fname, 'FILE')
            context_parts.append(f'{fname} ({ftype}): {fdesc}')
    
    # If any dynamic calls were found, mention them
    if 'DYNAMIC_CALL_VAR' in dependencies.get('called_programs', []):
        context_parts.append('\n=== NOTE ===')
        context_parts.append('This program contains dynamic CALL statements using variables.')
        context_parts.append('The actual program called at runtime depends on the variable value.')

        # Join all parts into one big string
    # '\n\n'.join = put two newlines between each part
    full_context = '\n\n'.join(context_parts)
 
    print(f'  Context assembled. Estimated size: {len(full_context)//4} tokens')

    prompt = f"""You are a senior IBM i developer and business analyst with 20 years of experience.
You have worked on manufacturing ERP, financial systems, and large IBM i modernisation projects.
You deeply understand RPG III, RPG IV fixed format, free-format RPGLE, CL, CLLE, and DB2 for i.

I have given you:
- The full source code of the program to analyse
- DDS sources of all logical files (LF) and physical files (PF) it uses
- Text descriptions of programs it calls

Your job is to explain {program_name} in a way that serves BOTH a developer and a business audience.
- Business audience: needs to understand what this program does in plain English, why it exists,
  what business rules it enforces, and what would break if it stopped working.
- Developer audience: needs enough technical detail to navigate the code — variable names,
  file names, called program names, SQL references — so they can cross-reference with the source.

The tone should be a business narrative with technical anchors woven in.
Not pure code commentary. Not pure business language. Both together.

Structure your response EXACTLY as follows. Use the exact headers shown.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PROGRAM: {program_name}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

━━━ WHAT THIS PROGRAM DOES ━━━
Write 3-4 sentences in plain English.
What business process does this program serve?
What role does it play — is it an entry point, a background processor, a validation routine, a report?
What would break or stop working if this program was removed?

━━━ PROGRAM INTERFACE ━━━
List all input and output parameters.
While checking the parameters keep in mind that this program can be fixed format, free format or both.
For each parameter:
  - Parameter name (exact variable name from source e.g. pEmpNo)
  - Direction: INPUT / OUTPUT / INPUT-OUTPUT
  - Data type and length (e.g. CHAR(7), PACKED(9:2), DATE)
  - Business meaning in plain English (e.g. "The employee number identifying who is requesting leave")
If the program has no parameters write: This program takes no parameters — it runs standalone.

━━━ THE BUSINESS STORY — STEP BY STEP ━━━
This is the most important section. Number every step.

For each step write it as a business narrative — what is happening, why, and what decision is made.
Also include in brackets the technical anchor so a developer can find it in the code.

Format for each step:
Step N — [Brief step title]
  Business: What is happening in plain terms. Why this step exists. What the business rule is.
            What happens if this check or action fails.
  Technical: Variable names, file names, opcodes, or SQL reference involved.
             e.g. (CHAIN pEmpNo EMPMST — checks employee master)
             e.g. (EXEC SQL-1: SELECT from LEAVEPF — see SQL Operations section)
             e.g. (Calls CUSTVAL — see Programs Called section for detail)

Good example:
  Step 1 — Validate Employee Exists
  Business: Before any leave request can be processed, the program confirms the employee
            number is registered in the system. If the employee is not found, the program
            stops immediately and returns an error — no leave can be applied for an
            unrecognised employee number.
  Technical: (CHAIN pEmpNo EMPMST — %FOUND(EMPMST) checked — if not found pStatus set to
             'NOT_FOUND' and program returns)

Bad example:
  Step 1 — CHAIN pEmpNo EMPMST sets indicator.

When a step involves calling another program, include a one-line business summary of what
that called program does — do not just say "calls CUSTVAL", say what CUSTVAL achieves
in business terms. Full detail of called programs is in the Programs Called section.

When a step involves an SQL operation, reference it as (SQL-N) so the reader
can look it up in the SQL Operations section.

When a step involves a special operation like OVRDBF, CPYF, or SBMJOB,
explain it inline as part of that step's narrative.

Cover every significant section of the program. Do not skip validations or
error paths — those are often the most important business rules.

━━━ FILES AND DATA ━━━
Show every file the program uses.
For each file:
  File Name (exact) | Type (PF/LF/DSPF/PRTF) | Business meaning | How used (Read/Write/Update/Delete)

If you have the DDS source, decode the field names into plain English for the fields
actually used by this program.
Example: SAPR = Sales Price, CUNO = Customer Number, ORST = Order Status
Focus on fields that appear in the program logic — not every field in the file.

━━━ PROGRAMS CALLED ━━━
List every external program this program calls.
For each:
  - Program name (exact)
  - What triggers the call — under what business condition
  - What it does in business terms (use description if available, infer from name and context)
  - What data is passed in and what comes back

If there are dynamic calls (CALL using a variable), note that the actual program
depends on the value of the variable at runtime and explain what that variable represents.

━━━ SQL OPERATIONS ━━━
Number each SQL operation as SQL-1, SQL-2 etc (matching references in the business story).
For each:
  - SQL-N: Type (SELECT/INSERT/UPDATE/DELETE/CALL)
  - Table involved
  - What it achieves in business terms
  - Key WHERE conditions or JOIN logic explained in plain English
  - Variables used (e.g. :pEmpNo, :wStatus)

━━━ ERROR HANDLING ━━━
List every error condition the program handles.
For each:
  - What can go wrong (business scenario not just technical)
  - How the program responds
  - What the user or calling program receives — message text if visible in source
  - Any error conditions NOT handled that could be a risk in production

━━━ OVERALL ASSESSMENT ━━━
Two short paragraphs:
  Paragraph 1 — Business: Is this a critical program or a supporting one? What breaks without it?
                How does it fit into the bigger application flow?
  Paragraph 2 — Developer: Any important observations before modifying this program.
                Hardcoded values, missing error handling, DSPLY or DUMP statements
                left in (debug code), tightly coupled dependencies, or anything a
                developer must know before making changes.

Here is the source code and context:

{full_context}"""





# ================================================================
# STEP 7: Make the second AI call
# ================================================================
    print('\nAI Call 2: Generating business story analysis...')
    print('This may take 15-30 seconds...')
 
    try:
        response = client.chat.completions.create(
            model='gpt-4o-mini',
            messages=[{'role': 'user', 'content': prompt}],
            temperature=0.3,    # Slightly higher than dep_finder — allows more natural language
            max_tokens=4000,
            timeout=120  # 120 second timeout for longer analysis
        )
    except Exception as e:
        print(f'  ERROR: OpenAI API call failed: {str(e)}')
        raise
        
    analysis_text = response.choices[0].message.content
    tokens_used   = response.usage.total_tokens
    print(f'  Analysis complete. Tokens used: {tokens_used}')
    print(f'  Estimated cost: ${tokens_used * 0.0000006:.4f} (less than ₹0.10)')

        # ================================================================
    # STEP 8: Save output to .txt file
    # ================================================================
    # datetime.now() = current date and time
    # strftime formats it as a readable string
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    output_dir = 'output'
    os.makedirs(output_dir, exist_ok=True)
    output_filename = os.path.join(output_dir, f'{program_name}_analysis.txt')
 
    # Build the full file content
    file_content = (
        f'IBM i Source Code Intelligence\n'
        f'Program: {program_name}\n'
        f'Library: {pgm_library}\n'
        f'Generated: {timestamp}\n'
        f'{'=' * 60}\n\n'
        f'{analysis_text}\n'
    )

    # Write to file
    # 'w' = write mode — creates file if not exists, overwrites if exists
    # encoding='utf-8' = standard text encoding
    try:
        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write(file_content)
        print(f'\n  Analysis saved to: {output_filename}')
    except IOError as e:
        print(f'  ERROR: Could not write analysis to {output_filename}: {str(e)}')
        raise
 
    # NOTE: To also save as PDF, install md2pdf and add:
    # from md2pdf.core import md2pdf
    # md2pdf(f'{program_name}_analysis.pdf', md_content=file_content)
    # That single line converts the text to a PDF file.
 
    return analysis_text


