from nbconvert import HTMLExporter


class Exporter:
    def __init__(self):
        self.html_exporter = HTMLExporter()  # template_name="classic")

    def run(self, notebook):

        (body, resources) = self.html_exporter.from_notebook_node(notebook)

        return body, resources
