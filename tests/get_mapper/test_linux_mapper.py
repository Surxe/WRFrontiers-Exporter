import unittest
import os
from unittest.mock import patch
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

# Import from the src directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))
from pathlib import Path
from mapper import linux_mapper


class TestBuildLaunchCmd(unittest.TestCase):
    """Test cases for _build_launch_cmd."""

    def setUp(self):
        self.exe = Path("/game/WRFrontiers-Win64-Shipping.exe")

    def test_non_headless_is_bare_umu_run(self):
        cmd = linux_mapper._build_launch_cmd(self.exe, headless=False)
        self.assertEqual(cmd, ["umu-run", str(self.exe)])

    @patch('shutil.which', return_value="/usr/games/gamescope")
    def test_headless_wraps_in_gamescope(self, _mock_which):
        cmd = linux_mapper._build_launch_cmd(self.exe, headless=True)
        # gamescope --backend headless ... -- umu-run <exe>
        self.assertEqual(cmd[0], "gamescope")
        self.assertIn("--backend", cmd)
        self.assertEqual(cmd[cmd.index("--backend") + 1], "headless")
        # The umu-run invocation is passed through after the '--' separator.
        sep = cmd.index("--")
        self.assertEqual(cmd[sep + 1:], ["umu-run", str(self.exe)])

    @patch('shutil.which', return_value=None)
    def test_headless_without_gamescope_raises(self, _mock_which):
        with self.assertRaises(FileNotFoundError):
            linux_mapper._build_launch_cmd(self.exe, headless=True)


if __name__ == '__main__':
    unittest.main()
