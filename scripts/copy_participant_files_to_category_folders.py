import os
import csv
import shutil
import unicodedata
import string

from fsklib.utils.common import normalize_string

# defines

############
if True:
    file_type = 'Musiken'
    find_segment_type = True
    ignore_segement_in_output_structure = False
else:
    file_type = 'PPCS'
    find_segment_type = False
    ignore_segement_in_output_structure = True

force_segment_type = ''  # S -> short or rhythm dance; F -> free skating/ dance
# input_csv_file_path = './OBM22/csv/participants.csv'
input_csv_file_path = './OBM22/csv/starting_order_sa.csv'
input_dir = './OBM22/' + file_type + '/all'
output_root_dir = './OBM22/' + file_type + '/sorted'
# input_dir = '/Volumes/MANNI/' + file_type + '/2 - Name korrigiert'
# output_root_dir = '/Volumes/MANNI/' + file_type + '/3 - sortiert'


if False:  # check
    should_create_directory_structure = False
    should_copy_files = False
    should_rename_files = False
    should_add_skating_number_to_file_name = False
    should_create_m3u_playlist = False  # one playlist per category and segment
else:  # copy
    should_create_directory_structure = True
    should_copy_files = True
    should_rename_files = True
    should_add_skating_number_to_file_name = True
    should_create_m3u_playlist = False  # one playlist per category and segment


# code
# return a valid directory / filename that can be stored to disc
def valid_filename(filename):
    filename = filename.replace(' ', '_').replace('/', '-').replace('ä', 'ae').replace('ö', 'oe').replace('ü', 'ue')

    whitelist = "-_.() %s%s" % (string.ascii_letters, string.digits)
    char_limit = 255
    # keep only valid ascii chars
    cleaned_filename = unicodedata.normalize('NFKD', filename).encode('ASCII', 'ignore').decode()

    # keep only whitelisted chars
    cleaned_filename = ''.join(c for c in cleaned_filename if c in whitelist)
    if len(cleaned_filename) > char_limit:
        print("Warning, filename truncated because it was over {}. Filenames may no longer be unique".format(char_limit))
    return cleaned_filename[:char_limit]


def find_indices_for_matching_search_string(string_list: list, search_string: str) -> set:
    indices = set()
    if not search_string:
        return indices
    search_string = normalize_string(search_string)
    for i, s in enumerate(string_list):
        if search_string in s:
            indices.add(i)

    return indices


def find_indices_for_full_name(string_list: list, given_name: str, family_name: str, check_family_name_only=False) -> set:
    name = given_name + family_name
    valid_idx_set = find_indices_for_matching_search_string(string_list, name)

    name = family_name + given_name
    valid_idx_set = valid_idx_set.union(find_indices_for_matching_search_string(string_list, name))

    if check_family_name_only:
        valid_idx_set = valid_idx_set.union(find_indices_for_matching_search_string(string_list, family_name))

    return valid_idx_set


