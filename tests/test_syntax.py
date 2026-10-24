import pathlib
import py_compile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent


class TestSyntax(unittest.TestCase):
    def test_every_py_file_compiles(self):
        files = sorted(p for p in ROOT.rglob("*.py"))
        self.assertGreater(len(files), 0)
        for f in files:
            with self.subTest(file=str(f.relative_to(ROOT))):
                py_compile.compile(str(f), doraise=True)


if __name__ == "__main__":
    unittest.main()
