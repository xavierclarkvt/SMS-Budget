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
        elif splitMessage[0] == 'report' or splitMessage[0] == 'rep': # create report of spending
            if len(splitMessage) > 1: # custom year or last month chosen
                repMonth = '-1'
                if splitMessage[1] == 'last': # get last month's data
                    repDate = date - datetime.timedelta(weeks = 4)
                    splitMessage[1] = str(repDate.year)
                    print(repDate)
                    repMonth = str(repDate.month)
                newPath = "./data/" + userNum + "_" + splitMessage[1] + ".csv"  # filepath to csv file for specific user
                createReport(repMonth, userNum, newPath, resp)
            else:
                createReport(str(date.month), userNum, path, resp)
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
    """Add a spending entry to the user's csv file.

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

    categoryTotal = float(amt)

    # writing to csv file
    with open(path, 'r+') as csvfile:
        for row in csv.reader(csvfile):
            print(row)
            if row[0] == month and row[3] == category:
                print("^chosen^")
                categoryTotal += row[2]
        # creating a csv writer object, write new entry at bottom
        csv.writer(csvfile).writerow([month, day, amt, category, description])
        csvfile.close()

    # TODO: maybe add words of affirmation if spending on good things or staying under a budget
    resp.message('${:s} spent on {:s}\n\n${:.2f} spent on {:s} in total this month'.format(amt, category, categoryTotal, category)) 



def undoLastEntry(path, resp):
    """Undo the last budget entry in the user's CSV file
    TODO: NEED TO MAKE HAVE CONFIRMATION

    Args:
        path ([type]): [description]
        resp (XML): Twilio TwiML MessagingResponse object for the response text
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


def createReport(month, userNum, path, resp):
    """Create a user's spending report for a specific month, for a specific year. 
    Also generate a PNG of a pie chart with matplotlib to send to the user, if entries for the given month are found.
    If no entries are found, or PATH doesn't exist, return an error message

    When preparing the pie chart, places any categories with a total amt less than 3% of the total spent into "Other" category.
    This makes the pie chart slightly cleaner.

    Unfortunately, needs to step though every line (so may be a little resource intensive)

    Args:
        month (String)): The month you'd like to get data for. 
                        If a negative number, gather data for the whole year (entire csv data) 
        userNum (String): User's iso phone number string, used in filename for pie chart png
        path (String): The path to the CSV you'd like to report over. Year is defined by the csv file PATH is pointing to. 
        resp (XML): Twilio TwiML MessagingResponse object for the response text
    """
    print(month)
    print(userNum)
    print(path)
    print(resp)

    # Break up the month by category
    runningTotal = {}
    totalSpent = 0.0

    if not os.path.exists(path): # file doesn't exist - only happens if year chosen doesn't exist
        resp.message("It seems like there are no entries for that year. Try again?")
        return

    with open(path, "r") as csvfile:
        csvReader = csv.reader(csvfile)
        next(csvReader)
        for row in csvReader:
            print(runningTotal)
            print(row)
            if int(month) < 0 or row[0] == month:
                amt = float(row[2])
                if not row[3] in runningTotal: # if category not already seen, create new entry
                    runningTotal[row[3]] = amt 
                else: # otherwise add to category
                    runningTotal[row[3]] += amt 
                totalSpent += amt
        csvfile.close()
    
    if len(runningTotal) == 0: # no entries for that month, return an error message
        print(runningTotal)
        resp.message("It seems like there are no entries for that month. Are you sure you meant " + str(month) + "?")
        return


    # create the response string
    # also create pie chart for mms
    labels = []
    values = []
    otherTotal = 0.0
    piePath = "/static/" + userNum + "_pie.png"

    dateRange = 'month' # change text based on selection
    if int(month) < 0:
        dateRange = 'year'

    responseString = "This {:s} you spent ${:.2f}, consisting of:\n".format(dateRange, totalSpent)
    for k,v in runningTotal.items():   
        responseString += "\t* ${:.2f} on {:s}\n".format(v, k)
        if v < (0.03 * totalSpent):
            otherTotal += v
        else:
            labels.append(k)
            values.append(v)

    if otherTotal > 0: # if there were values placed into the "other" category
        labels.append('other')
        values.append(otherTotal)
        
    # Create pie chart as png
    plt.pie(values, labels=labels, textprops={"fontsize":20, "fontweight":"bold"}, autopct='%.1f%%') # TODO: Style better (?)
    plt.axis('equal') # needed to make the pie chart a circle
    plt.savefig("." + piePath) # save as png
    plt.clf() # clear previous pie chart (if there is one)

    msg = resp.message(responseString)
    msg.media(piePath)


if __name__ == "__main__":
    app.run(debug=True)
