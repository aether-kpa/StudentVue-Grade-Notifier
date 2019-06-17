
from requests import Session
from smtplib import SMTP
from bs4 import BeautifulSoup
from ast import literal_eval
import grades


# Gets course names and links to classes as well as current grade
def get_courses(session):

    # Get html from gradebook page and scrape it to get the rows where classes are listed
    page = session.get("https://rcsvue.rochester.k12.mi.us/PXP_Gradebook.aspx?AGU=0")
    soup = BeautifulSoup(str(page.content), features="html.parser")
    rows = soup.find_all("tr", {"class": ["altrow1", "altrow2"]})

    classes = {}

    '''Each class has a blocks of links that describe each of its columns. All of the <a> tags are found
       in each row, and the second <a> tag contains all of the useful information.'''
    for link_block in rows:
        a_tag_list = link_block.find_all("a")

        name = a_tag_list[1].string[:-12]
        link = a_tag_list[1]["href"]
        classes.update({name: link})

    return classes


# Checks if a class has already been included in the message (used to format later lines)
def classnames_in_message(classlist, message):
    for key in classlist.keys():
        if key in message:
            return True
    return False


def add_user():
    url = "https://rcsvue.rochester.k12.mi.us/Login_Student_PXP.aspx"
    username = input("What is your StudentVue username?")
    password = input("What is your StudentVue password?")
    email = input("What is the email you want the updates to be sent to? \n")

    values = {"__VIEWSTATE": "8zl4rfZJu73lQNzZuzIQfbXWACbqd1Gxh4dCbaxYzbLaEeHXbHPnU7pV1nJkiArzMfoWZbBj5vYumsTk7CeB2h3Rx"
                             "qD0Wf+EshHfAyEMsAc=",
              "__EVENTVALIDATION": "CCnv9LCyDAgLVe7TQ6jAXKtZ1xxhQK45jSShNcakKFOtuSj65EXeeocmg8ROTZPENZgWuw7FH8kyTTOv85Z"
                                   "SHeqzZGlYj7xN2Z3WH3SMNsoTj4bICFDj/DctKsjyhSuBhmIYfrJXR6sjf1Rn4vyMqlZ5T0EbL2AqFefiad"
                                   "AYV3U=",
              "username": "karora4561",
              "password": "rcska6046"}

    print("Username: " + username)
    print("Password: " + password)
    print("Email: " + email + "\n")

    correct = input("Is this information correct? (Y/N)")
    correct = correct.upper()

    grades1 = grades.information

    while correct != "N" and correct != "Y":
        correct = input("Please enter a valid answer. (Y/N)")
        correct = correct.upper()

    while correct == "N":
        print("Re-enter the information. \n")

        username = input("What is your StudentVue username?")
        password = input("What is your StudentVue password?")
        email = input("What is the email you want the updates to be sent to? \n")

        correct = input("Is this information correct? (Y/N)")
        correct = correct.upper()

        while correct != "N" and correct != "Y":
            correct = input("Please enter a valid answer. (Y/N)")

        session = Session()

        # Login to page and gather class information
        session.post(url, data=values)
        classes = get_courses(session)

        for index, key, value in enumerate(classes.items()):

            # Resets variables
            tracker = {}

            # Go to each class page
            page = session.get("https://rcsvue.rochester.k12.mi.us/" + value)
            html = BeautifulSoup(str(page.content), features="html.parser")

            # Get all of the rows of grades
            rows = html.find_all("tr", {"class": ["altrow1", "altrow2"]})

            # Remove extra altrows
            rows, multiple = alt_row_remover(rows)

            # If there are no assignments posted go to the next class
            if "There are no assignments" in str(rows[0]):
                continue

            # Grabs the name and point value from each grade block
            for grade_block in rows:
                a_tag_list = grade_block.find_all("a")

                name = a_tag_list[1].string
                points = a_tag_list[6].string

                # Mark assignment ungraded if it has the word "possible" in it
                graded = True

                if "Possible" in points:
                    graded = False

                grades1.information[username][str(index)].update({name: graded})

        grades1.information[username].update({"email": email})
        print(grades1)


# Removes extra altrows due to some classes weighing homework and tests differently
def alt_row_remover(rows):
    counter = 0
    multiple = 0

    while counter < len(rows):
        try:
            if "%" in rows[counter].find_all("td")[1].string:
                rows.remove(rows[counter])
                counter = 0
                multiple += 1
                continue

        except IndexError:
            pass

        counter += 1

    return rows, multiple


