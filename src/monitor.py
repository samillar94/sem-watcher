from email.message import EmailMessage
import smtplib
import ssl
import time
import json
import datetime
import requests

print("monitor did its imports", flush=True)


## GLOBAL VARS

services = ["maxmin", "score", "risk"]

validCase = {
    "inputs": {
        "a1": 5,
        "a2": 6,
        "a3": 7,
        "a4": 8,
        "c": 70
    },
    "expected": {
        "maxmin": {
            "lines": [
                "Maximum attendance: Canvas activities: 8 hours",
                "Minimum attendance: Lecture sessions: 5 hours"
            ]
        },
        "score": {
            "data": {
                "score": 0.20022727272727275
            }
        },
        "risk": {
            "lines": [
                "Significant risk of failure - more engagement needed"
            ]
        }
    }

} 

logfilename = 'log.json'


## FUNCTIONS

def monitor():

    attempts = 0

    while attempts < 10:

        try:

            print("monitor() attempt started")

            results = []

            for service in services:
                results.append(test(service))

            now = datetime.datetime.now()

            testObj = {
                "date/time": now,
                "tests": results
            }

            j = json.dumps(testObj, indent=4, sort_keys=True, default=str)
            
            print("About to write "+j)

            removeLastCharacter(logfilename)

            with open(logfilename, 'a') as outfile:
                outfile.write(",\n" + j + "]")
                print("Written")

            return "Success"

        except Exception as e:
            
            print(f"Unexpected error: {e} \nTrying again")

            attempts += 1
    
    return f"Failure on {attempts} attempts"


def test(service):

    print(f"\ntest({service}) started")

    working = False

    ep = "http://sem-proxy.40103709.qpc.hal.davecutting.uk/?service="+service 
    for key, value in validCase["inputs"].items():
        ep += "&" + key + "=" + str(value) 

    print(f"ep = {ep}")
    r = requests.get(ep).content
    r = json.loads(r)

    print(f"r = {r}")

    expected = validCase["expected"][service]

    if "error" not in r:
        print("Bad response from the service")
    elif r["error"]:
        print(service+" returned an error")
        sendEmail("Ah, Sam? ... You might wanna look at this.")
    else:

        ## Iterate through expected results
        for key, value in expected.items():
            if r[key]:
                if key == "data":
                    for datakey, datavalue in value.items():
                        if r["data"][datakey] and r["data"][datakey] == datavalue:
                            print("Result item matched expected: "+str(datavalue))
                            working = True
                        else:
                            print(f"Result item {str(r['data'][datakey])} did not match expected {str(datavalue)}")
                elif key == "lines" and len(value) == len(r["lines"]):
                    for line in value:
                        if line in r["lines"]:
                            print("Expected line found in results")
                            working = True
                        else:
                            print("Expected line not found in results")
                else:
                    print("Result contained the wrong number of lines")
            else:
                print("Result did not contain the expected keys")            

        latency = requests.get(ep).elapsed.total_seconds()
        print("Latency: "+str(latency))

    return service+"-validCase-working: "+str(working)




def sendEmail(text):
    sender = ""
    password = ""
    recipient = "40103709@ads.qub.ac.uk"

    subject = "sem-watcher brings grave tidings"
    body = text

    em = EmailMessage()
    em["From"] = sender
    em["To"] = recipient
    em["Subject"] = subject
    em.set_content(body)

    context = ssl.create_default_context()

    try:
        with smtplib.SMTP_SSL("stmp.gmail.com", 465, context=context) as smtp:
            smtp.login(sender, password)
            smtp.sendmail(sender, recipient, em.as_string())
    except:
        print("Couldn't send the email, sorry")

def idleState():
    print("idleState() run")
    while True:
        monitor()
        print("monitor() completed")
        time.sleep(900)

## GPT-3.5 function
def removeLastCharacter(filename):
    with open(filename, 'r') as file:
        content = file.read()

    if content:
        new_content = content[:-1]

        with open(filename, 'w') as file:
            file.write(new_content)

def reset(): ## not used
    now = datetime.datetime.now()

    initObj = [{
        "log init date/time": now
    }]

    j = json.dumps(initObj, indent=4, sort_keys=True, default=str)

    with open(logfilename, 'w') as outfile:
        outfile.write(j)


## MAIN

idleState()