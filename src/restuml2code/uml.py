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
from lark import Lark
import os

class uml(docutils.nodes.General, docutils.nodes.Element):

    def __init__(self, rawsource='', *children, **attributes):

        docutils.nodes.Element.__init__(self, rawsource, *children, **attributes)

        if ':restuml2code:' in rawsource:
            dir_path = os.path.dirname(os.path.realpath(__file__))
            grammar_file_path = os.path.join(dir_path, "puml.ebnf")
            f = open(grammar_file_path)

            parser = Lark(f.read(), debug=True)
            self.parse_tree = parser.parse(rawsource + '\n')
