import csv
from dataclasses import dataclass
from  datetime import date, datetime
import os
import pathlib
import logging
import traceback
from typing import Dict, List, Set

from . import model, output

# settings
input_DEU_participant_csv_file_path = pathlib.Path('./GBB21Test/csv/Meldeliste_GBB_deu_athletes.csv')
input_DEU_club_csv_file_path = pathlib.Path('./DEU/clubs-DEU.csv')
input_DEU_categories_csv_file_path = pathlib.Path('./GBB21Test/csv/Meldeliste_GBB_deu_categories.csv')
input_DEU_competition_info_csv_file_path = pathlib.Path('./GBB21Test/csv/Meldeliste_GBB_deu_competition.csv')
output_athletes_file_path = pathlib.Path('./GBB21Test/person.csv')
output_participant_file_path = pathlib.Path('./GBB21Test/participants.csv')
output_odf_participant_dir = pathlib.Path('./GBB21Test/')


class DeuMeldeformularCsv:
    # static member
    deu_category_to_gender = {'Herren' : model.Gender.MALE, 'Damen' : model.Gender.FEMALE, 'Einzellauf': model.Gender.FEMALE, 'Paarlaufen' : model.Gender.TEAM, 'Eistanzen' : model.Gender.TEAM, 'Synchron': model.Gender.TEAM}

    def __init__(self) -> None:
        self.unknown_ids = { '888888' : 0, '999999' : 0 }

    def convert_date(self, d: str) -> date:
        if not d:
            return date.today()
        try:
            return datetime.fromisoformat(d).date()
        except:
            try:
                return datetime.strptime(d, "%d.%m.%Y").date()
            except:
                try:
                    return datetime.strptime(d, "%d.%m.%y").date()
                except:
                    print(f"Unable to parse participant birthday '{d}'")
                    return date.today()

    def convert(self, input_participants: str, input_clubs: str, input_categories: str, input_event_info: str, outputs: List[
        output.OutputBase]):
        if not os.path.isfile(input_participants):
            print('Participants file not found.')
            return 1
        if not os.path.isfile(input_clubs):
            print('Club file not found.')
            return 2
        if not os.path.isfile(input_categories):
            print('Categories file not found.')
            return 3

        competition = model.Competition("Test", "LV", "here", date.today(), date.today())
        if input_event_info:
            event_info_file = open(input_event_info, 'r')
            info_reader = csv.DictReader(event_info_file, delimiter=',')
            for comp_dict in info_reader:
                competition.name = comp_dict['Name']
                competition.organizer = comp_dict['Veranstalter']
                competition.place = comp_dict['Ort']
                competition.start = date.fromisoformat(comp_dict['Start Datum'])
                end = comp_dict['End Datum']
                competition.end = date.fromisoformat(end) if end else competition.start

        for output in outputs:
            output.add_event_info(competition)

        # read clubs
        try:
            clubs_file = open(input_clubs, 'r', encoding="utf-8")
            club_reader = csv.DictReader(clubs_file, delimiter=';')

            club_dict = {}
            regions = set()

            for club in club_reader:
                abbr = club['Abk.']
                region = club['Region']
                club_dict[abbr] = model.Club(club['Name'], abbr, region)
                regions.add(region)
        except:
            print('Error while parsing clubs.')
        finally:
            clubs_file.close()

        # read categories
        try:
            categories_dict: Dict[str, model.Category] = {} # cat_name -> category
            category_numbers: Dict[str, int] = {} # str(cat_type + cat_level + cat_gender) -> number
            cats_file = open(input_categories, 'r')
            cat_reader = csv.DictReader(cats_file)
            for cat_dict in cat_reader:
                cat_name = cat_dict['Wettbewerb/Prüfung'].strip()
                cat_deu_type = cat_dict['Disziplin'].strip()
                cat_deu_level = cat_dict['Kategorie'].strip()

                cat_type = model.CategoryType.from_value(cat_deu_type, model.DataSource.DEU)
                cat_gender = DeuMeldeformularCsv.deu_category_to_gender[cat_deu_type] if cat_deu_type in DeuMeldeformularCsv.deu_category_to_gender else model.Gender.FEMALE
                cat_level = model.CategoryLevel.from_value(cat_deu_level, model.DataSource.DEU)

                if not cat_type or not cat_gender or not cat_level:
                    print('Warning: Unable to convert category following %s|%s|%s' % (cat_name, cat_name, cat_level))
                    continue

                if str(cat_name).startswith("Basic Novice"):
                    cat_level = model.CategoryLevel.NOVICE_BASIC
                elif str(cat_name).startswith("Intermediate Novice"):
                    cat_level = model.CategoryLevel.NOVICE_INTERMEDIATE

                if cat_level == model.CategoryLevel.NOTDEFINED:
                    cat_level = model.CategoryLevel.NOVICE_ADVANCED

                cat_id = cat_type.ODF() + cat_level.ODF() + cat_gender.ODF()
                if cat_id in category_numbers:
                    category_numbers[cat_id] += 1
                else:
                    category_numbers[cat_id] = 0
                categories_dict[cat_name] = model.Category(cat_name, cat_type, cat_level, cat_gender, category_numbers[cat_id])
        except Exception as e:
            print('Error while converting categories.')
            print(e)
        finally:
            cats_file.close()


        try:
            pars_file = open(input_participants, 'r')
            deu_athlete_reader = csv.DictReader(pars_file)
            check_field_names = True

            next_is_male_partner = False
            par_ids = set()

            @dataclass
            class CoupleEntries:
                couple: model.Couple
                categories: Set[model.Category]
            couple_dict: Dict[str, CoupleEntries] = {} # safe a list of couple members (storing ID -> CoupleEntry)
            team_dict: Dict[str, model.ParticipantTeam] = {}  # a map storing (team_id -> team participant), will be added at the end
            person_last = None

            for athlete in deu_athlete_reader:
                # print(par)

                field_names = ['Wettbewerb/Prüfung', 'Team ID', 'Team Name', 'ID ( ehm. Sportpassnr.)', 'Name', 'Vorname', 'Geb. Datum', 'Vereinskürzel']
                # check if all csv field names exist
                if check_field_names:
                    missing_field_name_found = False
                    for field_name in field_names:
                        if field_name not in athlete:
                            print('Error: Invalid participant csv file. Missing column "%s"' % field_name)
                            missing_field_name_found = True
                    if missing_field_name_found:
                        break
                    check_field_names = False

                par_category = athlete['Wettbewerb/Prüfung'].strip()
                par_team_id = athlete['Team ID'].strip().replace(" ","")
                par_team_name = athlete['Team Name'].strip()
                par_id = athlete['ID ( ehm. Sportpassnr.)'].strip()
                par_family_name = athlete['Name'].strip()
                par_first_name = athlete['Vorname'].strip()
                par_bday = athlete['Geb. Datum'].strip()
                par_bday = self.convert_date(par_bday)
                par_club_abbr = athlete['Vereinskürzel'].strip()
                par_role = athlete['Rolle'].strip()
                par_role = model.Role.from_value(par_role if par_role else 'TN', model.DataSource.DEU)
                par_place_status = athlete['Platz/Status'].strip()
                par_points = athlete['Punkte'].strip()

                if not par_id:
                    par_id = '888888'

                if par_id in self.unknown_ids:
                    offset = self.unknown_ids[par_id]
                    self.unknown_ids[par_id] += 1
                    par_id = str(int(par_id) + offset)

                cat = None
                if par_category in categories_dict:
                    cat = categories_dict[par_category]
                else:
                    print('Warning: Cannot find category "%s" for athlete "%s %s". Skipping athlete.' % (par_category, par_first_name, par_family_name))
                    continue

                cat_type = cat.type
                cat_gender = cat.gender
                cat_level = cat.level

                if not (par_first_name and par_family_name) and not par_team_name:
                    print('Warning: Athlete name or team name is missing.')
                    print(athlete)
                    print('Skipping athlete.')

                # guess athlete gender
                couple_found = False
                par_gender = model.Gender.FEMALE # default e.g. for sys teams
                if cat_type in [model.CategoryType.PAIRS, model.CategoryType.ICEDANCE]:
                    if par_team_id:
                        if par_team_id.endswith(str(par_id)): # team id ends with male team id
                            par_gender = model.Gender.MALE
                        elif par_team_id.startswith(str(par_id)):
                            par_gender = model.Gender.FEMALE
                        else:
                            print("Error: Unable to add couple. ID cannot be found in team id for following participant: %s" % str(athlete))
                            continue
                        if next_is_male_partner and par_gender == model.Gender.MALE:
                            par_id_last = person_last.id
                            if par_team_id.startswith(par_id_last):
                                couple_found = True
                        next_is_male_partner = False
                    else: # no team id set -> assume: first is female, second is male
                        if next_is_male_partner:
                            par_gender = model.Gender.MALE
                            next_is_male_partner = False
                            couple_found = True
                        else:
                            next_is_male_partner = True
                else:
                    if cat_gender != model.Gender.TEAM: # single skater -> use category gender
                        par_gender = cat_gender
                    if next_is_male_partner:
                        print('Error: Skipping athlete. No partner can be found for: %s' % str(person_last))
                    next_is_male_partner = False

                if par_club_abbr in club_dict:
                    par_club = club_dict[par_club_abbr]
                elif par_club_abbr in regions:
                    par_club = model.Club("", "", par_club_abbr)
                else:
                    print('Error: Club not found: "%s". Cannot derive nation for following athlete.')
                    print(athlete)
                    print('Skipping athlete.')
                    continue

                # avoide duplicate persons
                person = model.Person(par_id, par_family_name, par_first_name, par_gender, par_bday, par_club)
                if par_id not in par_ids:
                    # add athletes data
                    for output in outputs:
                        output.add_person(person)
                    par_ids.add(par_id)

                # add participants
                par = None

                if cat_type in [model.CategoryType.MEN, model.CategoryType.WOMEN, model.CategoryType.SINGLES]:
                    par = model.ParticipantSingle(person, cat, par_role)
                else: # couple or team
                    if cat_type == model.CategoryType.SYNCHRON:
                        if par_team_id in team_dict:
                            team_dict[par_team_id].team.persons.append(person)
                        else:
                            team = model.Team(par_team_id, par_team_name, person.club, [person])
                            team_dict[par_team_id] = model.ParticipantTeam(team, cat, par_role)
                        continue # add teams in the end
                    else: # couple
                        if next_is_male_partner:
                            person_last = person
                            continue

                        couple = None
                        if couple_found:  # couple without team id
                            # fix team id for couples
                            par_team_id = person_last.id + '-' + par_id
                            couple = model.Couple(person_last, person)
                            couple_found = False
                        elif par_team_id not in couple_dict:
                            if par_gender == model.Gender.MALE:
                                couple = model.Couple(None, person)
                            else:
                                couple = model.Couple(person, None)
                        else:
                            couple_dict[par_team_id].categories.add(cat)
                        if couple:  # new couple
                            if par_team_id not in couple_dict:
                                couple_dict[par_team_id] = CoupleEntries(couple, categories={cat})
                            else:
                                couple_dict[par_team_id].categories.add(cat)

                        if par_gender == model.Gender.MALE:
                            couple_dict[par_team_id].couple.partner_2 = person
                        else:
                            couple_dict[par_team_id].couple.partner_1 = person

                        continue # add couples in the end

                person_last = person

                if par == None:
                    print("Error: unable to create participant")
                    continue

                par.status = par_place_status
                par.points = par_points
                for output in outputs:
                    output.add_participant(par)

            for couple_entries in couple_dict.values():
                couple = couple_entries.couple
                if (couple.partner_1 and couple.partner_2 and
                        couple.partner_1.id and couple.partner_2.id):
                    for couple_cat in couple_entries.categories:
                        for output in outputs:
                            output.add_participant(model.ParticipantCouple(couple, couple_cat, model.Role.ATHLETE))
                else:
                    print("Error: Incomplete couple in category: %s" % str(couple.cat.name))
                    persons = [person for person in [couple.couple.partner_1, couple.couple.partner_2] if person]
                    for person in persons:
                        print(f"Skipping {person.name}")

            for team in team_dict.values():
                for output in outputs:
                    output.add_participant(team)

            # write files
            for output in outputs:
                output.write_file()

        except Exception as e:
            print('Error while parsing participants')
            traceback.print_exc()
        finally:
            pars_file.close()

if __name__ == '__main__':
    exit(DeuMeldeformularCsv().convert(input_DEU_participant_csv_file_path,
                                             input_DEU_club_csv_file_path,
                                             input_DEU_categories_csv_file_path,
                                             input_DEU_competition_info_csv_file_path, [
                                                # output.PersonCsvOutput(output_athletes_file_path),
                                                output.ParticipantCsvOutput(output_participant_file_path),
                                                output.OdfParticOutput(output_odf_participant_dir)
                                           ]
                                           ))
else:
    print = logging.info

