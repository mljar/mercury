import os
import json
import uuid
from IPython.display import display_javascript, display_html, display, HTML

JSON_CSS = """.renderjson a              { text-decoration: none; }
.renderjson .disclosure    { color: grey; font-size: 125%; }
.renderjson .syntax        { color: grey; }
.renderjson .string        { color: #fe46a5; }
.renderjson .number        { color: #0f9b8e; }
.renderjson .boolean       { color: black; }
.renderjson .key           { color: #2684ff; }
.renderjson .keyword       { color: gray; }
.renderjson .object.syntax { color: gray; }
.renderjson .array.syntax  { color: gray; }"""


def JSON(json_data={}, level=1):
    if isinstance(json_data, dict):
        json_str = json.dumps(json_data)
    else:
        json_str = json_data
    id = str(uuid.uuid4())

    # Minimized version based on https://raw.githubusercontent.com/caldwell/renderjson/master/renderjson.js
    # Changes:
    # 1. Replace \n with \\n
    # 2. Remove module exports
    js = """var renderjson=function(){var t=function(){for(var t=[];arguments.length;)t.push(n(s(Array.prototype.shift.call(arguments)),o(Array.prototype.shift.call(arguments))));return t},n=function(){for(var t=Array.prototype.shift.call(arguments),e=0;e<arguments.length;e++)arguments[e].constructor==Array?n.apply(this,[t].concat(arguments[e])):t.appendChild(arguments[e]);return t},e=function(t,n){return t.insertBefore(n,t.firstChild),t},r=function(t,n){var e=n||Object.keys(t);for(var r in e)if(Object.hasOwnProperty.call(t,e[r]))return!1;return!0},o=function(t){return document.createTextNode(t)},s=function(t){var n=document.createElement("span");return t&&(n.className=t),n},l=function(t,n,e){var r=document.createElement("a");return n&&(r.className=n),r.appendChild(o(t)),r.href="#",r.onclick=function(t){return e(),t&&t.stopPropagation(),!1},r};function a(i,c,u,p,y){var _=u?"":c,f=function(r,a,i,c,u){var f,g=s(c),h=function(){f||n(g.parentNode,f=e(u(),l(y.hide,"disclosure",(function(){f.style.display="none",g.style.display="inline"})))),f.style.display="inline",g.style.display="none"};n(g,l(y.show,"disclosure",h),t(c+" syntax",r),l(a,null,h),t(c+" syntax",i));var d=n(s(),o(_.slice(0,-1)),g);return p>0&&"string"!=c&&h(),d};return null===i?t(null,_,"keyword","null"):void 0===i?t(null,_,"keyword","undefined"):"string"==typeof i&&i.length>y.max_string_length?f('"',i.substr(0,y.max_string_length)+" ...",'"',"string",(function(){return n(s("string"),t(null,_,"string",JSON.stringify(i)))})):"object"!=typeof i||[Number,String,Boolean,Date].indexOf(i.constructor)>=0?t(null,_,typeof i,JSON.stringify(i)):i.constructor==Array?0==i.length?t(null,_,"array syntax","[]"):f("[",y.collapse_msg(i.length),"]","array",(function(){for(var e=n(s("array"),t("array syntax","[",null,"\\n")),r=0;r<i.length;r++)n(e,a(y.replacer.call(i,r,i[r]),c+"    ",!1,p-1,y),r!=i.length-1?t("syntax",","):[],o("\\n"));return n(e,t(null,c,"array syntax","]")),e})):r(i,y.property_list)?t(null,_,"object syntax","{}"):f("{",y.collapse_msg(Object.keys(i).length),"}","object",(function(){var e=n(s("object"),t("object syntax","{",null,"\\n"));for(var r in i)var l=r;var u=y.property_list||Object.keys(i);for(var _ in y.sort_objects&&(u=u.sort()),u){(r=u[_])in i&&n(e,t(null,c+"    ","key",'"'+r+'"',"object syntax",": "),a(y.replacer.call(i,r,i[r]),c+"    ",!0,p-1,y),r!=l?t("syntax",","):[],o("\\n"))}return n(e,t(null,c,"object syntax","}")),e}))}var i=function t(e){var r=new Object(t.options);r.replacer="function"==typeof r.replacer?r.replacer:function(t,n){return n};var o=n(document.createElement("pre"),a(e,"",!1,r.show_to_level,r));return o.className="renderjson",o};return i.set_icons=function(t,n){return i.options.show=t,i.options.hide=n,i},i.set_show_to_level=function(t){return i.options.show_to_level="string"==typeof t&&"all"===t.toLowerCase()?Number.MAX_VALUE:t,i},i.set_max_string_length=function(t){return i.options.max_string_length="string"==typeof t&&"none"===t.toLowerCase()?Number.MAX_VALUE:t,i},i.set_sort_objects=function(t){return i.options.sort_objects=t,i},i.set_replacer=function(t){return i.options.replacer=t,i},i.set_collapse_msg=function(t){return i.options.collapse_msg=t,i},i.set_property_list=function(t){return i.options.property_list=t,i},i.set_show_by_default=function(t){return i.options.show_to_level=t?Number.MAX_VALUE:0,i},i.options={},i.set_icons("⊕","⊖"),i.set_show_by_default(!1),i.set_sort_objects(!1),i.set_max_string_length("none"),i.set_replacer(void 0),i.set_property_list(void 0),i.set_collapse_msg((function(t){return t+" item"+(1==t?"":"s")})),i}();"""

    display(HTML(f'<style>{JSON_CSS}</style><div id="{id}"></div>'))
    display(
        HTML(
            f'<script>{js} renderjson.set_show_to_level({str(level)}); document.getElementById("{id}").appendChild(renderjson({json_str}))</script>'
        )
    )
