import csv
import re
import random
import math

class MapFile:
    
    def __init__(self, filepath, filename, reserved):
        self.m_path = filepath
        self.m_filename = filename 
        self.m_reserved = reserved # can't be used for mapping, they are um unique names
        self.m_csv = csv.reader(open((filepath + filename), 'rb'), delimiter=',', quotechar='"')
        self.m_ids = []
        self.extract()

    def extract(self):        
        self.m_ids = []    # data rows
        for row in self.m_csv:
            self.m_ids.append(row)

    def get_id_sample(self):
        return self.m_ids[0:10]
 
    def get_col_cnt(self):
        return len(self.m_ids[0])  # bit of a hack
        
    def get_row_cnt(self):
        return len(self.m_ids)     # bit of a hack

    def validate_duplicates(self):
        # find/warn duplicates in map
        double_dipper = dict() 
        for items in self.m_ids:
            if items[0] in double_dipper: 
                # exists
                double_dipper[items[0]] += 1
            else:
                # new
                double_dipper[items[0]] = 1           
        problems = []
        for key in double_dipper:
            if double_dipper[key] > 1:
                problems.append(key)
        return problems

    def validate_reserved(self):
        probs = []
        for items in self.m_ids:
            if items[0] in self.m_reserved:
                probs.append(items)
        return probs

    def find_replacement(self, uid):
        for items in self.m_ids:
            if items[0] == uid:
                return items[1]
        return None

