from flask import Flask, request, redirect
from twilio.twiml.messaging_response import MessagingResponse
import os
import csv
import datetime
import matplotlib.pyplot as plt

app = Flask(__name__)

@app.route("/sms", methods=['GET', 'POST'])
def incoming_sms():
    # Get the message the user sent our Twilio number
    incomingMessage = request.values.get('Body', None).lower()
    splitMessage = incomingMessage.split()
    userNum = request.values.get('From', None)
    date = datetime.datetime.now()
    path = "./data/" + userNum + "_" + str(date.year) + ".csv"  # filepath to csv file for specific user

    # Start our TwiML response
    resp = MessagingResponse()

    # if csv doesnt exist for user, create a new one
    if not os.path.exists(path) :
        print('CSV doesn\'t exist. \nCreating ' + path)

        # writing to csv file
        with open(path, 'w') as csvfile:
            # creating a csv writer object, write headers to top
            csv.writer(csvfile).writerow(["month", "day", "amount", "category", "description"])
            csvfile.close()

    try:
        if '.' in splitMessage[0]: # presumably number, do default add
            addEntry(splitMessage, date, path, resp)
        elif splitMessage[0] == 'undo': # undo last add (TODO: add confirmation)
            undoLastEntry(path, resp)
        elif splitMessage[0] == 'report' or splitMessage[0] == 'rep':
            if len(splitMessage) > 1:
                pass
            else:
                createReport(date, userNum, path, resp)
        elif splitMessage[0] == 'aid':
            pass #print help message

        else:
            resp.message("There was a problem - You probably didn't have enough arguments. Try again or send 'aid' for help.")
    
    except Exception as e: # There was some error - send a default error message back
        print(e)
        resp.message("There was a problem. Try again or send 'aid' for help.\nError: " + str(e))
    finally:
        return str(resp)



def addEntry(splitMessage, date, path, resp):
    """AddEntry - add a spending entry to the user's csv file.

    Args:
        splitMessage (String[]): The message the user sent seperated into an array by spaces
        path (String): the file path to the user's csv file
        resp (XML): Twilio TwiML MessagingResponse object for the response text
    """
    amt = "{:.2f}".format(float(splitMessage[0])) # make sure number w/ two decimal points
    category = splitMessage[1]
    description = ''

    if len(splitMessage) > 2: # if there is a description, join all words after [1] to create it
        description = "{:.50s}".format(' '.join(splitMessage[2:])) # truncate to first 50 characters

    # get date set up for csv
    month = date.month
    day = date.day

    # writing to csv file
    with open(path, 'a') as csvfile:
        # creating a csv writer object, write headers to top
        csv.writer(csvfile).writerow([month, day, amt, category, description])
        csvfile.close()

    # TODO: maybe add words of affirmation if spending on good things or staying under a budget
    resp.message('${0} spent on {1}\n\n${2} spent on {1} in total this month'.format(amt, category, '[NEED TO ADD]')) #TODO: make get spending for category for month



def undoLastEntry(path, resp):
    """Undo the last budget entry in the user's CSV file
    TODO: NEED TO MAKE HAVE CONFIRMATION

    Args:
        path ([type]): [description]
        resp ([type]): [description]
    """
    lastLine = None

    with open(path, "r") as csvfile:
        for row in csv.reader(csvfile):
            lastLine = row
        csvfile.close()

    with open(path, "rb+") as csvfile:

        # Move the pointer (similar to a cursor in a text editor) to the end of the file
        csvfile.seek(0, os.SEEK_END)

        # This code means the following code skips the very last character in the file -
        # i.e. in the case the last line is null we delete the last line
        # and the penultimate one
        pos = csvfile.tell() - 1

        # Read each character in the file one at a time from the penultimate
        # character going backwards, searching for a newline character
        # If we find a new line, exit the search
        while pos > 0 and csvfile.read(1) != "\n":
            pos -= 1
            csvfile.seek(pos, os.SEEK_SET)

        # So long as we're not at the start of the file, delete all the characters ahead
        # of this position
        if pos > 0:
            csvfile.seek(pos, os.SEEK_SET)
            csvfile.truncate()
        
        csvfile.close()
    
    resp.message("Deleted " + str(lastLine) + ". Hopefully you meant to do that.") # TODO: NEED TO HAVE A CONFIRMATION, NEEDS TO STATE WHAT THAT LINE BEING DELETED IS
                                                                            # TODO: NEED TO NOT ALLOW DELETING HEADER LINE



def createReport(date, userNum, path, resp):
    # Break up the month by category
    month = str(date.month)
    runningTotal = {}
    totalSpent = 0.0
    with open(path, "r") as csvfile:
        for row in csv.reader(csvfile):
            if row[0] == month:
                amt = float(row[2])
                if not row[3] in runningTotal: # if category not already seen, create new entry
                    runningTotal[row[3]] = amt 
                else: # otherwise add to category
                    runningTotal[row[3]] += amt 
                totalSpent += amt
        csvfile.close()

    # create the response string
    # TODO: Maybe make have an "other" catagory for anything that doesn't end up being a full 2% of the total
    # also create pie chart for mms
    labels = []
    values = []
    piePath = "/static/" + userNum + "_pie.png"
    responseString = "This month you spent ${:.2f}, consisting of:\n".format(totalSpent)
    for k,v in runningTotal.items():   
        responseString += "${:.2f} on {:s}\n".format(v, k)
        labels.append(k)
        values.append(v)
        
    plt.clf() # clear previous pie chart (if there is one)
    plt.pie(values, labels=labels, textprops={"fontsize":20, "fontweight":"bold"}, autopct='%.1f%%') # TODO: Style better (?)
    plt.axis('equal')
    plt.savefig("." + piePath)

    msg = resp.message(responseString)
    msg.media(piePath)


if __name__ == "__main__":
    app.run(debug=True)
