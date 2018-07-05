import psycopg2
import pandas as pd
import sqlalchemy
import json
import requests
import pprint
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("user", type=str, 
        help="username to access postgresql database")
parser.add_argument("password", type=str, 
        help="password to access postgresql database")
parser.add_argument("database", type=str, 
        help="database name")
parser.add_argument("--host","-H", type=str, 
        help="database host")
parser.add_argument("--port","-p", type=str, 
        help="database port")
args = parser.parse_args()



def connect(user, password, db, host, port):
    url = 'postgresql://{}:{}@{}:{}/{}'
    url = url.format(user,password,host,port,db)
    print(url)
    con = sqlalchemy.create_engine(url)
    return con

def get_trip_data(url,con):
    try:
        data = requests.get(url)
    except requests.exceptions.RequestException as error:
        print(error)
        return None
    datas = data.json()['data']
    # initialize rows
    d = {'company_name':[],
         'device_type':[],
         'trip_id':[],
         'trip_duration':[],
         'trip_distance':[],
         'start_point':[],
         'end_point':[],
         'accuracy':[],
         'route':[],
         'sample_rate':[],
         'device_id':[],
         'start_time':[],
         'end_time':[],
         'parking_verification':[],
         'standard_cost':[],
         'actual_cost':[]}
    for i in range(len(datas)):
        entry = datas[i]
        for k in d:
            if k in entry:
                if k=='start_point' or k=='end_point':
                    x = entry[k]['coordinates'][0]
                    y = entry[k]['coordinates'][1]
                    point = str((x,y))
                    d[k].append(point)
                else:
                    d[k].append(entry[k])
            else:
                d[k].append(None)
    df = pd.DataFrame(data=d)
    df.to_sql('trips',con,if_exists='append',index=False)

def get_status_change_data(url,con):
    try:
        data = requests.get(url)
    except requests.exceptions.RequestException as error:
        print(error)
        return None
    datas = data.json()['data']
    # initialize rows
    d = {'company_name':[],
         'device_type':[],
         'device_id':[],
         'event_type':[],
         'reason':[],
         'event_time':[],
         'location':[],
         'battery_pct':[],
         'associated_trips':[]}
    for i in range(len(datas)):
        entry = datas[i]
        for k in d:
            if k in entry:
                if k=='location':
                    x = entry[k]['coordinates'][0]
                    y = entry[k]['coordinates'][1]
                    point = str((x,y))
                    d[k].append(point)
                else:
                    d[k].append(entry[k])
            else:
                d[k].append(None)
    df = pd.DataFrame(data=d)
    df.to_sql('status_change',con,if_exists='append',index=False)

print(args)
user = args.user
password = args.password
db = args.database
host = "localhost"
if args.host is not None:
    host = args.host
port = 5432
if args.port is not None:
    port = args.port
con = connect(user,password,db,host,port)

print("Writing lemon trip data.")
get_trip_data("http://localhost:8000/lemon_trips.json",con)
print("Writing bat trip data.")
get_trip_data("http://localhost:8000/bat_trips.json",con)
print("writing lemon status change data.")
get_status_change_data("http://localhost:8000/lemon_status_change.json",con)
print("writing bat status change data.")
get_status_change_data("http://localhost:8000/bat_status_change.json",con)
