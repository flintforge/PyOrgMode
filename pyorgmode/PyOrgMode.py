# -*- coding: utf-8 -*-
'''
###############################################################################
#
#   pyorgmode, a python module for processing org-mode files
#   Copyright (C) 2010 Jonathan BISSON (bissonjonathan on the google thing).
#   All Rights Reserved
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#
###############################################################################


pyorgmode process org-mode files and can create, read, parse and modify
orgfiles, by "bookkeeping" python objects

'''

import re
import time


def split_iter(string):
    '''
    use a generator to prevent memory overheads when loading LARGE org files
    '''
    return (x.group(0) for x in re.finditer(r".*\n", string))


# blank space instead of 'None' for None
def xstr(s):
    return '' if s is None else str(s)


class OrgDirective:
    rgx_directives = re.compile('^#\+([\w]+):\s*(.*)$')



class OrgDate:
    """Functions for date management"""

    format = 0
    TIMED = 1
    DATED = 2
    WEEKDAYED = 4
    ACTIVE = 8
    INACTIVE = 16
    RANGED = 32
    REPEAT = 64
    CLOCKED = 128

    RGX = {'start': '[[<]', # todo : check begin and end item match
           'end':   '[]>]',
           'date':  '([0-9]{4})-([0-9]{2})-([0-9]{2})(\s+([\w.]+))?',
           'time':  '([0-9]{2}):([0-9]{2})',
           'clock': '([0-9]{1}):([0-9]{2})', # ~ TODO : clock can be many hours digits long
           'repeat': '[\+\.]{1,2}\d+[dwmy]'}


    rgxDate = '(?P<date>{date})(\s+(?P<time>{time}))?'.format(**RGX)

    rgxDateTimeRange = ('{start}(?P<date>{date})\s+(?P<time1>{time})'
                        '-(?P<time2>{time}){end}').format(**RGX)
    rgxDateRange = ('{start}(?P<date1>{date}(\s+{time})?){end}--'
                    '{start}(?P<date2>{date}(\s+{time})?){end}').format(**RGX)

    rgxDateSingle = ('{start}(?P<datetime>{date}(\s+{time})?)'
                     '(\s+(?P<repeat>{repeat}))?{end}').format(**RGX)

    rgxClock = '(?P<clocked>{clock})'.format(**RGX)


    def __init__(self, value):
        """
        Initialisation of an OrgDate element.
        """

        # todo
        '''
        self.date
        self.time
        self.clock
        self.repeat
        self.active
        '''
        self.value = None
        self.repeat = None
        self.set(value)

    def parse_datetime(self, s):
        """
        Parses an org-mode date time string.
        Returns (timed, weekdayed, time_struct, repeat).
        """
        s = re.search(self.rgxDate, s)

        # fix this. the wd is already in a capture
        weekdayed = len(s.group('date').split()) > 1
        weekday_suffix = ""
        if weekdayed:
            weekday_suffix = s.group('date').split()[1]
        formats = {
            'timed_dated':[True, '{0} {1} {2}', '%Y-%m-%d %a %H:%M'],
            'timed':[True, '{0} {2}', '%Y-%m-%d %H:%M'],
            'nottimed_dated':[False, '{0} {1}', '%Y-%m-%d %a'],
            'notdated':[False, '{0}', '%Y-%m-%d'],
        }

        format_date = (s.group('time') and (
            'timed_dated' if weekday_suffix else 'timed'
        )) or 'nottimed_dated' if weekday_suffix else 'notdated'

        return (formats[format_date][0],
                weekdayed,
                time.strptime(
                    formats[format_date][1].format(
                        s.group('date').split()[0],
                        weekday_suffix,
                        s.group('time')),
                    formats[format_date][2]))


    def set(self,value):

        # whether it is an active date-time or not
        if value[0] == '<':
            self.format |= self.ACTIVE
        elif value[0] == '[':
            self.format |= self.INACTIVE

        match = re.search(self.rgxDateTimeRange, value)

        if match:
            timed, weekdayed, self.value = self.parse_datetime(
                match.group('date') + ' ' + match.group('time1'))
            if weekdayed:
                self.format |= self.WEEKDAYED
            timed, weekdayed, self.end = self.parse_datetime(
                match.group('date') + ' ' + match.group('time2'))
            self.format |= self.TIMED | self.DATED | self.RANGED
            return

        match = re.search(self.rgxDateRange, value)
        if match:
            timed, weekdayed, self.value = self.parse_datetime(
                match.group('date1'))
            if timed:
                self.format |= self.TIMED
            if weekdayed:
                self.format |= self.WEEKDAYED
            timed, weekdayed, self.end = self.parse_datetime(
                match.group('date2'))
            self.format |= self.DATED | self.RANGED
            return

        # single date with no range
        match = re.search(self.rgxDateSingle, value)
        if match:
            timed, weekdayed, self.value = self.parse_datetime(
                match.group('datetime'))

            if match.group('repeat'):
                self.repeat = match.group('repeat')
                self.format |= self.REPEAT
            self.format |= self.DATED
            if timed:
                self.format |= self.TIMED
            if weekdayed:
                self.format |= self.WEEKDAYED
            self.end = None
            return

        # clock
        match = re.search(self.rgxClock, value)
        if match:
            self.value = value
            self.format |= self.CLOCKED


    def get_value(self):
        """
        Get the timestamp as a text according to the format
        """

        if not self.value:
            return ''

        if self.format & self.CLOCKED:
            return self.value

        fmt_dict = {'time': '%H:%M'}
        if self.format & self.ACTIVE:
            fmt_dict['start'], fmt_dict['end'] = '<', '>'
        else:
            fmt_dict['start'], fmt_dict['end'] = '[', ']'
        if self.format & self.WEEKDAYED:
            fmt_dict['date'] = '%Y-%m-%d %a'
        if self.format & self.CLOCKED:
            fmt_dict['clock'] = "%H:%M"
        elif not self.format & self.WEEKDAYED:
            fmt_dict['date'] = '%Y-%m-%d'

        if self.format & self.RANGED:
            if self.value[:3] == self.end[:3]:
                # range is between two times on a single day
                assert self.format & self.TIMED
                return (time.strftime(
                    '{start}{date} {time}-'.format(**fmt_dict), self.value) +
                    time.strftime('{time}{end}'.format(**fmt_dict),self.end))
            else:
                # range is between two days
                if self.format & self.TIMED:
                    return (time.strftime(
                        '{start}{date} {time}{end}--'.format(**fmt_dict),
                        self.value) +
                        time.strftime('{start}{date} {time}{end}'.format(**fmt_dict),self.end))
                else:
                    return (time.strftime(
                        '{start}{date}{end}--'.format(**fmt_dict), self.value) +
                        time.strftime('{start}{date}{end}'.format(**fmt_dict),self.end))

        '''
        if self.format & self.CLOCKED:
            # clocked time, return as is
            return self.value
        '''
        #else: # non-ranged time
        # Repeated
        if self.format & self.REPEAT:
            fmt_dict['repeat'] = ' ' + self.repeat
        else:
            fmt_dict['repeat'] = ''
        if self.format & self.TIMED:
            return time.strftime(
                '{start}{date} {time}{repeat}{end}'.format(**fmt_dict), self.value)
        else:
            return time.strftime(
                '{start}{date}{repeat}{end}'.format(**fmt_dict), self.value)

