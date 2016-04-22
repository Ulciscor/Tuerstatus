#!/usr/bin/python
# -*- coding: utf-8 -*-

# IMPORTS
import datetime
import sys
import time

import RPi.GPIO as GPIO
import sqlite3 as lite


GPIO.setwarnings(False)

# Mapping of GPIO Pins
DISPLAY_RS = 7
DISPLAY_E = 8
DISPLAY_DATA = [25, 24, 23, 18]
LED_RED = 16
LED_YELLOW = 20
LED_GREEN = 21
TASTER_MENUE = 12
TASTER_UP = 17
TASTER_DOWN = 27
TASTER_OK = 22
TASTER_STATUS = 5

# Display
DISPLAY_WIDTH = 20  # Character per Line
DISPLAYROWADR = [0x80, 0xC0, 0x94, 0xD4]    # Addresses of the display rows

# Database
DB_PATH = '/var/www/db.sqlite3'

# CONSTANTS
DISPLAY_CHR = True
DISPLAY_CMD = False
E_PULSE = 0.0005
E_DELAY = 0.0005
TASTER_TIME = 0.1  # Time interval for taster loops 
TPS = int((1 / TASTER_TIME) + 1)  # Number for taster loops
DIFF_TO_FROM_DATE = 15 # Default minutes to start of scheduled date from witch on the options in menue change
START_DIFF_MIN = 15  # Default minute distance for delayed start 
END_DIFF_MIN = 3  # Default hour distance for set end
MIN_PER_CLICK = 1  # Default amount minutes per click in time set
STATUS_ARRAY = ['SelfLab','OpenLab']
TIMEOUT = 10 # Timeout in s after if inactive  

# Global variables
toggleClock = True  # Toggle for clock dots
con = None          # For a database connection
statusOpen = False  # if lab is generally open True
# statusDateScheduled = False # Toggle context sensitive menue to start/end date
timeoutTimer =  0   # Timer
timeoutBool = False # Bool to timer
startTimeChanged = datetime.datetime.now()
curWorkingDateID = ''
newFlag = False

def main():
    initGPIO() # DO NOT REMOVE - CAN FUCK UP THE HARDWARE
    display_init()
    menueScreen()
    
