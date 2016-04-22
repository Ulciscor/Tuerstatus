from django.db import models

class Date(models.Model):
    start = models.DateTimeField()
    end = models.DateTimeField()
    user = models.CharField(max_length=50)
    type = models.IntegerField()
    repeat = models.IntegerField(default=0)
    link = models.IntegerField(default=0)
    started = models.BooleanField(default=False)
    topic_id = models.IntegerField(default=0)
    edit = models.BooleanField(default=False)
    deleted = models.BooleanField(default=False)
    
    def __str__(self):
        return "Date (" + str(self.pk) + "): " + str(self.start) + " - " + str(self.end) + " Type: " + str(self.type) + " Repeat: " + str(self.repeat) + " Link: " + str(self.link) + " Started: " + str(self.started) + ")"
    
    def delete(self):
        self.deleted = True
        self.edit = True
        self.save()