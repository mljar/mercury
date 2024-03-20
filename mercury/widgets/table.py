from itables import show

import ipywidgets
from IPython.display import display
from .manager import WidgetsManager

import warnings


def Table(data=None, width="auto", text_align="center"):
    if data is None:
        raise Exception("Please provide data!")

    if "DataFrame" not in str(type(data)):
        raise Exception("Wrong data provided! Expected data type is 'DataFrame'.")

    if "%" in width:
        raise Exception("Wrong width provided! You can't provide value using '%'.")
    
    if text_align not in ["center","left","right"]:
        raise Exception("Wrong align provided! You can choose one of following options: 'left', 'right', 'center'.")

    text_align= f"dt-{text_align}"
    show(data, classes=["display", "cell-border"], columnDefs=[{"className":text_align,"width":width,"targets":"_all"}])

