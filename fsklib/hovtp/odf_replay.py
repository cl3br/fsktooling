import mysql.connector
import getpass
from fsklib.hovtp.base import OdfSender


class OdfFsmReader:
    def __init__(self, db_name, where='OdfMessageType = "DT_CUMULATIVE_RESULT"', url = '127.0.0.1', user = 'sa'):
        pw = getpass.getpass("MySQL-Server-Password: ")
        self.connection = mysql.connector.connect(user=user, password=pw, host=url, database=db_name)
        self.cursor = self.connection.cursor()
        where_statement = f"WHERE {where} " if where else ""
        self.cursor.execute("SELECT Id, Message, OdfMessageType, Version, CreationStamp "
                            "FROM odfmessage " +
                            where_statement +
                            "ORDER BY CreationStamp ASC")

    def __iter__(self):
        return self.cursor.__iter__()

    def __del__(self):
        # close database connection
        self.connection.close()


def main():
    sender = OdfSender("127.0.0.1", "11111")

    reader = OdfFsmReader("gbb22_20221106_final", where="")
    for odf in reader:
        import time
        #time.sleep(0.1)
        print(f"Send {odf[2]}")
        sender.send_odf(odf[1], odf[2])


if __name__ == "__main__":
    main()

