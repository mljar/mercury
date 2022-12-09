import json
import time

from nbconvert import HTMLExporter


class Exporter:
    def __init__(self):
        self.html_exporter = HTMLExporter()  # template_name="classic")
        
        # prompt
        #self.html_exporter.exclude_input_prompt = True
        #self.html_exporter.exclude_output_prompt = True
        
        # hide code
        #self.html_exporter.exclude_input = True


    def run(self, notebook):

        (body, resources) = self.html_exporter.from_notebook_node(notebook)

        return body, resources
