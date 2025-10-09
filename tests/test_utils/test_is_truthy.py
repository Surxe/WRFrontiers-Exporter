import unittest
import sys
import os

# Add the src directory to the Python path to import utils
src_path = os.path.join(os.path.dirname(__file__), '..', '..', 'src')
sys.path.insert(0, src_path)

# Import directly from the src.utils module to avoid conflicts with tests.utils
import importlib.util
spec = importlib.util.spec_from_file_location("src_utils", os.path.join(src_path, "utils.py"))
src_utils = importlib.util.module_from_spec(spec)
spec.loader.exec_module(src_utils)

is_truthy = src_utils.is_truthy


class TestIsTruthy(unittest.TestCase):
    """Test cases for the is_truthy function.
    
    The is_truthy function should return True for various representations of truthy values
    and False for everything else.
    """

    def test_boolean_true(self):
        """Test is_truthy returns True for boolean True."""
        self.assertTrue(is_truthy(True))

    def test_string_true_lowercase(self):
        """Test is_truthy returns True for lowercase 'true'."""
        self.assertTrue(is_truthy('true'))

    def test_string_true_capitalized(self):
        """Test is_truthy returns True for capitalized 'True'."""
        self.assertTrue(is_truthy('True'))

    def test_string_true_uppercase(self):
        """Test is_truthy returns True for uppercase 'TRUE'."""
        self.assertTrue(is_truthy('TRUE'))

    def test_string_t_lowercase(self):
        """Test is_truthy returns True for lowercase 't'."""
        self.assertTrue(is_truthy('t'))

    def test_string_t_uppercase(self):
        """Test is_truthy returns True for uppercase 'T'."""
        self.assertTrue(is_truthy('T'))

    def test_integer_one(self):
        """Test is_truthy returns True for integer 1."""
        self.assertTrue(is_truthy(1))

    def test_boolean_false(self):
        """Test is_truthy returns False for boolean False."""
        self.assertFalse(is_truthy(False))

    def test_string_false(self):
        """Test is_truthy returns False for string 'false'."""
        self.assertFalse(is_truthy('false'))

    def test_string_false_capitalized(self):
        """Test is_truthy returns False for string 'False'."""
        self.assertFalse(is_truthy('False'))

    def test_string_f(self):
        """Test is_truthy returns False for string 'f'."""
        self.assertFalse(is_truthy('f'))

    def test_integer_zero(self):
        """Test is_truthy returns False for integer 0."""
        self.assertFalse(is_truthy(0))

    def test_integer_two(self):
        """Test is_truthy returns False for integer 2."""
        self.assertFalse(is_truthy(2))

    def test_empty_string(self):
        """Test is_truthy returns False for empty string."""
        self.assertFalse(is_truthy(''))

    def test_none(self):
        """Test is_truthy returns False for None."""
        self.assertFalse(is_truthy(None))

    def test_random_string(self):
        """Test is_truthy returns False for random string."""
        self.assertFalse(is_truthy('random'))

    def test_list(self):
        """Test is_truthy returns False for list."""
        self.assertFalse(is_truthy([True]))

    def test_dict(self):
        """Test is_truthy returns False for dictionary."""
        self.assertFalse(is_truthy({'true': True}))

    def test_mixed_case_true(self):
        """Test is_truthy returns False for mixed case 'TrUe' (not in TRUE_THO list)."""
        self.assertFalse(is_truthy('TrUe'))

    def test_whitespace_true(self):
        """Test is_truthy returns False for 'true' with whitespace."""
        self.assertFalse(is_truthy(' true '))

    def test_yes_no_strings(self):
        """Test is_truthy returns False for 'yes'/'no' strings."""
        self.assertFalse(is_truthy('yes'))
        self.assertFalse(is_truthy('no'))


if __name__ == '__main__':
    unittest.main()