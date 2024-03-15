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
    mail.To = ";".join(recipients) 
    mail.Send()

def countdown(seconds):
    while seconds > 0:
        sys.stdout.write("\r")
        sys.stdout.write(f" Retrying again in {seconds} second(s)...    ")
        sys.stdout.flush()
        time.sleep(1)
        seconds -= 1
    print("\n \n")
    
def countdown(c):      
    while c:  
        m, s = divmod(c, 60)  
        timer = '{:02d}:{:02d}'.format(m, s)  
        print(f" Retrying again in {timer} ...    ", end="\r")  
        time.sleep(1)  
        c -= 1    

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
    pythoncom.CoInitialize()
    try:
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
                # send_email(f"<b>{environment}: {failed}</b>", f"<a href={url}>Go to monitor URL</a>" + html, recipients)
                logging.warning(f"Some services are failing in the {url} Monitor: {failed}")
                results.append(False)
    finally:
        pythoncom.CoUninitialize()

def mainMethod(project):
    logging.basicConfig(filename=os.path.abspath('monitor.log'), level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    # env = str(sys.argv[1])
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

    
    # parser = argparse.ArgumentParser(description="Just an example",
    #                              formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    # parser.add_argument("-a", "--archive", action="store_true", help="archive mode")
    # parser.add_argument("-v", "--verbose", action="store_true", help="increase verbosity")
    # parser.add_argument("-B", "--block-size", help="checksum blocksize")
    # parser.add_argument("--ignore-existing", action="store_true", help="skip files that exist")
    # parser.add_argument("--exclude", help="files to exclude")
    # parser.add_argument("src", help="Source location")
    # parser.add_argument("dest", help="Destination location")
    # args = parser.parse_args()
    # config = vars(args)
    # print(config)
    
    # print(dict(filter(lambda e:env in e[1], monitorsURLS.items() ) ) )
    # while True:    
    threads = []
    results = []
    recipients = ["raul.herrera@autozone.com"]
    # recipients = ["raul.herrera@autozone.com", "saul.bravo@autozone.com"]
    for url,environment in monitorURLS.items():
        thread = threading.Thread(target=process_url, args=(url,environment,recipients, results))
        thread.start()
        threads.append(thread)
    # os.system('cls')

    for thread in threads:
        thread.join()
        
    if any(item is None for item in results):
        logging.error("One or more connections are down, please verify connection!")
        print("\n Error: One or more connections are down, please verify connection ! \n")            
        return {'Error': 'One or more connections are down, please verify connection !'}
    elif not all(results):
        logging.warning("Some of the monitors have services in failure status")
        print("\n Some of the monitors have services in failure status \n")
        return {'Error': 'Some of the monitors have services in failure status'}
        # send_email("Monitors failed", "Some of the monitors have services in failure status. Please verify email.", recipients)
        # print(" \n Waiting before checking again \n")
#            break
    else:
        logging.info("All the services of all the monitors are working correctly")
        print("\n All the services of all the monitors are working correctly \n")
        return {'Success': 'All the services of all the monitors are working correctly'}
    # countdown(600)
        # os.system('cls')

@app.errorhandler(404)
def not_found(error=None):
        response = jsonify({
                'message': 'Resource Not Found',
                'status': 404
        }) #Se define una respuesta para decir el tipo de error que se capturó
        response.status_code = 404 #Definimos el mensaje del servidor de error 404 para que nos diga algo específico y no solo erro 505 o status 200
        return response
    
@app.route('/run', defaults={'project': {}})
@app.route('/run/<project>', methods=['GET'])
def run_monitor(project):
    return mainMethod(project)

if __name__ == "__main__":
    app.run(load_dotenv=True)
    