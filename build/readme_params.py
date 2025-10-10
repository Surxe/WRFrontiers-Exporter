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





def generate_cli_docs():
    """Generate CLI argument documentation."""
    
    lines = []
    
    # Group by category for better organization
    categories = {
        "Configuration Parameters": [],
        "Force Options": [],
        "Control Options": []
    }
    
    def categorize_param(param_name, details):
        """Categorize a parameter for CLI documentation."""
        arg_name = details["arg"]
        help_text = details.get("help", "")
        
        if arg_name.startswith("--force-"):
            return "Force Options"
        elif arg_name.startswith("--should-"):
            return "Control Options"
        else:
            return "Configuration Parameters"
    
    def add_cli_param(param_name, details):
        """Add CLI parameter to appropriate category."""
        category = categorize_param(param_name, details)
        arg_name = details["arg"]
        help_text = details.get("help", "")
        arg_type = details.get("type")
        
        # Format argument based on type
        if arg_type == bool:
            arg_display = arg_name
        elif hasattr(arg_type, '__origin__') and str(arg_type).startswith('typing.Literal'):
            # Extract choices for Literal types
            try:
                from typing import get_args
                choices = list(get_args(arg_type))
                arg_display = f"{arg_name} {{{','.join(choices)}}}"
            except:
                arg_display = f"{arg_name} VALUE"
        else:
            arg_display = f"{arg_name} {param_name.upper()}"
        
        categories[category].append(f"- `{arg_display}` - {help_text}")
    
    # Process all parameters
    for param_name, details in PARAMETERS_SCHEMA.items():
        add_cli_param(param_name, details)
        
        # Process section_params if they exist
        if "section_params" in details:
            for sub_param, sub_details in details["section_params"].items():
                add_cli_param(sub_param, sub_details)
    
    # Generate documentation by category
    for category, params in categories.items():
        if params:  # Only add category if it has parameters
            lines.append(f"### {category}")
            lines.extend(params)
            lines.append("")
    
    return "\n".join(lines)


def generate_by_process_section():
    """Generate parameter documentation organized by process steps."""
    
    # Define the process order and mapping
    process_steps = [
        {
            "title": "Step 1: Dependencies",
            "description": "Download and update required tools (BatchExport, DepotDownloader)",
            "sections": ["Dependencies"]
        },
        {
            "title": "Step 2: Steam Download", 
            "description": "Download/update War Robots Frontiers game files from Steam",
            "sections": ["Steam Download"]
        },
        {
            "title": "Step 3: Mapping",
            "description": "Generate mapper file using DLL injection with Dumper-7", 
            "sections": ["Mapping"]
        },
        {
            "title": "Step 4: Batch Export",
            "description": "Export game assets to JSON format",
            "sections": ["Batch Export"]
        }
    ]
    
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
    
    # Add logging first (global configuration)
    if "Logging" in sections_data:
        lines.extend([
            "#### General Configuration",
            "",
        ])
        for param_name, details, is_section_param in sections_data["Logging"]:
            add_parameter_doc_to_lines(lines, param_name, details, is_section_param)
        lines.append("")
    
    # Add process steps
    for step in process_steps:
        lines.extend([
            f"#### {step['title']}",
            f"*{step['description']}*",
            "",
        ])
        
        for section_name in step['sections']:
            if section_name in sections_data:
                for param_name, details, is_section_param in sections_data[section_name]:
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
    
    lines = [
        "## Configuration",
        "",
        "Copy `.env.example` to `.env` and configure the following parameters:",
        "",
    ]
    
    # Add process-organized documentation
    lines.append(generate_by_process_section())
    
    return "\n".join(lines)


def write_parameter_docs():
    """Write parameter documentation to files."""
    build_dir = Path(__file__).parent
    
    # Generate different formats
    full_section = generate_full_parameter_section()
    env_vars_only = generate_by_process_section()
    cli_args_only = generate_cli_docs()
    
    # Write full section
    full_path = build_dir / "readme_parameters_section.md"
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(full_section)
    
    # Write environment variables only
    env_path = build_dir / "readme_env_vars.md"
    with open(env_path, "w", encoding="utf-8") as f:
        f.write("### Environment Variables\n\n")
        f.write("Copy `.env.example` to `.env` and configure the following parameters:\n\n")
        f.write(env_vars_only)
    
    # Write CLI args only
    cli_path = build_dir / "readme_cli_args.md"
    with open(cli_path, "w", encoding="utf-8") as f:
        f.write("## Command Line Arguments\n\n")
        f.write("All environment variables can be overridden via command line arguments.\n\n")
        f.write(cli_args_only)
    
    return full_path, env_path, cli_path


