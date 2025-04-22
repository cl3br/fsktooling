import csv, os

# settings
input_directory = './OBM22/csv/all'
output_file_name = 'merge.csv'


def merge_csv_in_directory(input_directory, output_file_name, delimiter=',', csv_has_header=True, log_file_name='log_merge_csv.txt', make_unique=False):
    file_list = []
    for directory_item in os.listdir(input_directory):
        file_path = os.path.join(input_directory, directory_item)
        if not os.path.isfile(file_path):
            continue # not a file

        file_name = directory_item

        file_name_and_extension = os.path.splitext(file_name)

        if len(file_name_and_extension) < 2:
            continue # there is no extension

        if file_name_and_extension[1] != '.csv':
            continue # not a csv extension

        if file_name == output_file_name:
            continue # ignore output file if performing multiple times in one directory

        file_list.append(file_path)

    merge_csv(file_list, os.path.join(input_directory, output_file_name), delimiter, csv_has_header, os.path.join(input_directory, log_file_name), make_unique)


def merge_csv(csv_file_list, output_file_path, delimiter=',', csv_has_header=True, log_file_path='log_merge_csv.txt', make_unique=False):

    fieldnames = {}
    output_list = []

    with open(os.path.join(log_file_path), 'w') as log_file:
        for file_path in csv_file_list:
            file_name = os.path.basename(file_path)

            with open(file_path, 'r') as csv_file:
                if csv_has_header:
                    reader = csv.DictReader(csv_file, delimiter=delimiter)
                    if not fieldnames:
                        fieldnames = reader.fieldnames
                    elif fieldnames != reader.fieldnames:
                        log_file.write("Invalid csv fieldnames for '%s'\n" % file_name)
                        continue
                else:
                    reader = csv.reader(csv_file, delimiter=delimiter)

                log_file.write("Reading '%s'\n" % file_name)

                for line in reader:
                    output_list.append(line)

        if output_list:
            if make_unique:
                output_list = list(set(output_list))

            with open(output_file_path, 'w') as csv_file:
                log_file.write("Writing csv file '%s'\n" % output_file_path)
                if csv_has_header:
                    writer = csv.DictWriter(csv_file, fieldnames, delimiter=delimiter)
                    writer.writeheader()
                else:
                    writer = csv.writer(csv_file, delimiter=delimiter)
                writer.writerows(output_list)


if __name__ == '__main__':
    merge_csv_in_directory(input_directory, output_file_name)
