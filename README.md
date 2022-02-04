# restuml2code
A tool for generating C source headers from SW component design in reStructuredText format.

Dependencies:
- docutils is used to parse reStructuredText files
- mako is used to render code templates using the parsed document content
- lark is used to parse puml sections.