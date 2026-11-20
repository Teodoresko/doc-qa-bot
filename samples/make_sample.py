"""Build the fictional sample manual used by the demo.

The product, brand and every value in it are made up for demo purposes.
Run:  python samples/make_sample.py
"""
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (PageBreak, Paragraph, SimpleDocTemplate, Spacer,
                                Table, TableStyle)

OUT = Path(__file__).with_name("brewline-x2-user-manual.pdf")
ss = getSampleStyleSheet()
H1 = ParagraphStyle("h1", parent=ss["Heading1"], fontSize=18, spaceAfter=8, textColor=colors.HexColor("#1e3a8a"))
H2 = ParagraphStyle("h2", parent=ss["Heading2"], fontSize=13, spaceBefore=10, spaceAfter=4)
P = ParagraphStyle("p", parent=ss["BodyText"], fontSize=10, leading=14)
NOTE = ParagraphStyle("note", parent=P, backColor=colors.HexColor("#fef3c7"), borderPadding=6, spaceBefore=6, spaceAfter=8)


def table(rows, widths):
    t = Table(rows, colWidths=widths)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a8a")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f1f5f9")]),
    ]))
    return t


def para(rows):
    return [[Paragraph(str(c), P) for c in r] for r in rows]


def steps(items):
    return [Paragraph(f"<b>{i}.</b> {s}", P) for i, s in enumerate(items, 1)]


story = []
add = story.extend

# Page 1 — cover + safety
add([
    Paragraph("Brewline X2 Smart Coffee Maker", H1),
    Paragraph("User Manual · Model BX2-100 · Revision 3.1", P),
    Paragraph("FICTIONAL SAMPLE DOCUMENT made for a software demo. Brand, product and specifications are invented.", NOTE),
    Paragraph("1. Important Safety Instructions", H2),
    Paragraph("Read all instructions before first use. Keep this manual for future reference.", P),
    *[Paragraph("• " + s, P) for s in [
        "Only connect the machine to a grounded outlet rated 220–240 V, 50/60 Hz.",
        "Never immerse the base, cord or plug in water or any other liquid.",
        "Do not touch the hot plate or the brew head during or right after brewing. Surfaces can reach 85 °C.",
        "Unplug the machine before cleaning, descaling or replacing the water filter.",
        "Children under 8 years must not use or clean the machine.",
        "Use only genuine Brewline filters and descaling solution. Other products may void the warranty.",
    ]],
    Paragraph("2. What's in the Box", H2),
    table(para([["Part", "Qty", "Part no."],
                ["Brewline X2 base unit", "1", "BX2-100"],
                ["Glass carafe, 1.5 L", "1", "BX2-CAR15"],
                ["Permanent mesh filter", "1", "BX2-MF01"],
                ["Charcoal water filter cartridge", "2", "BX2-WF02"],
                ["Measuring scoop (7 g)", "1", "BX2-SC07"],
                ["Water hardness test strip", "1", "BX2-HT01"]]), [90 * mm, 20 * mm, 50 * mm]),
    PageBreak(),
])

# Page 2 — parts + controls
add([
    Paragraph("3. Product Overview", H2),
    Paragraph("The Brewline X2 has a 1.8 L removable water tank at the back, a swing-out filter basket at the front, "
              "and a keep-warm hot plate under the carafe. The control panel has four buttons and a round status ring.", P),
    table(para([["Button", "Short press", "Hold 3 seconds"],
                ["POWER", "Turn on / off", "Factory reset (with machine off)"],
                ["BREW", "Start or pause brewing", "Start descaling program"],
                ["STRENGTH", "Cycle Mild → Regular → Bold", "Toggle Iced mode (brews 40% less water)"],
                ["TIMER", "Show / set delayed start", "Toggle 12 / 24 hour clock"]]), [32 * mm, 60 * mm, 70 * mm]),
    Paragraph("Status ring colours", H2),
    table(para([["Colour", "Meaning"],
                ["Solid white", "Ready"],
                ["Pulsing white", "Brewing"],
                ["Solid amber", "Keep-warm active (turns off after 40 minutes by default)"],
                ["Pulsing amber", "Descaling needed or descaling in progress"],
                ["Solid red", "Error — check the display for an E-code (see section 9)"],
                ["Blue blink", "Wi-Fi pairing mode"]]), [40 * mm, 122 * mm]),
    PageBreak(),
])

