import subprocess
import sys
import unittest

from checkbox_detection import Checkbox, available_detectors, get_detector


class PublicInterfaceTest(unittest.TestCase):
    def test_registered_detectors_are_available(self):
        self.assertEqual(available_detectors(), ("dummy_v1", "opencv_v1", "opencv_v2"))
        self.assertTrue(callable(get_detector("opencv_v2").detect))
        self.assertEqual(Checkbox(bbox=(0, 0, 1, 1), is_checked=False).bbox, (0, 0, 1, 1))

    def test_import_does_not_depend_on_http_layer(self):
        code = """
import builtins
real_import = builtins.__import__
def guarded_import(name, *args, **kwargs):
    if name.split('.')[0] in {'api', 'fastapi', 'starlette'}:
        raise AssertionError(f'Unexpected HTTP dependency: {name}')
    return real_import(name, *args, **kwargs)
builtins.__import__ = guarded_import
from checkbox_detection import Checkbox, available_detectors, get_detector, validate_image
assert 'opencv_v2' in available_detectors()
"""
        subprocess.run([sys.executable, "-c", code], check=True, capture_output=True, text=True)


if __name__ == "__main__":
    unittest.main()
