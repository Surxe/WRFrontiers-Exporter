#!/usr/bin/env python3
"""
Helper script to update README.md with generated parameter documentation.
"""

import re
from pathlib import Path

def update_readme_with_markers():
    """Update README.md content between markers."""
    
    repo_root = Path(__file__).parent.parent
    readme_path = repo_root / "README.md"
    params_doc_path = Path(__file__).parent.parent / ".temp" / "readme_parameters_section.md"
    
    if not readme_path.exists():
        print("README.md not found")
        return False
    
    if not params_doc_path.exists():
        print("Generated parameter docs not found. Run readme_params.py first.")
        return False
    
    # Read files
    with open(readme_path, "r", encoding="utf-8") as f:
        readme_content = f.read()
    
    with open(params_doc_path, "r", encoding="utf-8") as f:
        params_content = f.read()
    
    # Define markers
    start_marker = "<!-- BEGIN_GENERATED_PARAMS -->"
    end_marker = "<!-- END_GENERATED_PARAMS -->"
    
    # Check if markers exist
    if start_marker not in readme_content or end_marker not in readme_content:
        print("Markers not found in README.md")
        print("Add these markers where you want the parameter docs:")
        print(f"    {start_marker}")
        print(f"    {end_marker}")
        return False
    
    # Replace content between markers
    pattern = f"{re.escape(start_marker)}.*?{re.escape(end_marker)}"
    replacement = f"{start_marker}\n{params_content}\n{end_marker}"
    
    new_readme_content = re.sub(pattern, replacement, readme_content, flags=re.DOTALL)
    
    # Write updated README
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(new_readme_content)

    # Remove the temporary params doc file
    params_doc_path.unlink(missing_ok=True)
    
    print("Successfully updated README.md with generated parameter documentation")
    return True

if __name__ == "__main__":
    success = update_readme_with_markers()
    exit(0 if success else 1)