def validate_generated_docs():
    """Validate that the generated documentation looks correct."""
    build_dir = Path(__file__).parent
    
    files_to_check = [
        "readme_parameters_section.md",
        "readme_env_vars.md", 
        "readme_cli_args.md"
    ]
    
    for filename in files_to_check:
        filepath = build_dir / filename
        
        if not filepath.exists():
            print(f"❌ Generated file {filepath} does not exist")
            return False
        
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Basic validation checks
            if len(content) < 100:
                print(f"⚠️  Warning: Generated file {filename} seems too short")
                return False
            
            # Check for expected content
            if filename == "readme_parameters_section.md":
                if "## Configuration" not in content or "#### General Configuration" not in content:
                    print(f"⚠️  Warning: {filename} missing expected sections")
                    return False
            
            print(f"✅ Generated {filename} ({len(content.splitlines())} lines)")
            
        except Exception as e:
            print(f"❌ Error validating {filename}: {e}")
            return False
    
    return True


def show_integration_options():
    """Show different options for integrating the generated docs into README."""
    
    print("\n📋 Integration Options for README.md:")
    print("=" * 50)
    
    print("\n1️⃣  **Manual Copy-Paste (Simplest)**")
    print("   - Copy content from build/readme_parameters_section.md")
    print("   - Paste into README.md replacing existing Configuration section")
    print("   - Pros: Simple, no dependencies")
    print("   - Cons: Manual process, can get out of sync")
    
    print("\n2️⃣  **Include Markers (Recommended)**")
    print("   - Add markers in README.md like:")
    print("     <!-- BEGIN_GENERATED_PARAMS -->")
    print("     <!-- END_GENERATED_PARAMS -->")
    print("   - Use a script to replace content between markers")
    print("   - Pros: Automated, preserves manual content")
    print("   - Cons: Requires additional automation")
    
    print("\n3️⃣  **Separate Documentation Files**")
    print("   - Keep parameter docs in separate .md files")
    print("   - Link to them from main README")
    print("   - Pros: Clean separation, easy maintenance")
    print("   - Cons: Users need to navigate to separate files")
    
    print("\n4️⃣  **Build Time Replacement**")
    print("   - Use template placeholders in README.md")
    print("   - Generate complete README.md at build time")
    print("   - Pros: Fully automated")
    print("   - Cons: README becomes a generated file")
    
    print("\n5️⃣  **GitHub Actions Integration**")
    print("   - Auto-update README on parameter schema changes")
    print("   - Commit updated docs automatically")
    print("   - Pros: Fully automated, always in sync")
    print("   - Cons: Requires CI setup")


def create_integration_script():
    """Create a helper script for README integration."""
    
    integration_script = '''#!/usr/bin/env python3
"""
Helper script to update README.md with generated parameter documentation.

Usage:
    python build/update_readme.py
"""

import re
from pathlib import Path

def update_readme_with_markers():
    """Update README.md content between markers."""
    
    repo_root = Path(__file__).parent.parent
    readme_path = repo_root / "README.md"
    params_doc_path = Path(__file__).parent / "readme_parameters_section.md"
    
    if not readme_path.exists():
        print("❌ README.md not found")
        return False
    
    if not params_doc_path.exists():
        print("❌ Generated parameter docs not found. Run build/readme_params.py first.")
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
        print("⚠️  Markers not found in README.md")
        print("Add these markers where you want the parameter docs:")
        print(f"    {start_marker}")
        print(f"    {end_marker}")
        return False
    
    # Replace content between markers
    pattern = f"{re.escape(start_marker)}.*?{re.escape(end_marker)}"
    replacement = f"{start_marker}\\n{params_content}\\n{end_marker}"
    
    new_readme_content = re.sub(pattern, replacement, readme_content, flags=re.DOTALL)
    
    # Write updated README
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(new_readme_content)
    
    print("✅ Successfully updated README.md with generated parameter documentation")
    return True

if __name__ == "__main__":
    success = update_readme_with_markers()
    exit(0 if success else 1)
'''
    
    script_path = Path(__file__).parent / "update_readme.py"
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(integration_script)
    
    return script_path


def main():
    """Main function to run the parameter documentation build."""
    
    print("🔧 Building README parameter documentation from PARAMETERS_SCHEMA...")
    print()
    
    try:
        # Generate documentation files
        full_path, env_path, cli_path = write_parameter_docs()
        
        # Validate generated files
        if not validate_generated_docs():
            print("❌ Validation failed")
            sys.exit(1)
        
        # Create integration helper script
        integration_script_path = create_integration_script()
        
        print("\n📁 Generated Files:")
        print(f"   📄 {full_path.name} - Complete parameter section")
        print(f"   📄 {env_path.name} - Environment variables only") 
        print(f"   📄 {cli_path.name} - CLI arguments only")
        print(f"   📄 {integration_script_path.name} - README integration helper")
        
        # Show integration options
        show_integration_options()
        
        print("\n🎉 Parameter documentation build completed successfully!")
        
    except Exception as e:
        print(f"❌ Error building parameter documentation: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()