class CsvFile:

    def __init__(self, filepath, filename, idcol):
        self.m_path = filepath
        self.m_filename = filename 
        self.m_csv = csv.reader(open((filepath + filename), 'rb'), delimiter=',', quotechar='"')
        self.m_idcol = idcol - 1 # zero indexed here...
        self.m_headers = []
        self.m_data = []
        self.m_mts = dict()
        self.m_print_limit = 100

        self.m_functions = [
            (0, '-------'),
            (1, 'avg1( [cols] )'),
            (2, 'avg2( [cols] )'),
            (3, 'avg3( [cols] )'),
            (4, 'skips( [cols] ) - NI'),
            (5, 'pick( col )'),
            (6, 'mapto( col, [translations] ) - NI'),
            (7, 'invent( data ) - NI'),
            (8, 'randomize( [choices] ) - NI'),
        ]
        self.extract()

        # sanity checks
        if len(self.m_headers) <= self.m_idcol:
            self.m_idcol = 0 

    def extract(self):        
        cnt = 0
        self.m_headers = []    # data headers
        self.m_data = []    # data rows
        for row in self.m_csv:
            if(cnt < 1):
                cnt = cnt + 1
                self.m_headers = row
            else:
                self.m_data.append(row)

    def idremap(self, mapp):
        # spin over the ids in data file
        # ask map file for any replacements
        # make replacements
        remapped = []
        for items in self.m_data:
            rep = mapp.find_replacement(items[self.m_idcol])
            if rep:
                remapped.append([items[self.m_idcol], rep])
                items[self.m_idcol] = rep
        return remapped 

    def duplicate_ids(self):
        # remap numeric and funky ids
        #self.idremap()

        # look for duplicates
        double_dipper = dict() 
        for user in self.get_ids():
            # login name
            if user in double_dipper: 
                # exists
                double_dipper[user] += 1
            else:
                # new
                double_dipper[user] = 1           
        problems = []
        for key in double_dipper:
            if double_dipper[key] > 1:
                problems.append(key)
        return problems

    def name(self):
        return self.m_filename

    def print_heads(self):
        ii = 0
        for item in self.m_headers:
            print str(ii) + " :  " + item
            ii += 1

    def execute(self, function_id, cols):
        cols = [x-1 for x in cols] # cols are not zero indexed in web gui...
        if function_id == 1:
            self.avg1(cols)
        elif function_id == 2:
            self.avg2(cols)
        elif function_id == 3:
            self.avg3(cols)
        elif function_id == 5:
            self.pick(cols)
        else:
            pass

    def print_ids(self):
        print "sample..."
        ii = 0
        for item in self.m_data:
            print str(ii) + " : " + item[self.m_idcol]    
            ii += 1
            if ii >= self.m_print_limit:
                break

    def print_col(self, col):
        print "sample..."
        ii = 0
        for row in self.m_data:
            ii += 1
            print row[self.m_idcol] + " : " + str(row[col])
            if ii >= self.m_print_limit:
                break

    def print_row(self, row):
        data = self.m_data[row] 
        for ii in range(0, len(data)):
            print self.m_headers[ii] + " : " + data[ii] 

    def heads_tuple(self):
        ids = range(1, len(self.m_headers) +1)
        return zip(ids, self.m_headers)

    def functions_tuple(self):
        return self.m_functions

    def get_id_header(self):
        return self.m_headers[self.m_idcol]

    def get_mts(self):
        return self.m_mts        

    def get_function_name(self, function_id):
        return self.m_functions[function_id][1]

    def get_function_id(self, function_id):
        return self.m_functions[function_id][0]

    def columns_tuple(self):
        ids = range(1, len(self.m_headers) +1)
        return zip(ids, self.m_headers)

    def get_col_cnt(self):
        return len(self.m_headers)
 
    def get_row_cnt(self):
        return len(self.get_ids())
 
    def get_id_sample(self):
        ret = self.get_ids()[0:10]
        return ret

    def get_ids(self):
        ret = []
        for item in self.m_data:
            ret.append(item[self.m_idcol])
        return ret

    def get_ids_old(self):
        ret = []
        for item in self.m_data:
            ret.append([item[self.m_idcol]])
        return ret
       
    def get_id_data(self): 
        ret = []
        for item in self.m_data:
            ret.append([item[self.m_idcol], item[self.m_fnamecol], item[self.m_lnamecol]])
        return ret

    def getpossible(self, col):
        re1 = re.compile(r'\[\d+\]')
        re2 = re.compile(r'\d+')
        header = self.m_headers[col] 
        tmp = str(re1.search(header).group())
        tmp = str(re2.search(tmp).group())
        return tmp

    def avg1(self, cols):
        # finds % of total points over all assignments
        # assignemnt value varies with points on that assignment
        self.m_mts = dict()
        for row in self.m_data:
            tot = 0
            pos = 0
            for col in cols:
                pos += float(self.getpossible(col))
                try:
                    tot += float(row[col])  
                except:
                    tot += 0
            per = int(math.floor(tot/pos * 100))
            self.m_mts.update({row[self.m_idcol] : per})

    def avg2(self, cols):
        # finds the average number of points per assignment over all assignments
        self.m_mts = dict()
        for row in self.m_data:
            tot = 0
            for col in cols:
                try:
                    tot += float(row[col])  
                except:
                    tot += 0
            per = int(math.floor(tot/len(cols)))
            self.m_mts.update({row[self.m_idcol] : per})

    def avg3(self, cols):
        # treats each assignement as same % of grade regardless of points
        # assignemnt value constant no matter how many points 
        self.m_mts = dict()
        for row in self.m_data:
            tot = 0
            for col in cols:
                try:
                    tot += (float(float(row[col]) / float(self.getpossible(col))))
                except:
                    tot += 0
            per = int(math.floor((tot * 100)/len(cols)))
            self.m_mts.update({row[self.m_idcol] : per})

    def skips(self, *cols):
        self.m_mts = dict()
        for row in self.m_data:
            tot = 0
            for col in cols:
                try:
                    # identify number of times a student skipped class 
                    if float(row[col]) == 0.0:
                        tot += 1
                except:
                    tot += 0
            per = int(math.floor((tot * 100)/len(cols)))
            self.m_mts.update({row[self.m_idcol] : per})

    def pick(self, cols):
        col = cols[0] # pick the first if multiple...
        self.m_mts = dict()
        for row in self.m_data:
            self.m_mts.update({row[self.m_idcol] : row[col]})
            #print row[self.m_idcol] + " : " + str(row[col])

    def mapto(self, col, trans):
        self.m_mts = dict()
        for row in self.m_data:
            try:
                res = trans[int(row[col]) - 1]
            except:
                res = None
            self.m_mts.update({row[self.m_idcol] : res})
 
    def invent(self, data):
        self.m_mts = dict()
        for row in self.m_data:
            self.m_mts.update({row[self.m_idcol] : data})

    def randomize(self, choices):
        numchoices = len(choices)
        self.m_mts = dict()
        for row in self.m_data:
            choice = int(math.floor(random.random() * numchoices)) # this should work for zero indexed arrays
            self.m_mts.update({row[self.m_idcol] : choices[choice]})
   