def initGPIO():
    GPIO.cleanup()
    GPIO.setmode(GPIO.BCM)
    # Initialising GPIO ports for display 
    GPIO.setup(DISPLAY_E, GPIO.OUT)
    GPIO.setup(DISPLAY_RS, GPIO.OUT)
    for i in range(0, len(DISPLAYROWADR)):
        GPIO.setup(DISPLAY_DATA[i], GPIO.OUT)
    # Initialising GPIO ports for LEDs
    GPIO.setup(LED_RED, GPIO.OUT)
    GPIO.setup(LED_YELLOW, GPIO.OUT)
    GPIO.setup(LED_GREEN, GPIO.OUT)
    # Initialising GPIO ports for taster -- Caution: Pull-Down
    GPIO.setup(TASTER_MENUE, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(TASTER_UP, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(TASTER_DOWN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(TASTER_OK, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(TASTER_STATUS, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    
def display_init():
    lcd_byte(0x33, DISPLAY_CMD)
    lcd_byte(0x32, DISPLAY_CMD)
    lcd_byte(0x28, DISPLAY_CMD)
    lcd_byte(0x0C, DISPLAY_CMD)  
    lcd_byte(0x06, DISPLAY_CMD)
    lcd_byte(0x01, DISPLAY_CMD)
    
def menueScreen():
##    global statusDateScheduled
    global statusOpen
          
    while 1:    
        start = True
        status = True
        
        while start and status:

            # Set base info menue screen
            display_output(1, string_center("Menü drücken"))

            # Update next date constantly 
            showNextDate()
            
            # Update time every second
            updateClock()
        
            # Wait for pressing START button
            for x in range(TPS): 
                if(GPIO.input(TASTER_MENUE) == 1):
                    start = False
                    break
                if(GPIO.input(TASTER_STATUS) == 1):
                    status = False
                    break
                if(GPIO.input(TASTER_OK) == 1) and statusOpen == False:
                    status = False
                    break
                time.sleep(TASTER_TIME)
            
            
        
        # If start has been pressed go to choice screen
        if start == False:
            if statusOpen == False:
                choiceScreenInit()
            else:
                choiceScreenEnd(1)     
        elif status == False and statusOpen == True:
            choiceScreenOpenOrSelfLab()
                
def showNextDate():

    global curWorkingDateID
##    global statusDateScheduled
        
    # Get's next date and time from database
    stamp = str(int(time.time()))  # Unix timestamp
    nextDate = doDBRequest('SELECT start, end, type, id FROM tuerstatus_date WHERE datetime(end)>=datetime(' + stamp + ',\'unixepoch\', \'localtime\') AND deleted !=1 ORDER BY datetime(start) LIMIT 1', False)
    date = str(nextDate)
    datelist = [x.strip("[( u)]\'") for x in date.split(',')]
    
    # Date found
    if date != '[]':
        startTime = datetime.datetime.strptime(datelist[0], '%Y-%m-%d %H:%M:%S')
        endTime = datetime.datetime.strptime(datelist[1], '%Y-%m-%d %H:%M:%S')
        statusStr = str(datelist[2])
        curWorkingDateID = str(datelist[3])

##        if startTime >= (datetime.datetime.now() -
##        datetime.timedelta(minutes=DIFF_TO_FROM_DATE)):
##            statusDateScheduled = True
##        else:
##            statusDateScheduled = False

        display_output(2, startTime.strftime('    %H:%M (%d.%m.)  '))
        display_output(3, endTime.strftime('bis %H:%M (' + STATUS_ARRAY[int(statusStr)-1]+')'))
    else: # No date found
        display_output(2, string_center("Keine Termine"))
        display_output(3, string_center("vorhanden"))

def choiceScreenInit():
    
    resetTimeoutTimer()
    
    global timeoutBool
    global newFlag
    global curWorkingDateID
    
    display_output(1, string_center("Auswahl"))
    display_output(3, string_center("OK drücken"))
    
    choices = '    Neu    Geplant  '
    choicesEmpty = ['           Geplant  ', '    Neu             ']
    choiceIndex = 1
    
    ok = True

    while ok:
        # Updating time
        updateClock()
        for x in range(TPS):
            # Flashing choice
            if ((x % 4 == 0) or ((x+1) % 4 == 0)):
                display_output(2, choices)
            else:
                display_output(2, choicesEmpty[choiceIndex])
            
            # Check for change in choice and update
            if(GPIO.input(TASTER_UP) == 1):
                resetTimeoutTimer()
                if choiceIndex > 0:
                    choiceIndex -= 1
                    break
            if(GPIO.input(TASTER_DOWN) == 1):
                resetTimeoutTimer()
                if choiceIndex < 1:
                    choiceIndex += 1
                    break
            # Checking for validation of choice
            if(GPIO.input(TASTER_OK) == 1):
                ok = not ok
                break
            # Checking for return
            if(GPIO.input(TASTER_MENUE) == 1) or timeoutBool:
                choiceIndex = 2
                ok = not ok
                break
        time.sleep(TASTER_TIME)
    
    # Choice: Geplanten Termin starten
    if(choiceIndex == 1):
        if statusOpen == False:
                choiceScreenStart()
        else:
                choiceScreenEnd(1)

    # Choice: Neuen Termin erstellen
    elif(choiceIndex == 0):
        now = datetime.datetime.now()
        timeNow = now.strftime('%Y-%m-%d %H:%M:%S')
        later = now + datetime.timedelta(hours=12)
        timeLater = later.strftime('%Y-%m-%d %H:%M:%S')
        ID = str(int(str(doDBRequest('SELECT id FROM tuerstatus_date ORDER BY id DESC LIMIT 1' , False)).strip("[( u)]\',"))+1)
        curWorkingDateID = ID
        newFlag = True
        doDBRequest('INSERT INTO tuerstatus_date VALUES('+ID+',\''+timeNow+'\',1,\'Terminal\',\''+timeLater+'\',0,0,0,0,0,0)', True)
        choiceScreenStart()
        
    # else
    # Choice: Abbrechen
        
def choiceScreenStart():
    
    resetTimeoutTimer()
    
    global startTimeChanged
    global timeoutBool
    global newFlag
    
    display_output(1, string_center("Startzeit"))
    display_output(3, string_center("OK drücken"))
    
    choices = '   Jetzt   Ändern   '
    choicesEmpty = ['           Ändern   ', '   Jetzt            ']
    choiceIndex = 0
    
    ok = True

    while ok and not newFlag:
        # Updating time
        updateClock()
        for x in range(TPS):
            # Flashing choice
            if ((x % 4 == 0) or ((x+1) % 4 == 0)):
                display_output(2, choices)
            else:
                display_output(2, choicesEmpty[choiceIndex])
            
            # Check for change in choice and update
            if(GPIO.input(TASTER_UP) == 1):
                resetTimeoutTimer()
                if choiceIndex > 0:
                    choiceIndex -= 1
                    break
            if(GPIO.input(TASTER_DOWN) == 1):
                resetTimeoutTimer()
                if choiceIndex < 1:
                    choiceIndex += 1
                    break
            # Checking for validation of choice
            if(GPIO.input(TASTER_OK) == 1):
                ok = not ok
                break
            # Checking for return
            if(GPIO.input(TASTER_MENUE) == 1) or timeoutBool:
                choiceIndex = 2
                ok = not ok
                break
        time.sleep(TASTER_TIME)

    if newFlag == True and choiceIndex != 2:
        choiceIndex = 1
        
    # Choice: Jetzt
    if(choiceIndex == 0):
        now = datetime.datetime.now()
        startTimeChanged = now
    # Choice: Spaeter
    elif(choiceIndex == 1 or newFlag):
        setTimeScreen(True, choiceIndex)
    # else
    # Choice: return
    
    if(choiceIndex < 2):
        choiceScreenEnd(choiceIndex)

def choiceScreenEnd(choiceIndexStart):
    
    resetTimeoutTimer()
    
    global startTimeChanged
    global timeoutBool
    global curWorkingDateID
    global newFlag
    
    display_output(1, string_center("Endzeit"))  
    display_output(3, string_center("OK drücken"))
    choices = '  Geplant   Ändern  '
    choicesEmpty = ['            Ändern  ', '  Geplant           ']
    choiceIndex = 0
    if  statusOpen == True:
        choices = '   Jetzt   Ändern   '
        choicesEmpty = ['           Ändern   ', '   Jetzt            ']
    ok = True

    while ok and not newFlag:
        # Updating time
        updateClock()
        for x in range(TPS):
            # Flashing choice
            if ((x % 4 == 0) or ((x+1) % 4 == 0)):
                display_output(2, choices)
            else:
                display_output(2, choicesEmpty[choiceIndex])
            
            # Check for change in choice and update
            if(GPIO.input(TASTER_UP) == 1):
                resetTimeoutTimer()
                if choiceIndex > 0:
                    choiceIndex -= 1
                    break
            if(GPIO.input(TASTER_DOWN) == 1):
                resetTimeoutTimer()
                if choiceIndex < 1:
                    choiceIndex += 1
                    break
            # Checking for validation of choice
            if(GPIO.input(TASTER_OK) == 1):
                ok = not ok
                break
            # Checking for return
            if(GPIO.input(TASTER_MENUE) == 1) or timeoutBool:
                choiceIndex = 2
                ok = not ok
                break
        time.sleep(TASTER_TIME)

    if newFlag == True and choiceIndex != 2:
        choiceIndex = 1
        
    # Choice: Nach Plan oder Jetzt (wenn offen)
    if(choiceIndex == 0):
        if statusOpen==True:
            closeNow()
        else:
            time.sleep(0.0000001)
            if choiceIndexStart == 0 or choiceIndexStart == 2:
                doDBRequest('UPDATE tuerstatus_date SET start = \'' + startTimeChanged.strftime('%Y-%m-%d %H:%M:%S') + '\' WHERE id = ' + curWorkingDateID, True)
        doDBRequest('UPDATE tuerstatus_date SET started = 1, link = 0, repeat=0 WHERE id = ' + curWorkingDateID, True)
    # Choice: Spaeter
    elif(choiceIndex == 1 or newFlag):
        setTimeScreen(False, choiceIndexStart)
        if newFlag:
            choiceScreenOpenOrSelfLab()
            newFlag = False
    # Else 
    # Choice: return
        
def choiceScreenOpenOrSelfLab():
    
    resetTimeoutTimer()

    global timeoutBool
    global curWorkingDateID
    
    display_output(1, string_center("Status"))  
    display_output(3, string_center("OK drücken"))
    
    choices = '  OpenLab  SelfLab  '
    choicesEmpty = ['           SelfLab  ', '  OpenLab           ']
    choiceIndex = 0
    
    ok = True

    while ok:
        # Updating time
        updateClock()
        for x in range(TPS):
            # Flashing choice
            if ((x % 4 == 0) or ((x+1) % 4 == 0)):
                display_output(2, choices)
            else:
                display_output(2, choicesEmpty[choiceIndex])
            
            # Check for change in choice and update
            if(GPIO.input(TASTER_UP) == 1):
                resetTimeoutTimer()
                if choiceIndex > 0:
                    choiceIndex -= 1
                    break
            if(GPIO.input(TASTER_DOWN) == 1):
                resetTimeoutTimer()
                if choiceIndex < 1:
                    choiceIndex += 1
                    break
            # Checking for validation of choice
            if(GPIO.input(TASTER_OK) == 1):
                ok = not ok
                break
            # Checking for return
            if(GPIO.input(TASTER_MENUE) == 1) or timeoutBool:
                choiceIndex = 2
                ok = not ok
                break
        time.sleep(TASTER_TIME)
    
    # Choice: OpenLab
    if(choiceIndex == 0):
        doDBRequest('UPDATE tuerstatus_date SET type = 2 WHERE id = ' + curWorkingDateID, True)
    # Choice: SelfLab
    elif(choiceIndex == 1):
        doDBRequest('UPDATE tuerstatus_date SET type = 1 WHERE id = ' + curWorkingDateID, True)
    # else
    # Choice: return
    
# For setting specific opening times - startTimeBool defines if used for start or end time
def setTimeScreen(startTimeBool, choiceIndexStart):
    
    resetTimeoutTimer()
    
    global startTimeChanged
    global timeoutBool
    global curWorkingDateID
    
    if(startTimeBool):
        display_output(1, string_center("Öffnen um"))
    else:
        display_output(1, string_center("Schließen um"))
        
    now = datetime.datetime.now()
    hours = int(now.strftime("%H"))
    minutes = int(now.strftime("%M"))
    
    hoursLimit = 0;
    minutesLimit = 0;
    
    if(startTimeBool):
        if minutes > (60 - START_DIFF_MIN):
            minutes = (minutes + START_DIFF_MIN) % 60
            hours = calcHours(hours, True)
        else:
            minutes += START_DIFF_MIN
        endTime = datetime.datetime.strptime(str(doDBRequest('SELECT end FROM tuerstatus_date WHERE id = ' + curWorkingDateID, False)).strip("[( u)]\'\',") , '%Y-%m-%d %H:%M:%S')
        hoursLimit = int(endTime.strftime("%H"))
        minutesLimit = int(endTime.strftime("%M"))
    else:
        if hours > (24 - END_DIFF_MIN):
            hours = (hours + END_DIFF_MIN) % 24
        else:
            hours += END_DIFF_MIN
        
        if choiceIndexStart == 1:
            startTimeChanged = datetime.datetime.strptime(str(doDBRequest('SELECT start FROM tuerstatus_date WHERE id = ' + curWorkingDateID, False)).strip("[( u)]\'\',") , '%Y-%m-%d %H:%M:%S')
        hoursLimit = int(startTimeChanged.strftime("%H"))
        minutesLimit = int(startTimeChanged.strftime("%M"))

    # Forth and Back :)
    calcHours(hours, True)
    calcHours(hours, False)
    calcMinutes(minutes, True)
    calcMinutes(minutes, False)

            
    # padding zeros 
    zHours = ''
    zMinutes = ''
    if hours < 10:
        zHours = '0'
    if minutes < 10:
        zMinutes = '0'
    
    timeStr = '       ' + zHours + str(hours) + ':' + zMinutes + str(minutes) + '       '
    timeEmpty = ['         :' + zMinutes + str(minutes) + '       ', '       ' + zHours + str(hours) + ':         ']
    timeIndex = 0
    
    ok = True
    
    while ok:
        # Updating time
        updateClock()
        for x in range(TPS):
            # Flashing choice
            if ((x % 4 == 0) or ((x+1) % 4 == 0)):
                display_output(2, timeStr)
            else:
                display_output(2, timeEmpty[timeIndex]) 
            # Check for change in time and update
            if(GPIO.input(TASTER_UP) == 1) :
                resetTimeoutTimer()
                if timeIndex == 0:
                    hours = calcHours(hours, True)
                    if (startTimeBool and hoursLimit < hours) or ((not startTimeBool) and hoursLimit > hours):
                        hours = hoursLimit
                else:
                    minutes = calcMinutes(minutes, True)
                    if (startTimeBool and hoursLimit == hours and minutesLimit < minutes) or ((not startTimeBool) and hoursLimit == hours and minutesLimit > minutes):
                        minutes = minutesLimit
                        
                # padding zeros
                zHours = ''
                zMinutes = ''
                if hours < 10:
                    zHours = '0'
                if minutes < 10:
                    zMinutes = '0'
                
                timeStr = '       ' + zHours + str(hours) + ':' + zMinutes + str(minutes) + '       '
                timeEmpty = ['         :' + zMinutes + str(minutes) + '       ', '       ' + zHours + str(hours) + ':         ']
                break
            if(GPIO.input(TASTER_DOWN) == 1):
                resetTimeoutTimer()
                if(timeIndex == 0):
                    hours = calcHours(hours, False)
                    if (startTimeBool and hoursLimit < hours) or ((not startTimeBool) and hoursLimit > hours):
                        hours = hoursLimit
                else:
                    minutes = calcMinutes(minutes, False)
                    if (startTimeBool and hoursLimit == hours and minutesLimit < minutes) or ((not startTimeBool) and hoursLimit == hours and minutesLimit > minutes):
                        minutes = minutesLimit
                
                # padding zeros 
                zHours = ''
                zMinutes = ''
                if hours < 10:
                    zHours = '0'
                if minutes < 10:
                    zMinutes = '0'
                
                timeStr = '       ' + zHours + str(hours) + ':' + zMinutes + str(minutes) + '       '
                timeEmpty = ['         :' + zMinutes + str(minutes) + '       ', '       ' + zHours + str(hours) + ':         ']
                break
            # Checking for validation of time
            if(GPIO.input(TASTER_OK) == 1):
                if(timeIndex < 1):
                    resetTimeoutTimer()
                    timeIndex += 1
                else:
                    ok = not ok
                break
            # Checking for return
            if(GPIO.input(TASTER_MENUE) == 1) or timeoutBool:
                if timeIndex == 1 and (GPIO.input(TASTER_MENUE) == 1):
                    timeIndex -= 1
                else: 
                    timeIndex = 2
                    ok = not ok
                break
            time.sleep(TASTER_TIME)
    
    # Skip and cancel if time index is 2 or higher
    if timeIndex < 2:
        # Choice: setTime
        zHours = ''
        zMinutes = ''
        if hours < 10:
            zHours = '0'
        if minutes < 10:
            zMinutes = '0'
            
        timeNow = now.strftime('%Y-%m-%d ') + zHours + str(hours) + ':' + zMinutes + str(minutes) + ':00'
        
        if(not startTimeBool):
            if choiceIndexStart == 0 or choiceIndexStart == 2:
                doDBRequest( 'UPDATE tuerstatus_date SET start = \'' + startTimeChanged.strftime('%Y-%m-%d %H:%M:%S') + '\' WHERE id = ' + curWorkingDateID, True)
            doDBRequest('UPDATE tuerstatus_date SET end = \'' + timeNow + '\' WHERE id = ' + curWorkingDateID, True)
            doDBRequest('UPDATE tuerstatus_date SET started = 1, link = 0, repeat = 0 WHERE id = ' + curWorkingDateID, True)
        else:
            startTimeChanged = datetime.datetime.strptime(timeNow, '%Y-%m-%d %H:%M:%S')
            
def openNow():
    global curWorkingDateID

    now = datetime.datetime.now()
    timeNow = now.strftime('%Y-%m-%d %H:%M:%S')
    doDBRequest('UPDATE tuerstatus_date SET start = \'' + timeNow + '\' WHERE id = ' + curWorkingDateID, True)

def closeNow():
    global curWorkingDateID

    now = datetime.datetime.now()
    timeNow = now.strftime('%Y-%m-%d %H:%M:%S')
    doDBRequest('UPDATE tuerstatus_date SET end = \'' + timeNow + '\' WHERE id = ' + curWorkingDateID, True)
            
def calcMinutes(minutesIn, boolInc):  # bool for increment/decrement 
    if(boolInc):
        minutesIn += MIN_PER_CLICK
        if minutesIn > 59:
            minutesIn = minutesIn % 60
    else:
        minutesIn -= MIN_PER_CLICK  
        if minutesIn < 0:
            minutesIn = minutesIn + 60
    return minutesIn
        
def calcHours(hoursIn, boolInc):  # bool for increment/decrement 
    if(boolInc):
        hoursIn += 1
        if hoursIn > 23:
            hoursIn = 0
    else:
        hoursIn -= 1    
        if hoursIn < 0:
            hoursIn = 23
    return hoursIn
            
def updateClock():
    # Update time (every second)
    now = datetime.datetime.now()
    
    timerRun()
    
    global toggleClock
    if toggleClock:
        display_output(0, now.strftime("%H:%M         %d.%m."))
        toggleClock = not toggleClock
    else:
        display_output(0, now.strftime("%H %M         %d.%m."))
        toggleClock = not toggleClock   
    updateLED()

def updateLED():
    global statusOpen
    
    # Get Unix timestamp for sql request
    stamp = str(int(time.time()))
    
    # Return status (if so !) of currently running and started event
    statusStr = str(doDBRequest('SELECT type, started FROM tuerstatus_date WHERE datetime(start)<=datetime(' + stamp + ',\'unixepoch\',\'localtime\') AND datetime(end)>=datetime(' + stamp + ',\'unixepoch\', \'localtime\') AND deleted !=1 AND started = 1 ORDER BY datetime(start) LIMIT 1' , False))
    statusList = [x.strip("[( u)]\'") for x in statusStr.split(',')]
    
    # If request returns an event (is not empty) - open
    if(statusStr.strip("[( u)]\'") != ''):
            statusType = statusList[0];
            if statusList[1] == '1':
                statusOpen = True
            # Set LEDs depending on Open-/SelfLab Status
            GPIO.output(LED_RED, 0)
            if statusType == '2':
                GPIO.output(LED_YELLOW, 0)
                GPIO.output(LED_GREEN, 1)
            elif statusType == '1':
                GPIO.output(LED_YELLOW, 1)
                GPIO.output(LED_GREEN, 0)
            else:
                setLEDclosed()
    else:
        setLEDclosed()

def setLEDclosed():
    global statusOpen
        
    # Lab closed 
    statusOpen = False
    # Set LEDs closed
    GPIO.output(LED_GREEN, 0)
    GPIO.output(LED_YELLOW, 0)
    GPIO.output(LED_RED, 1)

def resetTimeoutTimer():
    global timeoutTimer
    global timeoutBool
    
    timeoutBool = False
    timeoutTimer = 0

def timerRun():
    
    global timeoutTimer
    global timeoutBool
    
    timeoutTimer +=1
    
    if timeoutTimer >= TIMEOUT:
        timeoutBool = True
        
def doDBRequest(sqlCommand, boolWrite):
    try:
        global con
        # if con is None:
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

def display_output(row, message):
    try:
        lcd_byte(DISPLAYROWADR[row], DISPLAY_CMD)
        lcd_string(message)
    except:
        lcd_byte(DISPLAYROWADR[row], DISPLAY_CMD)
        lcd_string(message.encode('ascii', 'ignore'))
            

def string_center(message):
    message = message.center(DISPLAY_WIDTH," ")
    return message
    
def lcd_string(message):
    message = kill_umlauts(message)
    message = message.ljust(DISPLAY_WIDTH," ")  
    for i in range(DISPLAY_WIDTH):
        lcd_byte(ord(message[i]),DISPLAY_CHR)

def kill_umlauts(message):
    try:
        message = message.replace('ä', chr(225))
        message = message.replace('ö', chr(239))
        message = message.replace('ü', chr(245))
        message = message.replace('Ä', chr(225))
        message = message.replace('Ö', chr(239))
        message = message.replace('Ü', chr(245))
        message = message.replace('ß', chr(226))
    except:
        return message
    return message
        
def lcd_byte(bits, mode):
    GPIO.output(DISPLAY_RS, mode)
    lcd_byte_sub_1()
    lcd_byte_sub_2(bits, True)
    lcd_byte_sub_3()
    lcd_byte_sub_1()
    lcd_byte_sub_2(bits, False)
    lcd_byte_sub_3()
    
def lcd_byte_sub_1():
    for i in range(0, len(DISPLAYROWADR)):
        GPIO.output(DISPLAY_DATA[i], False)
    
def lcd_byte_sub_2(bits, highBits):
    bitShift = [0x10, 0x20, 0x40, 0x80]
    
    if(not highBits):
        bitShift = [0x01, 0x02, 0x04, 0x08]
    
    for i in range(0, len(DISPLAYROWADR)):
        if bits & bitShift[i] == bitShift[i]:
            GPIO.output(DISPLAY_DATA[i], True)
        
    
def lcd_byte_sub_3():
    time.sleep(E_DELAY) 
    GPIO.output(DISPLAY_E, True)  
    time.sleep(E_PULSE)
    GPIO.output(DISPLAY_E, False)  
    time.sleep(E_DELAY)   
    
    
if __name__ == '__main__':
    main()
