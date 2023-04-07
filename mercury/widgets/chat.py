from IPython.display import display, HTML


def Chat(messages=[]):
    html = """<div style="padding: 20px;">"""

    left_msg = """<div style="background: #efefef; padding: 10px; float: left; border-radius: 10px 10px 10px 0px; margin: 5px; margin-right: 50px">
<pre style="background: #efefef; color: black;">
{}
</pre>
</div>
<div style="clear: both;"></div>"""
    right_msg = """<div style="background: cornflowerblue; color: #fff; padding: 10px; float: right; border-radius: 10px 10px 0px 10px; margin: 5px; margin-left: 50px">
<pre style="background: cornflowerblue; color: #fff;">
{}
</pre>
</div>
<div style="clear: both;"></div>"""
    style = left_msg
    for m in messages:
        html += style.format(m)
        style = left_msg if style == right_msg else right_msg

    html += "</div>"

    display(HTML(html))
