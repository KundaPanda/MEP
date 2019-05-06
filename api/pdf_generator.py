from tempfile import NamedTemporaryFile
from fpdf import FPDF
import qrcode
import os
import time
from PyPDF2 import PdfFileMerger, PdfFileReader


def create_qr(data):
    """creates a qr code from data

    Arguments:
        data {[string/integer]} -- [data to be contained in the code]

    Returns:
        [path] -- [path to created and saved image (png)]
    """
    qr = qrcode.QRCode(
        version=2,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        border=1.5,
        box_size=25,
    )
    qr.add_data(data)
    image = qr.make_image(fill_color="black", back_color="white")
    img_path = NamedTemporaryFile(delete=False)
    image.save(img_path, "PNG")
    return img_path


# def create_image_page(codes_array, start, stop, current_parent_offset, img, draw):
#     if not img:
#         img = Image.new("RGB", (2480, 3508), "white")
#     if not draw:
#         draw = ImageDraw.Draw(img)
#     i = start
#     y_offset = current_parent_offset * 3508
#     draw.rectangle(((60 + y_offset, 64), (2420 + y_offset, 3444)),
#                    "white", "black", 1)
#     for y in range(64 + y_offset, 1755 + y_offset, 1690):
#         for x in range(60, 2200, 590):
#             if (i > stop):
#                 return
#             code = str(codes_array[i])
#             qr_code = create_qr(code)

#             draw.rectangle(((x, y), (x + 590, y + 1690)),
#                            fill="white", outline="black", width=1)
#             # content dimensions: 570 x 1670
#             content_offset = {
#                 'x': x + 10,
#                 'y': y + 10
#             }
#             # qr code here
#             img.paste(qr_code, (content_offset['x'], content_offset['y']))
#             # draw.rectangle(((content_offset['x'], content_offset['y']), (
#             #     content_offset['x'] + 570, content_offset['y'] + 570)), fill="green")
#             content_offset['y'] += 570
#             w, h = FONT.getsize(code)
#             draw.line(((content_offset['x'], content_offset['y']),
#                        (content_offset['x'] + 570, content_offset['y'])), "black", 1)
#             draw.text(
#                 (content_offset['x'] + ((570 - w) / 2), content_offset['y']), code, 'black', FONT)
#             content_offset['y'] += FONT.size + 20
#             draw.line(((content_offset['x'], content_offset['y']),
#                        (content_offset['x'] + 570, content_offset['y'])), "black", 1)
#             content_offset['y'] += 10
#             # insert custom code desin here as image
#             draw.rectangle(((content_offset['x'], content_offset['y']), (
#                 content_offset['x'] + 570, 1670 + y + 10)), "red")
#             i += 1


# def create_image(codes_array, filename):
#     # only under 1000 codes
#     total_size = 3508 * ((len(codes_array) - 1) // 8 + 1)
#     image = Image.new("RGB", (2480, total_size), "white")
#     draw = ImageDraw.Draw(image)
#     for code_index in range(0, len(codes_array), 8):
#         upper = code_index + 7
#         if upper > len(codes_array) - 1:
#             upper = len(codes_array) - 1
#         create_image_page(codes_array, code_index,
#                           upper, code_index // 8, image, draw)
#         current_y = code_index // 8
#         current_y *= 3508
#         draw.line(((0, current_y), (2480, current_y)), "black", 1)
#     print("saving")
#     # buffer = BytesIO()
#     # image.save(buffer)
#     image.save(os.path.abspath("api/public/%s" % filename))
#     print("saved")