# Page 3 — first use + brewing
add([
    Paragraph("4. Before First Use", H2),
    *steps(["Remove all packaging and stickers. Wash the carafe and mesh filter in warm soapy water.",
            "Soak a charcoal water filter cartridge in cold water for 5 minutes, then push it into the holder inside the tank.",
            "Test your water hardness with the strip (dip 1 second, read after 60 seconds) and set it as described in section 8.",
            "Fill the tank to MAX with water only and run one full brew cycle without coffee. Discard the water.",
            "Repeat once more. The machine is now ready."]),
    Paragraph("5. Brewing Coffee", H2),
    *steps(["Fill the tank with fresh cold water. The scale on the tank shows cups (1 cup = 125 ml).",
            "Put the mesh filter (or a size 4 paper filter) in the basket.",
            "Add ground coffee: one level scoop (7 g) per cup. Medium grind works best.",
            "Close the basket, place the carafe on the hot plate and press BREW.",
            "Press STRENGTH before brewing to choose Mild, Regular or Bold. Bold slows the water flow for a stronger extraction.",
            "Brewing 10 cups takes about 9 minutes. The machine beeps three times when done."]),
    Paragraph("Drip-stop: you can remove the carafe for up to 30 seconds during brewing to pour a cup. "
              "If the carafe is away longer than 30 seconds, brewing pauses and the basket may overflow.", NOTE),
    PageBreak(),
])

# Page 4 — timer + app
add([
    Paragraph("6. Delayed Start Timer", H2),
    *steps(["Make sure the clock is set (press TIMER, then use STRENGTH to change hours and BREW to change minutes).",
            "Press TIMER twice. The display shows the start time flashing.",
            "Set the start time the same way, then wait 5 seconds. A small clock icon confirms the timer is active.",
            "Prepare water and coffee as normal. The machine starts brewing at the set time."]),
    Paragraph("Tip: for best taste, do not leave ground coffee in the basket for more than 12 hours before a timed brew.", P),
    Paragraph("7. Wi-Fi and the Brewline App", H2),
    Paragraph("The Brewline app (iOS 16+ / Android 11+) lets you start brews, set schedules and receive descaling reminders. "
              "The X2 supports 2.4 GHz Wi-Fi only; 5 GHz networks are not supported.", P),
    *steps(["Install the Brewline app and create an account.",
            "With the machine on, hold TIMER and STRENGTH together for 5 seconds until the ring blinks blue.",
            "In the app tap Add device → Brewline X2 and follow the prompts. Keep the phone within 3 m of the machine.",
            "Pairing takes up to 2 minutes. The ring turns solid white when connected.",
            "If pairing fails, check that your router uses WPA2 or WPA3 and that the network name has no special characters."]),
    PageBreak(),
])

# Page 5 — water hardness + descaling
add([
    Paragraph("8. Water Hardness Setting", H2),
    Paragraph("The machine counts brew cycles and asks for descaling based on your water hardness. "
              "To set it: with the machine off, hold STRENGTH for 3 seconds, then press STRENGTH to choose level 1–4 and BREW to save.", P),
    table(para([["Level", "Test strip result", "Descale reminder after"],
                ["1 — Soft", "0–1 red squares", "120 brew cycles"],
                ["2 — Medium", "2 red squares", "80 brew cycles (factory default)"],
                ["3 — Hard", "3 red squares", "50 brew cycles"],
                ["4 — Very hard", "4 red squares", "30 brew cycles"]]), [35 * mm, 55 * mm, 72 * mm]),
    Paragraph("10. Descaling", H2),
    Paragraph("Descale when the status ring pulses amber, or at least every 3 months. Descaling takes about 35 minutes.", P),
    *steps(["Empty the carafe and remove the mesh filter and the water filter cartridge.",
            "Pour one bottle (250 ml) of Brewline descaler (part BX2-DS250) into the tank and add water up to the 1.0 L mark.",
            "Place the empty carafe on the hot plate.",
            "Hold BREW for 3 seconds. The ring pulses amber and the program runs in stages with pauses. Do not switch off.",
            "When the machine beeps twice, empty the carafe, rinse the tank and fill it to MAX with clean water.",
            "Press BREW to run the rinse cycle. Repeat the rinse once more, then reinstall the water filter.",
            "The descale counter resets automatically."]),
    Paragraph("Never use vinegar. Acetic acid can damage the seals in the heating block and is not covered by the warranty.", NOTE),
    PageBreak(),
])

