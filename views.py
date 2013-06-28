from django.core.urlresolvers import reverse
from django.views.generic import TemplateView
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, render
from django.conf import settings
from djangotailoring.views import TailoredDocView
from djangotailoring.project import getsubjectloader
from mynav.nav import main_nav, tasks_nav
from .steps import steps_nav
from mypump.csvfile import CsvFile, MapFile
from .models import *
from .forms import ( 
    Data_Loader_File_Upload_Form, 
    Data_Loader_File_Review_Form,
    Data_Loader_Data_Digest_Form,
    Data_Loader_MTS_Load_Form,
    Data_Loader_Archive_Form
)

# Create your views here.

def file_upload_view(request):
    #Log_Request(request)

    #configure_source_data(request.user.username)

    profile = request.user.get_profile()
    prefs = profile.prefs

    try:
        digestion = Digestion.objects.get(pk=prefs["digestion_pk"])
    except:  
        digestion = Digestion(user=request.user)
        digestion.save()
        prefs['digestion_pk'] = digestion.id
        profile.prefs = prefs
        profile.save()
 
    try:
        active_csv_data = digestion.data_file.disk_name()
    except:
        active_csv_data = "*no data files uploaded*"
    try:
        active_csv_map = digestion.map_file.disk_name()
    except:
        active_csv_map = "*no map files uploaded*"

   
    if request.method == 'POST':
        form = Data_Loader_File_Upload_Form(
            request=request,
            data=request.POST, 
            files=request.FILES
        )
        if form.is_valid():
            # Do valid form stuff here
            form.save_data(digestion)
            return redirect('myloader:file_upload')
    else:
        try:
            df = digestion.data_file.id
        except: 
            df = 0   
        try:
            mf = digestion.map_file.id
        except:
            mf = 0
        form = Data_Loader_File_Upload_Form(
            request=request,
            initial={'select_datafile' : df, 'select_idmap': mf}
        )

    return render(request, 'myloader/file_upload.html', {
        "main_nav": main_nav(request.user, 'staff_view'),
        "tasks_nav": tasks_nav(request.user, 'publisher'),
        "steps_nav": steps_nav(request.user, 'review'),
        "form": form,
        "args": request.GET,
        "active_csv_map": active_csv_map,
        "active_csv_data": active_csv_data
    })

def mp_map_download_view(request):
    import os

    # if not admin don't do it
    staffmember = request.user.is_staff
    if not staffmember:
        return redirect('/')

    # send the results
    try:
        file_name = "mp_name_map.csv"
        file_path = os.path.dirname(__file__) + '/uploads/other/' + file_name
        
        f = open(file_path, 'w')
        # select MP_Name, user_id from mydata4_Source1 where not MP_Name=user_id group by MP_Name;  
        new = Source1.objects.exclude(user_id__in=User.objects.filter(is_staff=True).values_list('username', flat=True)).values_list('MP_Name', 'user_id')
        # old = Source1.objects.mp_names()
        ss = ""
        # for nn in mp_names:
        for nn in new:
            ss += str(nn[0]) + "," + str(nn[1]) + "\n"
        ss = ss[0:len(ss)-1]
        f.write(ss)
        f.close()

        fsock = open(file_path,"rb")
        response = HttpResponse(fsock, content_type='application/octet-stream')
        response['Content-Disposition'] = 'attachment; filename=' + file_name            
    except IOError:
        response = HttpResponseNotFound("error creating the file")

    return response

     

