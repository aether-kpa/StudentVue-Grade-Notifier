
import constants
from modules import *

def main():

    student = Student(constants.VUE_USERNAME, constants.VUE_PASSWORD, constants.NOTIFICATION_USERNAME, URL)

    student.login()
    student.getName()
    student.getClasses()
    student.updateAssignments()
    student.constructMessage()
    student.sendEmail(student.message.text)
    print(student.__dict__)

    #Thanks for joining email


main()
