import asyncio
import os
import tempfile

from subprocess import PIPE, Popen
from pyppeteer import launch

import concurrent.futures


async def html_to_pdf(html_file, pdf_file, pyppeteer_args=None):
    """Convert a HTML file to a PDF"""
    browser = await launch(
        handleSIGINT=False,
        handleSIGTERM=False,
        handleSIGHUP=False,
        headless=True,
        args=["--no-sandbox"],
    )

    page = await browser.newPage()
    await page.setViewport(dict(width=994, height=768))
    await page.emulateMedia("screen")

    await page.goto(f"file://{html_file}", {"waitUntil": ["networkidle2"]})

    page_margins = {
        "left": "20px",
        "right": "20px",
        "top": "30px",
        "bottom": "30px",
    }

    dimensions = await page.evaluate(
        """() => {
        return {
            width: document.body.scrollWidth,
            height: document.body.scrollHeight,
            offsetWidth: document.body.offsetWidth,
            offsetHeight: document.body.offsetHeight,
            deviceScaleFactor: window.devicePixelRatio,
        }
    }"""
    )
    width = dimensions["width"]
    height = dimensions["height"]

    await page.evaluate(
        """
    function getOffset( el ) {
        var _x = 0;
        var _y = 0;
        while( el && !isNaN( el.offsetLeft ) && !isNaN( el.offsetTop ) ) {
            _x += el.offsetLeft - el.scrollLeft;
            _y += el.offsetTop - el.scrollTop;
            el = el.offsetParent;
        }
        return { top: _y, left: _x };
        }
    """,
        force_expr=True,
    )

    await page.addStyleTag(
        {
            "content": """
                #notebook-container {
                    box-shadow: none;
                    padding: unset
                }
                div.cell {
                    page-break-inside: avoid;
                    break-inside: avoid;
                }
                div.output_wrapper {
                    page-break-inside: avoid;
                    break-inside: avoid;
                }
                div.output {
                    page-break-inside: avoid;
                    break-inside: avoid;
                }
                /* Jupyterlab based HTML uses these classes */
                .jp-Cell-inputWrapper {
                    page-break-inside: avoid;
                    break-inside: avoid;
                }
                .jp-Cell-outputWrapper {
                    page-break-inside: avoid;
                    break-inside: avoid;
                }
                .jp-Notebook {
                    margin: 0px;
                }
                /* Hide the message box used by MathJax */
                #MathJax_Message {
                    display: none;
                }
         """
        }
    )

    await page.pdf(
        {
            "path": pdf_file,
            "format": "A4",
            "printBackground": True,
            "margin": page_margins,
        }
    )

    await browser.close()


def install_chromium():
    command = ["pyppeteer-install"]
    with Popen(command, stdout=PIPE, stderr=PIPE) as proc:
        print(proc.stdout.read())
        print(proc.stderr.read())


def to_pdf(html_input_file, pdf_output_file):

    # make sure chromium is installed
    # install_chromium()

    # convert notebook to PDF
    pool = concurrent.futures.ThreadPoolExecutor()
    pool.submit(
        asyncio.run,
        html_to_pdf(
            html_input_file,
            pdf_output_file
            # "slides2.slides.html?print-pdf", "slides-my.pdf"
        ),
    ).result()