def file_review_view(request):
    #Log_Request(request)

    #configure_source_data(request.user.username)

    profile = request.user.get_profile()
    prefs = profile.prefs

    try:
        digestion = Digestion.objects.get(pk=prefs["digestion_pk"])
    except:  
        digestion = Digestion(user=request.user)
        digestion.save()
        prefs['digestion_pk'] = digestion.id
        profile.prefs = prefs
        profile.save()

    try:
        # anyone who has logged into the system is reserved from mapping
        reserved = User.objects.values_list('username')
        reserved = [x[0] for x in reserved]
        map_file_path = settings.MYCOACH_PROJECT_ROOT + digestion.map_file.path
        mapp  = MapFile(map_file_path, digestion.map_file.disk_name(), reserved) # assume id in row 1
    except:
        return redirect('file_upload_view')

    # rows map
    try:
        map_file_row_cnt  = mapp.get_row_cnt() 
    except:
        map_file_row_cnt = "*error: unable to count rows*"
    # cols map
    try:
        map_file_col_cnt = mapp.get_col_cnt()
    except:
        map_file_col_cnt =  "*error: unable to count cols*"
    # id sample map
    try:
        map_file_sample = mapp.get_id_sample()
    except:
        map_file_sample =  ["*error: unable to find id sample*"]
    # duplicates in map 
    try:
        map_file_dups = mapp.validate_duplicates()
    except:
        map_file_dups = []
    # reserved in map 
    try:
        map_file_reserved = mapp.validate_reserved()
    except:
        map_file_reserved = []
    # sample ids in map
    try:
        map_file_id_sample = mapp.get_id_sample()
    except:
        map_file_id_sample = [] 
  
    # data  
    try: 
        data_file_path = settings.MYCOACH_PROJECT_ROOT + digestion.data_file.path
        data  = CsvFile(data_file_path, digestion.data_file.disk_name(), digestion.get_id_column())
    except:
        return redirect('file_upload_view')

    # make id replacements in data
    try:
        remapped_ids = data.idremap(mapp)
    except:
        remapped_ids = []
 

    # rows data
    try:
        data_file_row_cnt = data.get_row_cnt() 
    except:
        data_file_row_cnt = "*error: unable to count rows*"
    # cols data
    try:
        data_file_col_cnt = data.get_col_cnt()
    except:
        data_file_col_cnt =  "*error: unable to count cols*"
    # id sample data
    try:
        data_file_id_sample = data.get_id_sample()
    except:
        data_file_id_sample =  "*error: unable to find id sample*"
    # id verify
    try:
        data_file_duplicate_ids = data.duplicate_ids()
    except:
        data_file_duplicate_ids = []
   
    if request.method == 'POST':
        form = Data_Loader_File_Review_Form(
            data=request.POST, 
            choices = data.heads_tuple()
        )
        if form.is_valid():
            # Do valid form stuff here
            form.save_data(digestion)
            return redirect('file_review_view')
    else:
        form = Data_Loader_File_Review_Form(
            initial = {'select_id_column' : digestion.get_id_column()},
            choices = data.heads_tuple()
        )
    
    return render(request, 'myloader/file_review.html', {
        "main_nav": main_nav(request.user, 'staff_view'),
        "tasks_nav": tasks_nav(request.user, 'publisher'),
        "steps_nav": steps_nav(request.user, 'review'),
        "form": form,
        "args": request.GET,
        "active_row_cnt": data_file_row_cnt,
        "active_col_cnt": data_file_col_cnt,
        "active_id_column": data.get_id_header() + " ( column " + str(digestion.get_id_column()) + " )",
        "active_id_sample": data_file_id_sample,
        "remapped_ids": remapped_ids,
        "duplicate_ids": data_file_duplicate_ids,
        "map_file_row_cnt": map_file_row_cnt,
        "map_file_col_cnt": map_file_col_cnt,
        "map_file_dups": map_file_dups,
        "map_file_reserved": map_file_reserved,
        "map_file_id_sample": map_file_id_sample,
    })

