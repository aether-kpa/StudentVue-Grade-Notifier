
from requests import Session
from bs4 import BeautifulSoup, ResultSet
from smtplib import SMTP
from constants import *
import ujson


class Student:

    '''Default values for some arguments are included because they are updated by the object when a new user is created,
       but then filled in during the deserialization process.'''
    def __init__(self, username: str, password: str, email: str, url: str, name="placeholder", classes=None):

        self.username = username
        self.password = password
        self.email = email
        self.url = url
        self.name = name

        # Avoid argument default value being mutable
        if classes is None:
            self.classes = []
        else:
            self.classes = classes

        self.session = Session()
        self.message = Message()

    # Login to StudentVue
    def login(self) -> bool:

        values = {
            "username": self.username,
            "password": self.password,
            "__VIEWSTATE": "8zl4rfZJu73lQNzZuzIQfbXWACbqd1Gxh4dCbaxYzbLaEeHXbHPnU7pV1nJkiArzMfoWZbBj5vYumsTk7CeB2h3Rx"
                             "qD0Wf+EshHfAyEMsAc=",
            "__EVENTVALIDATION": "CCnv9LCyDAgLVe7TQ6jAXKtZ1xxhQK45jSShNcakKFOtuSj65EXeeocmg8ROTZPENZgWuw7FH8kyTTOv85Z"
                                 "SHeqzZGlYj7xN2Z3WH3SMNsoTj4bICFDj/DctKsjyhSuBhmIYfrJXR6sjf1Rn4vyMqlZ5T0EbL2AqFefiad"
                                 "AYV3U="
        }

        page = self.session.post(self.url + "Login_Student_PXP.aspx", data=values)

        # Return success of login
        soup = BeautifulSoup(str(page.content), features="html.parser")

        if len(soup.find_all("span", {"class": "ERROR"})) > 0:
            return False

        return True

    # Get student's name
    def getName(self) -> None:

        page = self.session.get(self.url + "Home_PXP.aspx")
        soup = BeautifulSoup(str(page.content), features="html.parser")
        text = soup.find("td", {"class": "UserHead"})
        name = text.string.split(" ")
        name = name[2] + " " + name[3]
        name = name.replace(",", "")
        self.name = name

    # Used for new students: get the names and links of all classes
    def getClasses(self) -> None:

        page = self.session.get(self.url + "PXP_Gradebook.aspx?AGU=0")
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
    def updateAssignments(self) -> None:

        for course in self.classes:
            course.getAssignments(self.session, self.url)

    # Tells message object to create the email
    def constructMessage(self) -> bool:

        update = self.message.constructMessage(self.classes, self.name)

        return update

    # Sends email with message specified in arguments
    def sendEmail(self, message: str, subject="Grade Update") -> None:

        Message.sendEmail(message, self.email, subject)


class Class:

    def __init__(self, name: str, url: str, grade="0%", old_grade="0%", graded_assignments=None):

        self.name = name
        self.url = url
        self.grade = grade
        self.old_grade = old_grade

        # Avoid argument default value being mutable
        if graded_assignments is None:
            self.graded_assignments = []
        else:
            self.graded_assignments = graded_assignments

        # Contains new data that the student needs to be updated about
        self.message = {}

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
    def getAssignments(self, session: Session, site_url: str) -> None:

        # Go to class page
        page = session.get(site_url + self.url)
        html = BeautifulSoup(str(page.content), features="html.parser")

        # Get all of the rows of grades
        rows = html.find_all("tr", {"class": ["altrow1", "altrow2"]})

        # Remove extra altrows
        rows, multiple = Class.alternateRowRemover(rows)

        # If there are no assignments posted go to the next class
        if "There are no assignments" in str(rows[0]):
            self.grade = 0.0
            return

        # Grabs the name and point value from each grade block
        for grade_block in rows:
            a_tag_list = grade_block.find_all("a")

            name = a_tag_list[1].string
            score = a_tag_list[6].string

            # Mark assignment ungraded if it has the word "possible" in it
            graded = True

            # Added try statement because if score box is left blank that shifts the number of <a> tags to the left one
            try:
                if "Possible" in score:
                    graded = False

            except TypeError:
                score = a_tag_list[5].string

                if "Possible" in score:
                    graded = False

            # If the assignment is new, add it to the message and the list of things that have been graded
            if name not in self.graded_assignments and graded:
                self.message[name] = score
                self.graded_assignments.append(name)

        # Update overall grade
        self.updateOverallGrade(html, multiple)

    # Calculate percent of score and also fix score string if needed
    def calculatePercent(self, score: str) -> tuple:

        numerator = float(score.split("/")[0])
        denominator = float(score.split("/")[1])

        if denominator == 0:
            score = "+" + str(numerator) + " (EC)"
            percentage = ""
        else:
            percentage = str((numerator/denominator) * 100)

        percentage = percentage[0:6]

        return percentage, score

    # Update overall class grade of student
    def updateOverallGrade(self, html: BeautifulSoup, multiple: int) -> None:

        # Find grade in class
        rows = html.find_all("tr", {"class": "row_subhdr"})

        # If class has extra altrows remove those
        if multiple:
            rows = rows[multiple:]

        string = str(rows[-1])

        self.old_grade = self.grade
        self.grade = string[string.find("("):string.find(")") + 1]
        self.grade = self.grade.replace("(", "").replace(")", "")

    # Find letter grade in class
    def letterGrade(self) -> str:

        grade = float(self.grade.replace("%", ""))

        if grade >= 92.5:
            letter_grade = "A"
        elif grade >= 89.5:
            letter_grade = "A-"
        elif grade >= 86.5:
            letter_grade = "B+"
        elif grade >= 82.5:
            letter_grade = "B"
        elif grade >= 79.5:
            letter_grade = "B-"
        elif grade >= 76.5:
            letter_grade = "C+"
        elif grade >= 72.5:
            letter_grade = "C"
        elif grade >= 66.5:
            letter_grade = "D+"
        elif grade >= 62.5:
            letter_grade = "D"
        elif grade >= 59.5:
            letter_grade = "D-"
        else:
            letter_grade = "E"

        return letter_grade


