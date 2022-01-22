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

from lark.visitors import Visitor
from lark import Token, Tree

class UmlDependencyScanner(Visitor):

    def __init__(self) -> None:
        super().__init__()
        self.headers = []
        self.header_deps = {}

    def _get_element_name(self, element, tree):
        data = element + '_name'
        for c in tree.children:
            if c.data == data:
                assert len(c.children) == 1
                assert isinstance(c.children[0], Token)
                return c.children[0].value
        return None

    def artifact(self, tree):
        assert tree.data == "artifact"
        artifact_name = self._get_element_name("artifact", tree)
        for c in tree.children:
            if c.data == "stereotype":
                stereotype_name = self._get_element_name("stereotype", c)
                if stereotype_name == 'header' and artifact_name not in self.headers:
                    self.headers.append(artifact_name)

    def _get_relation_attributes(self, tree):
        attr = {}
        for c in tree.children:
            if isinstance(c, Tree):
                if c.data == "relation_from":
                    attr["relation_from"] = c.children[0].value
                elif c.data == "relation_to":
                    attr["relation_to"] = c.children[0].value
                elif c.data == "stereotype":
                    attr["stereotype"] = self._get_element_name("stereotype", c)
        return attr

    def dependency(self, tree):
        dep_attr = self._get_relation_attributes(tree)
        if dep_attr["stereotype"] == "include" and dep_attr["relation_from"] in self.headers:
            self.header_deps.setdefault(dep_attr["relation_from"], [])
            self.header_deps[dep_attr["relation_from"]].append(dep_attr["relation_to"])
