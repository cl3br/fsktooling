import os
import datetime
import traceback
import csv
from typing import List

import model
import output

# settings
input_DEU_participant_csv_file_path = 'BJM22/deu_athletes.csv'
input_DEU_club_csv_file_path = './DEU/clubs-DEU.csv'
input_DEU_categories_csv_file_path = 'BJM22/categories.csv'
output_athletes_file_path = './BJM22Test/person.csv'
output_participant_file_path = './BJM22Test/participants.csv'
output_odf_participant_file_path = './BJM22Test/DT_PARTIC_UPDATE.xml'


class DeuMeldeformularConverter:
    # static member
    deu_type_to_isucalcfs = {'Herren' : 'S', 'Damen' : 'S', 'Einzellauf': 'S', 'Paarlaufen' : 'P', 'Eistanzen' : 'D', 'Synchron': 'T'}
    deu_gender_to_isucalcfs = {'Herren' : 'M', 'Damen' : 'F', 'Einzellauf': 'F', 'Paarlaufen' : 'T', 'Eistanzen' : 'T', 'Synchron': 'T'}
    deu_level_to_isucalcfs = {'Meisterklasse' : 'S', 'Juniorenklasse' : 'J', 'Jugendklasse' : 'J', 'Nachwuchsklasse' : 'V', 'nicht definiert' : 'O'} # Intermediate Novice => I; Basic Novice => R

    def convert(input_participants: str, input_clubs: str, input_categories: str, outputs: List[output.OutputBase]):
        if not os.path.isfile(input_participants):
            print('Participants file not found.')
            return 1
        if not os.path.isfile(input_clubs):
            print('Club file not found.')
            return 2
        if not os.path.isfile(input_categories):
            print('Categories file not found.')
            return 3
        
        # read clubs
        try:
            clubs_file = open(input_clubs, 'r')
            club_reader = csv.DictReader(clubs_file, delimiter=';')

            club_dict = {}

            for club in club_reader:
                abbr = club['Abk.']
                club_dict[abbr] = model.Club(club['Name'], abbr, club['Region'])
        except:
            print('Error while parsing clubs.')
        finally:
            clubs_file.close()

        # read categories
        try:
            categories_dict = {}
            cats_file = open(input_categories, 'r')
            cat_reader = csv.DictReader(cats_file)
            for cat_dict in cat_reader:
                cat_name = cat_dict['Wettbewerb/Prüfung']
                cat_deu_type = cat_dict['Disziplin']
                cat_deu_level = cat_dict['Kategorie']
                
                cat_type = DeuMeldeformularConverter.deu_type_to_isucalcfs[cat_deu_type] if cat_deu_type in DeuMeldeformularConverter.deu_type_to_isucalcfs else ''
                cat_gender = DeuMeldeformularConverter.deu_gender_to_isucalcfs[cat_deu_type] if cat_deu_type in DeuMeldeformularConverter.deu_gender_to_isucalcfs else ''
                cat_level = DeuMeldeformularConverter.deu_level_to_isucalcfs[cat_deu_level] if cat_deu_level in DeuMeldeformularConverter.deu_level_to_isucalcfs else ''

                if not cat_type or not cat_gender or not cat_level:
                    print('Warning: Unable to convert category following %s|%s|%s' % (cat_name, cat_name, cat_level))
                else:
                    categories_dict[cat_name] = model.Category(cat_name, cat_type, cat_level, cat_gender)
                    # categories_dict[cat_name] = {'Kategorie-Name' : cat_name, 'Kategorie-Typ' : cat_type, 'Kategorie-Geschlecht': cat_gender, 'Kategorie-Level': cat_level}
        except:
            print('Error while converting categories.')
        finally:
            cats_file.close()
            

        try:
            pars_file = open(input_participants, 'r')
            deu_athlete_reader = csv.DictReader(pars_file)
            check_field_names = True

            next_is_male_partner = False
            team_dict = {} # a map storing (team_id -> team participant), will be added at the end
            couple_dict = {} # safe a list of couple members (storing ID -> par), if partner is found -> create participant and delete from this list
            athlete_last = None

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
                par_team_id = athlete['Team ID'].strip()
                par_team_name = athlete['Team Name'].strip()
                par_id = athlete['ID ( ehm. Sportpassnr.)'].strip()
                par_family_name = athlete['Name'].strip()
                par_first_name = athlete['Vorname'].strip()
                par_bday = athlete['Geb. Datum'].strip()
                par_bday = datetime.datetime.fromisoformat(par_bday) if par_bday else None
                par_club_abbr = athlete['Vereinskürzel'].strip()
                par_place_status = athlete['Platz/Status'].strip()
                par_points = athlete['Punkte'].strip()

                cat = None
                if par_category in categories_dict:
                    cat = categories_dict[par_category]
                else:
                    print('Warning: Cannot find category "%s" for athlete "%s %s". Skipping athlete.' % (par_category, par_first_name, par_family_name))
                    continue

                cat_type = cat.type
                cat_gender = cat.gender
                cat_level = cat.level

                # guess athlete gender
                par_gender = 'F'
                couple_found = False
                if cat_type in ['P', 'D']:
                    if par_team_id:
                        if par_team_id.endswith(str(par_id)): # team id ends with male team id
                            par_gender = 'M'
                        elif par_team_id.startswith(str(par_id)):
                            par_gender = 'F'
                        else:
                            print("Error: Unable to add couple. ID cannot be found in team id for following participant: %s" % str(athlete))
                            continue
                        if next_is_male_partner and par_gender == 'M':
                            par_id_last = athlete_last['ID ( ehm. Sportpassnr.)'].strip()
                            if par_team_id.startswith(par_id_last):
                                couple_found = True
                        next_is_male_partner = False
                    else: # no team id set -> assume: first is female, second is male
                        if next_is_male_partner:
                            par_gender = 'M'
                            next_is_male_partner = False
                            couple_found = True
                        else:
                            next_is_male_partner = True
                else:
                    if cat_type != 'T': # single skater -> use category gender
                        par_gender = cat_gender
                    if next_is_male_partner:
                        print('Error: Skipping athlete. No partner can be found for: %s' % str(athlete_last))
                    next_is_male_partner = False

                if par_club_abbr in club_dict:
                    par_club = club_dict[par_club_abbr]
                else:
                    print('Error: Club not found: "%s". Cannot derive nation for following athlete.')
                    print(athlete)
                    print('Skipping athlete.')
                    athlete_last = athlete
                    continue
                
                # add athletes data
                person = model.Person(par_id, par_family_name, par_first_name, par_gender, par_bday, par_club)
                for output in outputs:
                    output.add_person(person)

                # add participants
                par = None

                if cat_type == 'S':
                    par = model.ParticipantSingle(person, cat)
                else: # couple or team
                    if cat_type == 'T': # Synchron
                        if par_team_id in team_dict:
                            team_dict[par_team_id].team.persons.append(person)
                        else:
                            team = model.Team(par_team_id, par_team_name, person.club, [person])
                            team_dict[par_team_id] = model.ParticipantTeam(team, cat)
                        continue # add teams in the end
                    else: # couple
                        if next_is_male_partner:
                            continue
                        # couple without team id
                        couple = None
                        if couple_found:
                            # fix team id for couples
                            par_female_id = athlete_last['ID ( ehm. Sportpassnr.)'].strip()
                            par_female_first_name = athlete_last['Vorname']
                            par_female_family_name = athlete_last['Name']
                            par_female_club_abbr = athlete_last['Vereinskürzel']
                            par_female_bday = athlete_last['Geb. Datum'].strip()
                            par_female_bday = datetime.datetime.fromisoformat(par_female_bday) if par_female_bday else None
                            par_team_id = par_female_id + '-' + par_id
                            person_female = model.Person(par_female_id, par_female_family_name, par_female_first_name, 'F', par_female_bday, club_dict[par_female_club_abbr])
                            couple = model.Couple(person_female, None)
                            couple_found = False
                        elif par_team_id not in couple_dict:
                            if par_gender == 'M':
                                couple = model.Couple(None, person)
                            else:
                                couple = model.Couple(person, None)
                        if couple:
                            couple_dict[par_team_id] = model.ParticipantCouple(couple, cat)
                        
                        if par_gender == 'M':
                            couple_dict[par_team_id].couple.partner_2 = person
                        else:
                            couple_dict[par_team_id].couple.partner_1 = person

                        continue # add couples in the end

                if par == None:
                    print("Error: unable to create participant")
                    continue

                par.status = par_place_status
                par.points = par_points
                for output in outputs:
                    output.add_participant(par)
                    
                athlete_last = athlete

            for couple in couple_dict.values():
                if couple.couple.partner_1.id and couple.couple.partner_2.id:
                    output.add_participant(couple)
                else:
                    print("Error: unable to add following couple: %s" % str(couple))

            for team in team_dict.values():
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
    exit(DeuMeldeformularConverter.convert(input_DEU_participant_csv_file_path, 
                                           input_DEU_club_csv_file_path, 
                                           input_DEU_categories_csv_file_path, [
                                                output.PersonCsvOutput(output_athletes_file_path),
                                                output.ParticipantCsvOutput(output_participant_file_path),
                                                output.OdfParticOutput(output_odf_participant_file_path)
                                           ]
                                           ))