class Message:

    def __init__(self):

        self.text = ""

    # Creates email with message data from each class
    def constructMessage(self, classes: list, name: str) -> bool:

        self.text += "Your grades have been updated " + name + "! \n \n \n"

        for course in classes:

            # Get new info from each class
            for assignment_name, score in course.message.items():
                if course.name not in self.text:
                    if self.classNamesInMessage(classes):
                        self.text += "\n \n \n"

                    self.text += course.name + " (" + str(course.old_grade) + " to " + str(course.grade)
                    self.text += "[" + course.letterGrade() + "]" + "): \n"

                percent, score = course.calculatePercent(score)

                self.text += "\n" + assignment_name + ": " + score

                if percent != "":
                    self.text += " (" + percent + "%)"

        if self.text == "Your grades have been updated " + name + "! \n \n \n":
            return False

        return True

    # Checks if any class names are in the message for formatting purposes
    def classNamesInMessage(self, classes: list) -> bool:

        for course in classes:
            if course.name in self.text:
                return True
        return False

    # Connects to SMTP server and sends email
    @staticmethod
    def sendEmail(message: str, email: str, subject: str) -> None:

        server = SMTP("smtp.gmail.com", 587)
        server.connect("smtp.gmail.com", 587)
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(SENDER_USERNAME, SENDER_PASSWORD)

        message = 'Subject: {}\n\n{}'.format(subject, message)

        server.sendmail(SENDER_USERNAME, email, message)
        server.quit()


'''Convert objects to JSON and store them in file - could make a different serialize function for storing new user data
   (when someone signs up) versus storing old user data (updater.py) but I decided that wasn't necessary, despite the
   slight efficiency gains. Right now I'm overwriting all of the dict even if it contains the same data, whereas I 
   could be checking for new data and only updating that.'''
def serialize(student: Student) -> None:

    # Update student information
    data = {
            student.username:
                {
                    "name": student.name,
                    "password": student.password,
                    "email": student.email,
                    "url": student.url,
                    "classes": {}
                }
            }

    # Update class information
    for course in student.classes:
        data[student.username]["classes"].update(
            {
                course.name:
                    {
                        "url": course.url,
                        "grade": course.grade,
                        "old_grade": course.old_grade,
                        "graded_assignments": []
                    }
            }
        )

        # Update assignment information
        for assignment in course.graded_assignments:
            data[student.username]["classes"][course.name]["graded_assignments"].append(assignment)

    # Update data in file and write to it
    with open("data.json", "r") as file:
        json = ujson.load(file)
        json.update(data)

    with open("data.json", "w") as file:
        ujson.dump(json, file, indent=4)


# Read JSON from file and turn data into objects
def unserialize(username: str, data: dict) -> Student:

    classes = []

    for course, info in data["classes"].items():
        classes.append(Class(course, info["url"], info["grade"], info["old_grade"], info["graded_assignments"]))

    return Student(username, data["password"], data["email"], data["url"], data["name"], classes)
