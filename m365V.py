#!/usr/bin/env python3
"""
m365V.py

This script uses the Microsoft Authentication Library (MSAL) to check if a user exists in Microsoft 365.

The script requires the following parameters:
- username: The username of the user to check.
- client_id: The client ID of an Azure AD application.
- client_secret: The client secret of the Azure AD application.
- tenant_id: The tenant ID of the Azure AD tenant.


To do:
- Add error handling.
- Add command-line arguments.
- Add logging.
- Add more detailed output.
- Add support for checking multiple users.
- Add support for checking user attributes.
- Add support for checking groups.
- Add support for checking licenses.
- Add support for checking roles.
- Add support for checking multiple applications using secrets

"""

import requests
import argparse
import msal

def check_user_exists(username, client_id, client_secret, tenant_id):
    # Set up the MSAL client
    authority = f"https://login.microsoftonline.com/{tenant_id}"
    app = msal.ConfidentialClientApplication(
        client_id,
        authority=authority,
        client_credential=client_secret
    )

    # Get an access token
    scopes = ["https://graph.microsoft.com/.default"]
    result = app.acquire_token_silent(scopes, account=None)
    if not result:
        result = app.acquire_token_for_client(scopes=scopes)

    if "access_token" in result:
        # Use the access token to make a request to Microsoft Graph
        graph_url = f"https://graph.microsoft.com/v1.0/users/{username}"
        headers = {
            'Authorization': 'Bearer ' + result['access_token']
        }
        response = requests.get(graph_url, headers=headers)

        if response.status_code == 200:
            print(f"User {username} exists.")
            return True
        elif response.status_code == 404:
            print(f"User {username} does not exist.")
            return False
        else:
            print(f"Error checking user, unknown status code: {response.status_code}")
            return None
    else:
        print(result.get("error"))
        print(result.get("error_description"))
        print(result.get("correlation_id"))
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check if a user exists in Microsoft 365.")
    parser.add_argument("username", help="The username of the user to check.")
    parser.add_argument("client_id", help="The client ID of an Azure AD application.")
    parser.add_argument("client_secret", help="The client secret of the Azure AD application.")
    parser.add_argument("tenant_id", help="The tenant ID of the Azure AD tenant.")
    args = parser.parse_args()

    check_user_exists(args.username, args.client_id, args.client_secret, args.tenant_id)
