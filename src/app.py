from flask import Flask
from flask import send_file
import requests
from flask import Response
import json
import datetime
from email.message import EmailMessage
import smtplib
import ssl
import time


app = Flask(__name__)

services = ["maxmin", "score", "risk"]

@app.route('/')
def idleState():
    while True:
        monitor()
        time.sleep(900)


@app.route('/log')
def downloadLog():
    path = 'log.json'
    return send_file(path, as_attachment=True)


@app.route('/delete')
def deleteFile():

    now = datetime.datetime.now()

    initObj = {
        "log init date/time": now
    }

    j = json.dumps(initObj, indent=4, sort_keys=True, default=str)

    with open('log.json', 'w') as outfile:
        outfile.write(j)

    return respond(json.dumps({"message": "Log reset"}), 200)


def monitor():

    attempts = 0

    while attempts < 10:

        try:

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
                            "score": 20
                        }
                    },
                    "risk": {
                        "lines": [
                            "Significant risk of failure - more engagement needed"
                        ]
                    }
                }

            } ## test cases

            results = []

            for service in services:
                results.append(test(service, validCase))

            now = datetime.datetime.now()

            testObj = {
                "date/time": now,
                "tests": results
            }

            j = json.dumps(testObj, indent=4, sort_keys=True, default=str)

            with open('log.json', 'a') as outfile:
                outfile.write(",\n" + j)

            return "Success"

        except:
            
            print("Unexpected error... Trying again 🙃")

            attempts += 1
    
    return f"Failure on {attempts} attempts"


def test(service, validCase):

    working = True

    ep = "http://localhost:8888/?" ## TODO detect cloud/local
    for key, value in validCase["inputs"]:
        ep += key + "=" + str(value) + "&"

    r = requests.get(ep).content
    r = json.loads(r)

    expected = validCase["expected"][service]

    if r["error"] == True:
        print(service+" returned an error")
        sendEmail("Ah, Sam? ... You might wanna look at this.")
        working = False
    else:

        ## Iterate through expected results
        for key, value in expected:
            if r[key]:
                if key == "data":
                    for datakey, datavalue in value:
                        if r["data"][datakey] and r["data"][datakey] == datavalue:
                            print("Result item matched expected: "+datavalue)
                        else:
                            working = False
                            print(f"Result item {r['data'][datakey]} did not match expected {datavalue}")
                elif key == "lines" and len(value) == len(r["lines"]):
                    for line in value:
                        if line in r["lines"]:
                            print("Expected line found in results")
                        else:
                            working = False
                            print("Expected line not found in results")
                else:
                    working = False
                    print("Result contained the wrong number of lines")

            else:
                working = False
                print("Result did not contain the expected keys")            

           
        latency = requests.get(ep).elapsed.total_seconds()


def respond(r, statusCode):
    response = Response(response=r, status=statusCode, mimetype="application/json")
    response.headers["Access-Control-Allow-Origin"]="*"
    return response

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

    with smtplib.SMTP_SSL("stmp.gmail.com", 465, context=context) as smtp:
        smtp.login(sender, password)
        smtp.sendmail(sender, recipient, em.as_string())


if __name__ == "__main__":
    app.run(host = "0.0.0.0", port=80)