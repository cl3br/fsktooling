from pathlib import Path
from typing import Optional
import xml.etree.ElementTree as ET


class OdfUpdater:
    def __init__(self, odf_xml_path: Path,
                 output_path: Optional[Path] = None,
                 suffix="_new",
                 override=False) -> None:
        self.input_path = odf_xml_path
        if output_path:
            self.output_path = output_path
        elif override:
            self.output_path = self.input_path
        else:
            self.output_path = self.input_path.parent / (self.input_path.stem + suffix + self.input_path.suffix)
        self.root: Optional[ET.ElementTree] = None

    def __enter__(self):
        self.root = ET.parse(self.input_path).getroot()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.write_xml()
        self.root = None

    def write_xml(self):
        if self.root is None:
            return

        xmlstr = ET.tostring(self.root, xml_declaration=True, encoding="utf-8")
        with open(self.output_path, "wb") as fp:
            fp.write(xmlstr)