# Connects to SMTP server and sends email
def send_email(message, username, password):
    message = "Your grades have been updated Karan Arora! \n \n" + message

    server = SMTP("smtp.gmail.com", 587)
    server.connect("smtp.gmail.com", 587)
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login(username, password)

    subject = "Grade Update"
    message = 'Subject: {}\n\n{}'.format(subject, message)

    server.sendmail("karanarora2001@gmail.com", "karanarora2001@gmail.com", message)
    server.quit()


def main():

    url = "https://rcsvue.rochester.k12.mi.us/Login_Student_PXP.aspx"
    email_username = "karanarora2001@gmail.com"
    email_password = "molangman"

    # RCS Login Credentials
    values = {"__VIEWSTATE": "8zl4rfZJu73lQNzZuzIQfbXWACbqd1Gxh4dCbaxYzbLaEeHXbHPnU7pV1nJkiArzMfoWZbBj5vYumsTk7CeB2h3Rx"
                             "qD0Wf+EshHfAyEMsAc=",
              "__EVENTVALIDATION": "CCnv9LCyDAgLVe7TQ6jAXKtZ1xxhQK45jSShNcakKFOtuSj65EXeeocmg8ROTZPENZgWuw7FH8kyTTOv85Z"
                                   "SHeqzZGlYj7xN2Z3WH3SMNsoTj4bICFDj/DctKsjyhSuBhmIYfrJXR6sjf1Rn4vyMqlZ5T0EbL2AqFefiad"
                                   "AYV3U=",
              "username": "karora4561",
              "password": "rcska6046"}

    # Message to be sent to the user and the string of text to be written to grades.txt
    message = ""
    write = ""

    session = Session()

    # Login to page and gather class information
    session.post(url, data=values)
    classes = get_courses(session)

    # add_user()
    # return

    f = open("grades.txt", "r")

    for key, value in classes.items():

        # Resets variables
        tracker = {}
        multiple = 0

        # Go to each class page
        page = session.get("https://rcsvue.rochester.k12.mi.us/" + value)
        html = BeautifulSoup(str(page.content), features="html.parser")

        # Get all of the rows of grades
        rows = html.find_all("tr", {"class": ["altrow1", "altrow2"]})

        # Remove extra altrows
        rows, multiple = alt_row_remover(rows)

        # If there are no assignments posted go to the next class
        if "There are no assignments" in str(rows[0]):
            tracker.update({'grade': "0.0"})
            write += str(tracker) + "\n"
            f.readline()
            continue

        # Translates stored data from file into dict
        currentgrades = literal_eval(f.readline())

        # Grabs the name and point value from each grade block
        for grade_block in rows:
            a_tag_list = grade_block.find_all("a")

            name = a_tag_list[1].string
            points = a_tag_list[6].string

            # Mark assignment ungraded if it has the word "possible" in it
            graded = True

            if "Possible" in points:
                graded = False

            tracker.update({"grade": currentgrades["grade"]})

            '''If the assignment has been graded and is not in the dict or it is ungraded in the 
               dict but graded on the website it is a new notification.'''
            try:
                if (name not in currentgrades.keys() and graded) or graded != currentgrades[name]:

                    # If the class's name has not been added
                    if key not in message:

                        # Finds letter grade in class
                        rows = html.find_all("tr", {"class": "row_subhdr"})

                        # If class has extra altrows remove those
                        if multiple:
                            rows = rows[multiple:]

                        string = str(rows[-1])
                        overall_grade = string[string.find("("):string.find(")") + 1]
                        old_grade = currentgrades["grade"]

                        tracker.update({"grade": overall_grade})

                        # Checks if the message already contains information (for formatting purposes)
                        if classnames_in_message(classes, message):
                            message += "\n \n"

                        message += key + " " + old_grade + " to " + overall_grade + ":"

                    # Calculate percentage grade on assignment
                    percent = (float(points.split("/")[0])) / (float(points.split("/")[1])) * 100
                    percent = str(percent)[0:6]
                    message += "\n" + name + ": " + points + " (" + percent + "%)"

            except KeyError:
                pass

            # Update assignment dict
            tracker.update({name: graded})
	    #print(tracker)

        # Update the text that is to be written to grades.txt with the new information from tracker
        write += str(tracker) + "\n"

    f.close()

    # Write text
    f = open("grades.txt", "w")
    f.write(write)
    f.close()

    # If the message has contents in it, email it to the user
    if message.replace("\n", ""):
        print(message)
        send_email(message, email_username, email_password)


main()
