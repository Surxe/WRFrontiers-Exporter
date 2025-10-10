from dotenv import load_dotenv

import os
import sys
import os
from typing import Literal, get_origin, get_args
from pathlib import Path
from loguru import logger
load_dotenv()

from utils import is_truthy

"""
Central configuration schema to provide a single source of truth for all documentation and functionality of options/args
"""

from options_schema import OPTIONS_SCHEMA

class ArgumentWriter:
    """
    Helper class to write command line arguments based on OPTIONS_SCHEMA
    """

    def __init__(self):
        self.schema = OPTIONS_SCHEMA

    def add_arguments(self, parser):
        def parse_details(details):
            arg_name = details["arg"]
            arg_type = details["type"]
            default = details["default"]
            help_text = details.get("help", "") + f" (default: {default})"
            
            if arg_type == bool:
                parser.add_argument(arg_name, action='store_true', default=None, help=help_text)
                logger.debug(f"Added boolean argument {arg_name} with action 'store_true'")
            elif get_origin(arg_type) is Literal:
                # Handle Literal types by extracting the choices
                choices = list(get_args(arg_type))
                parser.add_argument(arg_name, choices=choices, default=None, help=help_text)
                logger.debug(f"Added choice argument {arg_name} with choices {choices} and default {default}")
            elif arg_type == Path:
                # Handle Path types
                parser.add_argument(arg_name, type=str, default=None, help=help_text)
                logger.debug(f"Added path argument {arg_name} with default {default}")
            else:
                parser.add_argument(arg_name, type=arg_type, default=None, help=help_text)
                logger.debug(f"Added argument {arg_name} with type {arg_type} and default {default}")

            # Add section options if any
            if "section_options" in details:
                for sub_option, sub_details in details["section_options"].items():
                    parse_details(sub_details)

        for option, details in self.schema.items():
            parse_details(details)

class Options:
    """
    A class to hold options for the application.
    """
    def __init__(self, args=None):

        # Initialize all options in the following preference
        # 1. Direct args (if provided)
        # 2. Environment variables (if set)
        # 3. Defaults from OPTIONS_SCHEMA

        # If args is provided, it should be a Namespace from argparse
        if args is not None:
            args_dict = vars(args)
        else:
            args_dict = {}

        # Process the schema to set all attributes
        combined_args_and_options = self._process_schema(OPTIONS_SCHEMA, args_dict)

        # Set attributes dynamically
        for key, value in combined_args_and_options.items():
            setattr(self, key, value)
            logger.debug(f"Set attribute {key} to value: {value}")

        # Setup loguru logging to /logs dir
        logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'logs')
        os.makedirs(logs_dir, exist_ok=True)
        if hasattr(self, 'output_data_dir') and self.output_data_dir:
            log_filename = str(self.output_data_dir).replace('\\', '/').rstrip('/').split('/')[-1] + '.log'
            # i.e. F:/WRF/2025-08-12/<exports> to 2025-08-12.log
        else:
            log_filename = 'default.log'
        log_path = os.path.join(logs_dir, log_filename)
        logger.remove()
        
        # Clear the log file before adding the handler
        with open(log_path, 'w') as f:
            pass
        logger.add(log_path, level=self.log_level, rotation="10 MB", retention="10 days", enqueue=True)
        logger.add(sys.stdout, level=self.log_level)
        
        self.validate()
        self.log()

    def _process_schema(self, schema, args_dict):
        """Process the option schema and set instance attributes."""

        print("Processing schema with args_dict:", args_dict)

        # Combine args and options
        combined_args_and_options = {}

        def process_option(option_name, details):
            # Convert arg name to attribute name (remove -- and convert - to _)
            attr_name = details["arg"].lstrip('--').replace('-', '_')
            
            # Get value in order of priority: args -> env -> default
            value = None

            logger.debug(f"Processing option: {option_name} (attr: {attr_name})")

            # 1. Check args first
            if attr_name in args_dict and args_dict[attr_name] is not None:
                value = args_dict[attr_name]
                logger.debug(f"Argument {attr_name} found in args with value: {value}")
            # 2. Check environment variable
            elif details["env"] in os.environ:
                env_value = os.environ[details["env"]]
                logger.debug(f"Environment variable {details['env']} found with value: {env_value}")
                # Convert environment string to proper type
                if details["type"] == bool:
                    value = is_truthy(env_value)
                elif details["type"] == Path:
                    value = Path(env_value) if env_value else None
                elif get_origin(details["type"]) is Literal:
                    # For Literal types, use the string value directly if it's valid
                    valid_choices = get_args(details["type"])
                    value = env_value if env_value in valid_choices else details["default"]
                else:
                    value = details["type"](env_value) if env_value else details["default"]
            # 3. Use default
            else:
                value = details["default"]
            
            # Store
            combined_args_and_options[option_name] = value
        
        # Process all options in the schema
        for option_name, details in schema.items():
            process_option(option_name, details)
            
            # Process section_options if they exist
            if "section_options" in details:
                for sub_option, sub_details in details["section_options"].items():
                    process_option(sub_option, sub_details)

        # If none of the --should-x args/options are in combined_args_and_options, default all to true for ease of use
        should_option_keys = [k for k in OPTIONS_SCHEMA if k != 'LOG_LEVEL']
        if not any(key in combined_args_and_options for key in should_option_keys):
            for key in should_option_keys:
                combined_args_and_options[key] = True
            logger.debug("No --should-x args/options provided, defaulting all to True")
            
        # If a --should-x is true, ensure options under its schema's section_options are provided (meaning not defaulted to None)
        missing_options = []
        for key in should_option_keys:
            if combined_args_and_options.get(key) is True:
                section_options = OPTIONS_SCHEMA[key].get("section_options", {})
                section = OPTIONS_SCHEMA[key]["section"]
                if section_options:
                    logger.debug(f"{key} is True, ensuring section_options for section {section} are provided")
                for sub_option in section_options:
                    if combined_args_and_options.get(sub_option) is None:
                        missing_options.append(sub_option)
                    logger.debug(f"Section option {sub_option} is set to {combined_args_and_options[sub_option]}")

        if missing_options:
            raise ValueError(f"The following options must be provided when their section's --should-x is true: {', '.join(missing_options)}")

        return combined_args_and_options

    def validate(self):
        """
        Validates the options.
        """
        
        
        
    def log(self):
        """
        Logs the options.
        """
        # Dynamically log all attributes that were set from the schema
        log_lines = ["Options initialized with:"]
        
        def log_option(option_name, details):
            attr_name = details["arg"].lstrip('--').replace('-', '_')
            if hasattr(self, attr_name):
                value = getattr(self, attr_name)
                # Don't log sensitive information
                if details.get("sensitive", False):
                    value = "***HIDDEN***"
                log_lines.append(f"{option_name}: {value}")
        
        # Log all options from schema
        for option_name, details in OPTIONS_SCHEMA.items():
            log_option(option_name, details)
            
            # Log section_options if they exist
            if "section_options" in details:
                for sub_option, sub_details in details["section_options"].items():
                    log_option(sub_option, sub_details)
        
        logger.info("\n".join(log_lines))

    def __str__(self):
        return f"Options(export_path={self.export_path}, game_name={self.game_name}, log_level={self.log_level})"
    
# Helper to initialize OPTIONS with direct args if available
def init_options(args=None):
    global OPTIONS
    OPTIONS = Options(args)
    return OPTIONS