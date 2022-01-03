# SMS-Budget
A budget-tracking solution utilizing SMS to log transactions into Google Sheets

Notes: Installed twilio helper (`pip install twilio`) and dotEnv (`pip install python-dotenv`) and flask (pip install flask) and matPlotLib (pip install matplotlib).
installed on a super cheap heroku instance - shouldn't need to be powerful.
TODO: add `requirements.txt` (may not be able to use `pip freeze`) (see this link: https://pip.pypa.io/en/stable/topics/repeatable-installs/)

Create a TwiML app first, and then set up a webhook for the specific phone number
Authorize the phone number and set up a webhook for that phone number in twilio

https://github.com/jpillora/node-google-sheets needed for connecting node to gsheets