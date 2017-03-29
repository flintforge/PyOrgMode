
import pyorgmode
import copy
try:
    import unittest2 as unittest
except ImportError:
    import unittest

def Get_Scheduled_Elements(element, data=[]):
    for child in element.__dict__.get('content'):
        if hasattr(child,'scheduled') and child.scheduled:
            data.append(copy.deepcopy(child.parent))
        Get_Scheduled_Elements(child,data)
    return data

class TestAgenda(unittest.TestCase):
    def test_agenda(self):
        input_file = pyorgmode.OrgDataStructure()
        output_file = pyorgmode.OrgDataStructure()
        input_file.load_from_file("tests/orgs/agenda.org")
        outfile = "/tmp/test_scheduled_output.org"

        # Get the scheduled elements (those with SCHEDULE, DEADLINE in them, not in the node name)
        scheduled_elements = Get_Scheduled_Elements(input_file.root)

        # Assign these element to the root (reparent each elements recursively, relevel them cleanly)
        output_file.root.append_clean(scheduled_elements)

        output_file.save_to_file(outfile)

        with open(outfile) as F: saved = F.readlines()

        self.assertEqual(saved,[
            '* Element 1\n',
            '   SCHEDULED: <2011-02-08>\n',
            '* Element 3\n',
            '   DEADLINE: <2011-02-08>\n',
            '** Test\n',
            '** Element 4\n',
            '   SCHEDULED: <2011-02-08>\n',
            '* Element 4\n',
            '   SCHEDULED: <2011-02-08>\n'])
