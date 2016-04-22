# -*- coding: iso-8859-1 -*-
from django.shortcuts import redirect
from django.http import HttpResponse
from django.template import RequestContext, loader
from .models import Date
import datetime
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.contrib import auth
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.conf import settings as config
from .discourse import Discourse

def index(request):
    dates = Date.objects.filter(end__gt = datetime.datetime.now(), deleted = False).order_by('start')[:5]
    repeatlist = Date.objects.filter(repeat__gt = 0).order_by('start')
    status = 0
    try:
        if dates.first().started:
            status = dates.first().type
        else:
            status = 0
    except:
        pass
    template = loader.get_template('index.html')
    context = RequestContext(request, {'list': dates, 'status': status, 'repeatlist': repeatlist})
    return HttpResponse(template.render(context))

def dates(request):
    if not request.user.is_authenticated():
        print(request.user.username)
        return redirect('/login')
    error = ""
    if request.POST:
        if request.POST['action'] == "edit":
            error = handleEdit(request)
        elif request.POST['action'] == "delete" or request.POST['action'] == "delete_all":
            handleDelete(request)
        else:
            error = handleNewDate(request)
#         return redirect('/dates/')
    dates = Date.objects.filter(end__gt = datetime.datetime.now(), deleted = False).order_by('start')
    #repeatlist = Date.objects.filter(repeat__gt = 0).order_by('start')
    today = datetime.datetime.today().__format__("%d.%m.%Y")
    time_start = datetime.datetime.now().__format__("%H:%M")
    time_end = (datetime.datetime.now() + datetime.timedelta(hours = 1)).__format__("%H:%M")
    template = loader.get_template('dates.html')
    context = RequestContext(request, {'list': dates, 'error': error, 'today': today, 'time_start':time_start, 'time_end':time_end})
    return HttpResponse(template.render(context))

def users(request):
    error = ""
    if not request.user.is_authenticated():
        return redirect('/login')
    if request.POST:
        if request.POST['action'] == "delete":
            error = deleteUser(request)
        else:
            error = addUser(request)
#         return redirect('/users/')
    users = User.objects.order_by('id')
    template = loader.get_template('users.html')
    context = RequestContext(request, {'list': users, 'error': error})
    return HttpResponse(template.render(context))

def settings(request):
    if not request.user.is_authenticated():
        return redirect('/login')
    template = loader.get_template('settings.html')
    msg = ""
    if request.POST:
        msg = changePassword(request);
    context = RequestContext(request, {'message': msg})
    return HttpResponse(template.render(context))

def handleNewDate(request):
    try:
        d = request.POST['startdate']
        t = request.POST['starttime']
        start = datetime.datetime.strptime(d + " " + t,"%d.%m.%Y %H:%M")
        d = request.POST['startdate']
        t = request.POST['endtime']
        end = datetime.datetime.strptime(d + " " + t,"%d.%m.%Y %H:%M")
        if start >= end:
            return "Endzeit muss spaeter als Startzeit sein."
        if end < datetime.datetime.now():
            return "Termin muss in der Zukunft liegen."
        possibleConflicts = Date.objects.filter(end__gt = start, start__lt = end, deleted = False)
        if possibleConflicts.count() > 0:
            return "Termin kollidiert mit vorhandenem Termin."
        type = 1
        if request.POST['type'] == "OpenLab":
            type = 2
        try:
            if Date.objects.get(start = start, end = end, deleted = False):
                return "Termin existiert bereits."
        except:
            pass
        repeat = 0
        if request.POST['repeat'] == "weekly":
            repeat = 1
        if request.POST['repeat'] == "daily":
            repeat = 2
        new = Date(start = start, end = end, user = request.user.username, type = type, repeat = repeat, link = 0, topic_id=0)
        
        # create weekly dates
        if repeat > 0:
            dayDelta = 7
            if repeat == 2:
                dayDelta = 1
            repeatCount = int(request.POST['repeatCount'])
            if repeatCount < 1 or repeatCount > 999:
                return "Anzahl der Wiederholungen muss zwischen 1 und 999 liegen."
            new.save()
            new.link = new.pk
            new.save()
            for i in range(0, repeatCount):
                start = start + datetime.timedelta(days=dayDelta)
                end = end + datetime.timedelta(days=dayDelta)
                currentDate = Date(start = start, end = end, user = request.user.username, type = type, repeat = repeat, link = new.link)
                currentDate.save()
            log("Following date repeating " + str(repeatCount) + " times")
        new.save()
        log(new.__str__() + " created by " + request.user.username)
        return ""
    except ValueError:
        return "Ungueltige Eingabe"

