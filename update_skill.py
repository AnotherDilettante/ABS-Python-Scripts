"""
Script to update all old script names to new names in SKILL.md
"""

# Read the file
with open(r'C:\Users\angus\Sync\Claude Code\ABS-Project\SKILL.md', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace all script name references
replacements = [
    ('s99_pipeline_control.py', 'start.py'),
    ('s00_readabs_datalist.py', 'config.py'),  
    ('s01_readabs_datadownload.py', 'download.py'),
    ('s02_readabs_plotting.py', 'generate_charts.py'),
    ('s05_dashboard.py', 'dashboard.py'),
    # Also replace inline code references
    ('`s99`', '`start`'),
    ('`s00`', '`config`'),
    ('`s01`', '`download`'),
    ('`s02`', '`generate_charts`'),
    ('`s05`', '`dashboard`'),
    # And command examples
    ('python s01', 'python download'),
    ('python s02', 'python generate_charts'),
    ('streamlit run s05', 'streamlit run dashboard'),
    ('python s99', 'python start'),
    # And parenthetical references
    ('(s99)', '(start.py)'),
    ('(s00)', '(config.py)'),
    ('(s01)', '(download.py)'),
    ('(s02)', '(generate_charts.py)'),
    ('(s05)', '(dashboard.py)'),
]

# Apply replacements
for old, new in replacements:
    content = content.replace(old, new)

# Write back
with open(r'C:\Users\angus\Sync\Claude Code\ABS-Project\SKILL.md', 'w', encoding='utf-8') as f:
    f.write(content)

print('SKILL.md updated successfully!')
print('\nUpdated references:')
for old, new in replacements:
    print(f'  {old} → {new}')
