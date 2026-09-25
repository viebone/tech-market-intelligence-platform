"""
Minimal, dependency-free .xlsx reader (standard library only).

Why not openpyxl: it isn't in this project's requirements, ONS's files are plain (one flat table per
sheet, shared strings, numbers) and were inspected in exactly this way on 2026-09-24
(research/2026-09-24-ons-licence-and-access-confirmation.md), so a ~70-line reader avoids a new
dependency in the Railway build. If a future publisher ships a workbook this can't read (formulas
that matter, merged-cell semantics, dates as serials), add openpyxl then — don't grow this file.

Returns, per sheet name, a list of (row_number, {column_letter: value}) with EMPTY CELLS OMITTED and rows
with no cells omitted. Values are `str` (shared/inline/formula strings) or `float` (numbers).
Booleans and error cells are returned as their raw text. Nothing here interprets meaning — that is the
adapter's job.
"""

from __future__ import annotations

import re
import zipfile
import xml.etree.ElementTree as ET
from io import BytesIO

_NS = {
    "m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
}
_M = "{%s}" % _NS["m"]

MAX_BYTES = 20 * 1024 * 1024          # a statistics workbook is tens/hundreds of KB; refuse anything absurd
MAX_UNCOMPRESSED_BYTES = 200 * 1024 * 1024   # guard against a zip bomb

Row = tuple[int, dict[str, "str | float"]]


class XlsxError(Exception):
    """The file is not a workbook this reader can read."""


def _col(ref: str) -> str:
    m = re.match(r"[A-Z]+", ref)
    if not m:
        raise XlsxError(f"bad cell reference {ref!r}")
    return m.group()


def _text(node: ET.Element) -> str:
    return "".join(t.text or "" for t in node.iter(_M + "t"))


def read_workbook(data: bytes) -> dict[str, list[Row]]:
    if len(data) > MAX_BYTES:
        raise XlsxError(f"file is {len(data)} bytes; refusing anything over {MAX_BYTES}")
    try:
        z = zipfile.ZipFile(BytesIO(data))
    except zipfile.BadZipFile as exc:
        raise XlsxError("not a zip/xlsx file") from exc
    if sum(i.file_size for i in z.infolist()) > MAX_UNCOMPRESSED_BYTES:
        raise XlsxError("workbook expands to an implausible size")

    shared: list[str] = []
    if "xl/sharedStrings.xml" in z.namelist():
        for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("m:si", _NS):
            shared.append(_text(si))

    workbook = ET.fromstring(z.read("xl/workbook.xml"))
    rels = {
        r.get("Id"): r.get("Target")
        for r in ET.fromstring(z.read("xl/_rels/workbook.xml.rels")).findall("rel:Relationship", _NS)
    }

    sheets: dict[str, list[Row]] = {}
    for sheet in workbook.find("m:sheets", _NS):
        name = sheet.get("name")
        target = rels.get(sheet.get("{%s}id" % _NS["r"]))
        if not name or not target:
            raise XlsxError("workbook sheet without a name or target")
        path = target.lstrip("/") if target.startswith("/") else "xl/" + target
        rows: list[Row] = []
        for row in ET.fromstring(z.read(path)).find("m:sheetData", _NS).findall("m:row", _NS):
            cells: dict[str, str | float] = {}
            for c in row.findall("m:c", _NS):
                ctype = c.get("t")
                v = c.find("m:v", _NS)
                if ctype == "inlineStr":
                    is_ = c.find("m:is", _NS)
                    val: str | float | None = _text(is_) if is_ is not None else None
                elif v is None or v.text is None:
                    val = None
                elif ctype == "s":
                    val = shared[int(v.text)]
                elif ctype in ("str", "b", "e"):
                    val = v.text
                else:
                    try:
                        val = float(v.text)
                    except ValueError:
                        val = v.text
                if val is None or (isinstance(val, str) and val == ""):
                    continue
                cells[_col(c.get("r"))] = val
            if cells:
                rows.append((int(row.get("r")), cells))
        sheets[name] = rows
    return sheets