def find_file_name_for_participant(participant, file_name_list, find_segment_type, force_segment_type) -> list:
    cat_type = participant['Kategorie-Typ']
    segment_type = participant['Segment-Typ']

    truncated_file_names = [normalize_string(os.path.splitext(s)[0]) for s in file_name_list]

    if force_segment_type:
        if not segment_type:
            segment_type = force_segment_type
        elif segment_type != force_segment_type:
            return []

    find_name = False
    find_name_partner = False
    find_team_name = False
    find_birthday = False

    if cat_type == 'S':
        find_name = True
        find_birthday = True
    elif cat_type == 'P' or cat_type == 'D':
        find_name = True
        find_name_partner = True
    elif cat_type == 'T':
        find_team_name = True

    valid_file_idxs_name = set()
    valid_file_idxs_family_name = set()
    if find_name:
        family_name = participant['Name']
        given_name = participant['Vorname']
        valid_file_idxs_name = find_indices_for_full_name(truncated_file_names, given_name, family_name)

        # if name is ambiguous -> check, if b-day exists and instersect
        valid_file_idxs_bday = set()
        if len(valid_file_idxs_name) > 1 and find_birthday:
            bday = participant['Geburtstag']
            valid_file_idxs_bday = find_indices_for_matching_search_string(truncated_file_names, bday)
            if valid_file_idxs_bday:
                valid_file_idxs_name_temp = valid_file_idxs_name.intersection(valid_file_idxs_bday)
                if valid_file_idxs_name_temp:
                    valid_file_idxs_name = valid_file_idxs_name_temp

        if not valid_file_idxs_name or cat_type == 'P' or cat_type == 'D':
            valid_file_idxs_family_name = find_indices_for_full_name(truncated_file_names, given_name, family_name, True)

    valid_file_idxs_name_partner = set()
    if find_name_partner:
        family_name = participant['Name-Partner']
        given_name = participant['Vorname-Partner']
        valid_file_idxs_name_partner = find_indices_for_full_name(truncated_file_names, given_name, family_name, True)

    valid_file_idxs_name_team = set()
    if find_team_name:
        team_name = participant['Team-Name']
        valid_file_idxs_name_team = find_indices_for_matching_search_string(truncated_file_names, team_name)

    valid_file_idxs_names = valid_file_idxs_name.union(valid_file_idxs_name_partner.union(valid_file_idxs_name_team))
    # find segment
    if find_segment_type:
        valid_file_idxs_segment = set()
        for valid_file_idx in valid_file_idxs_names:
            file_name = truncated_file_names[valid_file_idx].upper()

            seg = str(participant['Segment-Abk.']).upper()
            segs = []

            if seg:
                segs.append(seg)

            if cat_type == 'D':             # dance
                if segment_type == 'S':         # short
                    segs.extend(['RD', 'RT', 'OD'])
                elif segment_type == 'F':       # free
                    segs.extend(['FD', 'KT'])
            else:                           # single, pairs and synchron
                if segment_type == 'S':         # short
                    segs.extend(['SP', 'KP'])
                elif segment_type == 'F':       # free
                    segs.extend(['FS', 'KR', 'KUER', 'FP'])

            for seg in segs:
                if file_name.endswith(seg):
                    valid_file_idxs_segment.add(valid_file_idx)
                    break
    else:  # find segment type
        valid_file_idxs_segment = valid_file_idxs_names

    # still ambiguous -> try to solve with intersections
    valid_file_idxs = set()
    if len(valid_file_idxs_segment) > 1:
        if find_name and valid_file_idxs_name:
            valid_file_idxs = valid_file_idxs_name
            # for pairs, only family name should be sufficient
            if find_name_partner:
                valid_file_idxs = valid_file_idxs_family_name
        if find_name_partner and valid_file_idxs_name_partner:
            if valid_file_idxs:
                valid_file_idxs = valid_file_idxs.intersection(valid_file_idxs_name_partner)
            else:
                valid_file_idxs = valid_file_idxs_name_partner
        if find_birthday and valid_file_idxs_bday:
            if valid_file_idxs:
                valid_file_idxs = valid_file_idxs.intersection(valid_file_idxs_bday)
            else:
                valid_file_idxs = valid_file_idxs_bday
        if find_team_name:
            if valid_file_idxs:
                valid_file_idxs = valid_file_idxs.intersection(valid_file_idxs_name_team)
            else:
                valid_file_idxs = valid_file_idxs_name_team
        valid_file_idxs = valid_file_idxs.intersection(valid_file_idxs_segment)
    else:
        valid_file_idxs = valid_file_idxs_segment

    valid_file_count = len(valid_file_idxs)

    files_found = set()
    if valid_file_count < 1:
        log_string = '\033[31m## missing ##\033[0m'
    elif valid_file_count > 1:
        log_string = '\033[35m## ambiguous ##\033[0m ('
        for valid_file_idx in valid_file_idxs:
            log_string += input_file_names_with_ext[valid_file_idx] + ','
            files_found.add(input_file_names_with_ext[valid_file_idx])
        log_string += ')'
    else:
        # file found
        valid_index = valid_file_idxs.pop()  # there is only one element
        log_string = '(\033[32m## found ##\033[0m ' + input_file_names_with_ext[valid_index] + ')'
        files_found.add(input_file_names_with_ext[valid_index])

    name = participant['Name'] + ', ' + participant['Vorname']
    # use team name for couples or teams
    if cat_type != 'S':
        name = participant['Team-Name']
    print('  ' + name + ' (' + participant['Nation'] + '/' + participant['Club-Abk.'] + ') ' + log_string)

    # convert set to list
    files_found = [f for f in files_found]
    return files_found


########
# main #
########

