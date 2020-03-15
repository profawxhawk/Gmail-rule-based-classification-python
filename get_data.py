from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import base64
import email
import pandas as pd
import sqlite3
import re
from datetime import datetime
import pytz
class database:
    def __init__(self,name):
        if not isinstance(name,str):
            raise TypeError("name of database not string.Stopping program.")
        self.conn = sqlite3.connect(name+'.db')
        self.c = self.conn.cursor()
        print(name+" database created")
    
    def create_table_from_df(self,name,df):
        try:
            if not isinstance(name,str):
                raise TypeError("name of database is not string.Stopping program.")
            if not isinstance(df,pd.DataFrame):
                raise TypeError("Not a dataframe.Stopping program.")

            df.to_sql(name,self.conn, if_exists='replace', index = False)
            # self.c.execute('CREATE TABLE '+name+' (Brand text, Price number)')
            # # self.c.execute('CREATE TABLE '+ name +' '+ '(ID, To, From, Subject, Message, CC, Date, Has_Image, Has_PDF)')
            # self.conn.commit()
            print(name+" table creation completed")
        except Exception as e:
            print ('An error occurred: '+str(e))


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
            
            response = self.gmail_service.users().messages().list(userId='me',maxResults=num_of_messages,labelIds=['INBOX']).execute()
            messages_id = []
            messages=[]
            
            if 'messages' in response:
                messages_id.extend(response['messages'])
            
            while 'nextPageToken' in response and (len(messages_id)<num_of_messages):
                page_token = response['nextPageToken']
                response = self.gmail_service.users().messages().list(userId='me',pageToken=page_token,maxResults=num_of_messages-len(messages),labelIds=['INBOX']).execute()
                messages_id.extend(response['messages'])

            for i in messages_id:
                messages.append(email.message_from_bytes(base64.urlsafe_b64decode(self.gmail_service.users().messages().get(userId='me', id=i['id'],format='raw').execute()['raw'])))

            print("Message fetch complete")
            return messages,messages_id

        except Exception as e:
            print ('An error occurred: '+str(e))

def get_message(email_message):    # reference https://gist.github.com/miohtama/5389146
    message=''
    text = ""
    try:
        if email_message.is_multipart():
            html = None
            for part in email_message.get_payload():
                if part.get_content_charset() is None:
                    text = part.get_payload(decode=True)
                    continue

                charset = part.get_content_charset()

                if part.get_content_type() == 'text/plain':
                    text = str(part.get_payload(decode=True), str(charset), "ignore")

                if part.get_content_type() == 'text/html':
                    html = str(part.get_payload(decode=True), str(charset), "ignore")

            if text is not None:
                return text.strip()
            elif html is not None:
                return html.strip()

            return "default error string"
        else:
            text = str(email_message.get_payload(decode=True), email_message.get_content_charset(), 'ignore')
            return text.strip()

    except Exception as e:
        print('An error occurred: '+str(e))
    


def get_attachment(email_message):
    image=0
    pdf=0
    if email_message.is_multipart():
        for i in email_message.walk():
            ctype = i.get_content_type()
            if 'image' in ctype:
                image=1
            if 'pdf' in ctype:
                pdf=1

    return (image,pdf)

def get_cc(email_message):
    if 'Cc' in email_message.keys():
        return email_message['Cc']
    return None

def get_email(email_address):
    temp = re.findall('[^<]+@[^>]+', email_address) 
    return ','.join(temp)


def convert_to_data(messages,message_ids,mail_base):
    col_names =  ['ID','To', 'From', 'Subject','Message','CC','Date','Time_Zone','UTC_time','Has_Image','Has_PDF']
    df  = pd.DataFrame(columns = col_names)
    for i,j in zip(messages,message_ids):
        To=get_email(i['To'])
        From=get_email(i['From'])
        Subject=i['Subject']
        date=datetime.strptime((i['Date'][0:(len(i['Date'])-6)]), "%a, %d %b %Y %H:%M:%S")
        timezone=i['Date'][(len(i['Date'])-6):]
        utc_time=datetime.strptime((i['Date']), "%a, %d %b %Y %H:%M:%S %z").astimezone(pytz.utc)
        utc_time=str(utc_time)[0:(len(str(utc_time))-6)]
        utc_time=datetime.strptime(utc_time, "%Y-%m-%d %H:%M:%S")
        message=get_message(i)
        cc=get_cc(i)
        attachment=get_attachment(i)
        df.loc[len(df)] = [j['id'],To,From,Subject,message,cc,date,timezone,utc_time,attachment[0],attachment[1]]
    
    mail_base.create_table_from_df('gmail',df)


    
    


if __name__ == '__main__':
    auth=GMAIL_auth('credentials.json')
    db=database('Mail_base')
    auth.gmail_auth_template()
    gmail_api=GMAIL_endpoint(auth)
    messages,message_ids=gmail_api.fetch_messages(5)
    convert_to_data(messages,message_ids,db)