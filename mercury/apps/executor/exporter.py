import copy
from nbconvert import HTMLExporter



class Exporter:
    def __init__(self, show_code=False):
        self.html_exporter = HTMLExporter()  # template_name="classic")
        
        # prompt
        #self.html_exporter.exclude_input_prompt = True
        #self.html_exporter.exclude_output_prompt = True
        
        # hide code
        self.html_exporter.exclude_input = not show_code
        self.html_exporter.exclude_input_prompt = not show_code
        self.html_exporter.exclude_output_prompt = not show_code


    def run(self, notebook, show_code=False):
        
        self.html_exporter.exclude_input = not show_code
        self.html_exporter.exclude_input_prompt = not show_code
        self.html_exporter.exclude_output_prompt = not show_code

        n = copy.deepcopy(notebook)
        # for cell in n.cells:
        #     if "outputs" in cell:
        #         to_remove = []
        #         for i, output in enumerate(cell["outputs"]):
        #             if "data" in output:
        #                 if "application/mercury+json" in output["data"]:
        #                     to_remove += [i]
        #         for i in to_remove:
        #             del cell["outputs"][i]

        (body, resources) = self.html_exporter.from_notebook_node(n)

        return body, resources
