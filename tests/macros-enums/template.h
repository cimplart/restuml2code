###
<%!                                             \
    def make_include_guard(file):               \
        return file.upper().replace('.', '_')   \
%>                                              \
###
<%!                                             \
    def get_brief(descr):                       \
        return descr[:descr.index(".")]         \
%>                                              \
<%!                                                                     \
    def get_enum_initializer(item):                                     \
        return ' = ' + item['value'] if 'value' in item else ''         \
%>                                                                      \
###
### render_macro_constant()
###
<%def name="render_macro_constant(const_item)" filter="trim">           \
#define ${const_item['name']} (${const_item['value']})    ///< ${const_item['description']}
</%def>                                                                 \
###
### render_type()
###
<%def name="render_type(type_item)" filter="trim">                      \
/** ${type_item['description']} */
% if type_item['kind'] == 'Typedef':
typedef ${type_item['type']};
% elif type_item['kind'] == 'Structure':
typedef struct ${type_item['type-name']} {
% for sel in type_item['elements']:
    /** ${sel['description']} */
    ${sel['type']} ${sel['field']};
% endfor
} ${type_item['type-name']};
% elif type_item['kind'] == 'Enumeration':
typedef enum ${type_item['type-name']} {
% for item in type_item['constants']:
    ${item['name']}${get_enum_initializer(item)},       ///< ${item['description']}
% endfor
} ${type_item['type-name']};
% endif
</%def>                                                                 \

/**!
 *
 * Header comment
 *
 * Copyright ...
 *
 */

#ifndef TEST_${make_include_guard(file)}
#define TEST_${make_include_guard(file)}

% for cg in content['macro-constants']:
/** ${cg['constants-group']} */
%    for c in cg['constants']:
${render_macro_constant(c)}
%    endfor

% endfor

% for t in content['types']:
${render_type(t)}

% endfor

#endif //TEST_${make_include_guard(file)}