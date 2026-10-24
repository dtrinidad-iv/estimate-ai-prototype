"""Generates demo measurement reports in several (fictional) provider formats.

The providers are made up on purpose; real provider templates are added the same way
once a client shares example reports. Run:  python -m scripts.make_samples
"""

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.graphics.shapes import Drawing, Polygon, Line
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

OUT = Path(__file__).resolve().parent.parent / "samples"
styles = getSampleStyleSheet()


def roof_sketch(color) -> Drawing:
    d = Drawing(460, 120)
    d.add(Polygon([30, 20, 230, 20, 190, 100, 70, 100], fillColor=colors.whitesmoke, strokeColor=color, strokeWidth=1.5))
    d.add(Polygon([230, 20, 430, 20, 390, 80, 270, 80], fillColor=colors.whitesmoke, strokeColor=color, strokeWidth=1.5))
    d.add(Line(70, 100, 190, 100, strokeColor=colors.red, strokeWidth=2))
    d.add(Line(270, 80, 390, 80, strokeColor=colors.red, strokeWidth=2))
    return d


def table(rows, header_color, col_widths=None):
    t = Table(rows, colWidths=col_widths, hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), header_color),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f3f5f8")]),
    ]))
    return t


def demo_provider_a(path: Path, address: str, report_no: str, m: dict, breakdown: list[tuple[str, int]]):
    """Demo Provider A: sq ft areas, 'x/12' pitch, lengths in ft with counts."""
    navy = colors.HexColor("#1d3557")
    doc = SimpleDocTemplate(str(path), pagesize=letter, topMargin=0.6 * inch)
    s = [
        Paragraph("<font color='#1d3557' size=18><b>DEMO PROVIDER A</b></font> &nbsp; Roof Measurement Report", styles["Title"]),
        Paragraph(f"Report #{report_no} &nbsp;|&nbsp; Property: {address}", styles["Normal"]),
        Spacer(1, 10), roof_sketch(navy), Spacer(1, 10),
        Paragraph("<b>Report Summary</b>", styles["Heading2"]),
    ]
    summary = [["Measurement", "Value"],
               ["Total Roof Area", f"{m['area']:,} sq ft"],
               ["Total Squares", f"{m['area'] / 100:.2f}"],
               ["Predominant Pitch", f"{m['pitch']}/12"],
               ["Total Roof Facets", str(m["facets"])]]
    s += [table(summary, navy, [2.5 * inch, 2 * inch]), Spacer(1, 12),
          Paragraph("<b>Lengths, Areas and Pitches</b>", styles["Heading2"])]
    lengths = [["Line Type", "Total Length", "Count"]]
    for label, key, unit in [("Ridges", "ridges", "Ridges"), ("Hips", "hips", "Hips"), ("Valleys", "valleys", "Valleys"),
                             ("Rakes", "rakes", "Rakes"), ("Eaves", "eaves", "Eaves"),
                             ("Step Flashing", "step", "Lines"), ("Headwall Flashing", "wall", "Lines")]:
        if key in m:
            lengths.append([label, f"{m[key]} ft", f"{m.get(key + '_n', 1)} {unit}"])
    s += [table(lengths, navy, [2 * inch, 1.5 * inch, 1.5 * inch]), Spacer(1, 6),
          Paragraph(f"Total Perimeter: {m['perimeter']} ft", styles["Normal"]), Spacer(1, 12),
          Paragraph("<b>Areas per Pitch</b>", styles["Heading2"])]
    s.append(table([["Roof Pitch", "Area (sq ft)", "% of Roof"]] +
                   [[p, f"{a:,}", f"{a / m['area'] * 100:.1f}%"] for p, a in breakdown], navy))
    s += [Spacer(1, 12), Paragraph(f"Suggested Waste Factor: {m['waste']}%", styles["Normal"]),
          Spacer(1, 18), Paragraph("<font size=7 color=grey>Demo Provider A is a fictional report layout used for demonstration. "
                                   "Measurements derived from aerial imagery.</font>", styles["Normal"])]
    doc.build(s)


