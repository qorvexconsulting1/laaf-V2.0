from laaf.reporting.csv_reporter import CSVReporter
from laaf.reporting.html_reporter import HTMLReporter
from laaf.reporting.json_reporter import JSONReporter
from laaf.reporting.pdf_reporter import PDFReporter

__all__ = ["CSVReporter", "HTMLReporter", "JSONReporter", "PDFReporter"]


def get_reporter(fmt: str):
    fmt = fmt.lower()
    reporters = {
        "csv": CSVReporter,
        "json": JSONReporter,
        "html": HTMLReporter,
        "pdf": PDFReporter,
    }
    if fmt not in reporters:
        raise ValueError(f"Unknown report format: {fmt!r}. Choose: csv, json, html, pdf")
    return reporters[fmt]()
