import re

file_path = r'c:\Users\arisf\OneDrive\Companies\Bivaset\App\Bivaset-Service-app\backend\handlers\project_details_handler.py'

# Read the file content
with open(file_path, 'r', encoding='utf-8') as file:
    content = file.read()

# First fix all keyboard initializations that don't use list()
pattern1 = r'(keyboard = )([a-zA-Z_]+\([^)]*\)\.inline_keyboard)'
replacement1 = r'\1list(\2)'
modified_content = re.sub(pattern1, replacement1, content)

# Fix keyboard concatenations
pattern2 = r'(keyboard \+= )(navigation_keyboard\.inline_keyboard)'
replacement2 = r'\1list(\2)'
modified_content = re.sub(pattern2, replacement2, modified_content)

# Save the modified content
with open(file_path, 'w', encoding='utf-8') as file:
    file.write(modified_content)

print("Fixed keyboard initializations successfully.")
