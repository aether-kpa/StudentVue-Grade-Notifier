
from requests import Session
from smtplib import SMTP
from bs4 import BeautifulSoup
import constants
import modules

def main(name):

    '''
    username = input("StudentVue Username:")
    password = input("StudentVue Password:")
    email = input("Notification Email:")
    '''

    username = "karora4561"
    password = "rcska6046"
    email = "karanarora2001@gmail.com"

    values = {
              "username": username,
              "password": password}

    session = Session()
    session.post(constants.URL, data=values)






