from pathlib import Path
import configparser
import importlib.util
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / 'Directional_line_buffer_Tool'
VALIDATOR_PATH = ROOT / 'scripts' / 'validate_plugin.py'
spec = importlib.util.spec_from_file_location('qgis_plugin_validator', VALIDATOR_PATH)
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


class PackageTests(unittest.TestCase):
    def test_tree(self):
        self.assertEqual(validator.validate_tree(PLUGIN), [])

    def test_metadata_version(self):
        parser = configparser.ConfigParser()
        parser.read(PLUGIN / 'metadata.txt', encoding='utf-8')
        self.assertEqual(parser['general']['version'], '0.3.3')
        self.assertEqual(parser['general']['qgisMinimumVersion'], '3.30')
        self.assertEqual(parser['general']['experimental'], 'False')

    def test_correct_class_factory(self):
        self.assertIn('classFactory', (PLUGIN / '__init__.py').read_text())

    def test_help_is_local(self):
        text = (PLUGIN / 'index-en.html').read_text()
        self.assertIn('Directional Line Buffer', text)
        self.assertNotIn('<script', text)

    def test_no_runtime_dependency(self):
        source = '\n'.join(p.read_text() for p in PLUGIN.glob('*.py'))
        self.assertNotIn('import shapely', source)
        self.assertNotIn('import requests', source)

    def test_zip_rejects_path_traversal(self):
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / 'bad.zip'
            with zipfile.ZipFile(archive, 'w') as z:
                z.writestr('../outside.txt', 'bad')
            self.assertTrue(validator.validate_zip(archive))

    def test_zip_rejects_duplicate_names(self):
        import warnings
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / 'bad.zip'
            with zipfile.ZipFile(archive, 'w') as z, warnings.catch_warnings():
                warnings.simplefilter('ignore', UserWarning)
                z.writestr('Directional_line_buffer_Tool/a.py', 'a')
                z.writestr('Directional_line_buffer_Tool/a.py', 'b')
            self.assertTrue(any('Duplicate' in s for s in validator.validate_zip(archive)))


if __name__ == '__main__':
    unittest.main()
