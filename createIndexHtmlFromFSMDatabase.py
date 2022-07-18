import mysql.connector
import io

cat_type_to_class = {
    0: 'men',
    1: 'women',
    2: 'pairs',
    3: 'icedance',
    4: 'synchron',
}

con = mysql.connector.connect(user='sa', password='fsmanager', host='127.0.0.1', database='test')

cursor = con.cursor()

query = "SELECT table_name FROM information_schema.tables WHERE table_schema = 'test'"
cursor.execute(query)

# print all database tables
print("Tables:")
for table_name in cursor:
    print(table_name)

# Get competition data
cursor.execute("SELECT Setting_Id, Name FROM competition")
(comp_setting_id, comp_name) = cursor.fetchone()
cursor.execute("SELECT Place, RinkName, StartDate, EndDate FROM competitionsetting")
(place, rink, start, end) = cursor.fetchone()

# html head
html = "<html><head>\n"
html += "  <title>" + comp_name + "</title>\n"
html += "  <meta name='DESCRIPTION' content='Event Results for " + comp_name + "'>\n"
html += "  <meta name='KEYWORDS' content='ISU, figure, skating, ice, skate, jump, spin, steps, competition, result, ladies, men, pairs, dance'>\n"
html += "  <link rel='stylesheet' href='styles.css'>\n"
html += "</head>\n"

def get_date(datetime) -> str:
    return datetime.strftime("%d.%m.%Y")

# html content - top - competition details
html += "<body>\n"
html += '  <div class="main_container">'
html += "    <table class=competition_header>"
html += '      <tr>\n'
html += '        <td class="competition_info header_left">\n'
html += '        </td>\n'
html += '        <td class="competition_info header_center">\n'
html += '           <h1>' + comp_name + '</h1>\n'
html += '           <h3>' + place + '</h3>\n'
html += '           <h3>' + get_date(start) + ' - ' + get_date(end) + '</h3>\n'
html += '           <h3>' + rink + '</h3>\n'
html += '        </td>\n'
html += '        <td class="competition_info header_right">\n'
html += '        </td>\n'
html += '      </tr>\n'
html += '    </table>\n'


html += '    <table class="categories">\n'
html += '      <thead><tr>\n'
html += '        <th>Kategorie</th>\n'
html += '        <th>Segment</th>\n'
html += '        <th></th>\n'
html += '        <th></th>\n'
html += '        <th></th>\n'
html += '        <th></th>\n'
html += '      </thead></tr>\n'

# categories and segemtens
cursor.execute("SELECT Id, Name, Level, Type FROM category")
for (cat_id, cat_name, cat_level, cat_type) in list(cursor):
    html += '      <tr class="category ' + cat_type_to_class[cat_type] + '">' \
            '<td>' + cat_name + '</td><td/>' \
            '<td>Meldungen</td>' \
            '<td>Ergebnis</td>' \
            '<td/><td/></tr>\n'
    cursor.execute("SELECT Name, ShortName, SegmentType FROM segment WHERE Category_Id = " + str(cat_id))
    for (seg_name, seg_short_name, seg_type) in cursor:
        html += '      <tr class="segment ' + cat_type_to_class[cat_type] + '"><td/>' \
                '<td>' + seg_name + '</td>' \
                '<td>Offizielle</td>' \
                '<td>Startreihenfolge</td>' \
                '<td>Detailiertes Ergebnis</td>' \
                '<td>Preisrichter-Noten</td>' \
                '</tr>\n'
html += '    </table>\n'

# close database connection
con.close()

# footer
html += '    <div class="footer">\n' \
        '      <p><a href="http://www.eissport-berlin.de">Zurück zur Homepage</a></p>\n' \
        '      <p><a href="mailto:info@eissport-berlin.de">Kontakt</a></p>\n' \
        '    </div>\n' \
        '  </div>\n' \
        '</body>\n</html>\n'

print(html)

# write html file to disk
with io.open('index.html', 'w', encoding="utf-8") as f:
    f.write(html)