class OrgPlugin:
    """
    Generic class for all plugins
    """
    def __init__(self):
        """ Generic initialization """
        self.processed = False
        # the plugin system stores the indentation before processing
        self.keepindent = True
        self.keepindent_value = ""

    def process(self,current,line):
        """
        A wrapper function for _process.
        Asks the plugin if it can manage this kind of line.
        """
        self.processed = False
        if self.keepindent :
            self.keepindent_value = line[0:len(line)-len(line.lstrip(" \t"))] # Keep a trace of the indentation
            return self._process(current,line.lstrip(" \t"))
        else:
            return self._process(current,line)

    def _process(self,current,line):
        """ used by the plugin for the management of the line. """
        self.processed = False
        return current

    def _append(self,current,element):
        """ Internal function that adds to current. """
        if self.keepindent and hasattr(element,"set_indent"):
            element.set_indent(self.keepindent_value)
        return current.append(element)

    def close(self,current):
        """ A wrapper function for closing the module. """
        self.processed = False
        return self._close(current)

    def _close(self,current):
        """ This is the function used by the plugin t
        o close everything that have been opened. """
        self.processed = False
        return current

class OrgElement:
    """
    Generic class for all Elements excepted text and unrecognized ones
    """
    def __init__(self):
        self.content = []
        self.parent = None
        self.level = 0
        self.indent = ""

    def __getitem__(self,i):
        return self.content[i]

    def append(self,element):
        # TODO Check validity
        self.content.append(element)
        # Check if the element got a parent attribute
        # If so, we can have childrens into this element
        if hasattr(element,"parent"):
            element.parent = self
        return element

    def set_indent(self,indent):
        """ Transfer the indentation from plugin to element. """
        self.indent = indent

    def output(self):
        """ Wrapper for the text output. """
        return self.indent+self._output()

    def _output(self):
        """ This is the function really used by the plugin. """
        return ""

    def __str__(self):
        """ Used to return a text when called. """
        return self.output()


