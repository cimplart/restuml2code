#
# restuml2code
# Copyright (C) 2022  Arthur Wisz
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import docutils.nodes
import docutils.parsers.rst
import docutils.utils
import docutils.frontend
from docutils.parsers.rst import Directive, directives, roles
from argparse import ArgumentParser
import json
from mako.template import Template
from mako.runtime import Context
from mako import exceptions
from io import StringIO
import pkg_resources
import os

try:
    from .restprocessor import RestProcessor
    from .uml import uml
    from .item import item
except:
    from restprocessor import RestProcessor
    from uml import uml
    from item import item

class UmlDirective(Directive):

    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = True
    option_spec = {}
    has_content = True

    node_class = uml

    def run(self):
        self.assert_has_content()
        text = '\n'.join(self.content)
        uml_node = self.node_class(rawsource=text)
        return [uml_node]

class ItemDirective(Directive):

    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True
    option_spec = {}
    has_content = False

    node_class = item

    def run(self):
        text = '\n'.join(self.content)
        item_node = self.node_class(rawsource=text)
        # Parse the directive contents.
        self.state.nested_parse(self.content, self.content_offset, item_node)
        return [ item_node ]

class IgnoredDirective(Directive):

    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = True
    option_spec = {}
    has_content = True

    def run(self):
        return []

def parse_rst(srcpath: str, text: str) -> docutils.nodes.document:
    parser = docutils.parsers.rst.Parser()
    components = (docutils.parsers.rst.Parser,)
    settings = docutils.frontend.OptionParser(components=components).get_default_values()
    document = docutils.utils.new_document(srcpath, settings=settings)
    parser.parse(text, document)
    return document

def sphinx_role_fn(name, rawtext, text, lineno, inliner, options={}, content=[]):
    return [], []

sphinx_roles = ['ref', 'any', 'doc', 'download', 'numref', 'envvar', 'token', 'keyword', 'option', 'term',
                'math', 'eq', 'abbr', 'command', 'dfn', 'file', 'guilabel', 'kbd', 'mailheader', 'makevar', 'manpage',
                'menuselection', 'mimetype', 'newsgroup', 'program', 'regexp', 'samp', 'pep', 'rfc' ]

def main():
    print("restuml2code version ", pkg_resources.get_distribution('restuml2code').version)
    parser = ArgumentParser()
    parser.add_argument("-i", "--input", dest="input", help="rst input file", metavar="INPUT-FILE", required=True)
    parser.add_argument("-t", "--template", dest="templ", help="header template", metavar="TEMPLATE", required=True)
    parser.add_argument("-o", "--odir", dest="odir", help="rst input file", metavar="OUTPUT-DIR", required=True)
    parser.add_argument("-d", "--dump", dest="dump", help="dump content dictionary", default=False, required=False, action='store_true')
    parser.add_argument("-v", "--verbose", dest="verbose", help="Be more articulate about what is going on",
                        default=False, required=False, action='store_true')

    args = vars(parser.parse_args())

    directives.register_directive('uml', UmlDirective)
    directives.register_directive('item', ItemDirective)
    directives.register_directive('todo', IgnoredDirective)

    # Prevent the 'Unknown interpreted text role' errors from docutils parser.
    for role in sphinx_roles:
        roles.register_local_role(role, sphinx_role_fn)

    with open(args['templ'], 'r') as f:
        templ_str = f.read()

    if args['verbose']:
        print("Analyzing code template...")
    header_templ = Template(templ_str)

    with open(args['input'], 'r') as f:
        text = f.read()
        if args['verbose']:
            print("Parsing input file...")
        doc = parse_rst(args['input'], text)
        visitor = RestProcessor(doc, text, args['verbose'])
        doc.walkabout(visitor)

        if not os.path.exists(args['odir']):
            if args['verbose']:
                print("Creating output directory...")
            os.mkdir(args['odir'])
        elif not os.path.isdir(args['odir']):
            print("ERROR: ", args['odir'], " is not a directory")

        for header in visitor._headers:
            try:
                if args['dump']:
                    print('------ Dump content for header: ', header, ' ------')
                    dump = json.dumps(visitor._headers[header], indent=3)
                    print(dump)
                if visitor._headers[header]['generated']:
                    buf = StringIO()
                    ctx = Context(buf, file=header, content=visitor._headers[header])
                    header_templ.render_context(ctx)
                    if args['verbose']:
                        print("Writing ", header)
                    with open(args['odir'] + '/' + header, "w") as outf:
                        outf.write(buf.getvalue())
                else:
                    if args['verbose']:
                        print("Skip writing ", header)
            except:
                print('Exception while rendering ' + header + ': ' + exceptions.text_error_template().render())

    if args['verbose']:
        print("Done.")

if __name__ == "__main__":
    main()