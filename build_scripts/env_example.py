#!/usr/bin/env python3
"""
Build script to generate .env.example from PARAMETERS_SCHEMA

This script creates a new .env.example file based on the parameter schema,
ensuring documentation stays in sync with the actual parameter definitions.
"""

import os
import sys
from pathlib import Path

# Add src directory to path to import params module
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from params import PARAMETERS_SCHEMA


def generate_env_example():
    """Generate .env.example content from PARAMETERS_SCHEMA."""
    
    # Header
    header = [
        "# Use forward slashes \"/\" in paths for compatibility across platforms",
    ]
    
    lines = header + [""]  # Add blank line after header
    
    def process_param(param_name, details, is_section_param=False):
        """Process a single parameter and add it to the lines."""
        env_var = details["env"]
        help_text = details.get("help", "")
        default = details.get("default", "")
        
        # Convert default value to string representation for .env file
        if default is None:
            default_str = ""
        elif isinstance(default, bool):
            default_str = "True" if default else "False"
        elif isinstance(default, Path):
            default_str = str(default) if default else ""
        else:
            default_str = str(default)
        
        # Add comment with help text
        if help_text:
            # Wrap long help text
            if len(help_text) > 80:
                # Simple word wrapping
                words = help_text.split()
                current_line = "# "
                for word in words:
                    if len(current_line + word) > 80:
                        lines.append(current_line.rstrip())
                        current_line = "# " + word + " "
                    else:
                        current_line += word + " "
                if current_line.strip() != "#":
                    lines.append(current_line.rstrip())
            else:
                lines.append(f"# {help_text}")
        
        # Add the environment variable with default value
        lines.append(f'{env_var}="{default_str}"')
        lines.append("")  # Blank line after each parameter
    
    # Process parameters by section
    sections_processed = set()
    
    for param_name, details in PARAMETERS_SCHEMA.items():
        section = details.get("section", "Other")
        
        # Add section header if we haven't processed this section yet
        if section not in sections_processed:
            if sections_processed:  # Add extra blank line between sections
                lines.append("")
            lines.append(f"# {section}")
            sections_processed.add(section)
        
        # Process main parameter
        process_param(param_name, details)
        
        # Process section_params if they exist
        if "section_params" in details:
            for sub_param, sub_details in details["section_params"].items():
                process_param(sub_param, sub_details, is_section_param=True)
    
    return "\n".join(lines)


def update_env_example():
    """Update the .env.example file with generated content."""
    repo_root = Path(__file__).parent.parent
    env_example_path = repo_root / ".env.example"
    
    try:
        # Generate new content
        new_content = generate_env_example()
        
        # Write to .env.example
        with open(env_example_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        
        print(f"✅ Successfully updated {env_example_path}")
        print(f"📄 Generated {len(new_content.splitlines())} lines")
        
        # Show summary of parameters
        param_count = len(PARAMETERS_SCHEMA)
        section_param_count = sum(
            len(details.get("section_params", {})) 
            for details in PARAMETERS_SCHEMA.values()
        )
        total_params = param_count + section_param_count
        
        print(f"📊 Processed {total_params} parameters ({param_count} main + {section_param_count} sub-parameters)")
        
    except Exception as e:
        print(f"❌ Error updating .env.example: {e}")
        return False
    
    return True


def validate_generated_file():
    """Validate that the generated .env.example file is properly formatted."""
    repo_root = Path(__file__).parent.parent
    env_example_path = repo_root / ".env.example"
    
    if not env_example_path.exists():
        print(f"❌ Generated file {env_example_path} does not exist")
        return False
    
    try:
        with open(env_example_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        # Basic validation checks
        has_header = any("Use forward slashes" in line for line in lines[:5])
        has_env_vars = any("=" in line and not line.strip().startswith("#") for line in lines)
        
        if not has_header:
            print("⚠️  Warning: Generated file missing expected header")
            return False
        
        if not has_env_vars:
            print("⚠️  Warning: Generated file contains no environment variables")
            return False
        
        print(f"✅ Generated file validation passed ({len(lines)} lines)")
        return True
        
    except Exception as e:
        print(f"❌ Error validating generated file: {e}")
        return False


def main():
    """Main function to run the build process."""
    print("🔧 Building .env.example from PARAMETERS_SCHEMA...")
    print()
    
    # Update the .env.example file
    if not update_env_example():
        sys.exit(1)
    
    # Validate the generated file
    if not validate_generated_file():
        sys.exit(1)
    
    print()
    print("🎉 Build completed successfully!")
    print()
    print("Next steps:")
    print("- Review the generated .env.example file")
    print("- Update any parameter descriptions if needed in PARAMETERS_SCHEMA")
    print("- Run this script again after schema changes to keep documentation in sync")


if __name__ == "__main__":
    main()