def handleDelete(request):
    if request.POST['action'] == "delete":
        log(Date.objects.get(pk=int(request.POST['id'])).__str__() + " deleted by " + request.user.username)
        Date.objects.get(pk=int(request.POST['id'])).delete()
    elif request.POST['action'] == "delete_all":
        link = request.POST['link']
        dates = Date.objects.filter(end__gt = datetime.datetime.now(), link = link)
        log("Dates with link " + link + " (" + str(len(dates)) + " matches)" + " deleted by " + request.user.username)
        for date in dates:
            date.delete()
        
def handleEdit(request):
    try:
        oldText = Date.objects.get(pk=int(request.POST['id'])).__str__()
        id = request.POST['id']
        date = Date.objects.get(pk=id)
        d = request.POST['startdate']
        t = request.POST['starttime']
        start = datetime.datetime.strptime(d + " " + t,"%d.%m.%Y %H:%M")
        d = request.POST['startdate']
        t = request.POST['endtime']
        end = datetime.datetime.strptime(d + " " + t,"%d.%m.%Y %H:%M")
        if start >= end:
            return "Endzeit muss spaeter als Startzeit sein"
        if end < datetime.datetime.now():
            return "Termin muss in der Zukunft liegen"
        possibleConflicts = Date.objects.filter(end__gt = start, start__lt = end, deleted = False).exclude(pk = id)
        if possibleConflicts.count() > 0:
            return "Termin kollidiert mit vorhandenem Termin."
        type = 1
        if request.POST['type'] == "OpenLab":
            type = 2
        date.start = start
        date.end = end
        date.type = type
        date.edit = True
        # Remove weekly link
        date.repeat = 0
        date.link = 0
        date.save()
        log(oldText + " changed to " + Date.objects.get(pk=int(request.POST['id'])).__str__() + " by " + request.user.username)
        return ""
    except:
        return "Fehler beim Bearbeiten"

def viewEdit(request, id):
    if not request.user.is_authenticated():
        return redirect('/login')
    try:
        id = request.POST['id']
        date = Date.objects.get(pk=id)
        start = date.start
        end = date.end
        type = date.type
        repeat = date.repeat
        template = loader.get_template('edit.html')
        context = RequestContext(request, {'start': start, 'end': end, 'type': type, 'id': id, 'repeat': repeat})
        return HttpResponse(template.render(context))
    except:
        return redirect('/dates/')

def deleteUser(request):
    log(User.objects.get(pk=int(request.POST['id'])).__str__() + " deleted by " + request.user.username)
    User.objects.get(pk=int(request.POST['id'])).delete()
    return ""

def addUser(request):
    newUser = request.POST['username']
    testUser = None
    try:
        testUser = User.objects.get(username=newUser)
        return "Der Benutzer " + newUser + " existiert bereits."
    except:
        pass
    email = request.POST['email']
    if not validateEmail(email):
        return "Ungültige E-Mail Adresse"
    password = User.objects.make_random_password(length=12)
    user = None
    if request.POST['type'] == "admin":
        user = User.objects.create_superuser(newUser, email, password)
    else:
        user = User.objects.create_user(newUser, email, password)
    
    send_mail("Zugangsdaten für das FabLab Webinterface", "Benutzername: " + newUser + "\nPasswort: " + password + "\nLink zum Webinterface: http://fablabtuer.ddns.net", 'fablabtuer@gmail.com',[email], fail_silently=False)
    log("User " + newUser + ": " + email + " (" + request.POST['type'] + ") created by " + request.user.username)
    return "Benutzer " + newUser + " erfolgreich erstellt. Die Zugangsdaten wurden an " + email + " geschickt."

