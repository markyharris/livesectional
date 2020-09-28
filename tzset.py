import subprocess
from flask import Flask, render_template, request, flash, redirect, url_for, send_file, Response

#Initiate flash session
app = Flask(__name__)


#Route to display system information.
@app.route('/tzset')
def tzset():
    tzlist = subprocess.run(['timedatectl', 'list-timezones'], stdout=subprocess.PIPE).stdout.decode('utf-8')
#    print(tzlist)


    return render_template('tzset.html', tzlist = tzlist)


#executed code
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=6000)
