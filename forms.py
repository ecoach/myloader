from django import forms
from django.conf import settings
from .models import CsvDataFile, CsvMapFile, Digestion, Digestion_Column
from datetime import datetime
from django.utils.importlib import import_module
mydata = import_module(settings.MYDATA)
Source1 = mydata.models.Source1
myutils = import_module(settings.MYDATA + '.utils')
configure_source_data = myutils.configure_source_data

class Data_Loader_File_Upload_Form(forms.Form):
    csv_data_file = forms.FileField(required=False)
    csv_idmap_file = forms.FileField(required=False)
    select_datafile = forms.ModelChoiceField(required=False, queryset=CsvDataFile.objects.all().order_by('-id'))
    select_idmap = forms.ModelChoiceField(required=False, queryset=CsvMapFile.objects.all().order_by('-id'))

    def __init__(self, request, *args, **kwargs):
        super(Data_Loader_File_Upload_Form, self).__init__(*args, **kwargs)
        #self.initial['select_datafile'] = 1

    def save_data(self, digestion):
        import os
        root_path = settings.DIR_UPLOAD_DATA
        # data file
        if self.cleaned_data["csv_data_file"] != None:
            csv = self.cleaned_data["csv_data_file"]
            dpath = 'datafiles/'
            ff = CsvDataFile(name=csv.name, path=dpath)  # save the file
            ff.save()
            destination = open(root_path + dpath + ff.disk_name(), 'wb+')
            for chunk in csv.chunks():
                destination.write(chunk)
            destination.close()
            digestion.data_file = ff    # start using new file reference
        elif self.cleaned_data["select_datafile"] != None:
            digestion.data_file = self.cleaned_data["select_datafile"]
        # map file
        if self.cleaned_data["csv_idmap_file"] != None:
            csv = self.cleaned_data["csv_idmap_file"]
            mpath = 'mapfiles/'
            ff = CsvMapFile(name=csv.name, path=mpath)   # save the file
            ff.save()
            destination = open(root_path + mpath + ff.disk_name(), 'wb+')
            for chunk in csv.chunks():
                destination.write(chunk)
            destination.close()
            digestion.map_file = ff     # start using new file reference
        elif self.cleaned_data["select_idmap"] != None:
            digestion.map_file = self.cleaned_data["select_idmap"]
        # persist choices
        digestion.save()

class Data_Loader_File_Review_Form(forms.Form):
    select_id_column = forms.ChoiceField(required=False)

    def __init__(self, choices, *args, **kwargs):
        super(Data_Loader_File_Review_Form, self).__init__(*args, **kwargs)
        self.fields['select_id_column'].choices = choices

    def save_data(self, digestion):
        if self.cleaned_data["select_id_column"] != None:
            digestion.data_file_id_column = self.cleaned_data["select_id_column"]
            digestion.save()

class Data_Loader_Data_Digest_Form(forms.Form):
    digestion_function = forms.ChoiceField(required=False)
    digestion_columns = forms.MultipleChoiceField(required=False, widget=forms.CheckboxSelectMultiple)
    mts_char = forms.ChoiceField(required=False)

    def __init__(self, function_choices, column_choices, mts_char_choices, *args, **kwargs):
        super(Data_Loader_Data_Digest_Form, self).__init__(*args, **kwargs)
        self.fields['digestion_function'].choices = function_choices
        self.fields['digestion_columns'].choices = column_choices
        self.fields['mts_char'].choices = mts_char_choices

    def save_data(self, digestion):
        if self.cleaned_data["digestion_function"] != None:
            digestion.function = self.cleaned_data["digestion_function"]
        if self.cleaned_data["digestion_columns"] != None:
            cols = self.cleaned_data["digestion_columns"]
            Digestion_Column.objects.all().filter(digestion=digestion).delete()
            for cc in cols:
                Digestion_Column(digestion=digestion, column_number=cc).save()
        if self.cleaned_data["mts_char"] != None:
            digestion.mts_characteristic = self.cleaned_data["mts_char"]
        digestion.save()

class Data_Loader_MTS_Load_Form(forms.Form):
    digestion_name  = forms.CharField(required=False)
    commit = forms.ChoiceField(widget=forms.RadioSelect, choices=(('0', 'Test run',), ('1', 'Commit',)), initial=0)

    def __init__(self, *args, **kwargs):
        super(Data_Loader_MTS_Load_Form, self).__init__(*args, **kwargs)

    def save_data(self, digestion, user, csv):
        if self.cleaned_data["digestion_name"] != None:
            digestion.name = self.cleaned_data["digestion_name"]
            digestion.save()
        if self.cleaned_data["commit"] == '1' and len(digestion.name) > 1:
            # pump digestion result into mysql database 
            try:
                digestion_columns = Digestion_Column.objects.all().filter(digestion=digestion.id).values_list('column_number')
                digestion_columns = [x[0] for x in digestion_columns]
                csv.execute(digestion.function, digestion_columns) 
            except:
                pass
            inserts = 0
            overwrites = 0
            mts = csv.get_mts()
            for key in mts:
                if configure_source_data(key): # make sure the user is added
                    inserts += 1
                else:
                    overwrites += 1
                ss = Source1.objects.get(user_id=key)
                setattr(ss, digestion.mts_characteristic, mts[key])
                try:
                    ss.save()
                except: 
                    pass
            """
                Source1.objects.get(user_id=key).update(**{
                    digestion.mts_characteristic: mts[key]
                })
            """
            # time the digestion ran
            digestion.created = datetime.now()
            digestion.inserts = inserts
            digestion.overwrites = overwrites
            digestion.save() 
            # make new digestion and save to prefs
            profile = user.get_profile()
            prefs = profile.prefs
            dg = Digestion(user=user)
            dg.save()
            prefs['digestion_pk'] = dg.id
            profile.prefs = prefs
            profile.save()
            return True
        return False
            

class Data_Loader_Archive_Form(forms.Form):
    digestion = forms.ModelChoiceField(required=True, queryset=Digestion.objects.all().order_by('-id'))

    def __init__(self, *args, **kwargs):
        super(Data_Loader_Archive_Form, self).__init__(*args, **kwargs)



