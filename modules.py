
class Record:

    def __init__(self, assignment, score, date):

        self.assignment = assignment
        self.score = score
        self.date = date

        try:
            self.percentage = float(score[0]/score[1]) * 100
        except ZeroDivisionError:
            self.percentage = "N/A"

class Student:

    def __init__(self, name, username, password, __VIEWSTATE, __EVENTVALIDATION):

        self.name = name
        self.username = username
        self.password = password
        self.__VIEWSTATE = __VIEWSTATE
        self.__EVENTVALIDATION = __EVENTVALIDATION