def create_pdf_page(codes_array, start, stop, pdf=None):
    """creates a single pdf page from codes_array[start:stop]

    Arguments:
        codes_array {[list]} -- [list of codes]
        start {[int]} -- [starting index]
        stop {[int]} -- [stop index]

    Keyword Arguments:
        pdf {[filepath]} -- [path to pdf to be appended to] (default: {None = new one will be created})
    """
    if not pdf:
        pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.set_font('Arial')
    pdf.set_font_size(16)
    pdf.set_margins(3, 3.5, 3)
    pdf.set_auto_page_break(False)
    pdf.add_page()
    # two rows
    i = start
    for y in range(3, 149, 145):
        # 4 per row
        for x in range(3, 157, 51):
            if i > stop:
                return
            offset = (x, y + 0.5)
            # ticket
            offset_padding = (offset[0] + 1.5, offset[1] + 1.5)
            pdf.set_xy(offset[0], offset[1])
            pdf.set_fill_color(150, 10, 10)
            pdf.cell(51, 145, "", 1, 1, 'c', True)
            code = codes_array[i]
            image_tempfile = create_qr(code)
            pdf.image(image_tempfile.name,
                      offset_padding[0], offset_padding[1], 48, 48, 'PNG')
            os.unlink(image_tempfile.name)
            image_tempfile.close()
            pdf.set_xy(offset_padding[0], offset[1] + 51)
            pdf.set_fill_color(10, 150, 10)
            pdf.cell(48, 6, str(code), 1, 1, 'C', True)
            pdf.set_xy(offset_padding[0], offset[1] + 58.5)
            pdf.cell(48, 85, fill=True)
            i += 1


def create_pdf(codes_array, filename):
    """creates multiple pdf files from codes_array and merges them into one

    Arguments:
        codes_array {[list]} -- [list of codes to export]
        filename {[string]} -- [filename of the output]

    Returns:
        [path] -- [path to the generated pdf]
    """
    total_gentime, total_savetime = 0, 0
    for pdf_part in range(len(codes_array) // 1000 + 1):
        upper_bound = len(codes_array)
        if upper_bound > (pdf_part + 1) * 1000:
            upper_bound = (pdf_part + 1) * 1000
        pdf = FPDF(orientation='P', unit='mm', format='A4')
        start = time.time()
        for code_index in range(pdf_part * 1000, upper_bound, 8):
            upper = code_index + 8
            if upper > upper_bound - 1:
                upper = upper_bound - 1
            create_pdf_page(codes_array, code_index, upper, pdf)
        stop = time.time()
        total_gentime += (stop - start)
        start = time.time()
        filepath = 'api/public/%s.pdf' % (filename + "_" + str(pdf_part))
        filepath = os.path.abspath(filepath)
        pdf.output(filepath, 'F')
        stop = time.time()
        total_savetime += (stop - start)
    print("Total:\n  Pdf generation time: %.2f seconds\n  Pdf save time: %.2f seconds\n" %
          (total_gentime, total_savetime))
    start = time.time()
    export_path = merge_pdf()
    stop = time.time()
    # print("Merge time: %.2f" % (stop - start))
    return (export_path)


def merge_pdf():
    """merges multiple pdf files into one from folder api/public

    Returns:
        [path] -- [created file]
    """
    filelist = [os.path.join(os.path.abspath("api/public"), f) for f in os.listdir(
        os.path.abspath("api/public")) if ('.pdf' in f)]
    merger = PdfFileMerger()
    for f in filelist:
        with open(f, 'rb') as pdf_file:
            merger.append(PdfFileReader(pdf_file))
        os.remove(f)
    export_path = os.path.join(os.path.abspath("api/public"), "export.pdf")
    merger.write(export_path)
    return export_path


def export_codes(codes_array, export_format="pdf"):
    """function to be called by the api, exports codes_array in a specified format (currently only pdf)

    Arguments:
        codes_array {[list]} -- [list of codes to be exported]

    Keyword Arguments:
        export_format {str} -- [export format type] (default: {"pdf"})

    Returns:
        [path] -- [path to the generated file]
    """
    # cleanup, will be removed, only for testing
    filelist = [f for f in os.listdir(os.path.abspath("api/public"))]
    for f in filelist:
        os.remove(os.path.join(os.path.abspath("api/public"), f))
    print("Number of codes: %s" % len(codes_array))
    if export_format == 'pdf':
        return create_pdf(codes_array, 'export')
    else:
        # redundant atm, future uses possible
        return create_pdf(codes_array, 'export')
