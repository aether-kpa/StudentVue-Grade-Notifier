
import constants
from modules import *

def main():

    student = Student(constants.VUE_USERNAME, constants.VUE_PASSWORD, constants.NOTIFICATION_USERNAME)

    student.login()
    student.getName()
    student.getClasses()
    student.updateAssignments()
    student.constructMessage()
    student.sendEmail()

    #Thanks for joining email


main()
