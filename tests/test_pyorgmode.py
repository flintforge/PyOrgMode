
"""Tests for parsing a file containing no headline
 but that contains a bold element (thanks whacked)
 You need the fr_FR.UTF-8 locale to run these tests
 """

import locale
import pyorgmode
from pyorgmode import OrgDataStructure, OrgNode
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
        assert(self.org.root[1].startswith('#+TITLE'))
        assert( type( self.org.root[15] ) is OrgNode.Element )

    def test_directives(self):

        expect = [
            ('TITLE', 'test.org'),
            ('EMAIL', 'flint@forge.systems'),
            ('DESCRIPTION', 'pyorgmode test file'),
            ('KEYWORDS', 'hacking, text'),
            ('LANGUAGE', ''),
            ('OPTIONS', 'H:2'),
            ('LANGUAGE', 'fr'),
            ('EXCLUDE_TAGS', 'nopub'),
            ('TODO', 'TODO  READY | DONE ALREADY'),
            ('PRIORITIES', 'A B C')]

        self.assertEqual( self.org.get_directives(), expect)
        self.assertEqual( self.org.directives, expect)

    def test_load_from_string(self):
        org = OrgDataStructure()
        org.load_from_string(self.org.output())
        self.assertEqual(org.output(),self.org.output())


    def test_dict(self):
        self.org.root.dict()
        # TODO complete

    def test_get_todo(self):

        T = self.org.get_todos(self.org.root,'TODO')
        todos = [(t.todo, t.heading) for t in T]
        self.assertEqual(
            todos,
            [   ('TODO', 'Table test'),
                ('TODO', 'Items'),
                ('TODO', 'keywords as workflow states'),
                ('TODO', 'keywords as types'),
                ('TODO', 'dependencies') ]
        )

        D = self.org.get_todos(self.org.root,'DONE')
        dones = [(d.todo, d.heading) for d in D]
        self.assertEqual(
            dones,
            [('DONE', 'Structure des documents'), ('DONE', '/Outlines/'), ('DONE', 'Sections')]
        )

    def test_get_tags(self):
        T = self.org.get_nodes_by_tags(self.org.root,'TAG1')
        #print (T)

    def test_get_headings(self):

        H = self.org.get_nodes_by_attribute(self.org.root,'heading','TAGS')

        assert(len(H) is 3)

        expect = [
            '* TAGS :TAG1::TAG2:\n** TAGS :TAG1:\n** TAGS :TAG1::TAG2:\n\n',
            '** TAGS :TAG1:\n',
            '** TAGS :TAG1::TAG2:\n\n'
        ]

        [ self.assertEqual( str(H[x]), expect[x]) for x in range(len(H)) ]

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


