
import docutils.nodes
import docutils.parsers.rst
import docutils.utils
import docutils.frontend
from docutils.parsers.rst import Directive, directives
from argparse import ArgumentParser
from restprocessor import RestProcessor
from uml import uml
import json
from mako.template import Template
from mako.runtime import Context
from mako import exceptions
from io import StringIO

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
    parser.add_argument("-t", "--template", dest="templ", help="header template", metavar="TEMPLATE", required=True)
    parser.add_argument("-o", "--odir", dest="odir", help="rst input file", metavar="OUTPUT-DIR", required=True)
    parser.add_argument("-d", "--dump", dest="dump", help="dump content dictionary", default=False, required=False, action='store_true')
    parser.add_argument("-v", "--verbose", dest="verbose", help="Be more articulate about what is going on",
                        default=False, required=False, action='store_true')

    args = vars(parser.parse_args())

    directives.register_directive('uml', UmlDirective)

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

        for header in visitor._headers:
            try:
                buf = StringIO()
                ctx = Context(buf, file=header, content=visitor._headers[header])
                header_templ.render_context(ctx)
                if args['verbose']:
                    print("Writing ", header)
                with open(args['odir'] + '/' + header, "w") as outf:
                    outf.write(buf.getvalue())
                if args['dump']:
                    print('------ Dump content for header: ', header, ' ------')
                    dump = json.dumps(visitor._headers[header], indent=3)
                    print(dump)
            except:
                print(exceptions.text_error_template().render())

    if args['verbose']:
        print("Done.")

if __name__ == "__main__":
    main()