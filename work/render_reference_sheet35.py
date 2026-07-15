from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / "vendor"))

import ezdxf
from ezdxf import bbox
from ezdxf.addons.drawing import Frontend, RenderContext, layout, svg
from ezdxf.math import BoundingBox2d, Vec2


ROOT = Path(__file__).resolve().parents[1]
doc = ezdxf.readfile(ROOT / "work" / "ISO_31_TO_35_REFERENCE.dxf")
msp = doc.modelspace()

x0, y0, x1, y1 = 235970.5, -135060.7, 262558.3, -102199.1


def in_last_sheet(entity):
    try:
        box = bbox.extents([entity])
        if not box.has_data:
            return False
        center = box.center
        return x0 <= center.x <= x1 and y0 <= center.y <= y1
    except Exception:
        return False


def render(name, page_width, page_height, box):
    backend = svg.SVGBackend()
    Frontend(RenderContext(doc), backend).draw_layout(msp, filter_func=in_last_sheet)
    page = layout.Page(page_width, page_height, margins=layout.Margins.all(0))
    svg_text = backend.get_string(page, render_box=box)
    (ROOT / "tmp" / "pdfs" / name).write_text(svg_text)


(ROOT / "tmp" / "pdfs").mkdir(parents=True, exist_ok=True)
render(
    "reference_sheet35.svg",
    265.878,
    328.616,
    BoundingBox2d([Vec2(x0, y0), Vec2(x1, y1)]),
)
render(
    "reference_sheet35_titleblock.svg",
    230.0,
    50.0,
    BoundingBox2d([Vec2(239400, -134900), Vec2(262400, -129900)]),
)
