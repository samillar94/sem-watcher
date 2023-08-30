from flask import Flask
from flask import send_file
from flask import Response
import json
import datetime
import subprocess


## FLASK APP

app = Flask(__name__)


## DESPARATELY TRYING TO GET DOCKER TO PRINT ANYTHING

app.logger.info("well, we got the imports done")
print("Hello, Docker! flushed", flush=True)
print("Hello, Docker!")


## GLOBAL VARS

logpath = 'log.json'


## FUNCTIONS

def respond(r, statusCode):
    try:
        response = Response(response=r, status=statusCode, mimetype="application/json")
        response.headers["Access-Control-Allow-Origin"]="*"
        return response
    except:
        return "Error in respond() function"


## ROUTES

@app.route('/')
def report():
    try:
        with open(logpath, 'r') as logfile:
            log = json.load(logfile)
            return respond(json.dumps(log), 200)
    except:
        return respond('\{"message": "Couldn\'t load log path '+logpath+'"}', 400)


@app.route('/log')
def downloadLog():
    return send_file(logpath, as_attachment=True)


@app.route('/delete')
def deleteFile():

    now = datetime.datetime.now()

    initObj = [{
        "log init date/time": now
    }]

    j = json.dumps(initObj, indent=4, sort_keys=True, default=str)

    with open(logpath, 'w') as outfile:
        outfile.write(j)

    return respond(json.dumps({"message": "Log reset"}), 200)


@app.route('/refresh')
def restartMonitor():
    subprocess.run('supervisorct1','restart','monitor_script')
    return respond(json.dumps({"message": "Monitor restarted - new results available shortly"}), 200)


## PROGRAM

if __name__ == "__main__":
    app.run(host = "0.0.0.0", port=80, debug=True)



