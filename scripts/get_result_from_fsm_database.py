import mysql.connector

from fsklib.fsm.result import extract

if __name__ == "__main__":
    con = mysql.connector.connect(user='sa', password='fsmanager', host='127.0.0.1', database='database')
    output_csv_file_name = "result.xlsx"
    extract(con, output_csv_file_name)