if __name__ == "__main__":
    input_file_names_with_ext = os.listdir(input_dir)

    categories = {}
    participants = []

    count_found = 0
    count_missing = 0
    count_ambiguous = 0

    with open(input_csv_file_path, 'r', encoding='utf-8') as f:
        csv_list_dict = csv.DictReader(f)

        # copy csv data to participant list
        # build category and segment structure (as nested dictionaries)
        for entry in csv_list_dict:
            participants.append(entry)
            cat_name = entry['Kategorie-Name']
            if cat_name in categories:
                categories[cat_name]['segments'][entry['Segment-Abk.']] = {
                                            'name': entry['Segment-Name'],
                                            'type': entry['Segment-Typ']
                                        }
            else:
                categories[cat_name] = {
                                            'type': entry['Kategorie-Typ'],
                                            'gender': entry['Kategorie-Geschlecht'],
                                            'level': entry['Kategorie-Level'],
                                            'segments': {
                                                entry['Segment-Abk.']: {
                                                    'name': entry['Segment-Name'],
                                                    'type': entry['Segment-Typ']
                                                }
                                            }
                                        }

    # print(categories)

    # create folder structure
    if should_create_directory_structure:
        for cat_name, cat_data in categories.items():
            cat_name = valid_filename(cat_name)
            category_dir = os.path.join(output_root_dir, cat_name)
            if not os.path.isdir(category_dir):
                os.mkdir(category_dir)

            if ignore_segement_in_output_structure:
                continue

            for seg in cat_data['segments']:
                segment_dir = os.path.join(category_dir, seg)
                if not os.path.isdir(segment_dir):
                    os.mkdir(segment_dir)

    files_found = set()

    cat_name_old = ''
    seg_name_old = ''
    playlist_dict = {}
    participants_out = []
    for participant in participants:
        cat_name = participant['Kategorie-Name']
        cat_type = participant['Kategorie-Typ']
        segment_name = participant['Segment-Name']
        segment_type = participant['Segment-Typ']
        segment_abbr = participant['Segment-Abk.']
        skating_number = participant['Startnummer']

        if cat_name_old != cat_name:
            print('# ' + cat_name)
            cat_name_old = cat_name

        if seg_name_old != segment_name:
            print('## ' + segment_name)
            seg_name_old = segment_name

            if playlist_dict:
                playlist_path = os.path.join(playlist_dict['dir'], '0 - Playlist.m3u')
                with open(playlist_path, 'w') as pf:
                    pf.writelines('%s\n' % n for i, n in sorted(playlist_dict['names'].items()))

                playlist_dict = {}

        participant_file_names = find_file_name_for_participant(participant, input_file_names_with_ext, find_segment_type, force_segment_type)

        participant['Status'] = ''
        participant['Musik'] = ''
        participants_out.append(participant)
        if not participant_file_names or len(participant_file_names) <= 0:
            count_missing += 1
            continue
        elif len(participant_file_names) > 1:  # multiple files found
            count_ambiguous += 1
            continue
        elif len(participant_file_names) == 1:
            count_found += 1
        else:
            continue

        files_found.update(set(participant_file_names))

        input_file_name = participant_file_names[0]
        input_file_path = os.path.join(input_dir, input_file_name)

        name_and_ext_tuple = os.path.splitext(input_file_name)
        input_file_name_ext = ''
        if len(name_and_ext_tuple) > 1:
            input_file_name_ext = name_and_ext_tuple[1]

        # add skating number
        output_file_name = ''
        if should_add_skating_number_to_file_name:
            output_file_name = '%02d-' % int(skating_number)
        if should_rename_files:
            name = participant['Vorname'] + '-' + participant['Name']
            # use team name for couples or teams
            if cat_type != 'S':
                name = participant['Team-Name'].replace(' ', '-').replace('/', '-')

            name = normalize_string(name)
            output_file_name += name.strip() + input_file_name_ext
        else:
            output_file_name += input_file_name

        cat_dir_name = valid_filename(cat_name)
        if ignore_segement_in_output_structure:
            output_file_dir = os.path.join(output_root_dir, cat_dir_name)
        else:
            output_file_dir = os.path.join(output_root_dir, cat_dir_name, segment_abbr)
        output_file_path = os.path.join(output_file_dir, output_file_name)

        # copy file
        if should_copy_files:
            shutil.copy(input_file_path, output_file_path)

        if should_create_m3u_playlist and skating_number:
            n = int(skating_number)
            if playlist_dict:
                playlist_dict['names'][n] = output_file_name
            else:
                playlist_dict = {
                                    'dir': output_file_dir,
                                    'names': {n: output_file_name}
                                }

        participant['Musik'] = output_file_name

    # print statistical data
    print('###########')
    print('Statistics:')
    print('Found: ' + str(count_found) + '(' + str(len(participants)) + ')')
    print('Missing: ' + str(count_missing) + '(' + str(len(participants)) + ')')
    print('Ambiguous: ' + str(count_ambiguous) + '(' + str(len(participants)) + ')')
    print('Files: ' + str(len(input_file_names_with_ext)))
    print('Unused files:')
    for input_file_name in input_file_names_with_ext:
        if input_file_name not in files_found:
            print(input_file_name)

    if participants_out:
        fieldnames = participants_out[0].keys()
        output_file_path = os.path.join(output_root_dir, 'participants.csv')
        with open(output_file_path, 'w', encoding="utf-8", newline='') as csv_file:
            print("Writing csv file '%s'\n" %  output_file_path)
            writer = csv.DictWriter(csv_file, fieldnames)
            writer.writeheader()
            writer.writerows(participants_out)
