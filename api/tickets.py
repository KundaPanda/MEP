import qrcode
import os
from bs4 import BeautifulSoup
import base64
from io import BytesIO

QR_PATH = "qr"
PUBLIC_PATH = "public"
TEMPLATES_PATH = "templates"

# TODO: Find a more effective way of doing this, it takes ages


def generate_page(codes, start_index=0, per_page=8, pagenum=1):
    """creates svgs from the desired template containing provided codes

    Arguments:
        codes {[array]} -- [array of codes to be exported]

    Keyword Arguments:
        start_index {int} -- [relative start in codes array] (default: {0})
        per_page {int} -- [number of codes per page -> template selection] (default: {8})
        pagenum {int} -- [page number] (default: {1})

    Returns:
        [bool OR BeautifySoup] -- [True if fail, else one div with codes in BeautifulSoup format]
    """
    # TODO COMMENT

    if not isinstance(codes, list) or codes == []:
        print("Invalid input!")
        return 1

    PAGE_TEMPLATE = BeautifulSoup(
        '<div class="codes-1"><div class="ticket-1"><div class="qr-1"><img src="." alt="QR Code"></div><div class="textbox-1"></div><div class="custom"></div></div><div class="ticket-2"><div class="qr-2"><img src="." alt="QR Code"></div><div class="textbox-2"></div><div class="custom"></div></div><div class="ticket-3"><div class="qr-3"><img src="." alt="QR Code"></div><div class="textbox-3"></div><div class="custom"></div></div><div class="ticket-4"><div class="qr-4"><img src="." alt="QR Code"></div><div class="textbox-4"></div><div class="custom"></div></div><div class="ticket-5"><div class="qr-5"><img src="." alt="QR Code"></div><div class="textbox-5"></div><div class="custom"></div></div><div class="ticket-6"><div class="qr-6"><img src="." alt="QR Code"></div><div class="textbox-6"></div><div class="custom"></div></div><div class="ticket-7"><div class="qr-7"><img src="." alt="QR Code"></div><div class="textbox-7"></div><div class="custom"></div></div><div class="ticket-5"><div class="qr-8"><img src="." alt="QR Code"></div><div class="textbox-8"></div><div class="custom"></div></div></div>',
        features="html.parser")
    page = PAGE_TEMPLATE
    page.find("div", {"class": "codes-1"})["class"] = "codes-%s" % (pagenum)

    for i in range(start_index, start_index + 8):
        if i < len(codes):
            code = codes[i]

            border_size = 0
            qr = qrcode.QRCode(
                version=2,
                error_correction=qrcode.constants.ERROR_CORRECT_M,
                border=border_size,
                # 25 = number of boxes in ver. 2 qr code
                box_size=(570 / (25 + border_size * 2)),
            )
            qr.add_data(code)
            qr.make()
            image = qr.make_image(fill_color="black", back_color="white")
            buffer = BytesIO()
            image.save(buffer, format="PNG")
            bytes_image = buffer.getvalue()

            qr_div = page.find("div",
                               {"class": "qr-%s" % (i - start_index + 1)})
            qr_holder = qr_div.find("img")
            encoded = "data:image/jpeg;base64,%s" % base64.b64encode(
                bytes_image).decode()
            qr_holder["src"] = encoded

            code_div = page.find(
                "div", {"class": "textbox-%s" % (i - start_index + 1)})
            code_div.string = (str(code))

    return page


def export_codes(codes, per_page=8, file_format="pdf"):
    """exports array of codes into desired format (pdf, )

    Arguments:
        codes {[array]} -- [array of codes to be exported]

    Keyword Arguments:
        per_page {int} -- [number of codes per page -> template choice] (default: {8})
        file_format {str} -- [output file format] (default: {"pdf"})
    """
    # generate all the separate svgs

    HTML_TEMPLATE = BeautifulSoup(
        open(os.path.join(TEMPLATES_PATH, "codes-8.html"), "r").read(),
        features="html.parser")
    target_page = HTML_TEMPLATE
    for i in range(0, len(codes), 8):
        target_page.find("body").append(
            generate_page(codes, i, per_page, (i // 8) + 1))
    html = target_page.prettify("utf-8")
    with open(os.path.join(PUBLIC_PATH, "export.html"), "wb") as afile:
        afile.write(html)

    shutil.rmtree(QR_PATH, ignore_errors=True)
    os.mkdir(QR_PATH)
    return "export.html"


# export_codes([123, 456, 789])
