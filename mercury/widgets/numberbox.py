import os
from uuid import uuid4


class NumberBox:
    BLUE = "#00B1E4"
    LIGHT_BLUE = "rgba(0, 177, 228, 0.5)"
    RED = "#FF6384"
    LIGHT_RED = "rgba(255, 99, 132, 0.5)"
    GREEN = "#00B275"
    LIGHT_GREEN = "rgb(0, 178, 117, 0.5)"

    def __init__(
        self,
        data,
        title="",
        percent_change=None,
        background_color="white",
        border_color="lightgray",
        data_color="black",
        title_color="gray",
    ):
        self.data = data
        self.title = title
        self.blox_type = "numeric"
        if isinstance(self.data, list):
            self.blox_type = "list"
        self.percent_change = percent_change
        self.background_color = background_color
        self.border_color = border_color
        self.data_color = data_color
        self.title_color = title_color
        # position when displayed as a list
        self.position = None

    def styles(self):
        return """<style scoped>
        .numberbox-container {
        width: 100%;
        display: flex;
        flex-direction: row;
        }
        @media (max-width: 800px) {
        .numberbox-container {
            flex-direction: column;
        }
        }
        </style>"""

    def _repr_html_(self):
        if self.blox_type == "list":
            bloxs = ""
            for i, b in enumerate(self.data):
                if isinstance(b, NumberBox):
                    # we dont set position for last item
                    # because we dont need to add margin for it
                    if i != len(self.data) - 1:
                        b.position = i
                    bloxs += b._repr_html_()

            return f"""{self.styles()}<div class="numberbox-container" style="display: flex; background: #fff;">{bloxs}</div>"""

        percent_change_html = ""
        if self.percent_change is not None:
            if self.percent_change > 0:
                percent_change_html = f"""
                <span style="font-size: 1.3em; color: {self.GREEN}; font-family: monospace;"> +{self.percent_change}%</span>
                """
            else:
                percent_change_html = f"""
                <span style="font-size: 1.3em; color: {self.RED}; font-family: monospace;"> {self.percent_change}%</span>
                """
        title_html = ""
        if self.title != "":
            title_html = f"""<span style="font-size: 2em; color: {self.title_color}; display: block; padding-top: 20px; font-family: monospace; line-height: 1.3em;">{self.title}</span>"""

        data_str = ""
        if isinstance(self.data, str):
            data_str = self.data
        else:
            data_str = f"{self.data:,}"

        margin = "0px" if self.position is None else "15px"
        return f"""
<div style="text-align: center; width: 100%; border: 1px solid {self.border_color}; margin-right: {margin}; margin-top: 15px; padding-top: 40px; padding-bottom: 30px; background: {self.background_color}; border-radius:5px">
  <span style="font-size: 4em; color: {self.data_color}; font-family: monospace; ">{data_str}</span>
  {percent_change_html}
  {title_html}
</div>
  """
