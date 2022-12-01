from nbconvert import HTMLExporter


class Exporter:
    def __init__(self):
        # 2. Instantiate the exporter. We use the `classic` template for now; we'll get into more details
        # later about how to customize the exporter further.
        self.html_exporter = HTMLExporter() #template_name="classic")

    def __call__(self, notebook):
        # 3. Process the notebook we loaded earlier
        (body, resources) = self.html_exporter.from_notebook_node(notebook)

        return body, resources