class OrgTodo():
    """Describes an individual TODO item for use in agendas and TODO lists"""
    def __init__(self, heading, todo_state,
                 scheduled=None, deadline=None,
                 tags=None, priority=None,
                 path=[0], node=None
                 ):
        self.heading = heading
        self.todo_state = todo_state
        self.scheduled = scheduled
        self.deadline = deadline
        self.tags = tags
        self.priority = priority
        self.node = node

    def __str__(self):
        string = self.todo_state + " " + self.heading
        return string

class OrgClock(OrgPlugin):
    """Plugin for Clock elements"""
    rgx = re.compile("(?:\s*)CLOCK:(?:\s*)((?:<|\[).*(?:>||\]))--((?:<|\[).*(?:>||\])).+=>\s*(.*)")

    def __init__(self):
        OrgPlugin.__init__(self)

    def _process(self,current,line):
        clocked = self.rgx.findall(line)
        if clocked:
            self._append(current,self.Element(clocked[0][0], clocked[0][1], clocked[0][2]))
            self.processed = True
        return current

    class Element(OrgElement):

        def __init__(self,start="",stop="",duration=""):
            OrgElement.__init__(self)
            self.start = OrgDate(start)
            self.stop = OrgDate(stop)
            self.duration = OrgDate(duration)

        def _output(self):
            # quick patch for duration padding before fixing OrgDate
            #
            duration = self.duration.get_value()
            if re.match('\d:\d\d',duration) : # single digit hour
                pad = ' '
            """Outputs the Clock element in text format (e.g CLOCK: [2010-11-20 Sun 19:42]--[2010-11-20 Sun 20:14] =>  0:32)"""
            return "CLOCK: %s--%s => %s%s\n" % \
                (self.start.get_value(),self.stop.get_value(),xstr(pad),self.duration.get_value())
            #"CLOCK: " + self.start.get_value() + "--" + self.stop.get_value() + " =>  " + self.duration.get_value()+"\n"

class OrgSchedule(OrgPlugin):
    """Plugin for Schedule elements"""
    rgx = re.compile(
        "(SCHEDULED|DEADLINE|CLOSED): (%s)" %
        "(<|\[)([0-9]{4}-[0-9]{2}-[0-9]{2})(>|\])")

    def __init__(self):
        OrgPlugin.__init__(self)

    def _process(self,current,line):

        # TODO check if it's a valid date
        sched = self.rgx.match(line)
        if sched :
            self.schedule = (sched.group(1), sched.group(2))
            self._append(current,self.Element(self.schedule))
            self.processed = True

        return current

    class Element(OrgElement):
        '''
            Schedule is an element taking into account
            DEADLINE, SCHEDULED and CLOSED parameters of elements
        '''

        def __init__(self,scheduled):

            OrgElement.__init__(self)

            if scheduled:
                self.type  = scheduled[0]
                self.scheduled = OrgDate(scheduled[1])

        def _output(self):
            output = "%s: %s\n" % ( self.type, self.scheduled.get_value())
            return output

