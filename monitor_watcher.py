import threading
import requests
import re
import win32com.client
import time
import urllib3
import pythoncom
import sys
import os
import logging
from  dotenv import load_dotenv
from flask_cors import CORS, cross_origin
# import argparse
from flask import Flask, jsonify, request, Response

app = Flask(__name__) 
load_dotenv()
app.config['CORS_HEADERS'] = 'Content-Type'
CORS(app)
def send_email(subject, body, recipients):
    outlook = win32com.client.Dispatch("Outlook.Application")
    mail = outlook.CreateItem(0)
    mail.Subject = subject
    mail.HTMLBody = body
    mail.Importance = 2
    mail.To = ";".join(recipients) 
    mail.Send()

def countdown(seconds):
    while seconds >= 0:
        minutes, secs = divmod(seconds, 60)
        timeformat = '{:02d}:{:02d}'.format(minutes, secs)
        sys.stdout.write("\r")
        sys.stdout.write(f" Retrying again in {timeformat}...    ")
        sys.stdout.flush()
        time.sleep(1)
        seconds -= 1
    print("\n")
def get_response(link):
    regex_span = r'<td[^>]*>\s*(?:<span[^>]*>)*([^<]+)(?:<\/span>)*<\/td>'
    
    try:
        urllib3.disable_warnings()
        start_time = time.time()
        response = requests.get(link, verify=False)
        end_time = time.time()
        
        logging.info(f"Response from {link}:")
        result = re.findall(regex_span, response.text)
        elapsed_time = end_time - start_time
        rounded_time = round(elapsed_time, 2)
        print(f"Response from {link}: {rounded_time} has taken seconds")
        logging.info(f"Time elapsed for {link}: {rounded_time} seconds \n")
        services = result[::3]
        status = result[1::3]
        return dict(zip(services, status)), response.text
    except Exception as e:
        logging.error(f"Failed to fetch response from {link}: {e}")
        return None, None

def process_url(url,environment, recipients, results):
    result, html = get_response(url)
    if result is None and html is None:
        logging.error("Connection to the servers is down, please verify connection")
        results.append(None)
        return 
    if result is None:
        results.append(False)
        return
    optimal = next(iter(result))
    if result[optimal] == "Optimal":
        logging.info(f"Everything is working in the {url} Monitor")
        results.append(True)
    else:
        failedServices = [key for key, value in result.items() if value != "OK"]
        del failedServices[0]
        if len(failedServices) > 0:
            failed = ", ".join(failedServices)
            pythoncom.CoInitialize()
            send_email(f"<b>{environment}: {failed}</b>", f"<a href={url}>Go to monitor URL</a>" + html, recipients)
            pythoncom.CoUninitialize()
            logging.warning(f"Some services are failing in the {url} Monitor: {failed}")
            results.append(False)

def mainMethod(project,check_every, keep_alive):
    logging.basicConfig(filename=os.path.abspath('monitor.log'), level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    monitorURLS = {
            'https://vmq-alfrescona-02.alldata.com:8446/cpp/monitor': 'CPP NA QA' , 
            'https://vmq-alfrescoeu-01.alldata.com:8446/cpp/monitor': 'CPP EU QA' ,
            'http://vmq-alfrescona-02.alldata.com:8091/monitor': 'VP NA QA' ,
            'http://vmq-alfrescoeu-01.alldata.com:8091/monitor': 'VP EU QA' ,
            'https://vmq-alfrescona-02.alldata.com:8445/pet/monitor': 'PET QA'
        }
    parameter = {}
    if project:
        parameter = dict(filter(lambda e:project in e[1].lower().replace(" ", ""), monitorURLS.items() ) )
    if parameter:
        monitorURLS = parameter

    # while True:  
    def job():  
        threads = []
        results = []
        environments = []
        recipients = ["raul.herrera@autozone.com"]
        # recipients = ["raul.herrera@autozone.com", "saul.bravo@autozone.com"]
        for url,env in monitorURLS.items():
            environments.append(env)
            thread = threading.Thread(target=process_url, args=(url,env,recipients, results))
            thread.start()
            threads.append(thread)
        for thread in threads:
            thread.join()
        pythoncom.CoInitialize()
            
        if any(item is None for item in results):
            logging.error("One or more connections are down, please verify connection!")
            print("\n Error: One or more connections are down, please verify connection ! \n")            
            # return {'Error': 'One or more connections are down, please verify connection !'}
        elif not all(results):
            logging.warning("Some of the monitors have services in failure status")
            print("\n Some of the monitors have services in failure status \n")    
            return None, None 
            # return {'Error': 'Some of the monitors have services in failure status'}
            
            # send_email("Monitors failed", "Some of the monitors have services in failure status. Please verify email.", recipients)
            # print(" \n Waiting before checking again \n")
        else:
            logging.info("All the services of all the monitors are working correctly")
            print("\n All the services of all the monitors are working correctly \n")
            # if check_every == 0 or keep_alive == 0:
            #     send_email(f"<b>checked: {environments} </b>","Everything is working correctly" , recipients)
            pythoncom.CoInitialize()
            # return {'Success': 'All the services of all the monitors are working correctly'}
        return environments, recipients
    if check_every == 0 or keep_alive == 0:
        job()
    else:
        counter = 0
        retries_amount = keep_alive//check_every
        failed = False
        while counter < retries_amount:
            counter+=1    
            environments, recipients = job()
            if environments is None and recipients is None:  
                failed = True      
                break
            if not counter == retries_amount:
                countdown(check_every)
        if not failed:
            send_email(f"<b>checked: {environments} </b>","Everything is working correctly" , recipients)

@app.errorhandler(404)
def not_found(error=None):
        response = jsonify({
                'message': 'Resource Not Found',
                'status': 404
        }) #Se define una respuesta para decir el tipo de error que se capturó
        response.status_code = 404 #Definimos el mensaje del servidor de error 404 para que nos diga algo específico y no solo erro 505 o status 200
        return response
    
@app.route('/run/<project>', defaults={'check_every': 0, 'keep_alive': 0}, methods=['GET'])
@app.route('/run/<project>/<int:check_every>/<int:keep_alive>/', methods=['GET'])
def run_monitor(project, check_every, keep_alive):
    print("Tiempo de verificación:", check_every)
    print("Tiempo de ejecución:", keep_alive)
    threading.Thread(target=mainMethod, args=(project, check_every, keep_alive)).start()
    return jsonify({'status': 'Monitoring started'})
    
    
@app.route('/run', methods=['GET'])
def run_monitor_default():
    print("No project specified")
    threading.Thread(target=mainMethod, args=(None, 0, 0)).start()
    return jsonify({'status': 'Monitoring started for default project'})

if __name__ == "__main__":
    app.run(load_dotenv=True)
    