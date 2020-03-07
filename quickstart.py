from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

class GMAIL_auth:
    SCOPES = ['https://www.googleapis.com/auth/gmail.modify']   # scope of the api (read,write,etc)                                         # location of the credentials.json file
    
    '''
    constructor which needs the location of the credentials.json file
    '''
    def __init__(self,location):
        if not isinstance(location,str):
            raise TypeError("location not string.Stopping program.")
        self.cred_location=location

    '''
    Template function to establish authorisation to google api and return a gmail service after building it
    '''
    def gmail_auth_template(self):
        """Shows basic usage of the Gmail API.
        Lists the user's Gmail labels.
        """
        try: 
            creds = None
            # The file token.pickle stores the user's access and refresh tokens, and is
            # created automatically when the authorization flow completes for the first
            # time.
            if os.path.exists('token.pickle'):
                with open('token.pickle', 'rb') as token:
                    creds = pickle.load(token)
            # If there are no (valid) credentials available, let the user log in.
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(self.cred_location, self.SCOPES)
                    creds = flow.run_local_server(port=0)
                # Save the credentials for the next run
                with open('token.pickle', 'wb') as token:
                    pickle.dump(creds, token)

            service = build('gmail', 'v1', credentials=creds)
            self.gmail_service=service
        except Exception as e:
            print ('An error occurred: '+str(e))
    
class GMAIL_endpoint:
    '''
    constructor which needs a GMAIL_auth object ( the object should have a gmail service object in it )
    '''
    def __init__(self,auth):
        if not isinstance(auth,GMAIL_auth) or ('gmail_service' not in dir(auth)):
            raise TypeError("Not a valid auth")
        self.gmail_service=auth.gmail_service

    '''
    Fetch latest num_of_messages messages from the users inbox
    '''
    def fetch_messages(self,num_of_messages):     
        try:
            response = self.gmail_service.users().messages().list(userId='me',maxResults=num_of_messages,label_ids=['INBOX']).execute()
            messages = []
            if 'messages' in response:
                messages.extend(response['messages'])
            
            while 'nextPageToken' in response and (len(messages)<num_of_messages):
                page_token = response['nextPageToken']
                response = self.gmail_service.users().messages().list(userId='me',pageToken=page_token,maxResults=num_of_messages-len(messages),label_ids=['INBOX']).execute()
                messages.extend(response['messages'])

            print("Message fetch complete")
            return messages

        except Exception as e:
            print ('An error occurred: '+str(e))

if __name__ == '__main__':
    auth=GMAIL_auth('credentials.json')
    auth.gmail_auth_template()
    gmail_api=GMAIL_endpoint(auth)
    # messages=gmail_api.fetch_messages(10)
    print(gmail_api.gmail_service.users().messages().get(userId='me', id='170b26baf3561ea6').execute()['payload']['headers'])


