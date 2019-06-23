
from vue import *
import ujson


def main() -> None:

    with open("data.json", "r") as file:
        json = ujson.load(file)

    # Create student object and perform actions
    for username, data in json.items():

        student = unserialize(username, data)

        student.login()
        student.updateAssignments()

        # If there's been an update to the student's information, send the email
        update = student.constructMessage()

        if update:
            student.sendEmail(student.message.text)
            serialize(student)


main()


# Checks through attributes of classes to make sure information is correct (just a test)
''' print(student.username)
    print(student.password)
    print(student.email)
    print(student.url)
    print(student.name)
    
    for course in student.classes:
        print(course.name)
        print(course.url)
        print(course.grade)
        print(course.old_grade)
        print(course.graded_assignments) '''