# Page 6 — error codes
add([
    Paragraph("9. Troubleshooting and Error Codes", H2),
    Paragraph("If the ring is solid red, the display shows a code. Unplug the machine for 10 seconds before trying again.", P),
    table(para([["Code", "Meaning", "What to do"],
                ["E01", "Water tank empty or not seated", "Fill the tank and press it down firmly until it clicks."],
                ["E02", "Carafe missing during brew", "Return the carafe within 30 seconds; press BREW to resume."],
                ["E03", "Heater overheat protection", "Unplug and let the machine cool for 20 minutes. If it repeats, contact support."],
                ["E04", "Scale build-up is blocking water flow", "Run the descaling program (section 10). If E04 returns within 5 cycles, run it twice in a row."],
                ["E05", "Temperature sensor fault", "Do not use the machine. Contact support for repair."],
                ["E06", "Filter basket open", "Close the basket until it clicks."],
                ["E07", "Wi-Fi module fault", "Brewing still works. Factory reset (section 3); if it persists, contact support."],
                ["E08", "Firmware update failed", "Keep the machine on and connected; the update retries within 1 hour."]]),
          [16 * mm, 52 * mm, 94 * mm]),
    Paragraph("Other problems", H2),
    table(para([["Problem", "Likely cause and fix"],
                ["Coffee tastes weak", "Use 7 g per cup, choose Bold, or grind slightly finer."],
                ["Coffee tastes bitter", "Use Mild, grind coarser, or reduce keep-warm time."],
                ["Water leaks under the machine", "Tank not seated, or the tank valve is dirty. Rinse the valve and reseat the tank."],
                ["Brewing takes longer than 12 minutes", "Machine needs descaling."],
                ["Basket overflows", "Grind too fine, too much coffee, or carafe removed for over 30 seconds."]]),
          [55 * mm, 107 * mm]),
    PageBreak(),
])

# Page 7 — cleaning + specs
add([
    Paragraph("11. Cleaning and Maintenance", H2),
    table(para([["Part", "How often", "How"],
                ["Carafe and lid", "Daily", "Warm soapy water or top rack of the dishwasher."],
                ["Mesh filter", "Daily", "Rinse under running water. Dishwasher safe."],
                ["Water tank", "Weekly", "Rinse with warm water. Do not put in the dishwasher."],
                ["Hot plate and housing", "Weekly", "Wipe with a damp cloth when cool. No abrasive cleaners."],
                ["Charcoal water filter", "Every 2 months or 60 tanks", "Replace with part BX2-WF02."],
                ["Descaling", "When reminded or every 3 months", "See section 10."]]), [45 * mm, 45 * mm, 72 * mm]),
    Paragraph("Keep-warm time can be changed in the app: 0 (off), 20, 40 (default), 60 or 120 minutes.", P),
    Paragraph("12. Technical Specifications", H2),
    table(para([["Item", "Value"],
                ["Model", "BX2-100"],
                ["Power", "1,000 W, 220–240 V ~ 50/60 Hz"],
                ["Water tank", "1.8 L, removable"],
                ["Carafe", "1.5 L glass (up to 12 cups)"],
                ["Brew temperature", "92–96 °C"],
                ["Standby power", "< 0.5 W (Wi-Fi off), < 2 W (Wi-Fi on)"],
                ["Auto-off", "After 40 minutes of keep-warm, or 5 minutes idle"],
                ["Dimensions (W × D × H)", "21 × 26 × 36 cm"],
                ["Weight", "3.2 kg"],
                ["Wi-Fi", "2.4 GHz 802.11 b/g/n"]]), [60 * mm, 102 * mm]),
    PageBreak(),
])

# Page 8 — warranty + support
add([
    Paragraph("13. Warranty", H2),
    Paragraph("Brewline gives a 2-year limited warranty from the date of purchase on the base unit, and 6 months on the glass carafe. "
              "Registering the product in the app within 30 days extends the base unit warranty to 3 years.", P),
    Paragraph("The warranty covers defects in materials and workmanship under normal household use. It does <b>not</b> cover:", P),
    *[Paragraph("• " + s, P) for s in [
        "Damage from scale build-up when the machine was not descaled as instructed.",
        "Damage from vinegar or non-Brewline descaling products.",
        "Broken glass from drops or impacts.",
        "Commercial use (offices with more than 10 users, cafés, hotels).",
        "Repairs or modifications by anyone other than an authorised Brewline service partner.",
    ]],
    Paragraph("To make a claim, keep your proof of purchase and contact support with the serial number from the label under the base (format BX2-YYMM-XXXXXX).", P),
    Paragraph("14. Customer Support", H2),
    Paragraph("Support is available Monday to Friday, 08:00–18:00 CET, through the help section of the Brewline app. "
              "Spare parts (filters, carafes, descaler) can be ordered in the app under Shop → Parts.", P),
    Paragraph("15. Disposal", H2),
    Paragraph("Do not throw the machine away with household waste. Take it to a collection point for electrical and electronic equipment. "
              "Used charcoal filters can go in general waste.", P),
])


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.grey)
    canvas.drawString(20 * mm, 10 * mm, "Brewline X2 User Manual · fictional demo document")
    canvas.drawRightString(190 * mm, 10 * mm, f"Page {doc.page}")
    canvas.restoreState()


SimpleDocTemplate(str(OUT), pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm,
                  topMargin=18 * mm, bottomMargin=18 * mm,
                  title="Brewline X2 User Manual (fictional demo)").build(story, onFirstPage=footer, onLaterPages=footer)
print("wrote", OUT)