def validateEmail(email):
    try:
        validate_email( email )
        return True
    except ValidationError:
        return False

def login(request):
    if request.user.is_authenticated():
        return redirect('/dates/')
    template = loader.get_template('login.html')
    error = ""
    if request.POST:
        user = authenticate(username=request.POST['user'], password=request.POST['pass'])
        if user is not None:
            #login successful
            log(user.username + " logged in from " + request.META.get('REMOTE_ADDR'))
            auth.login(request, user)
            return redirect('/dates/')
        else:
            #wrong login data
            log(request.POST['user'] + " failed to log in from " + request.META.get('REMOTE_ADDR'))
            error = "Benutzer oder Passwort falsch"
    #render login page
    context = RequestContext(request, {'error': error})
    return HttpResponse(template.render(context))

def logout(request):
    auth.logout(request)
    return redirect('/')

def changePassword(request):
    user = authenticate(username = request.user.username, password=request.POST['old_pass'])
    if user is None:
        return "Das alte Passwort war falsch. Das Passwort wurde nicht geändert."
    if len(request.POST['new_pass']) < 6:
        return "Das neue Passwort muss mindestens 6 Zeichen lang sein."
    if request.POST['new_pass'] != request.POST['new_pass2']:
        return "Das neue Passwort stimmt nicht mit dem Bestätigungsfeld überein."
    user.set_password(request.POST['new_pass'])
    user.save()
    auth.login(request, user)
    return "Passwort erfolgreich geändert!"

def forumUpdate(request):
    return HttpResponse("Deaktiviert, aber fertig konfiguriert!")
    # Config
    HOST = 'http://127.0.0.1' # Host adress here
    API_KEY = '123abc' # API key here
    CATEGORY_ID = 1 # Category here
    THRESHOLD = 14      # Only next X days will be considered for postings
    SCHEDULE_LINK = 'Link to website here'
    
    
    # Apply config
    forum = Discourse()
    forum.setConfig(HOST, API_KEY)
    CATEGORY_ID = str(CATEGORY_ID)
       
    # New dates
    dates = Date.objects.filter(end__gt = datetime.datetime.now(), 
                                topic_id = 0, 
                                start__lt = datetime.datetime.now() + datetime.timedelta(days=THRESHOLD),
                                type = 1,
                                deleted = False).exclude(user = 'Terminal')
    
    for d in dates:
        d.edit = False
        title = d.start.strftime("%a %e.%m.%Y, SelfLab von %H:%M bis ")\
            + d.end.strftime("%H:%M Uhr")
        text = "Der komplette Plan für die nächsten Tage ist zu finden unter " + SCHEDULE_LINK
        d.topic_id = forum.createTopic(title, text, CATEGORY_ID)
        d.save()
    
    # Post Updates
    dates = Date.objects.filter(topic_id__gt = 0, 
                                edit = True, 
                                type = 1)
       
    for d in dates:
        d.edit = False
        d.save()
        title = d.start.strftime("%a %e.%m.%Y, SelfLab von %H:%M bis ")\
            + d.end.strftime("%H:%M Uhr")
        text = ""
        if d.deleted == False:
            text = " Der Termin hat sich geändert! Der neue Termin ist nun " + title
        else:
            title = title + " entfällt!"
            text = "Der Termin " + title
        forum.updateTitle(d.topic_id, title)
        forum.createPost(d.topic_id, text)
    return HttpResponse("success!")

def log(line):
    try:
        f = open(config.LOG_FILE, "a+")
        f.write(datetime.datetime.now().__str__() + ": " +line + "\n")
        f.close()
    except:
        pass
    
