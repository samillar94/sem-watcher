from email.message import EmailMessage
import smtplib
import ssl
import time
import json
import datetime
import requests
import os
from dotenv import load_dotenv

load_dotenv()

print("monitor did its imports", flush=True)



## GLOBAL VARS

PASSWORD = os.getenv("PASSWORD")

services = ["maxmin", "sort", "total", "score", "risk", "percents"] 

testCases = {
    "valid1": {
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
                    "Maximum attendance:",
                    "- Canvas activities: 8 hours",
                    "Minimum attendance:",
                    "- Lecture sessions: 5 hours"
                ]
            },
            "sort": {
                "lines": [
                    "Canvas activities: 8 hours",
                    "Support sessions: 7 hours",
                    "Lab sessions: 6 hours",
                    "Lecture sessions: 5 hours"
                ]
            },
            "total": {
                "data": {
                    "total": 26
                }
            },
            "score": {
                "data": {
                    "score": 0.20022727272727275
                }
            },
            "risk": {
                "data": {
                    "risky": True
                }
            },
            "percents": {
                "lines": [
                    "Lecture sessions: 15% attendance",
                    "Lab sessions: 27% attendance",
                    "Support sessions: 16% attendance",
                    "Canvas activities: 9% attendance"
                ]
            }

        }
    },
    "valid2": {
        "inputs": {
            "a1": 5,
            "a2": 22,
            "a3": 44,
            "a4": 38,
            "c": 70
        },
        "expected": {
            "risk": {
                "data": {
                    "risky": True
                }
            }

        }
    },
    "valid3": {
        "inputs": {
            "a1": 5,
            "a2": 22,
            "a3": 44,
            "a4": 39,
            "c": 70
        },
        "expected": {
            "risk": {
                "data": {
                    "risky": False
                }
            }

        }
    },
    "invalid1": {
        "inputs": {
            "a1": 5555,
            "a2": 6,
            "a3": 7,
            "a4": 8,
            "c": 70
        },
        "expected": {
            "risk": {
                "error": True
            }
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

            results = {}

            for service in services:
                try:
                    results[service] = test(service)
                except Exception as e:
                    print("Hmmm.\n"+{str(e)})

            now = datetime.datetime.now()

            testObj = {
                "date/time": now,
                "tests": results
            }

            j = json.dumps(testObj, indent=4, sort_keys=True, default=str)
            
            print("About to write: "+j)

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

    report = {}

    for suitename, suite in testCases.items():

        responding = False
        working = False
        passed = False
        latency = None

        ep = "http://sem-proxy.40103709.qpc.hal.davecutting.uk/?service="+service 
        for param, case in suite["inputs"].items():
            ep += "&" + param + "=" + str(case) 

        print(f"ep = {ep}")
        notes = [f"Endpoint: {ep}"]

        r = requests.get(ep).content
        r = json.loads(r)

        print(f"r = {r}")
        notes.append(f"Response: {str(r)}")

        try:
            expected = suite["expected"][service] 
        except:
            continue

        try:

            if "error" not in r:
                raise Exception("Bad response from the service")
                break
            # elif r["error"]:
            #     responding = True
            #     raise Exception(service+" returned an error")
            else:
                responding = True
                working = True
                ## Iterate through expected results
                for key, value in expected.items():
                    if key in r:
                        if key == "data":
                            for datakey, datavalue in value.items():
                                if r["data"][datakey] and r["data"][datakey] == datavalue:
                                    print("Result item matched expected: "+str(datavalue))
                                    passed = True
                                else:
                                    raise Exception(f"Result item {str(r['data'][datakey])} did not match expected {str(datavalue)}")
                        elif key == "lines" and len(value) == len(r["lines"]):
                            for line in value:
                                if line in r["lines"]:
                                    print("Expected line found in results")
                                    passed = True
                                else:
                                    raise Exception("Expected line not found in results")
                        elif key == "error":
                            if r["error"] == value:
                                print("Error returned as expected")
                                passed = True
                            else:
                                raise Exception("Query should have thrown an error but didn't")
                        else:
                            raise Exception("Result contained the wrong number of lines")
                    else:
                        raise Exception("Result did not contain the expected keys")            

        except Exception as e:
            notes.append("Error: "+str(e))
            print("The "+service+" service is not working properly: "+str(e))
            sendEmail("The "+service+" service is not working properly:\n\n"+str(e))

        latency = requests.get(ep).elapsed.total_seconds()

        report[suitename] = {"responding": responding, "working": working, "passed": passed, "latency": latency, "notes": notes}

    return report


def sendEmail(text):
    sender = "smillar36qub@gmail.com"
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
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as smtp:
            smtp.login(sender, PASSWORD)
            smtp.sendmail(sender, recipient, em.as_string())
    except Exception as e:
        print("Couldn't send the email, sorry: "+str(e))


def idleState():
    print("idleState() run")
    while True:
        monitor()
        print("monitor() completed", flush=True)
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


## PROGRAM

idleState()