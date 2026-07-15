from pathlib import Path

import ezdxf
from ezdxf.addons.drawing import Frontend, RenderContext
from ezdxf.addons.drawing.layout import Page, Settings, Units
from ezdxf.addons.drawing.svg import SVGBackend


source = Path("tmp/ISO_31_TO_35_CONVERTED.dxf")
target = Path("tmp/reference_iso_31_35.svg")
doc = ezdxf.readfile(source)
msp = doc.modelspace()
context = RenderContext(doc)
backend = SVGBackend()
Frontend(context, backend).draw_layout(msp, finalize=True)
page = Page(1200, 500, units=Units.mm)
settings = Settings(fit_page=True, fixed_stroke_width=0.12, output_layers=True)
target.write_text(backend.get_string(page, settings=settings), encoding="utf-8")
print(target)
