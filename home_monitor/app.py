from __future__ import division
import time
import json
import logging                                              
from datetime import datetime, timedelta                                          
from functools import wraps                                                       
import serial                                                              
from influxdb import InfluxDBClient                                               
import json
from urllib.request import urlopen
from subprocess import PIPE, Popen
import psutil

influxdb = None
ser = None

import os 

# Return CPU temperature as a character string                                      
def getCPUtemperature():
    res = os.popen('vcgencmd measure_temp').readline()
    return(res.replace("temp=","").replace("'C\n",""))


    
def get_sensors():
    global ser                                                                
    ser.write(b'r')
    ts = time.time()
    time.sleep(1)                                              
    json_info = ser.readline().decode('utf-8')
    logging.info(json_info)                                                    
    json_info = json_info.replace('\n', '')                                       
    json_info = json_info.replace('\r', '')                                       
    json_info = json_info.replace('\'', '\"')                                     
    m = json.loads(json_info)
    darksky_req = urlopen("https://api.darksky.net/forecast/647d1410c98cd66fccfe71d3bfc6f6a9/41.279,-8.1928?units=si")
    darksky = json.loads(darksky_req.read().decode('utf-8'))
    json_body = [
        {
            "measurement": "home_sensors",
            "time": datetime.fromtimestamp(ts).strftime('%Y-%m-%dT%H:%M:%SZ'),
            "fields": {
                m[0]["columns"][0]: float(m[0]["points"][0]),
                m[0]["columns"][1]: float(m[0]["points"][1]),
                m[0]["columns"][2]: float(m[0]["points"][2]),
                m[0]["columns"][3]: float(m[0]["points"][3]),
                m[0]["columns"][4]: float(m[0]["points"][4]),
		        "ext_temp": float(darksky["currently"]["temperature"]),
                "ext_humidity": float(darksky["currently"]["humidity"]*100),
                "ext_heat_index": float(darksky["currently"]["apparentTemperature"]),
		        "ext_pressure": float(darksky["currently"]["pressure"]),
		        "ext_precipProbability": float(darksky["currently"]["precipProbability"]), 
		        "ext_precipIntensity":  float(darksky["currently"]["precipIntensity"])
            }
        },
        {
            "measurement": "motion",
            "time": datetime.fromtimestamp(ts).strftime('%Y-%m-%dT%H:%M:%SZ'),
            "fields": {
                "detected": m[0]["columns"][5]
            }
        }
    ]

    global influxdb
    
    try:
        influxdb.write_points(json_body)
    except:
        logging.exception('Unexpected error InfluxDB')

def getRAMinfo():
    p = os.popen('free')
    i = 0
    while 1:
        i = i + 1
        line = p.readline()
        if i==2:
            return(line.split()[1:4])

def get_pc_monitor():
    ts = time.time()
    #ram = psutil.phymem_usage()
    RAM_stats = getRAMinfo()
    disk = psutil.disk_usage('/')
    #logging.info(getCPUuse().replace('%',''))
    json_body = [
        {
            "measurement": "pc_details",
            "time": datetime.fromtimestamp(ts).strftime('%Y-%m-%dT%H:%M:%SZ'),
            "fields": {
                 "CPU_temp": float(getCPUtemperature()),
  	             "CPU_usage": float(psutil.cpu_percent(interval=None)),
                 "RAM_total": float(round(int(RAM_stats[0]) / 1000,1)),
                 "RAM_used": float(round(int(RAM_stats[1]) / 1000,1)),
                 "RAM_free": float(round(int(RAM_stats[2]) / 1000,1)),
                 "DISK_total": float(disk.total / 2**30),
                 "DISK_free": float(disk.free / 2**30),
                 "DISK_perc": float(disk.percent),
                 "DISK_used": float(disk.used / 2**30)
            }
        }
    ]

    global influxdb

    try:
        influxdb.write_points(json_body)
    except:
        logging.exception('Unexpected error InfluxDB')
          
if __name__ == '__main__':
    loglevel = logging.DEBUG
    logging.basicConfig(format='%(asctime)-15s [%(levelname)s] %(message)s',
                        datefmt='%Y/%m/%d %H:%M:%S',
                        level=loglevel)
    logging.info('aWarehouse starting...')
    global influxdb
    influxdb = InfluxDBClient('influxdb', 8086, 'root', 'root', 'home_monitor')
    influxdb.create_database('home_monitor')
    influxdb.create_retention_policy('awesome_policy', '3d', 3, default=True)
    global ser
    ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=4)
    #get_meteo()
    while(True):
        get_sensors()
        get_pc_monitor()
        time.sleep(900)

			