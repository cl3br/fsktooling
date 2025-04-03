import mysql.connector.connection
from openpyxl import Workbook
from xml.etree import ElementTree as ET
from datetime import date


def extract(db_connection: mysql.connector.connection, output_file_path, competition_code="", debug=False):

    cursor = db_connection.cursor()
    processed_categories = []
    data = list()
    data.append(["Wettbewerb/Prüfung",
                 "Team ID",
                 "Team Name",
                 "ID ( ehm. Sportpassnr.)",
                 "Name",
                 "Vorname",
                 "Geb. Datum",
                 "Vereinskürzel",
                 "Rolle",
                 "Platz/Status",
                 "Punkte"
    ])

    def check_attribute(attributes: dict, key):
        if not key in attributes:
            return ""
        return attributes[key]

    def check_id(attributes: dict) -> str:
        if not "IFId" in attributes:
            return ""

        id = attributes["IFId"]
        try:
            id_int = int(id)
            if id_int >= 999999:
                return "999999"
            elif id_int >= 888888:
                return "888888"
            else:
                return id
        except:
            return id

    def check_birthday(attributes: dict):
        if not "BirthDate" in attributes:
            return ""

        try:
            return date.fromisoformat(attributes["BirthDate"])
        except:
            return ""

    # participant result from ODF messages
    cursor.execute("SELECT Id, Message, OdfMessageType, Version, CreationStamp "
                   "FROM odfmessage "
                   "WHERE OdfMessageType = \"DT_CUMULATIVE_RESULT\" "
                   "ORDER BY CreationStamp DESC")
    for (odf_id, odf_message, odf_type, odf_message_version, odf_stamp) in list(cursor):
        root = ET.fromstring(odf_message)
        desc = root.find("Competition/ExtendedInfos/SportDescription")
        cat_name = desc.attrib["EventName"]

        if cat_name in processed_categories:
            continue

        if debug:
            print(cat_name)
        processed_categories.append(cat_name)

        for result in root.findall("Competition/Result"):
            rank = ""
            points = ""
            if "Rank" not in result.attrib:
                rank = "zurückgezogen"
            elif "Result" in result.attrib:
                rank = result.attrib["Rank"]
                points = result.attrib["Result"]
            else:
                print(f"No points detected in {result}")
                continue

            athletes = list(result.findall("Competitor/Composition/Athlete/Description"))
            team_id = ""
            if not athletes:
                # sys team
                res_desc = result.find("Competitor/Description")
                a = res_desc.attrib
                d = [cat_name, check_id(a), check_attribute(a, "TeamName"), "", "", "", "", "", "TN", rank, points]
                if debug:
                    print(d)
                data.append(d)
            elif len(athletes) == 2:
                # team id for pairs / dance
                team_id = "-".join([check_id(athlete.attrib) for athlete in athletes])
                if len(team_id) < 11:
                    team_id = ""

            for athlete in athletes:
                a = athlete.attrib
                family_name = check_attribute(a, "FamilyName")
                given_name = check_attribute(a, "GivenName")
                d = [cat_name, team_id, "", check_id(a), family_name, given_name, check_birthday(a), "", "TN", rank, points]
                if debug:
                    print(d)
                error = False
                if not rank and not points:
                    print("Warning - No result for:")
                    error = True
                if not family_name or not given_name:
                    print("Warning - Family name or given name is missing for:")
                    error = True

                if error:
                    print(d)
                    print("Skipping athlete!")
                else:
                    data.append(d)


    map_officials_from_FSM_to_DEU = {0 : "SR",
                                     1 : "PR",
                                     2 : "TC",
                                     3 : "TS",
                                     4 : "TI",
                                     5 : "DO",
                                     6 : "RO"}

    official_data = set()
    # get competition id
    where = f" WHERE ShortName = \"{competition_code}\"" if competition_code else ""
    cursor.execute("SELECT Id FROM competition" + where)
    row = cursor.fetchone()
    if row:
        competition_id = row[0]
    else:
        print("ERROR: No competition found in database")
        return

    # get officials from categories and segments
    cursor.execute(f"SELECT Id, Name, Level, Type, SortOrder FROM category WHERE Competition_Id = {str(competition_id)}")
    for (cat_id, cat_name, cat_level, cat_type, cat_order) in list(cursor):
        cursor.execute("SELECT Id, Name, ShortName, SegmentType FROM segment WHERE Category_Id = " + str(cat_id))
        if debug:
            print(cat_name)

        for (seg_id, seg_name, seg_short_name, seg_type) in list(cursor):
            cursor.execute("SELECT person.FederationId, person.FirstName, person.LastName, person.BirthDate, officialinsegment.OfficialFunction "
                           "FROM officialinsegment "
                           "    JOIN person ON person.id = officialinsegment.Person_Id "
                          f"WHERE officialinsegment.Segment_Id = {str(seg_id)} ")
            if debug:
                print(seg_name)

            for (fed_id, first_name, last_name, birthday, function) in list(cursor):
                d = (cat_name, "", "", fed_id, last_name, first_name, birthday, "", map_officials_from_FSM_to_DEU[function], "", "")
                if debug:
                    print(d)
                official_data.add(d)

    data.extend([list(d) for d in official_data])

    # close database connection
    db_connection.close()

    # create excel file
    wb = Workbook()
    ws = wb.active
    for row in data:
        ws.append(row)
    wb.save(output_file_path)




