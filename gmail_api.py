#Copyright (C) 2022 Arianna Leah Fischer, Harvest Digital Ltd. 

# Python imports
from __future__ import print_function
import os.path
import re
import sys

# Google API Client imports
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

"""
A sample script that gets all unread emails using GMAIL API, checks them against list of senders, and does something with them. 
Finally, it marks them as read.
This script requires that you have an OAuth2 credentials.json file. Please review Google's Gmail API Python Quickstart 
to generate credentials.json file and propertly authenticate this app.
You can find the quickstart guide here: https://developers.google.com/gmail/api/quickstart/python
Happy coding!
"""

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://mail.google.com/']
USER_ID = 'me'
LABEL_A = "INBOX"
LABEL_B = "UNREAD"
SENDERS = ['example-mail@gmail.com']  # TODO(developer) - Add list of senders you wish to check unread email for. 

def authenticate():
    """
    Authenticates GMAIL API with OAuth2 authentication, and creates GMAIL service.
    @rtype <class 'googleapiclient.discovery.Resource'>
    @returns GMAIL: The authenticated and built gmail service google api client
    """ 
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        # Call the Gmail API
        GMAIL = build('gmail', 'v1', credentials=creds)
        return GMAIL

    except HttpError as error:
        # TODO(developer) - Handle errors from gmail API.
        print(f'An error occurred: {error}')


def get_sender(GMAIL, msg_id):
    """
    Gets senders and message IDs from email inbox with label UNREAD and returns list of dict of Sender and Message_ID.
    @type GMAIL: <class 'googleapiclient.discovery.Resource'>
    @param GMAIL: The authenticated and built gmail service google api client
    @type msg_id: str
    @param msg_id: The id of the message in question
    @rtype: dict <str>
    @returns: A dictionary with the message sender and message_id, of the form:
            [{'Sender': 'example-email@gmail.com', 'Message_ID': '17xx3e00ec9b4a0x'}]
    """ 
    tmp = { }
    message = GMAIL.users().messages().get(userId=USER_ID, id=msg_id).execute()  # fetch the message using API
    payload = message['payload']  # get payload of the message 
    headers = payload['headers']  # get headers of the payload
    for items in headers: # getting the Sender
        if items['name'] == 'From':
            msg_from = items['value']
            if "<" and ">" in msg_from:
                pattern = "<(.*?)>"  # regex to find substring in between '<' and '>'
                msg_from = re.search(pattern, msg_from).group(1) # just gets the email, not name
            tmp['Sender'] = msg_from
            tmp['Message_ID'] = msg_id
    return tmp
    

def read_mail(GMAIL):
    """
    Gets senders and message IDs from email inbox with label UNREAD and returns list of dict of Sender and Message_ID.
    @type GMAIL: <class 'googleapiclient.discovery.Resource'>
    @param GMAIL: The authenticated and built gmail service google api client
    @rtype: list <str>
    @returns: List of message ids that matched SENDERS
    @rtype: list <str>
    @returns: List of all unread message ids
    """ 
    unread = GMAIL.users().messages().list(userId=USER_ID, labelIds = [LABEL_A, LABEL_B]).execute().get('messages')
    if unread is None:
        return [], []
    unread_list = []
    for msg in unread:
        unread_list.append(msg['id'])
    senders = []
    for msg in unread:
        msg_id = msg['id']
        sender = get_sender(GMAIL, msg_id)
        senders.append(sender)
    msgs_to_process = []
    # looks for new senders in list of senders, and appends affirmative result to msgs_to_processs
    for sender in senders:
        if sender['Sender'] in SENDERS:
            msgs_to_process.append(sender['Message_ID'])
    return msgs_to_process, unread_list

def do_something(GMAIL, msg_ids):
    """
    Does something to mail to be processed with gmail service and message ids. 
    @type GMAIL: <class 'googleapiclient.discovery.Resource'>
    @param GMAIL: The authenticated and built gmail service google api client
    @type list <str>
    @param msg_ids: Message IDs to do something with. 
    """ 
    print("GMAIL Object: ", GMAIL)
    print("Do something with the following message ids: ", msg_ids)

    
def mark_as_read(GMAIL, msg_ids):
    """
    Marks all message with passed message ids as read. 
    @type GMAIL: <class 'googleapiclient.discovery.Resource'>
    @param GMAIL: The authenticated and built gmail service google api client
    @type list <str>
    @param msg_ids: Message IDs to mark messages as read.
    """ 
    for msg_id in msg_ids:
        GMAIL.users().messages().modify(userId=USER_ID, id=msg_id, body={ 'removeLabelIds': ['UNREAD']}).execute() 

def main():
    """
    Main function.
    """
    GMAIL = authenticate()
    mail_to_process, unread_mail = read_mail(GMAIL) # check mail for unread emails. mail_to_process is a list of emails you want to capture, and unread_email is all unread email.
    if not mail_to_process: # check if there is no emails you want to process
        print("No new emails to process, marking all mail as read.")
        if unread_mail:
            mark_as_read(GMAIL, unread_mail) # if unread_mail is not empty, mark as read then exit. 
        sys.exit()
    print("Messages to process: ", mail_to_process)
    do_something(GMAIL, mail_to_process)  # do something with messages you want to process.
    print("Marking following messages as read...")
    print("Messages to be labelled read: ", unread_mail)
    mark_as_read(GMAIL, unread_mail) # mark all messages in unread mail as read. 
    print("...done")

if __name__ == '__main__':
    main()