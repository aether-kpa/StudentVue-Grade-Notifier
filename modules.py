
from requests import Session
from bs4 import BeautifulSoup, ResultSet
from smtplib import SMTP
from constants import *
#import psutil
import ujson


class Student:

    def __init__(self, username: str, password: str, email: str, name="placeholder", classes=[]):

        self.name = name
        self.username = username
        self.password = password
        self.email = email
        self.classes = classes
        self.session = Session()
        self.message = Message()

    # Login to StudentVue
    def login(self):

        values = {
            "username": self.username,
            "password": self.password,
            "__VIEWSTATE": "8zl4rfZJu73lQNzZuzIQfbXWACbqd1Gxh4dCbaxYzbLaEeHXbHPnU7pV1nJkiArzMfoWZbBj5vYumsTk7CeB2h3Rx"
                             "qD0Wf+EshHfAyEMsAc=",
            "__EVENTVALIDATION": "CCnv9LCyDAgLVe7TQ6jAXKtZ1xxhQK45jSShNcakKFOtuSj65EXeeocmg8ROTZPENZgWuw7FH8kyTTOv85Z"
                                 "SHeqzZGlYj7xN2Z3WH3SMNsoTj4bICFDj/DctKsjyhSuBhmIYfrJXR6sjf1Rn4vyMqlZ5T0EbL2AqFefiad"
                                 "AYV3U="
        }

        self.session.post(URL, data=values)

    # Get student's name
    def getName(self):
        pass

    # Used for new students: get the names and links of all classes
    def getClasses(self):

        page = self.session.get("https://rcsvue.rochester.k12.mi.us/PXP_Gradebook.aspx?AGU=0")
        soup = BeautifulSoup(str(page.content), features="html.parser")
        rows = soup.find_all("tr", {"class": ["altrow1", "altrow2"]})

        '''Each class has a blocks of links that describe each of its columns. All of the <a> tags are found
           in each row, and the second <a> tag contains all of the useful information.'''
        for link_block in rows:

            a_tag_list = link_block.find_all("a")
            name = a_tag_list[1].string

            # Added because Jazz Band would get cut off since it didn't have S2 in it
            if "S1" in name or "S2" in name:
                name = a_tag_list[1].string[:-12]
            else:
                name = a_tag_list[1].string[:-8]

            link = a_tag_list[1]["href"]
            self.classes.append(Class(name, link))

    # Update all grades for student
    def updateAssignments(self):

        for course in self.classes:
            course.getAssignments(self.session)

    def constructMessage(self):

        self.message.constructMessage(self.classes, self.name)

    def sendEmail(self, message: str, subject="Grade Update"):

        self.message.sendEmail(message, self.email, subject)

class Assignment:

    def __init__(self, name: str, score: tuple):

        self.name = name
        self.score = score

    def calculatePercent(self) -> str:

        percentage = ""

        numerator = float(self.score.split("/")[0])
        denominator = float(self.score.split("/")[1])

        if denominator == 0:
            self.score = "+" + str(numerator) + " (EC)"
            percentage = ""
        else:
            percentage = str((numerator/denominator) * 100)

        percentage = percentage[0:6]

        return percentage


class Class:

    def __init__(self, name: str, url: str, grade="0%", old_grade="0%", ):

        self.name = name
        self.url = url
        self.grade = "0%"
        self.old_grade = "0%"
        self.assignments = []
        self.message = []

    # Removes extra altrows due to some classes weighing homework and tests differently
    @staticmethod
    def alternateRowRemover(rows: ResultSet) -> tuple:

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

    # Get all assignments for a class
    def getAssignments(self, session: Session):

        # Go to class page
        page = session.get("https://rcsvue.rochester.k12.mi.us/" + self.url)
        html = BeautifulSoup(str(page.content), features="html.parser")

        # Get all of the rows of grades
        rows = html.find_all("tr", {"class": ["altrow1", "altrow2"]})

        # Remove extra altrows
        rows, multiple = self.alternateRowRemover(rows)

        # If there are no assignments posted go to the next class
        if "There are no assignments" in str(rows[0]):
            self.grade = 0.0
            return

        # Grabs the name and point value from each grade block
        for grade_block in rows:
            a_tag_list = grade_block.find_all("a")

            name = a_tag_list[1].string
            points = a_tag_list[6].string

            # Mark assignment ungraded if it has the word "possible" in it
            graded = True

            # Added try statement because if score box is left blank that shifts the number of <a> tags to the left one
            try:
                if "Possible" in points:
                    graded = False

            except TypeError:
                points = a_tag_list[5].string

                if "Possible" in points:
                    graded = False

            assignment = Assignment(name, points)

            # If the assignment is new, add it to the message and the list of things that have been graded
            if not self.assignmentNameInList(assignment) and graded:
                self.message.append(assignment)
                self.assignments.append(assignment)

        # Update overall grade
        self.updateOverallGrade(html, multiple)

    # Check if assignment's name already exists in data
    def assignmentNameInList(self, assignment: Assignment) -> bool:

        for homework in self.assignments:
            if assignment.name == homework.name:
                return True

        return False


    # Update overall class grade of student
    def updateOverallGrade(self, html: BeautifulSoup, multiple: int):

        # Finds letter grade in class
        rows = html.find_all("tr", {"class": "row_subhdr"})

        # If class has extra altrows remove those
        if multiple:
            rows = rows[multiple:]

        string = str(rows[-1])

        self.old_grade = self.grade
        self.grade = string[string.find("("):string.find(")") + 1]
        self.grade = self.grade.replace("(", "").replace(")", "")


class Message:

    def __init__(self):

        self.text = ""

    def constructMessage(self, classes: list, name: str):

        self.text += "Your grades have been updated " + name + "! \n \n"

        for course in classes:
            for assignment in course.message:
                if course.name not in self.text:
                    if self.classNamesInMessage(classes):
                        self.text += "\n \n \n"

                    self.text += course.name + " (" + str(course.old_grade) + " to " + str(course.grade) + "): \n"

                self.text += "\n" + assignment.name + ": " + assignment.score

                percent = assignment.calculatePercent()

                if percent != "":
                    self.text += " (" + percent + "%)"

    # Checks if any class names are in the message for formatting purposes
    def classNamesInMessage(self, classes: list) -> bool:

        for course in classes:
            if course.name in self.text:
                return True
        return False

    # Connects to SMTP server and sends email
    def sendEmail(self, message: str, email: str, subject: str):

        #print(message)

        #print(psutil.cpu_percent())
        #print(psutil.virtual_memory())

        server = SMTP("smtp.gmail.com", 587)
        server.connect("smtp.gmail.com", 587)
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(SENDER_USERNAME, SENDER_PASSWORD)

        message = 'Subject: {}\n\n{}'.format(subject, message)

        server.sendmail(SENDER_USERNAME, email, message)
        server.quit()