def data_digest_view(request):
    #Log_Request(request)

    #configure_source_data(request.user.username)

    profile = request.user.get_profile()
    prefs = profile.prefs

    try:
        digestion = Digestion.objects.get(pk=prefs["digestion_pk"])
    except:  
        digestion = Digestion(user=request.user)
        digestion.save()
        prefs['digestion_pk'] = digestion.id
        profile.prefs = prefs
        profile.save()

    try:
        # anyone who has logged into the system is reserved from mapping
        reserved = User.objects.values_list('username')
        reserved = [x[0] for x in reserved]
        map_file_path = settings.MYCOACH_PROJECT_ROOT + digestion.map_file.path
        mapp  = MapFile(map_file_path, digestion.map_file.disk_name(), reserved) # assume id in row 1
    except:
        return redirect('file_upload_view')

    # rows map
    try:
        map_file_row_cnt  = mapp.get_row_cnt() 
    except:
        map_file_row_cnt = "*error: unable to count rows*"
    # cols map
    try:
        map_file_col_cnt = mapp.get_col_cnt()
    except:
        map_file_col_cnt =  "*error: unable to count cols*"
    # id sample map
    try:
        map_file_sample = mapp.get_id_sample()
    except:
        map_file_sample =  ["*error: unable to find id sample*"]
    # duplicates in map 
    try:
        map_file_dups = mapp.validate_duplicates()
    except:
        map_file_dups = []
    # reserved in map 
    try:
        map_file_reserved = mapp.validate_reserved()
    except:
        map_file_reserved = []
    # sample ids in map
    try:
        map_file_id_sample = mapp.get_id_sample()
    except:
        map_file_id_sample = [] 

    # data  
    try:
        data_file_path = settings.MYCOACH_PROJECT_ROOT + digestion.data_file.path
        data  = CsvFile(data_file_path, digestion.data_file.disk_name(), digestion.get_id_column())
    except:
        return redirect('file_upload_view')

    # make id replacements in data
    try:
        remapped_ids = data.idremap(mapp)
    except:
        remapped_ids = []
 
    # mts charactoristic
    if digestion.mts_characteristic and len(digestion.mts_characteristic) > 0:
        mts_char = digestion.mts_characteristic
        mts_char_report = mts_char
    else:
        mts_char = []
        mts_char_report = "*no mts char selected*"
    # digestion function
    if digestion.function > 0:
        digestion_function = data.get_function_name(digestion.function)
        digestion_function_select = data.get_function_id(digestion.function)
    else:
        digestion_function = "*digestion funtion not selected*" 
        digestion_function_select = 0
    # digestion columns
    try:
        digestion_columns = Digestion_Column.objects.all().filter(digestion=digestion.id).values_list('column_number')
        digestion_columns = [x[0] for x in digestion_columns]
        digestion_columns_select = digestion_columns
    except:
        #digestion_columns = "*digestion columns not selectd*" 
        digestion_columns = []
        digestion_columns_select = []

    chars = Source1._meta.get_all_field_names()
    chars.remove('id')
    chars.remove('user_id')
    chars.remove('updated')
    chars = sorted(chars)
    chars = tuple((cc, cc) for cc in chars)

    if request.method == 'POST':
        form = Data_Loader_Data_Digest_Form(
            data=request.POST, 
            function_choices = data.functions_tuple(),
            column_choices = data.columns_tuple(),
            mts_char_choices = chars
        )
        if form.is_valid():
            # Do valid form stuff here
            form.save_data(digestion)
            return redirect('data_digest_view')
    else:
        form = Data_Loader_Data_Digest_Form(
            initial = {'digestion_function' : digestion_function_select, 'digestion_columns' : digestion_columns_select, 'mts_char' : mts_char},
            function_choices = data.functions_tuple(),
            column_choices = data.columns_tuple(),
            mts_char_choices = chars
        )
    try:
        data.execute(digestion.function, digestion_columns_select) 
    except:
        pass
    return render(request, 'myloader/data_digest.html', {
        "main_nav": main_nav(request.user, 'staff_view'),
        "tasks_nav": tasks_nav(request.user, 'publisher'),
        "steps_nav": steps_nav(request.user, 'review'),
        "form": form,
        "args": request.GET,
        "digestion_function": digestion_function,
        "digestion_columns": digestion_columns,
        "mts_char": mts_char_report,
        "digestion_result" : data.get_mts(), 
    })

