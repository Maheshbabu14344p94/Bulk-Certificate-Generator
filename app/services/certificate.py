from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.pdfbase.pdfmetrics import stringWidth


OUTPUT_DIR = Path(__file__).resolve().parents[2] / "generated"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

def draw_centered_text(
    c,
    text,
    x,
    y,
    font_name,
    font_size,
    color,
):
    c.setFont(font_name, font_size)
    c.setFillColor(color)
    c.drawCentredString(x, y, text)


def draw_wrapped_center_text(
    c,
    text,
    x,
    y,
    max_width,
    font_name,
    font_size,
    color,
):
    """
    Draw centered text and reduce font size when necessary.
    """

    size = font_size

    while size > 10:
        width = stringWidth(text, font_name, size)

        if width <= max_width:
            break

        size -= 1

    c.setFont(font_name, size)
    c.setFillColor(color)
    c.drawCentredString(x, y, text)


# ---------------------------------------------------------
# Certificate generator
# ---------------------------------------------------------

def generate_certificate(job, recipient):
    """
    Generate one professional PDF certificate.

    Each recipient gets an independent PDF.
    """

    # Clean recipient name for the filename
    safe_name = "".join(
        character if character.isalnum() or character in (" ", "_", "-") else "_"
        for character in recipient.name
    ).strip()

    safe_name = safe_name.replace(" ", "_")

    filename = (
        f"{safe_name}_certificate_{recipient.id}.pdf"
    )

    path = OUTPUT_DIR / filename

    # Landscape A4
    page_w, page_h = landscape(A4)

    c = canvas.Canvas(
        str(path),
        pagesize=(page_w, page_h),
        pageCompression=1,
    )

    # -----------------------------------------------------
    # Color palette
    # -----------------------------------------------------

    background = colors.HexColor("#080D1D")
    panel = colors.HexColor("#0E162B")
    teal = colors.HexColor("#18D6B2")
    teal_dark = colors.HexColor("#0C9F8A")
    white = colors.HexColor("#F7FAFF")
    muted = colors.HexColor("#AAB6D3")
    line = colors.HexColor("#263553")
    gold = colors.HexColor("#F4C96B")

    center_x = page_w / 2

    # -----------------------------------------------------
    # Background
    # -----------------------------------------------------

    c.setFillColor(background)
    c.rect(
        0,
        0,
        page_w,
        page_h,
        fill=1,
        stroke=0,
    )

    # -----------------------------------------------------
    # Inner certificate panel
    # -----------------------------------------------------

    c.setFillColor(panel)
    c.roundRect(
        35,
        35,
        page_w - 70,
        page_h - 70,
        12,
        fill=1,
        stroke=0,
    )

    # -----------------------------------------------------
    # Outer border
    # -----------------------------------------------------

    c.setStrokeColor(teal_dark)
    c.setLineWidth(2)
    c.roundRect(
        35,
        35,
        page_w - 70,
        page_h - 70,
        12,
        fill=0,
        stroke=1,
    )

    # -----------------------------------------------------
    # Inner border
    # -----------------------------------------------------

    c.setStrokeColor(line)
    c.setLineWidth(0.8)
    c.roundRect(
        48,
        48,
        page_w - 96,
        page_h - 96,
        9,
        fill=0,
        stroke=1,
    )

    # -----------------------------------------------------
    # Decorative corner accents
    # -----------------------------------------------------

    accent_size = 55

    c.setStrokeColor(teal)
    c.setLineWidth(2)

    # Top-left
    c.line(60, page_h - 75, 60 + accent_size, page_h - 75)
    c.line(60, page_h - 75, 60, page_h - 75 - accent_size)

    # Top-right
    c.line(
        page_w - 60,
        page_h - 75,
        page_w - 60 - accent_size,
        page_h - 75,
    )
    c.line(
        page_w - 60,
        page_h - 75,
        page_w - 60,
        page_h - 75 - accent_size,
    )

    # Bottom-left
    c.line(60, 75, 60 + accent_size, 75)
    c.line(60, 75, 60, 75 + accent_size)

    # Bottom-right
    c.line(
        page_w - 60,
        75,
        page_w - 60 - accent_size,
        75,
    )
    c.line(
        page_w - 60,
        75,
        page_w - 60,
        75 + accent_size,
    )

    # -----------------------------------------------------
    # Top brand mark
    # -----------------------------------------------------

    c.setFillColor(teal)
    c.circle(center_x, page_h - 82, 13, fill=1, stroke=0)

    draw_centered_text(
        c,
        "C",
        center_x,
        page_h - 88,
        "Helvetica-Bold",
        14,
        background,
    )

    draw_centered_text(
        c,
        "CERTIFLOW",
        center_x,
        page_h - 108,
        "Helvetica-Bold",
        8,
        muted,
    )

    # -----------------------------------------------------
    # Main title
    # -----------------------------------------------------

    draw_centered_text(
        c,
        "CERTIFICATE OF COMPLETION",
        center_x,
        page_h - 155,
        "Helvetica-Bold",
        27,
        white,
    )

    # Accent line
    c.setStrokeColor(teal)
    c.setLineWidth(2)
    c.line(
        center_x - 105,
        page_h - 168,
        center_x + 105,
        page_h - 168,
    )

    # -----------------------------------------------------
    # Subtitle
    # -----------------------------------------------------

    draw_centered_text(
        c,
        "This certificate is proudly presented to",
        center_x,
        page_h - 198,
        "Helvetica",
        12,
        muted,
    )

    # -----------------------------------------------------
    # Recipient name
    # -----------------------------------------------------

    draw_wrapped_center_text(
        c,
        recipient.name,
        center_x,
        page_h - 255,
        page_w - 250,
        "Helvetica-Bold",
        36,
        white,
    )

    # Name underline
    name_width = min(
        stringWidth(
            recipient.name,
            "Helvetica-Bold",
            30,
        ),
        300,
    )

    c.setStrokeColor(gold)
    c.setLineWidth(1.5)

    c.line(
        center_x - name_width / 2,
        page_h - 270,
        center_x + name_width / 2,
        page_h - 270,
    )

    # -----------------------------------------------------
    # Completion text
    # -----------------------------------------------------

    draw_wrapped_center_text(
        c,
        f"for successfully completing {job.course_name}",
        center_x,
        page_h - 302,
        page_w - 260,
        "Helvetica",
        12,
        muted,
    )

    # -----------------------------------------------------
    # Event / program
    # -----------------------------------------------------

    draw_wrapped_center_text(
        c,
        job.event_name,
        center_x,
        page_h - 342,
        page_w - 250,
        "Helvetica-Bold",
        16,
        teal,
    )

    # -----------------------------------------------------
    # Information divider
    # -----------------------------------------------------

    c.setStrokeColor(line)
    c.setLineWidth(0.8)

    c.line(
        110,
        105,
        page_w - 110,
        105,
    )

    # -----------------------------------------------------
    # Issuer section
    # -----------------------------------------------------

    issuer_x = 150

    draw_centered_text(
        c,
        "ISSUED BY",
        issuer_x,
        82,
        "Helvetica-Bold",
        8,
        muted,
    )

    draw_centered_text(
        c,
        job.issuer_name,
        issuer_x,
        65,
        "Helvetica-Bold",
        11,
        white,
    )

    # -----------------------------------------------------
    # Date section
    # -----------------------------------------------------

    date_x = center_x

    draw_centered_text(
        c,
        "ISSUE DATE",
        date_x,
        82,
        "Helvetica-Bold",
        8,
        muted,
    )

    draw_centered_text(
        c,
        job.issue_date,
        date_x,
        65,
        "Helvetica-Bold",
        11,
        white,
    )

    # -----------------------------------------------------
    # Certificate ID section
    # -----------------------------------------------------

    certificate_id = (
        f"CF-{job.id:04d}-{recipient.id:04d}"
    )

    id_x = page_w - 150

    draw_centered_text(
        c,
        "CERTIFICATE ID",
        id_x,
        82,
        "Helvetica-Bold",
        8,
        muted,
    )

    draw_centered_text(
        c,
        certificate_id,
        id_x,
        65,
        "Helvetica-Bold",
        10,
        white,
    )

    # -----------------------------------------------------
    # Footer
    # -----------------------------------------------------

    draw_centered_text(
        c,
        "Authentically generated by CertiFlow Bulk Certificate Studio",
        center_x,
        43,
        "Helvetica",
        7,
        muted,
    )

    # -----------------------------------------------------
    # Save PDF
    # -----------------------------------------------------

    c.save()

    return path