def demo_provider_b(path: Path, address: str, job_ref: str, m: dict, breakdown: list[tuple[str, float]]):
    """Demo Provider B: areas in squares, 'x:12' slopes, lengths in LF, different labels."""
    teal = colors.HexColor("#0f766e")
    doc = SimpleDocTemplate(str(path), pagesize=letter, topMargin=0.6 * inch)
    s = [
        Paragraph("<font color='#0f766e' size=18><b>DEMO PROVIDER B</b></font>", styles["Title"]),
        Paragraph(f"Roof Geometry Summary &nbsp;&middot;&nbsp; Job Ref {job_ref}", styles["Normal"]),
        Paragraph(f"Site Address: {address}", styles["Normal"]),
        Spacer(1, 10), roof_sketch(teal), Spacer(1, 10),
    ]
    s.append(table([["ROOF SQUARES", "AREA", "PRIMARY SLOPE", "PLANES"],
                    [f"{m['squares']:.2f}", f"{m['squares'] * 100:,.0f} SF", f"{m['pitch']}:12", str(m["facets"])]], teal))
    s += [Spacer(1, 14), Paragraph("<b>Linear Measurements</b>", styles["Heading2"])]
    s.append(table([["Edge", "LF"],
                    ["Eave Length", f"{m['eaves']} LF"], ["Rake Length", f"{m['rakes']} LF"],
                    ["Ridge Length", f"{m['ridges']} LF"], ["Hip Length", f"{m['hips']} LF"],
                    ["Valley Length", f"{m['valleys']} LF"], ["Step Flash", f"{m['step']} LF"],
                    ["Headwall", f"{m['wall']} LF"], ["Drip Edge (Eave + Rake)", f"{m['eaves'] + m['rakes']} LF"]],
                   teal, [2.5 * inch, 1.5 * inch]))
    s += [Spacer(1, 14), Paragraph("<b>Slope Breakdown</b>", styles["Heading2"]),
          table([["Slope", "Squares"]] + [[p, f"{q:.2f}"] for p, q in breakdown], teal, [1.5 * inch, 1.5 * inch]),
          Spacer(1, 14), Paragraph(f"Recommended Waste: {m['waste']}%", styles["Normal"]),
          Spacer(1, 18), Paragraph("<font size=7 color=grey>Demo Provider B is a fictional report layout used for demonstration.</font>",
                                   styles["Normal"])]
    doc.build(s)


def field_worksheet(path: Path):
    """A hand-typed contractor worksheet in no known template: exercises the generic parser + AI fallback."""
    doc = SimpleDocTemplate(str(path), pagesize=letter, topMargin=0.8 * inch)
    body = """
    <b>Roof Measurement Worksheet</b><br/>Prepared by field tech after site visit, 3 Oct.<br/><br/>
    Homeowner: Garcia residence, 412 Birch Hollow Rd.<br/><br/>
    Overall the roof area comes out to approximately 1,980 sq ft, single story ranch with one dormer.<br/>
    Main slope is 7/12 on all faces, dormer is roughly the same.<br/>
    Ridge line measured at 64 LF. No hips on this house.<br/>
    Eave line around the house totals 140 LF; the gable rakes add another 88 LF.<br/>
    Two short valleys at the dormer, 24 LF combined.<br/>
    Sidewall flashing where the dormer meets the main roof: 16 LF. Chimney has 6 LF of apron flashing.<br/>
    Customer wants a bid on architectural shingles.
    """
    doc.build([Paragraph(body, styles["Normal"])])


def main():
    OUT.mkdir(exist_ok=True)
    demo_provider_a(OUT / "demo_a_1428_maple_ave.pdf", "1428 Maple Ave, Springfield", "DA-240918",
               dict(area=2846, pitch=6, facets=14, ridges=92, ridges_n=4, hips=48, hips_n=2, valleys=36, valleys_n=3,
                    rakes=118, rakes_n=6, eaves=164, eaves_n=8, step=28, step_n=3, wall=14, wall_n=1,
                    perimeter=282, waste=12),
               [("6/12", 2410), ("4/12", 436)])
    demo_provider_b(OUT / "demo_b_77_ridgeview_dr.pdf", "77 Ridgeview Dr, Lakeside", "DB-55102",
             dict(squares=31.25, pitch=9, facets=18, ridges=104, hips=72, valleys=58, rakes=96, eaves=188,
                  step=42, wall=20, waste=14),
             [("9:12", 21.40), ("12:12", 7.85), ("4:12", 2.00)])
    # Deliberately inconsistent: pitch areas don't add up and the eaves line is missing.
    demo_provider_a(OUT / "demo_a_needs_review_oak_st.pdf", "9 Oak St, Riverton", "DA-240977",
               dict(area=2200, pitch=5, facets=9, ridges=70, ridges_n=2, hips=20, hips_n=2, valleys=12, valleys_n=1,
                    rakes=96, rakes_n=4, step=18, step_n=2, wall=0, wall_n=0, perimeter=240, waste=10),
               [("5/12", 1650), ("3/12", 400)])
    field_worksheet(OUT / "field_worksheet_unknown_format.pdf")
    for p in sorted(OUT.glob("*.pdf")):
        print("wrote", p.relative_to(OUT.parent))


if __name__ == "__main__":
    main()