class OrgDrawer(OrgPlugin):
    """A Plugin for drawers"""
    rgx = re.compile("(?:\s*)(?::)(\w+)(?::)\s*(.*)^")

    def __init__(self):
        OrgPlugin.__init__(self)

    def _process(self,current,line):
        drawer = self.rgx.match(line)
        if isinstance(current, OrgDrawer.Element): # We are in a drawer
            self.processed = True
            if drawer:
                if drawer.group(1).upper() == "END": # Ending drawer
                    current = current.parent
                elif drawer.group(2): # Adding a property
                    self._append(current,self.Property(drawer.group(1),drawer.group(2)))
            else: # Adding text in drawer
                self._append(current,line.rstrip("\n"))
        elif drawer: # Creating a drawer
            current = self._append(current,OrgDrawer.Element(drawer.group(1)))
        else:
            return current
        return current # It is a drawer, change the current also (even if not modified)

    class Element(OrgElement):
        """A Drawer object, like :properties: """

        def __init__(self,name=""):
            OrgElement.__init__(self)
            self.name = name

        def _output(self):
            output = ":" + self.name + ":\n"
            for element in self.content:

                output += str(element) + "\n"
            output += self.indent + ":END:\n"
            return output

    class Property(OrgElement):
        """A Property object, used in drawers."""
        def __init__(self,name="",value=""):
            OrgElement.__init__(self)
            self.name = name
            self.value = value

        def _output(self):
            """Outputs the property in text format (e.g. :name: value)"""
            return ":" + self.name + ": " + self.value

class OrgTable(OrgPlugin):
    """ table management"""
    def __init__(self):
        OrgPlugin.__init__(self)
        self.regexp = re.compile("^\s*\|")

    def _process(self,current,line):
        table = self.regexp.match(line)
        if table:
            if not isinstance(current,self.Element):
                current = current.append(self.Element())
            current.append(line.rstrip().strip("|").split("|"))
            self.processed = True
        else:
            if isinstance(current,self.Element):
                current = current.parent
        return current

    class Element(OrgElement):
        """
        Table Element
        """

        def __init__(self):
            OrgElement.__init__(self)

        def _output(self):
            output = ""
            for element in self.content:
                output += "|"
                for cell in element:
                    output += str(cell) + "|"
                output += "\n"
            return output