def mts_load_view(request):
    #Log_Request(request)

    #configure_source_data(request.user.username)

    profile = request.user.get_profile()
    prefs = profile.prefs

    try:
        digestion = Digestion.objects.get(pk=prefs["digestion_pk"])
    except:  
        digestion = Digestion(user=request.user)
        digestion.save()
        prefs['digestion_pk'] = digestion.id
        profile.prefs = prefs
        profile.save()

    try:
        # anyone who has logged into the system is reserved from mapping
        reserved = User.objects.values_list('username')
        reserved = [x[0] for x in reserved]
        map_file_path = settings.MYCOACH_PROJECT_ROOT + digestion.map_file.path
        mapp  = MapFile(map_file_path, digestion.map_file.disk_name(), reserved) # assume id in row 1
    except:
        return redirect('file_upload_view')

    # rows map
    try:
        map_file_row_cnt  = mapp.get_row_cnt() 
    except:
        map_file_row_cnt = "*error: unable to count rows*"
    # cols map
    try:
        map_file_col_cnt = mapp.get_col_cnt()
    except:
        map_file_col_cnt =  "*error: unable to count cols*"
    # id sample map
    try:
        map_file_sample = mapp.get_id_sample()
    except:
        map_file_sample =  ["*error: unable to find id sample*"]
    # duplicates in map 
    try:
        map_file_dups = mapp.validate_duplicates()
    except:
        map_file_dups = []
    # reserved in map 
    try:
        map_file_reserved = mapp.validate_reserved()
    except:
        map_file_reserved = []
    # sample ids in map
    try:
        map_file_id_sample = mapp.get_id_sample()
    except:
        map_file_id_sample = [] 

    # data
    try:
        data_file_path = settings.MYCOACH_PROJECT_ROOT + digestion.data_file.path
        data  = CsvFile(data_file_path, digestion.data_file.disk_name(), digestion.get_id_column())
    except:
        return redirect('file_upload_view')
        
    # make id replacements in data
    try:
        remapped_ids = data.idremap(mapp)
    except:
        remapped_ids = []
 
    # digestion name
    if digestion.name and len(digestion.name) > 0:
        digestion_name = digestion.name
        digestion_name_reprint = digestion_name
    else:
        digestion_name = "*digestion not named*" 
        digestion_name_reprint = ''

    if request.method == 'POST': 
        form = Data_Loader_MTS_Load_Form(
            data=request.POST, 
        )
        if form.is_valid():
            # Do valid form stuff here
            if form.save_data(digestion, request.user, data):
                return redirect('archive_view')
            else:
                return redirect('mts_load_view')
    else:
        form = Data_Loader_MTS_Load_Form(
            initial = {'digestion_name' : digestion_name_reprint},
        )

    return render(request, 'myloader/mts_load.html', {
        "main_nav": main_nav(request.user, 'staff_view'),
        "tasks_nav": tasks_nav(request.user, 'publisher'),
        "steps_nav": steps_nav(request.user, 'review'),
        "form": form,
        "args": request.GET,
        "digestion_id" : digestion.id, 
        "digestion_name": digestion_name,
        "digestion": digestion,
    })

def archive_view(request):
    #Log_Request(request)

    #configure_source_data(request.user.username)

    profile = request.user.get_profile()
    prefs = profile.prefs

    profile = request.user.get_profile()
    prefs = profile.prefs

    try:
        digestion = Digestion.objects.get(pk=prefs["digestion_pk"])
    except:  
        digestion = Digestion(user=request.user)
        digestion.save()
        prefs['digestion_pk'] = digestion.id
        profile.prefs = prefs
        profile.save()

    if request.method == 'POST': 
        form = Data_Loader_Archive_Form(
            data=request.POST, 
        )
        if form.is_valid():
            # Copy the old digestion
            new = form.cleaned_data['digestion'] # still old
            cols = Digestion_Column.objects.filter(digestion=new.id) # old cols
            new.id = digestion.id # becomes new
            new.user = digestion.user # becomes new
            new.save() # save new
            Digestion_Column.objects.filter(digestion=new.id).delete() # delete existing cols
            for cc in cols:     # copy old cols
                cc.id = None    # become new
                cc.digestion_id = new.id
                cc.save() 
            return redirect('archive_view')
    else:
        form = Data_Loader_Archive_Form()

    return render(request, 'myloader/archive.html', {
        "main_nav": main_nav(request.user, 'staff_view'),
        "tasks_nav": tasks_nav(request.user, 'publisher'),
        "steps_nav": steps_nav(request.user, 'review'),
        "form": form,
        "args": request.GET,
        "digestion_name": digestion.get_name(),
        "digestion": digestion,
    })

def help_view(request):

    return render(request, 'myloader/help.html', {
        "main_nav": main_nav(request.user, 'staff_view'),
        "tasks_nav": tasks_nav(request.user, 'publisher'),
        "steps_nav": steps_nav(request.user, 'review'),
    })



