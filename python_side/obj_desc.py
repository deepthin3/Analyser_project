# Gets IBMi object descriptions via paramiko SSH
# Queries QSYS2.OBJECT_STATISTICS for info about files using QSH

import os 
import paramiko
from dotenv import load_dotenv
from pathlib import Path

# Load .env from parent directory (project root)
load_dotenv(dotenv_path=Path(__file__).parent.parent / '.env')

def get_descriptions(object_names, pgm_library, dta_library, source_types=None):
    """
    Get object descriptions from IBM i via paramiko SSH.
    Uses DSPOBJD via system command — confirmed working on pub400.
    Parses the Text field from DSPOBJD output.
    """
    if not object_names:
        return {}

    host     = os.getenv('IBMI_HOST')
    user     = os.getenv('IBMI_USER')
    password = os.getenv('IBMI_PASS')
    port     = 2222

    FILE_TYPES = {'PF', 'LF', 'DSPF', 'PRTF'}

    descriptions = {
        n.upper(): 'No description available'
        for n in object_names
    }

    if not all([host, user, password]):
        print('  WARNING: Missing SSH credentials — skipping descriptions')
        return descriptions

    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=host, username=user,
                    password=password, port=port, timeout=30)

        for obj_name in object_names:
            obj_upper = obj_name.upper()
            stype     = (source_types or {}).get(obj_upper, 'UNKNOWN')
            library   = dta_library if stype in FILE_TYPES else pgm_library

            # Determine object type for DSPOBJD
            if stype in {'PF', 'LF', 'DSPF', 'PRTF'}:
                obj_type = '*FILE'
            else:
                obj_type = '*PGM'

            # Run DSPOBJD via system command — confirmed working on pub400
            cmd = (
                f"system 'DSPOBJD OBJ({library}/{obj_upper}) "
                f"OBJTYPE({obj_type})'"
            )

            stdin, stdout, stderr = ssh.exec_command(cmd)
            out = stdout.read().decode('utf-8', errors='ignore')

            # Parse the Text field from DSPOBJD output
            # Output line format:
            # SRCEXTRACT     *PGM         RPGLE          352256     Copies each member to IFS path
            # Object name is first token — find the line containing our object
            for line in out.split('\n'):
                # Check if this line contains our object name
                stripped = line.strip()
                if stripped.upper().startswith(obj_upper):
                    # Split the line into tokens
                    # Format: OBJNAME  TYPE  ATTR  SIZE  TEXT...
                    # TEXT starts after the 4th token (size number)
                    parts = stripped.split()
                    if len(parts) >= 5:
                        # Tokens 0=name, 1=type, 2=attr, 3=size, 4+=text
                        desc = ' '.join(parts[4:]).strip()
                        if desc:
                            descriptions[obj_upper] = desc
                            print(f'    {obj_upper}: {desc}')
                    elif len(parts) == 4:
                        # No description text — object exists but no text
                        print(f'    {obj_upper}: No description')
                    break

        ssh.close()

        found = sum(
            1 for v in descriptions.values()
            if v != 'No description available'
        )
        print(f'  Descriptions found: {found} of {len(object_names)}')

    except Exception as e:
        print(f'  WARNING: Could not get descriptions: {str(e)}')
        print('  Analysis continues without descriptions')

    return descriptions

def get_pf_from_lf(lf_source):
    import re
    # re.search finds the first match of a pattern in a string
    # PFILE\s*\( = the word PFILE followed by optional spaces and opening bracket
    # (?:\w+/)? = optional library prefix like LEAVELIB/
    # (\w+) = capture group — the PF name we want
    # \s*\) = optional spaces and closing bracket
    # re.IGNORECASE = match PFILE or pfile or Pfile

    match = re.search(
        r'PFILE\s*\(\s*(?:\w+/)?(\w+)\s*\)',
        lf_source,
        re.IGNORECASE
    )
    if match:
        # match.group(1) = first capture group = the PF name
        return match.group(1).upper()
    return None  # PFILE not found

















