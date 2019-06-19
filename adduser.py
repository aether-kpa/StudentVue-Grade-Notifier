
from requests import Session
from smtplib import SMTP
from bs4 import BeautifulSoup
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
    student.updateGrades()

    '''file = open("data.json", "w")

    json.dump(record.__dict__, file)'''


main()




