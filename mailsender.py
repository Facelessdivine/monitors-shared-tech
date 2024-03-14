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

def process_url(url, recipients, results):
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
                send_email(f"{url} failed: {failed}", html, recipients)
                logging.warning(f"Some services are failing in the {url} Monitor: {failed}")
                results.append(False)
    finally:
        pythoncom.CoUninitialize()

if __name__ == "__main__":
    # Configurar el registro de eventos
    logging.basicConfig(filename=os.path.abspath('monitor.log'), level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    while True:
        monitorsURLS = [
             "https://vmq-alfrescona-02.alldata.com:8446/cpp/monitor",
            "https://vmq-alfrescoeu-01.alldata.com:8446/cpp/monitor",
            "http://vmq-alfrescona-02.alldata.com:8091/monitor",
            "http://vmq-alfrescoeu-01.alldata.com:8091/monitor",
            "https://vmq-alfrescona-02.alldata.com:8445/pet/monitor"
        ]
        
        threads = []
        results = []
        recipients = ["raul.herrera@autozone.com"]
        # recipients = ["raul.herrera@autozone.com", "saul.bravo@autozone.com"]
        for url in monitorsURLS:
            thread = threading.Thread(target=process_url, args=(url,recipients, results))
            thread.start()
            threads.append(thread)
        os.system('cls')

        for thread in threads:
            thread.join()
            
        if any(item is None for item in results):
            logging.error("One or more connections are down, please verify connection!")
            print("\n Error: One or more connections are down, please verify connection ! \n")            
        elif not all(results):
            logging.warning("Some of the monitors have services in failure status")
            print("\n Some of the monitors have services in failure status \n")
            # send_email("Monitors failed", "Some of the monitors have services in failure status. Please verify email.", recipients)
            print(" \n Waiting before checking again \n")
#            break
        else:
            logging.info("All the services of all the monitors are working correctly")
            print("\n All the services of all the monitors are working correctly \n")
        countdown(3600)
        os.system('cls')