class OrgNode(OrgPlugin):

    '''
        an orgnode with the optional default formating :
        # ORDER = enum('NODE,TODO,DATE,PRIO,HEADING,TAGD')
        all fields except the node (* stars) are optionnal

        todo :
        - detect the todo and done in the OrgCommands
          (#+seq_todo) before instanciating a node
        - make the order flexible
    '''

    # seq_todo
    todo_list = ['TODO','READY']
    done_list = ['DONE']

    date_format = '%Y-%m-%d %a'

    rgxs = (
        "^(?P<node>\*+)\s+",
        '((?P<todo>%s|%s)\s+)?' % (
            '|'.join(todo_list),
            '|'.join(done_list)
        ),
        '(<(?P<date>[0-9]{4}-[0-9]{2}-[0-9]{2}\s+[\w.]+)>\s+)?',
        '((?P<prio>\[.*?\])\s+)?',
        '(?P<heading>.*?)', # non greedy
        '(?P<padding>\s*)', # the padded space before the tags
        '(:(?P<tags>[\w:]+):)?$',
    )

    regexp = re.compile(len(rgxs)*'%s' % rgxs)

    def __init__(self):
        OrgPlugin.__init__(self)
        # If the line starts by an indent, it is not a node
        self.keepindent = False


    def _process(self,current,line):

        match = self.regexp.search(line)

        if match:
            level,todo,date,prio,head,padding,tags = match.group('node','todo','date','prio','heading','padding','tags')

            level = len(level)
            if current.parent :
                current.parent.append(current)
            # a new level ?
            if (level > current.level): # Yes
                parent = current # Parent is now the current node
            else: # the parent of the current node is the parent
                parent = current.parent
                # If we are going back one or more levels,
                # walk through parents
                while level < current.level:
                    current = current.parent
                    parent = current.parent

            # Create a new node and assign parameters
            current = OrgNode.Element(
                level=level,
                todo=todo,
                prio=prio and prio.strip('[#]'),
                date=date,
                heading=head.strip(),
                padding=padding,
                tags=tags and tags.split(':'),
                parent=parent
            )

            self.processed = True

        return current

    def _close(self,current):
        # Add the last node
        if current.level > 0 and current.parent:
            current.parent.append(current)

    class Element(OrgElement):
        # Defines an OrgMode Node in a structure
        # The ID is auto-generated using uuid.
        # The level 0 is the document itself

        def __init__(self, level=0, todo='', date=None, prio='', heading='', padding='', tags=[], parent=None):
            OrgElement.__init__(self)
            self.level = level
            self.todo = todo or ''
            self.cdate = date and time.strptime(date,OrgNode.date_format)
            self.date = date and '<'+date+'>' # temporary. not finished. todo : check for validity of date here
            self.priority = prio or ''
            self.heading = heading
            self.padding = padding
            self.tags = tags or ''
            self.parent = parent
            # TODO  Scheduling structure

        def _output(self):

            if self.level is 0 :
                return ''.join([str(element) for element in self.content])

            output = '%s %s%s%s%s%s%s%s' % (
                self.level*'*',
                xstr(self.todo and self.todo+' '),
                xstr(self.date and self.date+' '),
                xstr(self.priority and '[#'+self.priority+'] '),
                xstr(self.heading),
                self.padding,
                xstr(self.tags and '%s%s%s\n' % (':',':'.join(self.tags),':')),
                ''.join([str(element) for element in self.content])
            )

            '''
            if self.parent :
                if self.priority:
                    output += "[#" + self.priority + "] "
                output = output + self.heading

                if self.tags :
                    output += '\t%s%s%s' % (':',':'.join(self.tags),':')
            '''
            '''
            for element in self.content:
                output += str(element)
            '''
            return output


        def dict(self):
            '''
            turn the node into a nested dictionnary
            to dump as is json
            '''
            return (
                { id(self) : {
                    'date':self.date,
                    'heading' : self.tags,
                    'tags' : self.tags,
                    'level' : self.level,
                    'content': [
                        n.dict() if
                        isinstance(n,OrgNode.Element) else
                        n._output() if isinstance(n,OrgElement) else
                        n
                        for n in self.content
                    ]
                }}
            )


        def append_clean(self,element):
            if isinstance(element,list):
                self.content.extend(element)
            else:
                self.content.append(element)
            self.reparent_cleanlevels(self)

        def reparent_cleanlevels(self,element=None,level=None):
            """
            Reparent the childs elements of 'element' and make levels simpler.
            Useful after moving one tree to another place or another file.
            """
            if element is None:
                element = self.root
            if hasattr(element,"level"):
                if level is None:
                    level = element.level
                else:
                    element.level = level

            if hasattr(element,"content"):
                for child in element.content:
                    if hasattr(child,"parent"):
                        child.parent = element
                        self.reparent_cleanlevels(child,level+1)


