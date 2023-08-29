import base64
from IPython.display import IFrame


def PDF(file_path=None, width="100%", height=800):
    try:
        content = None
        with open(file_path, "rb") as fin:
            content = fin.read()
        base64_pdf = base64.b64encode(content).decode("utf-8")

        return IFrame(
            f"data:application/pdf;base64,{base64_pdf}", width=width, height=height
        )
    except Exception as e:
        print("Problem with displaying PDF")
