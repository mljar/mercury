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

        self.set_exporter()

    def set_exporter(self):
        if self.is_presentation:
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

    def set_is_presentation(self, new_value):
        if self.is_presentation != new_value:
            self.is_presentation = new_value
            self.set_exporter()

    def set_reveal_theme(self, new_value):
        if self.reveal_theme != new_value:
            self.reveal_theme = new_value
            self.set_exporter()

    def set_show_code(self, new_value):
        self.show_code = new_value
        self.html_exporter.exclude_input = not self.show_code
        self.html_exporter.exclude_input_prompt = not self.show_code
        self.html_exporter.exclude_output_prompt = not self.show_code

    def set_show_prompt(self, new_value):
        self.show_prompt = new_value
        self.html_exporter.exclude_input_prompt = not self.show_prompt
        self.html_exporter.exclude_output_prompt = not self.show_prompt

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
            body = self.remove_header(body)

        return body

    def remove_header(self, nb_body):
        body = copy.deepcopy(nb_body)
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
