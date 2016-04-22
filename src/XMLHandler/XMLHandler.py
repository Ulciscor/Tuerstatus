#!/usr/bin/python3
# -*- coding: utf-8 -*-

# Gets a set number of next dates and exports them either to a FTP-Server or dropbox (witchever is set) as an XML-File
# Is called regularly by a cron job

# IMPORTS
import datetime
import sys
import time
import ftplib
import dropbox
import numpy as np

import sqlite3 as lite
from xml.sax.saxutils import escape


# Database
DB_PATH = '/var/www/db.sqlite3'

# Constants
AMOUNT = '5' # Number of dates that are fetched
FILENAME = 'dates.xml'
REFRESH = 10 # Refresh time in seconds

# FTP
FTP_SERVER =  '' #'ftp.hostedftp.com'
USER = ''
PASSWORD = ''

# Dropbox
DB_TOKEN = ''

# Global variables
con = None          # For a database connection

def main():
    oldDates = []
    boolFirst = True
    boolChanged = True
    
    while 1:
        time.sleep(REFRESH)
        # Get's next date and time from database
        stamp = str(int(time.time()))  # Unix timestamp
        nextDates = doDBRequest('SELECT start, end, type, started, user FROM tuerstatus_date WHERE datetime(end)>=datetime(' + stamp + ',\'unixepoch\', \'localtime\') AND deleted !=1 ORDER BY datetime(start) LIMIT ' + AMOUNT, False)

        if not(boolFirst):
            # Check if any changes have happend
            boolChanged = not(np.array_equal(oldDates, nextDates))
        else:
            # Set true on first call
            boolFirst = False

        if boolChanged:
            # print('Changes')
            # Write dates to XML file
            with open(FILENAME, encoding='utf-8', mode='w') as f:
                f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
                f.write('<dates>')
                for i in range(len(nextDates)):
                    date = nextDates[i]
                    dateStr = str(date)
                    datelist = [x.strip("[( u)]\'") for x in dateStr.split(',')]
                    f.write('''
                        <date>
                            <start>{0}</start>
                            <end>{1}</end>
                            <type>{2}</type>
                            <started>{3}</started>
                            <user>{4}</user>
                        </date>
                    '''.format(datelist[0],datelist[1],datelist[2],datelist[3],datelist[4]))
                f.write('</dates>')
                f.close()

            # Write file to FTP Server
            try:
                session = ftplib.FTP(FTP_SERVER, USER, PASSWORD)
                file = open(FILENAME,'rb')                  # file to send
                session.cwd('/xml')
                # print(str(session.pwd()))
                session.storbinary('STOR '+FILENAME, file)     # send the file
                file.close()                                    # close file and FTP
                session.quit()
            except ftplib.Error as e:
                print("Error: ", e.args[0])
                sys.exit(1)
            # Save old data for comparison
            oldDates = nextDates
            

    ##    # Write file to dropbox
    ##    try:
    ##        dbc = dropbox.client.DropboxClient(DB_TOKEN)
    ##        uploadFile = open(FILENAME, 'rb')              # Datei öffnen,
    ##        response = dbc.put_file(FILENAME, uploadFile, True)  # ... hochladen
    ##        # print('uploaded:', response)
    ##        uploadFile.close()                          # ... und schließen
    ##    except dropbox.Error as e:
    ##        print("Error: ", e.args[0])
    ##        sys.exit(1)

def doDBRequest(sqlCommand, boolWrite):
    try:
        global con
        con = lite.connect(DB_PATH)
        cur = con.cursor()
        cur.execute(sqlCommand)
        if(boolWrite):
            con.commit()
        else:       
            ListSQL = cur.fetchall()
    except lite.Error as e:
        print("Error: ", e.args[0])
        sys.exit(1)
    finally:
        if con:
            con.close()
            if(not boolWrite):
                return ListSQL

if __name__ == '__main__':
    main()
