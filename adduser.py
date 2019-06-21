
import constants
from vue import *


def main() -> None:

    #inputs

    #while constants.VUE_USERNAME == "":
     #   input("fix")

    student = Student(constants.VUE_USERNAME, constants.VUE_PASSWORD, constants.NOTIFICATION_USERNAME, URL)

    if not student.login():
        print("Username or password is incorrect")
        return

    student.getName()
    student.getClasses()
    student.updateAssignments()
    student.constructMessage()
    #student.sendEmail(student.message.text)
    serialize(student)


    #student.sendEmail("Thanks for joining the StudentVue Grade Notifier! \n \n - Karan Arora",
                      #"Subscribed to Grade Updates")


main()
