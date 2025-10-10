#!/usr/bin/env python3
"""
Build script to generate README parameter documentation from PARAMETERS_SCHEMA

This script creates markdown documentation for all parameters that can be
included in the README.md file, ensuring documentation stays in sync.
"""

import os
import sys
from pathlib import Path

# Add src directory to path to import params module
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from params import PARAMETERS_SCHEMA


def generate_by_process_section():
    """Generate parameter documentation organized by sections from PARAMETERS_SCHEMA."""
    
    lines = []
    
    # Group parameters by section
    sections_data = {}
    for param_name, details in PARAMETERS_SCHEMA.items():
        section = details.get("section", "Other")
        if section not in sections_data:
            sections_data[section] = []
        sections_data[section].append((param_name, details, False))
        
        # Add section_params
        if "section_params" in details:
            for sub_param, sub_details in details["section_params"].items():
                sections_data[section].append((sub_param, sub_details, True))
    
    # Generate documentation for each section
    for section, params in sections_data.items():
        lines.extend([
            f"#### {section}",
            "",
        ])
        for param_name, details, is_section_param in params:
            add_parameter_doc_to_lines(lines, param_name, details, is_section_param)
        lines.append("")
    
    return "\n".join(lines)



def add_parameter_doc_to_lines(lines, param_name, details, is_section_param=False, indent_level=0):
    """Add documentation for a single parameter to the lines list."""
    env_var = details["env"]
    help_text = details.get("help", "")
    default = details.get("default", "")
    arg_name = details["arg"]
    
    # Convert default value to readable string
    if default is None:
        default_str = "None"
    elif isinstance(default, bool):
        default_str = f'`"{str(default).lower()}"`'
    elif isinstance(default, str):
        if default == "":
            default_str = '`""` (empty for latest)' if 'manifest' in param_name.lower() else '`""`'
        else:
            default_str = f'`"{default}"`'
    else:
        default_str = f'`"{default}"`'
    
    # Create the parameter entry
    indent = "  " * indent_level if is_section_param else ""
    bullet = "-" if not is_section_param else "*"
    
    lines.append(f"{indent}{bullet} **{env_var}** - {help_text}")
    lines.append(f"{indent}  - Default: {default_str}")
    lines.append(f"{indent}  - Command line: `{arg_name}`")
    
    # Add links if present
    if "links" in details:
        for link_name, link_url in details["links"].items():
            lines.append(f"{indent}  - See [{link_name}]({link_url}) for available values")
    
    # Add extended help if present
    if "help_extended" in details:
        lines.append(f"{indent}  - {details['help_extended']}")
    
    lines.append("")  # Blank line after each parameter


def generate_full_parameter_section():
    """Generate the complete parameter documentation section."""
    
    lines = []
    
    # Add process-organized documentation
    lines.append(generate_by_process_section())
    
    return "\n".join(lines)


def write_parameter_docs():
    """Write parameter documentation to files."""
    build_dir = Path(__file__).parent.parent / ".temp"
    os.makedirs(build_dir, exist_ok=True)
    
    # Generate different formats
    full_section = generate_full_parameter_section()
    env_vars_only = generate_by_process_section()
    
    # Write full section
    full_path = build_dir / "readme_parameters_section.md"
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(full_section)
    
    return full_path


def validate_generated_docs():
    """Validate that the generated documentation looks correct."""
    build_dir = Path(__file__).parent.parent / ".temp"
    
    files_to_check = [
        "readme_parameters_section.md"
    ]
    
    for filename in files_to_check:
        filepath = build_dir / filename
        
        if not filepath.exists():
            print(f"Generated file {filepath} does not exist")
            return False
        
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Basic validation checks
            if len(content) < 100:
                print(f"Warning: Generated file {filename} seems too short")
                return False
            
            # Check for expected content
            if filename == "readme_parameters_section.md":
                if "#### Logging" not in content:
                    print(f"Warning: {filename} missing expected sections")
                    return False
            
            print(f"Generated {filename} ({len(content.splitlines())} lines)")
            
        except Exception as e:
            print(f"Error validating {filename}: {e}")
            return False
    
    return True

def main():
    """Main function to run the parameter documentation build."""
    
    print("Building README parameter documentation from PARAMETERS_SCHEMA...")
    print()
    
    try:
        # Generate documentation files
        full_path = write_parameter_docs()
        
        # Validate generated files
        if not validate_generated_docs():
            print("Validation failed")
            sys.exit(1)
        
        print("\nGenerated Files:")
        print(f"   {full_path.name} - Complete parameter section")
        
        print("\nParameter documentation build completed successfully!")
        
    except Exception as e:
        print(f"Error building parameter documentation: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()