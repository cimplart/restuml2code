
import docutils.nodes
import docutils.parsers.rst
import docutils.utils
import docutils.frontend
from docutils.parsers.rst import Directive, directives
from argparse import ArgumentParser
from restprocessor import RestProcessor
from uml import uml
import json

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
        # TODO Parse the directive contents.
        return [uml_node]

def parse_rst(srcpath: str, text: str) -> docutils.nodes.document:
    parser = docutils.parsers.rst.Parser()
    components = (docutils.parsers.rst.Parser,)
    settings = docutils.frontend.OptionParser(components=components).get_default_values()
    document = docutils.utils.new_document(srcpath, settings=settings)
    parser.parse(text, document)
    return document

def main():
    parser = ArgumentParser()
    parser.add_argument("-i", "--input", dest="input", help="rst input file", metavar="INPUT-FILE", required=True)
    parser.add_argument("-o", "--odir", dest="odir", help="rst input file", metavar="OUTPUT-DIR", required=True)

    args = vars(parser.parse_args())

    directives.register_directive('uml', UmlDirective)

    with open(args['input'], 'r') as f:
        text = f.read()
        doc = parse_rst(args['input'], text)
        visitor = RestProcessor(doc, text)
        doc.walkabout(visitor)
        dump = json.dumps(visitor._headers, indent=3)
        print(dump)

if __name__ == "__main__":
    main()