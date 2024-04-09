import os
from pypdf import PdfWriter
import traceback


def pdf_cat(input_files, output_file_path):
    merger = PdfWriter()

    try:
        for pdf in input_files:
            merger.append(pdf)

        merger.write(output_file_path)
    except:
        traceback.print_exc()
    finally:
        merger.close()


def pdf_cat_dir(directory, output_file_name):
    def is_pdf_file(file_name):
        return os.path.isfile(os.path.join(directory, file_name)) and file_name != output_file_name and file_name.endswith('.pdf')
    file_names = sorted(filter(is_pdf_file, os.listdir(directory)))
    if not file_names:
        return
    file_names = [os.path.join(directory, file_name) for file_name in file_names]
    pdf_cat(file_names, os.path.join(directory, output_file_name))


def pdf_cat_dir_r(top):
    pdf_cat_dir(top, os.path.basename(os.path.dirname(top)) + '.pdf')
    for root, dirs, _ in os.walk(top):
        for dir in dirs:
            pdf_cat_dir(os.path.join(root, dir), dir + '.pdf')


if __name__ == '__main__':
    top_dir = '/Volumes/BEV/PPCS/3 - sortiert/'
    pdf_cat_dir_r(top_dir)
