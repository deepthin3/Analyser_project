# Quick test to debug obj_desc.py
import obj_desc

# Test data from the AIRLINERP analysis
object_names = ['CONTROLRP', 'MSGSFLCL', 'AIRLISTR', 'FAIRLINEDSP', 'AIRMASTER', 'AIRMASL1']
source_types = {'CONTROLRP': 'RPGLE', 'MSGSFLCL': 'CLLE', 'AIRMASTER': 'PF', 'AIRMASL1': 'LF', 'FAIRLINEDSP': 'DSPF'}

print("Testing obj_desc.get_descriptions()...")
print(f"Object names: {object_names}")
print(f"Source types: {source_types}")
print()

descriptions = obj_desc.get_descriptions(object_names, 'TESTLIB', 'TESTLIB', source_types)

print()
print("Results:")
for name, desc in descriptions.items():
    print(f"  {name}: {desc}")
