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

import docutils
import docutils.nodes
from typing import NamedTuple, Any, List

try:
    from .uml import uml
except:
    from uml import uml

class RestProcessor(docutils.nodes.SparseNodeVisitor):

    class KeyEntry(NamedTuple):
        row_label: str
        rownum: int
        attr_key: str
        tables: List[int]

    _PASS=0
    _FUNCTION_TABLE=1
    _TYPE_TABLE=2

    _ROW_KEYS = [
        KeyEntry('Type name:', 1, 'type-name', [_TYPE_TABLE]),
        KeyEntry('Function name:', 1, 'function-name', [_FUNCTION_TABLE]),
        KeyEntry('Description:', 2, 'description', [_TYPE_TABLE, _FUNCTION_TABLE]),
        KeyEntry('Declared in:', 4, 'header', [_TYPE_TABLE, _FUNCTION_TABLE]),
        KeyEntry('Kind:', 3, 'kind', [_TYPE_TABLE]),
        KeyEntry('Type:', 5, 'type', [_TYPE_TABLE]),
        KeyEntry('Elements:', 5, 'elements', [_TYPE_TABLE]),
        #KeyEntry('Range:', 6, 'range', [_TYPE_TABLE]),
        KeyEntry('Syntax:', 3, 'syntax', [_FUNCTION_TABLE]),
        KeyEntry('May be called from ISR:', 5, 'allowed-from-isr', [_FUNCTION_TABLE]),
        KeyEntry('Reentrancy:', 6, 'is-reentrant', [_FUNCTION_TABLE]),
        KeyEntry('Return value:', 7, 'return-value', [_FUNCTION_TABLE]),
        KeyEntry('Parameters [in]:', -1, 'in-params', [_FUNCTION_TABLE]),
        KeyEntry('Parameters [out]:', -1, 'out-params', [_FUNCTION_TABLE]),
        KeyEntry('Parameters [in-out]:', -1, 'inout-params', [_FUNCTION_TABLE]),
    ]

    def __init__(self, doc, text, verbose=False) -> None:
        super().__init__(doc)
        self._headers = {}
        self._lines = text.splitlines()
        self._state = self._PASS
        self._verbose = verbose

    def _verbose_print(self, *args, **kwargs):
        if self._verbose:
            print(*args, **kwargs)

    def visit_section(self, node: docutils.nodes.section) -> None:
        for c in node.children:
            if isinstance(c, docutils.nodes.title):
                self._verbose_print("Parsing section: " + c.astext())
                current_section = c.astext()
                if 'Module Interface Types' in current_section:
                    self._state = self._TYPE_TABLE
                    self._verbose_print("Parsing module types")
                    self._elem_section = node
                elif 'Module Interface Functions' in current_section:
                    self._state = self._FUNCTION_TABLE
                    self._verbose_print("Parsing module functions")
                    self._elem_section = node
                break

    def depart_section(self,node: docutils.nodes.section) -> None:
        if hasattr(self, '_elem_section'):
            if node == self._elem_section:
                self._state = self._PASS

    def visit_table(self, node: docutils.nodes.table) -> None:
        self.rownum = 0
        self._elem_attributes = {}

    def depart_table(self, node):
        self.rownum = -1
        if self._state != self._PASS and 'header' in self._elem_attributes:
            header = self._elem_attributes['header']
            self._headers.setdefault(header, {})
            self._headers[header].setdefault('functions', [])
            self._headers[header].setdefault('types', [])
            if self._state == self._FUNCTION_TABLE:
                #TODO check function attributes
                self._elem_attributes.setdefault('in-params', [])
                self._elem_attributes.setdefault('out-params', [])
                self._elem_attributes.setdefault('inout-params', [])
                self._headers[header]['functions'].append(self._elem_attributes)
            elif self._state == self._TYPE_TABLE:
                #TODO check type attributes
                self._headers[header]['types'].append(self._elem_attributes)
        elif self._state != self._PASS:
            raise RuntimeError('Invalid syntax: missing header in SW element specification')

    def visit_row(self, node):
        self.rownum += 1
        #print("table row " + str(self.rownum) + ' has ' + str(len(node.children)) + " elems")

    # Nested rows (e.g. function parameters) have the 1st column omitted by the grid table parser,
    # so we have to figure out the column number depending on the count of '|' before the paragraph text.
    def get_colnum(self, node: docutils.nodes.paragraph, content) -> None:
        content = content.splitlines()[0]
        src_line = self._lines[node.line - 1]
        cont_pos = src_line.find(content)
        assert cont_pos > -1
        return src_line[1:cont_pos].count('|')

    def visit_paragraph(self, node: docutils.nodes.paragraph) -> None:
        content = node.astext()
        if self.rownum > 0 and self._state != self._PASS:
            colnum = self.get_colnum(node, content)

            if colnum == 1:
                row_label_found = False
                for row_spec in self._ROW_KEYS:
                    if row_spec.row_label in content and self._state in row_spec.tables:
                        if row_spec.rownum > -1:
                            self._assert_syntax(self.rownum == row_spec.rownum, node.line)
                        self._attr_to_add = row_spec.attr_key
                        row_label_found = True
                        break
                if not row_label_found:
                    elem_type = 'function' if self._state == self._FUNCTION_TABLE else 'type'
                    print("WARNING: unrecognized " + elem_type + " attribute " + content)
            else:
                if self._state == self._TYPE_TABLE:
                    if self.rownum < 5:
                        self._assert_syntax(colnum == 2, node.line)
                        self._assert_syntax(self._attr_to_add not in self._elem_attributes, node.line)
                        self._elem_attributes[self._attr_to_add] = content
                    else:
                        assert 'kind' in self._elem_attributes
                        if self._attr_to_add == 'elements':
                            self._assert_syntax(colnum in [2, 3, 4], node.line)
                            self._elem_attributes.setdefault(self._attr_to_add, [])
                            if colnum == 2:
                                self._elem_attributes[self._attr_to_add].append({ 'type': content })
                            elif colnum == 3:
                                self._elem_attributes[self._attr_to_add][-1]['field'] = content
                            elif colnum == 4:
                                self._elem_attributes[self._attr_to_add][-1]['description'] = content.replace('\n', ' ')
                        elif self._attr_to_add == 'type':
                            self._assert_syntax(colnum == 2)
                            self._elem_attributes[self._attr_to_add] = content
                elif self._state == self._FUNCTION_TABLE:
                    if self.rownum <= 6:
                        self._assert_syntax(colnum == 2, node.line)
                        self._assert_syntax(self._attr_to_add not in self._elem_attributes, node.line)
                        if self._attr_to_add == 'allowed-from-isr':
                            self._elem_attributes[self._attr_to_add] = 'Yes' in content or 'yes' in content
                        elif self._attr_to_add == 'is-reentrant':
                            self._elem_attributes[self._attr_to_add] = (content == 'Reentrant') or 'Yes' in content or 'yes' in content
                        else:
                            self._elem_attributes[self._attr_to_add] = content
                    elif self.rownum == 7:
                        self._assert_syntax(colnum in [2, 3], node.line)
                        if colnum == 2:
                            if content == 'None' or content == 'none':
                                content = 'void'
                            self._elem_attributes[self._attr_to_add] = { 'type': content }
                        else:
                            self._elem_attributes[self._attr_to_add]['description'] = content.replace('\n', ' ')
                    else:
                        self._assert_syntax(colnum in [2, 3], node.line)
                        self._elem_attributes.setdefault(self._attr_to_add, [])
                        if colnum == 2:
                            self._elem_attributes[self._attr_to_add].append({ 'name': content })
                        else:
                            self._elem_attributes[self._attr_to_add][-1]['description'] = content.replace('\n', ' ')

    def _strip_code_block(self, str):
        return str.replace('.. code-block::', '').strip()

    # code blocks are handled here
    def visit_literal_block(self, node: docutils.nodes.literal_block) -> None:
        content = node.astext()
        if self.rownum > 0 and self._state != self._PASS:
            # literal_block node has no line
            #colnum = self.get_colnum(node, content)

            if self._state == self._TYPE_TABLE:
                if self.rownum == 5:
                    if self._attr_to_add == 'type':
                        self._elem_attributes[self._attr_to_add] = self._strip_code_block(content)
            elif self._state == self._FUNCTION_TABLE:
                if self.rownum == 3:
                    self._assert_syntax(self._attr_to_add not in self._elem_attributes, node.line)
                    self._elem_attributes[self._attr_to_add] = self._strip_code_block(content)


    def visit_uml(self, node: uml) -> None:
        #print('uml: ' + node.rawsource)
        pass

    def depart_uml(self, node: uml) -> None:
        pass

    def unknown_visit(self, node: docutils.nodes.Node) -> None:
        """Called for all other node types."""
        #print('Unknown node: ' + str(node))

        #if isinstance(node, docutils.nodes.Element):
        #    print("Unknown element: " + node.astext())
        pass

    def _assert_syntax(self, condition, line):
        if not condition:
            msg = 'Invalid syntax on line ' + str(line)
            print(msg)
            raise RuntimeError(msg)
