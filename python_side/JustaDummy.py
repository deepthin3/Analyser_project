import paramiko
import os
from dotenv import load_dotenv
load_dotenv()

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(
    hostname=os.getenv('IBMI_HOST'),
    username=os.getenv('IBMI_USER'),
    password=os.getenv('IBMI_PASS'),
    port=2222
)

# Test RUNSQL via system command directly
# Note: single quotes inside the SQL use double single quotes
stdin, stdout, stderr = ssh.exec_command(
    "system 'DSPOBJD OBJ(VAVAN1/CONTROLRP) OBJTYPE(*PGM)'"
)
out = stdout.read().decode('utf-8', errors='ignore')
obj_upper = 'CONTROLRP' 
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
                             
                            print(f'    {obj_upper}: {desc}')
                    elif len(parts) == 4:
                        # No description text — object exists but no text
                        print(f'    {obj_upper}: No description')
                    break

ssh.close()
 
 