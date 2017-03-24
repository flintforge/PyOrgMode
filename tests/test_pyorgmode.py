
"""Tests for parsing a file containing no headline
 but that contains a bold element (thanks whacked)
 You need the fr_FR.UTF-8 locale to run these tests
 """

import locale
import pyorgmode
from pyorgmode import OrgDataStructure
try:
    import unittest2 as unittest
except ImportError:
    import unittest


class Testpyorgmode(unittest.TestCase):

    def setUp(self):
        locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')
        self.org = OrgDataStructure()
        self.infile = "tests/orgs/test.org"
        self.org.load_from_file(self.infile)
        assert(self.org.root.content)
        self.outfile = "/tmp/output.org"

    def test_quick(self):
        topnodes = self.org.toplevel_nodes()
        headings = [T.heading for T in topnodes]
        assert(headings)
        assert(topnodes)


    def test_dict(self):
        self.org.root.dict()
        # TODO complete

    def test_load_save_noheadline_org(self):

        infile = "tests/orgs/no_headline.org"
        org = pyorgmode.OrgDataStructure()
        org.load_from_file(infile)
        assert(org.root.content)
        org.save_to_file(self.outfile)
        with open(infile) as F: original = F.readlines()
        with open(self.outfile) as F: saved = F.readlines()
        self.assertEqual(saved, original)

    def test_load_save_org(self):
        self.org.save_to_file(self.outfile)
        with open(self.infile) as F: original = F.readlines()
        with open(self.outfile) as F: saved = F.readlines()
        self.assertEqual(saved, original)


if __name__ == '__main__':
    unittest.main()
