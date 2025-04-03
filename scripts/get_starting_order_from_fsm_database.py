import mysql.connector

from fsklib.output import ParticipantCsvOutput
from fsklib import model

con = mysql.connector.connect(user='sa', password='fsmanager', host='127.0.0.1', database='test')

cursor = con.cursor()

csv = ParticipantCsvOutput('starting_order.csv')


# categories and segments
cursor.execute("SELECT Id, Name, Level, Type, SortOrder FROM category")
for (cat_id, cat_name, cat_level, cat_type, cat_order) in list(cursor):
    cursor.execute("SELECT Id, Name, ShortName, SegmentType FROM segment WHERE Category_Id = " + str(cat_id))
    print(cat_name)
    cat_type = model.CategoryType.from_value(cat_type, model.DataSource.FSM)
    cat_level = model.CategoryLevel.from_value(cat_level, model.DataSource.FSM)
    cat = model.Category(cat_name, cat_type, cat_level, cat_type.to_gender(), cat_order)

    for (seg_id, seg_name, seg_short_name, seg_type) in list(cursor):
        print(seg_name)
        seg = model.Segment(seg_name, seg_short_name, model.SegmentType.from_value(seg_type, model.DataSource.FSM))
        if cat_type in [model.CategoryType.MEN, model.CategoryType.WOMEN]: # singles
            cursor.execute("SELECT person.FederationId, person.FirstName, person.LastName, person.BirthDate, person.Gender, person.Nation_Id, club.Name, person.Club, competitorresult.StartNumber "
                           "FROM competitorresult "
                           "    JOIN entry ON competitorresult.Entry_Id = entry.Id "
                           "    JOIN single ON entry.Competitor_Id = single.Competitor_Id_Pk "
                           "    JOIN person ON person.Id = single.Person_Id "
                           "    JOIN club ON club.ShortName = person.Club "
                          f"WHERE competitorresult.Segment_Id = {str(seg_id)} "
                           "ORDER BY competitorresult.StartNumber ASC")

            for (id, first_name, last_name, bday, gender, nation, club_name, club_abbr, start_number) in cursor:
                print("%d - %s %s" % (start_number, first_name, last_name))
                club = model.Club(club_name, club_abbr, nation)
                couple = model.Person(id, last_name, first_name, model.Gender.from_value(gender, model.DataSource.FSM), bday, club)
                participant = model.ParticipantSingle(couple, cat)
                csv.add_participant_with_segment_start_number(participant, seg, start_number)

        elif cat_type in [model.CategoryType.PAIRS, model.CategoryType.ICEDANCE]: # pairs
            cursor.execute("SELECT partner1.FederationId, partner1.FirstName, partner1.LastName, partner1.BirthDate, partner1.Gender, partner1.Nation_Id, club1.Name, partner1.Club,"
                           "       partner2.FederationId, partner2.FirstName, partner2.LastName, partner2.BirthDate, partner2.Gender, partner2.Nation_Id, club2.Name, partner2.Club,"
                           "       competitorresult.StartNumber "
                           "FROM competitorresult "
                           "    JOIN entry ON competitorresult.Entry_Id = entry.Id "
                           "    JOIN couple ON entry.Competitor_Id = couple.Competitor_Id_Pk "
                           "    JOIN person AS partner1 ON partner1.Id = couple.PersonLady_Id "
                           "    JOIN person AS partner2 ON partner2.Id = couple.PersonMale_Id "
                           "    JOIN club AS club1 ON club1.ShortName = partner1.Club "
                           "    JOIN club AS club2 ON club2.ShortName = partner2.Club "
                           "WHERE competitorresult.Segment_Id = " + str(seg_id))

            for (id1, first_name1, last_name1, bday1, gender1, nation1, club_name1, club_abbr1, id2, first_name2, last_name2, bday2, gender2, nation2, club_name2, club_abbr2, start_number) in cursor:
                print("%d - %s %s / %s %s" % (start_number, first_name1, last_name1, first_name2, last_name2))
                club1 = model.Club(club_name1, club_abbr1, nation1)
                club2 = model.Club(club_name2, club_abbr2, nation2)
                partner1 = model.Person(id1, last_name1, first_name1, model.Gender.from_value(gender1, model.DataSource.FSM), bday1, club1)
                partner2 = model.Person(id2, last_name2, first_name2, model.Gender.from_value(gender2, model.DataSource.FSM), bday2, club2)
                couple = model.Couple(partner1, partner2)
                participant = model.ParticipantCouple(couple, cat)
                csv.add_participant_with_segment_start_number(participant, seg, start_number)
        elif cat_type == model.CategoryType.SYNCHRON:
            cursor.execute(
                "SELECT synchronizedteam.FederationId, synchronizedteam.Name, synchronizedteam.Nation_Id, club.Name, synchronizedteam.Club, competitorresult.StartNumber "
                "FROM competitorresult "
                "    JOIN entry ON competitorresult.Entry_Id = entry.Id "
                "    JOIN synchronizedteam ON entry.Competitor_Id = synchronizedteam.Competitor_Id_Pk "
                "    JOIN club ON club.ShortName = synchronizedteam.Club "
                "WHERE competitorresult.Segment_Id = " + str(seg_id))

            for (id, name, nation, club_name, club_abbr, start_number) in cursor:
                print("%d - %s" % (start_number, name))
                club = model.Club(club_name, club_abbr, nation)
                sys_team = model.Team(id, name, club, [])
                participant = model.ParticipantTeam(sys_team, cat)
                csv.add_participant_with_segment_start_number(participant, seg, start_number)
        for x in cursor:
            print(x)

csv.write_file()

# close database connection
con.close()
