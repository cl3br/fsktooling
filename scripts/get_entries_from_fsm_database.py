from typing import List

import mysql.connector

from fsklib import model
from fsklib.output import ParticipantCsvOutput

con = mysql.connector.connect(user='sa', password='fsmanager', host='127.0.0.1', database='kbb24')

cursor = con.cursor()

fake_start_number=True

if fake_start_number:
    csv = ParticipantCsvOutput('fake_starting_order.csv')
else:
    csv = ParticipantCsvOutput('entries.csv')

# categories and segments
cursor.execute("SELECT Id, Name, Level, Type, SortOrder FROM category")
for (cat_id, cat_name, cat_level, cat_type, cat_order) in list(cursor):
    print(cat_name)
    cat_type: model.CategoryType | None = model.CategoryType.from_value(cat_type, model.DataSource.FSM)
    if cat_type is None:
        cat_type = model.CategoryType.SINGLES
    cat_level = model.CategoryLevel.from_value(cat_level, model.DataSource.FSM)
    if cat_level is None:
        cat_level = model.CategoryLevel.SENIOR
    cat = model.Category(cat_name, cat_type, cat_level, cat_type.to_gender(), number=cat_order)

    cursor.execute(f"SELECT Name, ShortName, SegmentType FROM segment WHERE Category_Id = {str(cat_id)} ORDER BY SegmentType ASC")
    segments: List[model.Segment] = []
    for (name, short_name, segment_type) in cursor:
        segments.append(model.Segment(name, short_name, model.SegmentType.from_value(segment_type, model.DataSource.FSM)))

    if cat_type in [model.CategoryType.MEN, model.CategoryType.WOMEN]: # singles
        cursor.execute("SELECT person.FederationId, person.FirstName, person.LastName, person.BirthDate, person.Gender, person.Nation_Id, person.Club "
                       "FROM entry "
                       "    JOIN single ON entry.Competitor_Id = single.Competitor_Id_Pk "
                       "    JOIN person ON person.Id = single.Person_Id "
                      f"WHERE entry.Category_Id = {str(cat_id)} "
                       "ORDER BY entry.Id ASC")

        for (number, (id, first_name, last_name, bday, gender, nation, club_abbr)) in enumerate(list(cursor), 1):
            print("%s %s" % (first_name, last_name))
            if club_abbr is None:
                club_abbr = ""
            cursor.execute("SELECT Name FROM club WHERE ShortName = '" + club_abbr + "'")
            result = cursor.fetchone()
            club_name = result[0] if result is not None else ""
            cursor.reset()
            person = model.Person(id, first_name, last_name, model.Gender.from_value(gender, model.DataSource.FSM), bday, model.Club(club_name, club_abbr, nation))
            participant = model.ParticipantSingle(cat, person)
            if fake_start_number:
                for segment in segments:
                    csv.add_participant_with_segment_start_number(participant, segment, number)
            else:
                csv.add_participant(participant)

    elif cat_type in [model.CategoryType.PAIRS, model.CategoryType.ICEDANCE]:  # pairs
        cursor.execute("SELECT partner1.FederationId, partner1.FirstName, partner1.LastName, partner1.BirthDate, partner1.Gender, partner1.Nation_Id, partner1.Club,"
                       "       partner2.FederationId, partner2.FirstName, partner2.LastName, partner2.BirthDate, partner2.Gender, partner2.Nation_Id, partner2.Club "
                       "FROM entry "
                       "    JOIN couple ON entry.Competitor_Id = couple.Competitor_Id_Pk "
                       "    JOIN person AS partner1 ON partner1.Id = couple.PersonLady_Id "
                       "    JOIN person AS partner2 ON partner2.Id = couple.PersonMale_Id "
                       "WHERE entry.Category_Id = " + str(cat_id))

        for (number, (id1, first_name1, last_name1, bday1, gender1, nation1, club_abbr1, id2, first_name2, last_name2, bday2, gender2, nation2, club_abbr2)) in enumerate(list(cursor), 1):
            print("%s %s / %s %s" % (first_name1, last_name1, first_name2, last_name2))
            if club_abbr1 is None:
                club_abbr1 = ""
            cursor.execute("SELECT Name FROM club WHERE ShortName = '" + club_abbr1 + "'")
            result = cursor.fetchone()
            club_name1 = result[0] if result is not None else ""
            cursor.reset()
            if club_abbr2 is None:
                club_abbr2 = ""
            cursor.execute("SELECT Name FROM club WHERE ShortName = '" + club_abbr2 + "'")
            result = cursor.fetchone()
            club_name2 = result[0] if result is not None else ""
            club1 = model.Club(club_name1, club_abbr1, nation1)
            club2 = model.Club(club_name2, club_abbr2, nation2)
            partner1 = model.Person(id1, first_name1, last_name1, model.Gender.from_value(gender1, model.DataSource.FSM), bday1, club1)
            partner2 = model.Person(id2, first_name2, last_name2, model.Gender.from_value(gender2, model.DataSource.FSM), bday2, club2)
            couple = model.Couple(partner1, partner2)
            participant = model.ParticipantCouple(cat, couple)
            if fake_start_number:
                for segment in segments:
                    csv.add_participant_with_segment_start_number(participant, segment, number)
            else:
                csv.add_participant(participant)
    elif cat_type == model.CategoryType.SYNCHRON:
        cursor.execute(
            "SELECT synchronizedteam.FederationId, synchronizedteam.Name, synchronizedteam.Nation_Id, synchronizedteam.Club "
            "FROM entry "
            "    JOIN synchronizedteam ON entry.Competitor_Id = synchronizedteam.Competitor_Id_Pk "
            "WHERE entry.Category_Id = " + str(cat_id))

        for (number, (id, name, nation, club_abbr)) in enumerate(list(cursor), 1):
            print("%s" % (name))
            if club_abbr is None:
                club_abbr = ""
            cursor.execute("SELECT Name FROM club WHERE ShortName = '" + club_abbr + "'")
            result = cursor.fetchone()
            club_name = result[0] if result is not None else ""
            cursor.reset()
            club = model.Club(club_name, club_abbr, nation)
            sys_team = model.Team(id, name, club, [])
            participant = model.ParticipantTeam(cat, sys_team)
            if fake_start_number:
                for segment in segments:
                    csv.add_participant_with_segment_start_number(participant, segment, number)
            else:
                csv.add_participant(participant)

# close database connection
con.close()

csv.write_file()

