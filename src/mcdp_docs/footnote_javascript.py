# -*- coding: utf-8 -*-
from mcdp_utils_xml import bs, copy_contents_into


def add_footnote_polyfill(soup):
    head = soup.find('head')
    if head is None:
        raise ValueError()
    x = bs(footnote_javascript)
    copy_contents_into(x, head)


# language=javascript
footnote_javascript = r'''
<style>
.footnote-simulation {
    font-size: smaller;
    padding-left: 2em;
    border-left: solid 2px grey;
    /*position: absolute;
    right: -20em;
    width: 20em;*/
    background-color: white;
    padding: 4px;

    display: none;
}
.footnote-marker {
    margin-left: 2px;
    color: blue !important;
    text-decoration: underline !important;
}
</style>
<script>

function click_marker(that_id) { 
    console.log('click ' + that_id);
    panel = document.getElementById(that_id);
    current = panel.style.display;
    if (current == 'block') {
        panel.style.display = 'none';
    } else {
        panel.style.display = 'block';
    }
}


function initialize_footnotes() {
    // Do one at a time
    var i = 0;
    while(true) {
        i+= 1;
        var elements = document.getElementsByTagName('footnote');
        console.log('Found footnotes: ' + elements.length);
        if(elements.length == 0) {
            break;
        }
    // for (var i=0; i<elements.length; i++) {
        var e = elements[0];
        var d = document.createElement('div');
        d.innerHTML = e.innerHTML;
        d.classList.add('footnote-simulation');
        this_id = 'myfootnote' + i;
        d.id = this_id;

        var a = document.createElement('a');
        a.classList.add('footnote-marker');
        a.innerHTML = '&dagger;';
        a.href = "javascript:click_marker('" + this_id + "')";
        // a.onclick = click_marker;

        // function(this) {
        //     console.log('click ' + this.id);
        //     current = d.style.display;
        //     if (current == 'block') {
        //         d.style.display = 'none';
        //     } else {
        //         d.style.display = 'block';
        //     }
        // }
        e.parentNode.insertBefore(a, e);
        e.parentNode.insertBefore(d, e);
        e.parentNode.removeChild(e);
    }
}

document.addEventListener("DOMContentLoaded", function(event) {
    // Your code to run since DOM is loaded and ready
    try {
        prince = Prince;
    } catch (e) {
        console.log("Not running in Prince");
        prince = null;
    }
    if (prince == null) {
        initialize_footnotes();
    }

});


</script>
'''


# footnote_javascript_old = r'''
# <style>
# .footnote-simulation {
#     font-size: smaller;
#     padding-left: 2em;
#     border-left: solid 2px grey;
#     /*position: absolute;
#     right: -20em;
#     width: 20em;*/
#     background-color: white;
#     padding: 4px;
#
#     display: none;
# }
# .footnote-marker {
#     margin-left: 2px;
#     color: blue !important;
#     text-decoration: underline !important;
# }
# </style>
# <script>
# try {
#     prince = Prince;
# } catch (e) {
#     console.log("Not running in Prince");
#     prince = null;
# }
# if(prince==null) {
#     var elements = document.getElementsByTagName('footnote');
#     for (var i=0; i<elements.length; i++) {
#         e = elements[i];
#         var d = document.createElement('div');
#         d.innerHTML = e.innerHTML;
#         d.classList.add('footnote-simulation');
#
#         var a = document.createElement('a');
#         a.classList.add('footnote-marker');
#         a.innerHTML = '&dagger;';
#         a.href = "javascript:";
#         a.onclick=function(){
#             // console.log('click');
#             current = d.style.display;
#             if (current == 'block') {
#                 d.style.display = 'none';
#             } else {
#                 d.style.display = 'block';
#             }
#         }
#         e.parentNode.insertBefore( a, e);
#         e.parentNode.insertBefore( d, e);
#         e.parentNode.removeChild(e);
#     }
# }
# </script>
#
# '''
