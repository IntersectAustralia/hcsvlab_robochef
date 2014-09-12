import unittest
import filecmp

from rdflib import Graph
from rdflib.query import Result
from hcsvlab_robochef.utils.manifester import *
from hcsvlab_robochef import configmanager

class TestGenerateManifest(unittest.TestCase):

    def setUp(self):
        configmanager.configinit()
        root_dir = configmanager.get_config("ROOT", None)
        self.rdf_dir = os.path.join(root_dir, "testdata")
        self.actural_manifest = os.path.join(self.rdf_dir, "manifest.json")
        self.sample_manifest = os.path.join(self.rdf_dir, "manifest_sample.json")

    def test_generate_manifest(self):
        create_manifest(self.rdf_dir, "turtle")
        self.assertTrue(os.path.exists(self.actural_manifest))
        self.assertTrue(filecmp.cmp(self.actural_manifest, self.sample_manifest))

    def tearDown(self):
        os.remove(self.actural_manifest)

# Alternative way to run the tests
suite = unittest.TestLoader().loadTestsFromTestCase(TestGenerateManifest)
unittest.TextTestRunner(verbosity=2).run(suite)

#
#if __name__ == '__main__':
#    unittest.main()
__author__ = 'seanl'
