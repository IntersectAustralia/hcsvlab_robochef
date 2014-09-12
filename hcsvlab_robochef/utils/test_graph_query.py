import unittest

from rdflib import Graph
from rdflib.query import Result
from hcsvlab_robochef.utils.manifester import *
from hcsvlab_robochef import configmanager

class TestGraphQueries(unittest.TestCase):

    def setUp(self):
        configmanager.configinit()
        corpus_basedir = configmanager.get_config("TEST_DATA_BASEDIR", None)
        rdf_file = os.path.join(corpus_basedir, "LD_T_6-metadata.rdf")
        self.graph = Graph().parse(rdf_file, format="turtle")

    def test_collection_query(self):
        pass

    def test_item_query(self):
        self.dump_graph()
        res = self.graph.query(ITEM_QUERY.replace("COLL", "mbep"))
        self.assertIsInstance(res, Result)
        self.assertEqual(len(res), 1)
        for row in res:
            self.assertEqual(str(row.item), "http://ns.ausnc.org.au/corpora/mbep/items/LD_T_6")
            self.assertEqual(str(row.identifier), "LD_T_6")
            break

    def test_document_query(self):
        pass

    def dump_graph(self):
        with open(os.path.join(os.path.dirname(__file__), 'graph.dump'), 'w') as gd:
            for subject, predicate, object in self.graph:
                gd.write("{0}\n".format((subject, predicate, object)))


# Alternative way to run the tests
suite = unittest.TestLoader().loadTestsFromTestCase(TestGraphQueries)
unittest.TextTestRunner(verbosity=2).run(suite)

#
#if __name__ == '__main__':
#    unittest.main()
__author__ = 'seanl'
