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
### render_type() ###
<%def name="render_type(type_item)">            \

/**
 * ${type_item['description']}
 * @ingroup ${content['module']}
 */
% if type_item['kind'] == 'Typedef':
typedef ${type_item['type']};
% elif type_item['kind'] == 'Structure':
typedef struct ${type_item['type-name']} {
% for sel in type_item['elements']:
    /** ${sel['description']} */
    ${sel['type']} ${sel['field']};
% endfor
} ${type_item['type-name']};
% endif
</%def>                                         \
### render_function() ###
<%def name="render_function(func_item)">        \

/**
 * @brief ${get_brief(func_item['description'])}
 * @ingroup ${content['module']}
 *
% for ipar in func_item['in-params']:
 * @param[in] ${ipar['name']} - ${ipar['description']}
% endfor
% for opar in func_item['out-params']:
 * @param[out] ${opar['name']} - ${opar['description']}
% endfor
% for iopar in func_item['inout-params']:
 * @param[in-out] ${iopar['name']} - ${iopar['description']}
% endfor
% if func_item['return-value']['type'] != "void":
 * @return ${func_item['return-value']['type']} - ${func_item['return-value']['description']}
% endif
 */
${func_item['syntax']};
</%def>                                         \
###

/**!
 *
 * ${content['description']}
 *
 * Copyright ...
 *
 */

#ifndef TEST_${make_include_guard(file)}
#define TEST_${make_include_guard(file)}
% if content['file-name'] == content['module'] + '.h':

/*!
 * @defgroup ${content['module']} ${content['module']}
 */

% endif
% for i in content['includes']:
#include "${i}"
% endfor

% for t in content['types']:
    ${render_type(t)}
% endfor

% for f in content['functions']:
    ${render_function(f)}
% endfor

#endif //TEST_${make_include_guard(file)}