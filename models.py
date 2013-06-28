from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class CsvDataFile(models.Model):
    # [12m Digestion__data_file] 
    path = models.CharField(max_length=260)
    name = models.CharField(max_length=260)

    def __unicode__(self):
        return str(self.id) + '_' + self.name

    def disk_name(self):
        return self.__unicode__()
    
class CsvMapFile(models.Model):
    # [12m Digestion__map_file]
    path = models.CharField(max_length=260)
    name = models.CharField(max_length=260)

    def __unicode__(self):
        return str(self.id) + '_' + self.name

    def disk_name(self):
        return self.__unicode__()

DIGESTION_FUNCTION_CHOICES = (
    ('sum', 'Sum([cols])'),
    ('avg', 'Average([cols])'),
    ('pick', 'Pick(col)'),
)

class Digestion(models.Model):
    # [12m Digestion_Column__digestion]
    user = models.ForeignKey(User, to_field='username') 
    created = models.DateTimeField(auto_now=False,blank=True, null=True)
    name = models.CharField(max_length=100)
    map_file = models.ForeignKey(CsvMapFile, null=True)
    data_file = models.ForeignKey(CsvDataFile, null=True)
    data_file_id_column = models.IntegerField(null=True)
    function = models.IntegerField(null=True)
    inserts = models.IntegerField(null=True)
    overwrites = models.IntegerField(null=True)
    mts_characteristic = models.CharField(max_length=100)

    def __unicode__(self):
        return str(self.id) + '_' + self.name

    def get_name(self):
        return self.__unicode__()

    def get_id_column(self):
        if self.data_file_id_column > 0:
            return self.data_file_id_column
        else:
            self.data_file_id_column = 1
            self.save()
            return self.data_file_id_column 
    
class Digestion_Column(models.Model):
    column_number = models.IntegerField()
    digestion = models.ForeignKey(Digestion)

