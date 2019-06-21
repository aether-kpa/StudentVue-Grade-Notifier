
import ujson


def main():

    username = input("Enter the username of the StudentVue account you would like to remove: ")
    password = input("Enter the password of the StudentVue account: ")

    with open("data.json", "r") as file:
        json = ujson.load(file)

        if username in json.keys():
            if json[username]["password"] == password:
                json.pop(username)

        else:
            print("The username or password entered is incorrect.")

    with open("data.json", "w") as file:
        ujson.dump(json, file, indent=4)


main()
