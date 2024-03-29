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
from typing import NamedTuple, Any, List, Dict
import copy

try:
    from .uml import uml
    from .item import item
    from .umldependencyscanner import UmlDependencyScanner
except:
    from uml import uml
    from item import item
    from umldependencyscanner import UmlDependencyScanner

class RestProcessor(docutils.nodes.SparseNodeVisitor):

    _PASS='pass'
    _FUNCTION_TABLE='function_table'
    _TYPE_TABLE='type_table'
    _MACRO_CONSTANTS_TABLE='macro_constants_table'
    _MACRO_FUNCTION_TABLE='macro_function_table'
    _SOURCE_FILE_DEPENDENCIES='source_file_dependencies'
    _SOURCE_FILE_TABLE='file_table'
    _VARIABLE_TABLE='variable_table'

    class KeyEntry(NamedTuple):
        row_label: str
        attr_key: str
        #tuple: state, rownum
        tables: Dict[ int, int ]

    # The number in the dict is the expected table row number. -1 is for moving/optional attributes.
    _ROW_KEYS = [
        KeyEntry('Type name:', 'type-name', dict([(_TYPE_TABLE, 1)])),
        KeyEntry('Function name:', 'function-name', dict([(_FUNCTION_TABLE, 1)])),
        KeyEntry('Constants Group:', 'constants-group', dict([(_MACRO_CONSTANTS_TABLE, 1)])),
        KeyEntry('Variables Group:', 'variables-group', dict([(_VARIABLE_TABLE, 1)])),
        KeyEntry('Identifier name:', 'identifier-name', dict([(_MACRO_FUNCTION_TABLE, 1)])),
        KeyEntry('Description:', 'description', dict([(_TYPE_TABLE, 2), (_FUNCTION_TABLE, 2), (_MACRO_FUNCTION_TABLE, 2)])),
        KeyEntry('Declared in:', 'header', dict([(_TYPE_TABLE, 4), (_FUNCTION_TABLE, 4), (_MACRO_CONSTANTS_TABLE, 2),
                                                 (_MACRO_FUNCTION_TABLE, 4),(_VARIABLE_TABLE, 2)])),
        KeyEntry('Constants:', 'constants', dict([(_MACRO_CONSTANTS_TABLE, 3), (_TYPE_TABLE, 5)])),
        KeyEntry('Variables:', 'variables', dict([(_VARIABLE_TABLE, 3)])),
        KeyEntry('Kind:', 'kind', dict([(_TYPE_TABLE, 3)])),
        KeyEntry('Type:', 'type', dict([(_TYPE_TABLE, 5)])),
        KeyEntry('Elements:', 'elements', dict([(_TYPE_TABLE, 5)])),
        KeyEntry('Syntax:', 'syntax', dict([(_FUNCTION_TABLE, 3), (_MACRO_FUNCTION_TABLE, 3)])),
        KeyEntry('May be called from ISR:', 'allowed-from-isr', dict([(_FUNCTION_TABLE, 5), (_MACRO_FUNCTION_TABLE, 5)])),
        KeyEntry('Reentrancy:', 'is-reentrant', dict([(_FUNCTION_TABLE, 6), (_MACRO_FUNCTION_TABLE, 6)])),
        KeyEntry('Return value:', 'return-value', dict([(_FUNCTION_TABLE, 7), (_MACRO_FUNCTION_TABLE, 7)])),
        KeyEntry('Parameters [in]:', 'in-params', dict([(_FUNCTION_TABLE, -1), (_MACRO_FUNCTION_TABLE, -1)])),
        KeyEntry('Parameters [out]:', 'out-params', dict([(_FUNCTION_TABLE, -1), (_MACRO_FUNCTION_TABLE, -1)])),
        KeyEntry('Parameters [in-out]:', 'inout-params', dict([(_FUNCTION_TABLE, -1), (_MACRO_FUNCTION_TABLE, -1)])),
        KeyEntry('Definition:', 'definition', dict([(_MACRO_FUNCTION_TABLE, -1)])),
        KeyEntry('Call cycle interval:', 'call-cycle-interval', dict([(_FUNCTION_TABLE, -1), (_MACRO_FUNCTION_TABLE, -1)]))
    ]

    def __init__(self, doc, text, verbose=False) -> None:
        super().__init__(doc)
        self._headers = {}
        self._lines = text.splitlines()
        self._state = self._PASS
        self._verbose = verbose
        self._rownum = -1
        self._globals = {}
        self._private_section = False

    def _verbose_print(self, *args, **kwargs):
        if self._verbose:
            print(*args, **kwargs)

    _SECTION_STATE_MAP = {
        "Types" : _TYPE_TABLE,
        "Functions" : _FUNCTION_TABLE,
        "Constants" : _MACRO_CONSTANTS_TABLE,
        "Variables" : _VARIABLE_TABLE,
        "Function-like Macros" : _MACRO_FUNCTION_TABLE,
        "Source File Description" : _SOURCE_FILE_TABLE,
        "Source File Dependencies" : _SOURCE_FILE_DEPENDENCIES,
        "Compile-time Configuration" : _MACRO_CONSTANTS_TABLE,
        "Link-time Configuration" : _TYPE_TABLE,
    }

    class HeaderAttribute(NamedTuple):
        name: str
        default: Any

    _HEADER_ATTRIBUTES = [
        HeaderAttribute('functions', []),
        HeaderAttribute('types', []),
        HeaderAttribute('variables', []),
        HeaderAttribute('macro-constants', []),
        HeaderAttribute('macro-functions', []),
        HeaderAttribute('includes', []),
        HeaderAttribute('file-name', ''),
        HeaderAttribute('description', ''),
        HeaderAttribute('generated', False)
    ]

    def visit_section(self, node: docutils.nodes.section) -> None:
        for c in node.children:
            if isinstance(c, docutils.nodes.title):
                self._verbose_print("Parsing section: " + c.astext())
                current_section = c.astext()
                for s in self._SECTION_STATE_MAP:
                    if s in current_section:
                        self._state = self._SECTION_STATE_MAP[s]
                        self._verbose_print("Parsing " + self._state.replace('_', ' '))
                        self._elem_section = node
                        self._private_section = ('Private' in current_section)
                        break
                break

    def depart_section(self,node: docutils.nodes.section) -> None:
        if hasattr(self, '_elem_section'):
            if node == self._elem_section:
                self._state = self._PASS

    def _add_header(self, header):
        self._headers.setdefault(header, {})
        for hattr in self._HEADER_ATTRIBUTES:
            self._headers[header].setdefault(hattr.name, copy.deepcopy(hattr.default))
        self._headers[header]['file-name'] = header

    def visit_table(self, node: docutils.nodes.table) -> None:
        self._rownum = 0
        self._elem_attributes = {}

    def depart_table(self, node):
        self._rownum = -1
        if self._state != self._PASS and 'header' in self._elem_attributes:
            header = self._elem_attributes['header']
            if header not in self._headers:
                self._add_header(header)
            if self._state == self._FUNCTION_TABLE:
                #TODO check function attributes
                self._elem_attributes.setdefault('in-params', [])
                self._elem_attributes.setdefault('out-params', [])
                self._elem_attributes.setdefault('inout-params', [])
                self._elem_attributes['private'] = self._private_section
                self._headers[header]['functions'].append(self._elem_attributes)
            elif self._state == self._TYPE_TABLE:
                #TODO check type attributes
                self._elem_attributes['private'] = self._private_section
                self._headers[header]['types'].append(self._elem_attributes)
            elif self._state == self._MACRO_CONSTANTS_TABLE:
                self._elem_attributes['private'] = self._private_section
                self._headers[header]['macro-constants'].append(self._elem_attributes)
            elif self._state == self._MACRO_FUNCTION_TABLE:
                #TODO check function macro attributes
                self._elem_attributes['private'] = self._private_section
                self._elem_attributes.setdefault('in-params', [])
                self._elem_attributes.setdefault('out-params', [])
                self._elem_attributes.setdefault('inout-params', [])
                self._headers[header]['macro-functions'].append(self._elem_attributes)
            elif self._state == self._VARIABLE_TABLE:
                #TODO check variable attributes
                self._elem_attributes['private'] = self._private_section
                self._headers[header]['variables'].append(self._elem_attributes)
        elif self._state == self._SOURCE_FILE_TABLE:
            pass
        elif self._state != self._PASS:
            raise RuntimeError('Invalid syntax: missing header in SW element specification')

    def visit_row(self, node):
        self._rownum += 1

    # Nested rows (e.g. function parameters) have the 1st column omitted by the grid table parser,
    # so we have to figure out the column number depending on the count of '|' before the paragraph text.
    def get_colnum(self, node: docutils.nodes.paragraph, content) -> None:
        content = content.splitlines()[0]
        src_line = self._lines[node.line - 1]
        cont_pos = src_line.find(content)
        assert cont_pos > -1
        return src_line[1:cont_pos].count('|')

    def _get_description(self, content):
        descr = content.replace('\n', ' ')
        if descr[-1] != '.':
             descr += '.'
        return descr

    def _add_type_attribute(self, colnum, node, content):
        if self._rownum < 5:
            self._assert_syntax(colnum == 2, node.line)
            self._assert_syntax(self._attr_to_add not in self._elem_attributes, node.line)
            self._elem_attributes[self._attr_to_add] = self._get_description(content) if self._attr_to_add == 'description' else content
        else:
            assert 'kind' in self._elem_attributes
            if self._attr_to_add == 'elements':
                self._assert_syntax(self._elem_attributes['kind'] == 'Structure', node.line)
                self._assert_syntax(colnum in [2, 3, 4], node.line)
                self._elem_attributes.setdefault(self._attr_to_add, [])
                if colnum == 2:
                    self._elem_attributes[self._attr_to_add].append({ 'type': content })
                elif colnum == 3:
                    self._elem_attributes[self._attr_to_add][-1]['field'] = content
                elif colnum == 4:
                    self._elem_attributes[self._attr_to_add][-1]['description'] = self._get_description(content)
            elif self._attr_to_add == 'type':
                self._assert_syntax(colnum == 2)
                self._elem_attributes[self._attr_to_add] = content
            elif self._attr_to_add == 'constants':
                self._assert_syntax(self._elem_attributes['kind'] == 'Enumeration', node.line)
                self._assert_syntax(colnum in [2, 3, 4], node.line)
                self._elem_attributes.setdefault(self._attr_to_add, [])
                if colnum == 2:
                    self._elem_attributes[self._attr_to_add].append({ 'name': content })
                elif colnum == 3:
                    self._elem_attributes[self._attr_to_add][-1]['value'] = content
                else:
                    self._elem_attributes[self._attr_to_add][-1]['description'] = self._get_description(content)

    def _add_function_attribute(self, colnum, node, content):
        if self._rownum <= 6:
            self._assert_syntax(colnum == 2, node.line)
            self._assert_syntax(self._attr_to_add not in self._elem_attributes, node.line)
            if self._attr_to_add == 'description':
                self._elem_attributes[self._attr_to_add] = self._get_description(content)
            elif self._attr_to_add == 'allowed-from-isr':
                self._elem_attributes[self._attr_to_add] = 'Yes' in content or 'yes' in content
            elif self._attr_to_add == 'is-reentrant':
                self._elem_attributes[self._attr_to_add] = (content == 'Reentrant') or 'Yes' in content or 'yes' in content
            else:
                self._elem_attributes[self._attr_to_add] = content
        elif self._rownum == 7:
            self._assert_syntax(colnum in [2, 3], node.line)
            if colnum == 2:
                if content == 'None' or content == 'none':
                    content = 'void'
                self._elem_attributes[self._attr_to_add] = { 'type': content }
            else:
                self._elem_attributes[self._attr_to_add]['description'] = self._get_description(content)
        else:
            self._assert_syntax(colnum in [2, 3], node.line)
            self._elem_attributes.setdefault(self._attr_to_add, [])
            if colnum == 2:
                self._elem_attributes[self._attr_to_add].append({ 'name': content })
            else:
                self._elem_attributes[self._attr_to_add][-1]['description'] = self._get_description(content)

    def _add_macro_constants_attribute(self, colnum, node, content):
        if self._rownum < 3:
            self._assert_syntax(colnum == 2, node.line)
            self._assert_syntax(self._attr_to_add not in self._elem_attributes, node.line)
            self._elem_attributes[self._attr_to_add] = self._get_description(content) if self._attr_to_add == 'description' else content
        else:
            self._assert_syntax(colnum in [2, 3, 4], node.line)
            self._elem_attributes.setdefault(self._attr_to_add, [])
            if colnum == 2:
                self._elem_attributes[self._attr_to_add].append({ 'name': content })
            elif colnum == 3:
                self._elem_attributes[self._attr_to_add][-1]['value'] = content.replace('\n', ' \\\n   ')
            else:
                self._elem_attributes[self._attr_to_add][-1]['description'] = self._get_description(content)

    def _add_variable_attribute(self, colnum, node, content):
        # _attr_to_add = 'variables-group'
        if self._rownum < 3:
            self._assert_syntax(colnum == 2, node.line)
            self._assert_syntax(self._attr_to_add not in self._elem_attributes, node.line)
            self._elem_attributes[self._attr_to_add] = content.strip()
        else:
            self._assert_syntax(colnum in [2, 3], node.line)
            self._elem_attributes.setdefault(self._attr_to_add, [])
            if colnum == 2:
                # Description or Syntax
                subattr = content.lower().replace(':', '')
                if subattr == 'description':
                    self._elem_attributes[self._attr_to_add].append({})
                self._subattr_to_add = subattr
            else:
                self._elem_attributes[self._attr_to_add][-1][self._subattr_to_add] = content

    def _add_macro_function_attribute(self, colnum, node, content):
        if self._rownum < 7:
            self._assert_syntax(colnum == 2, node.line)
            self._assert_syntax(self._attr_to_add not in self._elem_attributes, node.line)
            if self._attr_to_add == 'description':
                self._elem_attributes[self._attr_to_add] = self._get_description(content)
            elif self._attr_to_add == 'allowed-from-isr':
                self._elem_attributes[self._attr_to_add] = 'Yes' in content or 'yes' in content
            elif self._attr_to_add == 'is-reentrant':
                self._elem_attributes[self._attr_to_add] = (content == 'Reentrant') or 'Yes' in content or 'yes' in content
            else:
                self._elem_attributes[self._attr_to_add] = content
        elif self._rownum == 7:
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
            if self._attr_to_add != 'definition':
                if colnum == 2:
                    self._elem_attributes[self._attr_to_add].append({ 'name': content })
                else:
                    self._elem_attributes[self._attr_to_add][-1]['description'] = content.replace('\n', ' ')
            else:
                if colnum == 2:
                    subattr = content.lower().replace(':', '')
                    #Allow to skip the condition for condition-less macros.
                    if len(self._elem_attributes[self._attr_to_add]) == 0 or subattr == 'condition':
                        self._elem_attributes[self._attr_to_add].append({ })
                    self._subattr_to_add = subattr
                else:
                    self._assert_syntax(self._subattr_to_add == 'condition', node.line)
                    condition_content = content.replace('``', '').replace('\n', ' ')
                    if condition_content == 'default':
                        condition_content = ''
                    self._elem_attributes[self._attr_to_add][-1][self._subattr_to_add] = condition_content
                    if len(self._elem_attributes[self._attr_to_add]) == 1:
                        if condition_content != '':
                            self._elem_attributes[self._attr_to_add][-1]['prepro-conditional'] = "#if"
                        else:
                            self._elem_attributes[self._attr_to_add][-1]['prepro-conditional'] = ""
                    elif condition_content != '':
                        self._elem_attributes[self._attr_to_add][-1]['prepro-conditional'] = "#elif"
                    else:
                        self._elem_attributes[self._attr_to_add][-1]['prepro-conditional'] = "#else"

    def _add_file_description(self, colnum, node, content):
        if self._rownum == 1:
            if colnum == 1:
                self._assert_syntax("File" in content, node.line)
            elif colnum == 2:
                self._assert_syntax("Generated" in content, node.line)
            elif colnum == 3:
                self._assert_syntax("Description" in content, node.line)
            else:
                self._assert_syntax(False, "Too many columns in source file table")
        else:
            if colnum == 1:
                self._file_to_add = content.strip()
            elif colnum == 2:
                self._file_is_generated = (content.strip().lower() == 'yes')
            elif colnum == 3:
                if self._file_to_add[-2:] == '.h':
                    if self._file_to_add not in self._headers:
                        self._add_header(self._file_to_add)
                    self._headers[self._file_to_add]['description'] = content.replace('\n', ' ').strip()
                    self._headers[self._file_to_add]['generated'] = self._file_is_generated


    def visit_paragraph(self, node: docutils.nodes.paragraph) -> None:
        content = node.astext()
        if self._rownum > 0 and self._state != self._PASS:
            colnum = self.get_colnum(node, content)

            if self._state == self._SOURCE_FILE_TABLE:
                self._add_file_description(colnum, node, content)
            elif colnum == 1:
                row_label_found = False
                for row_spec in self._ROW_KEYS:
                    if row_spec.row_label in content and self._state in row_spec.tables.keys():
                        expected_rownum = row_spec.tables[self._state]
                        if expected_rownum > -1:
                            self._assert_syntax(self._rownum == expected_rownum, node.line)
                        self._attr_to_add = row_spec.attr_key
                        row_label_found = True
                        break
                if not row_label_found:
                    elem_type = self._state.replace('_', ' ')
                    print("WARNING: unrecognized " + elem_type + " attribute " + content)
            else:
                if self._state == self._FUNCTION_TABLE and content == "'...":
                    content = "..."
                add_method_name = '_add_' + self._state.replace('_table', '') + '_attribute'
                add_method = getattr(self, add_method_name)
                add_method(colnum, node, content)


    def _strip_code_block(self, str):
        return str.replace('.. code-block::', '').strip()

    # code blocks are handled here
    def visit_literal_block(self, node: docutils.nodes.literal_block) -> None:
        content = node.astext()
        if self._rownum > 0 and self._state != self._PASS:
            # literal_block node has no line
            #colnum = self.get_colnum(node, content)

            if self._state == self._TYPE_TABLE:
                if self._rownum == 5:
                    if self._attr_to_add == 'type':
                        self._elem_attributes[self._attr_to_add] = self._strip_code_block(content)
            elif self._state == self._FUNCTION_TABLE:
                if self._rownum == 3:
                    self._assert_syntax(self._attr_to_add not in self._elem_attributes, node.line)
                    self._elem_attributes[self._attr_to_add] = self._strip_code_block(content)
            elif self._state == self._MACRO_FUNCTION_TABLE:
                if self._attr_to_add == 'syntax':
                    if self._rownum == 3:
                        self._assert_syntax(self._attr_to_add not in self._elem_attributes, node.line)
                        self._elem_attributes[self._attr_to_add] = self._strip_code_block(content)
                if self._attr_to_add == 'definition':
                    self._assert_syntax(self._subattr_to_add == 'code', node.line)
                    code_lines = self._strip_code_block(content).split('\n')
                    self._elem_attributes[self._attr_to_add][-1][self._subattr_to_add] = code_lines
                    if 'condition' not in self._elem_attributes[self._attr_to_add][-1]:
                        self._elem_attributes[self._attr_to_add][-1]['condition'] = ''
                        self._elem_attributes[self._attr_to_add][-1]['prepro-conditional'] = ''
            elif self._state == self._VARIABLE_TABLE:
                self._elem_attributes[self._attr_to_add][-1][self._subattr_to_add] = content


    def visit_uml(self, node: uml) -> None:
        if self._state == self._SOURCE_FILE_DEPENDENCIES:
            depScanner = UmlDependencyScanner()
            self._assert_syntax(hasattr(node, 'parse_tree'), node.line,
                                        msg='File dependency diagram not found, or missing :restuml2code: directive')
            depScanner.visit_topdown(tree=node.parse_tree)
            for header in depScanner.header_deps:
                if header not in self._headers:
                    self._add_header(header)
                self._headers[header]['includes'] += depScanner.header_deps[header]

    def depart_uml(self, node: uml) -> None:
        pass

    def visit_item(self, node: item) -> None:
        pass

    def depart_item(self, node: item) -> None:
        pass

    def visit_field(self, node: docutils.nodes.field) -> None:
        field_body = ''
        for c in node.children:
            if isinstance(c, docutils.nodes.field_name):
                field_name = c.astext()
            elif isinstance(c, docutils.nodes.field_body):
                field_body = c.astext().strip()
        if self._state == self._PASS:
            #global field
            #Any global field may be added to header attributes except for the reserved ones.
            if field_name in [ a.name for a in self._HEADER_ATTRIBUTES ]:
                self._assert_syntax(False, node.line, msg = "'" + field_name + "' cannot be used for a global field name" )
            else:
                self._globals[field_name] = field_body

    # Copy global attributes to all headers.
    def depart_document(self, node: docutils.nodes.document) -> None:
        for gf in self._globals:
            for header in self._headers:
                self._headers[header][gf] = self._globals[gf]


    def unknown_visit(self, node: docutils.nodes.Node) -> None:
        """Called for all other node types."""

        #if isinstance(node, docutils.nodes.Element):
        #    print("Unknown element: " + node.astext())
        pass

    def _assert_syntax(self, condition, line, msg = ''):
        if not condition:
            if len(msg) == 0:
                msg = 'Error (line ' + str(line) +'): invalid syntax'
            else:
                msg = 'Error (line ' + str(line) +'): ' + msg
            print(msg)
            raise RuntimeError(msg)
