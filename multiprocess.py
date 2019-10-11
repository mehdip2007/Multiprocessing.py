#####import libraries
import pymongo
import multiprocessing
import pandas as pd
import collections
###while using collection API you might get depcrecated warning use the following to remove it.

try:
    collectionsAbc = collections.abc
except AttributeError:
    collectionsAbc = collections

######function interpret the mongo path fields
def flatten(d, parent_key='', sep='.'):
    items = {}
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, collections.MutableMapping):
            items.update(flatten(v, new_key, sep=sep).items())
        elif isinstance(v, list):
            for i, e in enumerate(v):
                items.update( flatten({new_key+sep+str(i): v[i]} ))
        else:
            items.update({new_key: v})
   
 return dict(items)


#####make the function to read file in mongo and put to dataframe to produce csv file

def getResultToCSV(l, queue,index):
    cnt =0
    ###CONNECTION URI
    myclient = pymongo.MongoClient("mongodb://user:pass@host:IP/DBNAME")  # PROD
    # readPrefs = pymongo.read_preferences.ReadPreference.SECONDARY                ######## you can define a read preference 
    mydb = myclient["DB"]  ##UAT , PROD
    mycol = mydb["Collection_Name"]
    ndf = pd.DataFrame()
    for i, element in enumerate(l):
        if i%1000==0:
            ndf.to_csv('result_%s.csv' % index, index=False , mode='a' , header=True)
            ndf =pd.DataFrame()
            print("%s >> %s" % ("*"*2*index,100*i/len(l)) )
            ####### you mongo query
        cursor = mycol.find({"billingAccount.accountCode" : element } ,
        {
        "_id" : 0,
        "billingAccount.billingPreferenceDetails.billDispatchDetails": 1,
        "billingAccount.accountCode" :1
        })


        for each in cursor:
            cnt+=1
            d = flatten(each)
            df = pd.DataFrame(d, index=[0])
            ndf = pd.concat([ndf, df], ignore_index=True, sort=False)
    print(cnt)
    ndf_list = ndf.values.tolist()
    ndf.to_csv('result_%s.csv' % index, index=False, mode='a', header=True)
    queue.put(index)


    return


###### funtion to scatter the files which are about to be generated by your processes
all_result = list()


def slice_it(li, cols=2):
    start = 0
    for i in range(cols):
        stop = start + len(li[i::cols])
        yield li[start:stop]
        start = stop



########start multi processing process  
#####at minimum you can use 2 cores
processes = []
queue = mp.Queue()
for idx,li in enumerate(slice_it(newLIST,int(cpu_count))):
    processes.append(mp.Process(target=getResultToCSV, args=(li, queue, idx )) )
    # print(i)
for process in processes:
    process.start()
for process in processes:
    process.join()
while not queue.empty():
    result = queue.get()
    print("process %s finished" % result)
