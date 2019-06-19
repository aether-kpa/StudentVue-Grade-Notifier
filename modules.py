
from requests import Session
from bs4 import BeautifulSoup, ResultSet
from smtplib import SMTP
from constants import *

class Assignment:

    def __init__(self, name: str, score: tuple, graded: bool):

        self.name = name
        self.score = score
        self.graded = graded

        if score[1] == 0:
            self.score = "+" + str(score[0]) + " (EC)"
            self.percentage = ""
        else:
            self.percentage = float(score[0] / score[1]) * 100


class Class:

    def __init__(self, name: str, url: str, grade):

        self.name = name
        self.url = url
        self.grade = 0
        self.old_grade = 0
        self.assignments = []

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
    def getAssignments(self, session: Session) -> dict:

        message = {}

        # Go to class page
        page = session.get("https://rcsvue.rochester.k12.mi.us/" + self.url)
        print("https://rcsvue.rochester.k12.mi.us/" + self.url)
        html = BeautifulSoup(str(page.content), features="html.parser")

        # Get all of the rows of grades
        rows = html.find_all("tr", {"class": ["altrow1", "altrow2"]})

        # Remove extra altrows
        rows, multiple = self.alternateRowRemover(rows)

        # If there are no assignments posted go to the next class
        if "There are no assignments" in str(rows[0]):
            self.grade = 0.0
            return message

        # Grabs the name and point value from each grade block
        for grade_block in rows:
            a_tag_list = grade_block.find_all("a")

            name = a_tag_list[1].string
            points = a_tag_list[6].string

            # Mark assignment ungraded if it has the word "possible" in it
            graded = True

            if "Possible" in points:
                graded = False

            assignment = Assignment(name, points, graded)

            if self.newAssignment(assignment):
                message.update({self.name: assignment})

            self.assignments.append(Assignment(name, points, graded))

        # Update overall grade
        self.updateOverallGrade(html, multiple)

        return message

    #Check if assignment's name already exists in data
    def assignmentNameInList(self, assignment: Assignment) -> bool:

        for homework in self.assignments:
            if assignment.name == homework.name:
                return True

        return False

    # Check if assignment is ungraded in data but graded in new check
    def differentGradedStatus(self, assignment: Assignment) -> bool:

        for homework in self.assignments:
            if assignment.name == homework.name:
                if assignment.graded != homework.graded:
                    return True

        return False

    # Combine previous two methods to determine if message should be constructed to email student
    def newAssignment(self, assignment: Assignment) -> bool:

        if not self.assignmentNameInList(assignment):
            if assignment.graded:
                return True

        elif self.differentGradedStatus(assignment):
            return True

        return False

    # Overcall class grade of student
    def updateOverallGrade(self, html: BeautifulSoup, multiple: int):

        # Finds letter grade in class
        rows = html.find_all("tr", {"class": "row_subhdr"})

        # If class has extra altrows remove those
        if multiple:
            rows = rows[multiple:]

        string = str(rows[-1])

        self.old_grade = self.grade
        self.grade = string[string.find("("):string.find(")") + 1]


class Student:

    def __init__(self, username: str, password: str, email: str, name="a"):

        self.name = name
        self.username = username
        self.password = password
        self.email = email
        self.classes = []
        self.session = Session()
        self.message = Message()

        self.login()
        self.getClasses()

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
            self.message.data.update(course.getAssignments(self.session))


class Message:

    def __init__(self):

        self.data = {}

    def constructMessage(self):

        text = ""

        for course, assignment in self.data.items():
            if course not in text:



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
                        try:
                            percent = (float(points.split("/")[0])) / (float(points.split("/")[1])) * 100
                        except ZeroDivisionError:
                            pass
                        percent = str(percent)[0:6]
                        message += "\n" + name + ": " + points + " (" + percent + "%)"

                except KeyError:
                    pass

                # Update assignment dict
                tracker.update({name: graded})
                # print(tracker)

            # Update the text that is to be written to grades.txt with the new information from tracker
            write += str(tracker) + "\n"

    # Connects to SMTP server and sends email
    def sendEmail(self, message, subject="Grade Update"):
        message = "Your grades have been updated Karan Arora! \n \n" + message

        server = SMTP("smtp.gmail.com", 587)
        server.connect("smtp.gmail.com", 587)
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(SENDER_USERNAME, SENDER_PASSWORD)

        message = 'Subject: {}\n\n{}'.format(subject, message)

        server.sendmail(SENDER_USERNAME, self.email, message)
        server.quit()

    def sendWelcome(self):
        pass
