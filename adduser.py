
from requests import Session
from constants import *
from modules import *
import json


def main():

    '''
    username = input("StudentVue Username:")
    password = input("StudentVue Password:")
    email = input("Notification Email:")
    '''

    username = "karora4561"
    password = "rcska6046"
    email = "karanarora2001@gmail.com"

    student = Student(username, password, email)
    student.login()
    student.getClasses()
    student.updateAssignments()
    student.constructMessage()
    student.sendEmail(student.message.text)


    '''file = open("data.json", "w")

    json.dump(record.__dict__, file)'''


main()




