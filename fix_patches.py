import re
import os

# Directory containing the test files
test_dir = r"d:\Repositories\WRFrontiers-Exporter\tests\test_dependency_manager"

# Pattern to match patch statements
pattern1 = r"with patch\('dependency_manager\.logger'\) as (\w+):"
pattern2 = r"with patch\('dependency_manager\.logger'\):"
pattern3 = r"@patch\('dependency_manager\.logger'\)"

# Replacement strings
replacement1 = r"with patch.object(src_dependency_manager, 'logger') as \1:"
replacement2 = r"with patch.object(src_dependency_manager, 'logger'):"
replacement3 = r"@patch.object(src_dependency_manager, 'logger')"

for filename in os.listdir(test_dir):
    if filename.endswith('.py') and filename.startswith('test_'):
        filepath = os.path.join(test_dir, filename)
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Apply replacements
        content = re.sub(pattern1, replacement1, content)
        content = re.sub(pattern2, replacement2, content)
        content = re.sub(pattern3, replacement3, content)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Updated {filename}")

print("All files updated!")