class OrgDataStructure(OrgElement):
    """
    Data structure containing all the nodes
    The root property contains a reference to the level 0 node
    """
    root = None
    '''
    to throw errors or let go when the structure conformancy isn't met.
    - only for goody todo_states for now
    '''
    STRICT = False

    #+directives: d
    rgx_directives = re.compile('^#\+([\w]+):\s*(.*)')

    def __init__(self):
        OrgElement.__init__(self)
        self.plugins = []
        self.load_plugins(OrgTable(),OrgDrawer(),OrgNode(),OrgSchedule(),OrgClock())
        '''
        The root node is used as a container for the file
        '''
        self.root = OrgNode.Element()
        self.root.parent = None
        self.level = 0
        self.commands = []


    def load_plugins(self,*arguments,**keywords):
        """
        Used to load plugins inside this DataStructure
        """
        for plugin in arguments:
            self.plugins.append(plugin)

    def set_todo_states(self,new_states):
        """
        Used to override the default list of todo states for any
        OrgNode plugins in this object's plugins list. Expects
        a list[] of strings as its argument. The list can be split
        by '|' entries into TODO items and DONE items. Anything after
        a second '|' will not be processed and be returned.
        Setting to an empty list will disable TODO checking.

        update : pass it a string matching the #+SEQ_TODO pattern
        """
        new_todo_states = []
        new_done_states = []

        A = new_states
        if self.STRICT :
            assert A.count('|') <= 1 and len(A.split()) >= 2

        if A.count('|'):
            td = A.split('|')
            new_todo_states = set(td[0].split() or ['TODO'])
            new_done_states = set(td[1].split() or ['DONE'])
        else:
            td = A.split()
            if len(td) > 1 :
                new_done_states = set([td.pop()])
                new_todo_states = set([td])


        #?
        for plugin in self.plugins:
            if plugin.__class__ == OrgNode:
                plugin.todo_list = new_todo_states
                plugin.done_list = new_done_states

        if new_states:
            return new_states # Return any leftovers

    def get_todo_states(self, list_type="todo"):
        '''
        Returns a list of todo states. An empty list means that
        instance of OrgNode has TODO checking disabled. The first argument
        determines the list that is pulled ("todo"*, "done" or "all").
        '''
        all_states = []
        for plugin in self.plugins:
            if plugin.__class__ == OrgNode:
                if plugin.todo_list and (list_type == "todo" or list_type == "all"):
                    all_states += plugin.todo_list
                if plugin.done_list and (list_type == "done" or list_type == "all"):
                    all_states += plugin.done_list
        return list(set(all_states))

    def add_todo_state(self, new_state):
        """
        Appends a todo state to the list of todo states of any OrgNode
        plugins in this objects plugins list.
        Expects a string as its argument.
        """
        for plugin in self.plugins:
            if plugin.__class__ == OrgNode:
                plugin.todo_list.append(new_state)

    def add_done_state(self, new_state):
        """
        Appends a todo state to the list of todo states of any OrgNode
        plugins in this objects plugins list.
        Expects a string as its argument.
        """
        for plugin in self.plugins:
            if plugin.__class__ == OrgNode:
                plugin.done_list.append(new_state)

    def remove_todo_state(self, old_state):
        """
        Remove a given todo state from both the todo list and the done list.
        Returns True if the plugin was actually found.
        """
        found = False
        for plugin in self.plugins:
            if plugin.__class__ == OrgNode:
                while old_state in plugin.todo_list:
                    found = True
                    plugin.todo_list.remove(old_state)
                while old_state in plugin.done_list:
                    found = True
                    plugin.done_list.remove(old_state)
        return found


    def _read(self,content):
        '''
            APPEND the content to the current OrgDataStructure
        '''
        current = self.root
        for line in content:
            for plugin in self.plugins:
                current = plugin.process(current,line)
                if plugin.processed: # Plugin found something
                    processed = True
                    break
                else:
                    processed = False

            if not processed and line: # Nothing special, just content
                current.append(line)

        for plugin in self.plugins:
            current = plugin.close(current)


    def load_from_file(self,file):
        with open(file,'r') as F:
            self._read(F)

    def load_from_string(self, string):
        self._read(split_iter(string))

    def save_to_file(self,name,node=None):
        ''' Dump this org in a file '''
        with open(name,'w') as F:
            node = node or self.root
            F.write(str(node))


    def toplevel_nodes(self):
        return [N for N in self.root.content if isinstance(N,OrgNode.Element)]

    def get_directives(self):
        '''
            #+DIRECTIVE: values
            (on top, before any node, otherwise it belongs to the content of a node)
        '''
        self.directives = [
            (m.group(1),m.group(2))
            for N in self.root.content if type(N) is str
            for m in [self.rgx_directives.match(N)] if m]
        return self.directives

    @staticmethod
    def get_nodes_by_attribute(node, attribute, value):
        found_nodes = []
        if isinstance(node, OrgNode.Element):
            # to throw an error if the attribute doesn't exist
            if node.__dict__[attribute] == value:
                found_nodes = [node]

            for nodes in node.content:

                f = OrgDataStructure.get_nodes_by_attribute(nodes, attribute, value)
                if f:
                    if not found_nodes : found_nodes = []
                    found_nodes += f

        return found_nodes if found_nodes else None


    @staticmethod
    def get_todos(node,value):
        return OrgDataStructure.get_nodes_by_attribute(node, 'todo', value)

    @staticmethod
    def get_nodes_by_heading(node,value):
        return OrgDataStructure.get_nodes_by_attribute(node, 'heading', value)

    @staticmethod
    def get_nodes_by_priority(node,value):
        return OrgDataStructure.get_nodes_by_attribute(node, 'priority', value)

    @staticmethod
    def get_nodes_by_tags(node,value):
        return OrgDataStructure.get_nodes_by_attribute(node, 'tags', value)
