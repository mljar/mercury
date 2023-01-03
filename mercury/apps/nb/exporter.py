import copy

from nbconvert import HTMLExporter, SlidesExporter


class Exporter:
    def __init__(
        self,
        show_code=False,
        show_prompt=False,
        is_presentation=False,
        reveal_theme="white",
    ):

        self.show_code = show_code
        self.show_prompt = show_prompt
        self.is_presentation = is_presentation
        self.reveal_theme = reveal_theme

        if is_presentation:
            self.html_exporter = SlidesExporter(
                template_name="reveal", reveal_theme=self.reveal_theme
            )
        else:
            self.html_exporter = HTMLExporter(template_name="lab")

        # prompt
        self.html_exporter.exclude_input_prompt = not self.show_prompt
        self.html_exporter.exclude_output_prompt = not self.show_prompt

        # hide code
        self.html_exporter.exclude_input = not self.show_code
        self.html_exporter.exclude_input_prompt = not self.show_code
        self.html_exporter.exclude_output_prompt = not self.show_code

    def export(self, notebook, full_header=True):
        #
        # notebook needs to be in nbformat
        #
        n = copy.deepcopy(notebook)

        # omit cells with "---" (starter from V1)
        n.cells = [
            cell
            for cell in n.cells
            if not "".join(cell.get("source", "")).startswith("---")
        ]

        # omit output with mercury widgets
        for cell in n.cells:
            if "outputs" in cell:
                cell["outputs"] = [
                    output
                    for output in cell["outputs"]
                    if not "application/mercury+json" in output.get("data", {})
                ]

        body, _ = self.html_exporter.from_notebook_node(n)

        # remove header
        if not full_header:
            index_start = body.find("<head>")
            index_end = body.find("</head>")

            if index_start != -1 and index_end != -1:
                body = body[:index_start] + "" + body[index_end + 7 :]

                body = body.replace("<!DOCTYPE html>", "")
                body = body.replace("<html>", "")
                body = body.replace("<body ", "<div ")
                body = body.replace("</body>", "</div>")
                body = body.replace("</html>", "")

        return body
