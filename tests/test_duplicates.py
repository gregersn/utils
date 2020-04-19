import os
import shutil
import unittest
from duplicates import Directory

class TestDuplicates(unittest.TestCase):
    @staticmethod
    def setUpClass():
        os.makedirs("__test__/a/b/c/d/e/f", exist_ok=True)
        os.makedirs("__test__/b/b/c/d/e/f", exist_ok=True)
        os.makedirs("__test__/c/a/b", exist_ok=True)
        os.makedirs("__test__/d/b/c", exist_ok=True)
        os.makedirs("__test__/e/b/c/d/e/g", exist_ok=True)
        os.makedirs("__test__/f/b/c/d/e/f", exist_ok=True)
        os.makedirs("__test__/f/b/c/d/e/g", exist_ok=True)


    @staticmethod
    def tearDownClass():
        if os.path.isdir("__test__"):
            shutil.rmtree("__test__")
    

    def test_scan(self):
        pass


    def test_directory(self):
        directory = Directory("__test__")

        self.assertEqual(len(directory.content), 6)

        a = Directory("__test__/a")
        b = Directory("__test__/b")
        c = Directory("__test__/c")
        d = Directory("__test__/d")
        e = Directory("__test__/e")
        f = Directory("__test__/f")

        self.assertEqual(a, b)
        self.assertNotEqual(a, c)
        self.assertNotEqual(b, c)

        self.assertNotEqual(a, d)
        self.assertNotEqual(b, d)
        self.assertNotEqual(c, d)

        self.assertNotEqual(a, e)
        self.assertNotEqual(a, f)
    
    def test_scan(self):
        directory = Directory("__test__")
        self.assertEqual(directory.size, 6)


    def test_duplicates(self):
        directory = Directory("__test__")
        duplicates = directory.duplicates()
        for d, values in duplicates.items():
            print(d, [v.directory for v in values])
        self.assertEqual(len(duplicates), 1)
    
    def test_haschild(self):
        a = Directory("__test__/a")
        b = Directory("__test__/a/b")
        c = Directory("__test__/a/b/c")
        d = Directory("__test__/d")

        self.assertTrue(a.has_child(b))
        self.assertTrue(a.has_child(c))
        self.assertFalse(a.has_child(d))
    


