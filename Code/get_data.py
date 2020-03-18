"""
get_data.py
====================================
The module which extracts the data from gmail and stores it in a database
"""

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
import html2text
from datetime import datetime
import pytz



class database:

    """A database class to generate a sql .db file and to do CRUD operations on tables in the database"""

    def __init__(self,name):
        """
        
        Constructor for database class

        Parameters
        ----------
        name
            A string indicating the name of the database.

        """
        if not isinstance(name,str):
            raise TypeError("name of database not string.Stopping program.")
        self.conn = sqlite3.connect(name+'.db')
        self.c = self.conn.cursor()
        print(name+" database connected")
    
    def create_table_from_df(self,name,df):
        """
        
        Function to create a sql table in the database from a given pandas dataframe

        Parameters
        ----------
        name
            A string indicating the name of the table.
        
        df
            The dataframe which needs to be converted.

        """
        try:
            # Sanity checks
            if not isinstance(name,str):                                              
                raise TypeError("name of database is not string.Stopping program.")
            if not isinstance(df,pd.DataFrame):
                raise TypeError("Not a dataframe.Stopping program.")
            
            # Use dataframe function to create sql table
            df.to_sql(name,self.conn, if_exists='replace', index = False)             
            print(name+" table creation completed")

        except Exception as e:
            print ('An error occurred: '+str(e))


class GMAIL_auth:
    """A gmail authenticator class to establish credentials and get access to gmail service for a given authenticated account"""

    SCOPES = ['https://www.googleapis.com/auth/gmail.modify']   # scope of the api (read,write,etc)                                         # location of the credentials.json file
    
    def __init__(self,location):
        """
        
        constructor which needs the location of the credentials.json file

        Parameters
        ----------
        location
            A string indicating the location of the credentials.json file

        """
        if not isinstance(location,str):
            raise TypeError("location not string.Stopping program.")
        self.cred_location=location

    def gmail_auth_template(self):
        """
        Template function to establish authorisation to google api and return a gmail service after building it
        """
        try: 
            creds = None
            # The file token.pickle stores the user's access and refresh tokens, and is
            # created automatically when the authorization flow completes for the first
            # time.
            if os.path.exists('../Storage/token.pickle'):
                with open('../Storage/token.pickle', 'rb') as token:
                    creds = pickle.load(token)
            # If there are no (valid) credentials available, let the user log in.
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(self.cred_location, self.SCOPES)
                    creds = flow.run_local_server(port=0)
                # Save the credentials for the next run
                with open('../Storage/token.pickle', 'wb') as token:
                    pickle.dump(creds, token)

            service = build('gmail', 'v1', credentials=creds)
            self.gmail_service=service
        except Exception as e:
            print ('An error occurred: '+str(e))
    
class GMAIL_endpoint:
    """A gmail endpoint class which uses a GMAIL_auth object to define APIs to interact with the authenticated users gmail messages"""

    def __init__(self,auth):
        """
        
        constructor which needs a GMAIL_auth object

        Parameters
        ----------
        auth
            A gmail auth object with established credentials and a gmail service object

        """
        if not isinstance(auth,GMAIL_auth) or ('gmail_service' not in dir(auth)):
            raise TypeError("Not a valid auth")
        self.gmail_service=auth.gmail_service


    def fetch_messages(self,num_of_messages):   
        """
        
        API to fetch the latest given number of messages

        Parameters
        ----------
        num_of_messages
            The number of mails to fetch from the users list of mails
        
        Returns
        -------
        messages,messages_id : tuple(list,list)
            messages is the list of messages ( in the format defined in https://developers.google.com/gmail/api/v1/reference/users/messages ) and messages_id is the list of corresponding message IDs

        """
        try:
            
            # extract all message_ids
            response = self.gmail_service.users().messages().list(userId='me',maxResults=num_of_messages).execute()
            messages_id = []
            messages=[]
            
            if 'messages' in response:
                messages_id.extend(response['messages'])
            
            # Keep getting message_ids till limit is reached
            while 'nextPageToken' in response and (len(messages_id)<num_of_messages):
                page_token = response['nextPageToken']
                response = self.gmail_service.users().messages().list(userId='me',pageToken=page_token,maxResults=num_of_messages-len(messages)).execute()
                messages_id.extend(response['messages'])

            # get messages from message_ids
            for i in messages_id:
                messages.append(email.message_from_bytes(base64.urlsafe_b64decode(self.gmail_service.users().messages().get(userId='me', id=i['id'],format='raw').execute()['raw'])))

            print("Message fetch complete")
            return messages,messages_id

        except Exception as e:
            print ('An error occurred: '+str(e))

def get_message(email_message):    # reference https://gist.github.com/miohtama/5389146
    """
        
        Function to get body of the email given a email in the Users.messages format. In case of multi parts the latest message is returned.

        Parameters
        ----------
        email_message
            The email whose body needs to be extracted
        
        Returns
        -------
        message : string
            message is the parsed body of the email ( can be parsed from normal email text body or from a HTML page body)

    """
    message=''
    text = ""
    try:
        if email_message.is_multipart():
            html = None
            for part in email_message.get_payload():
                if part.get_content_charset() is None:
                    text = str(part.get_payload(decode=True))
                    continue

                charset = part.get_content_charset()

                if part.get_content_type() == 'text/plain':
                    text = str(part.get_payload(decode=True), str(charset), "ignore")

                if part.get_content_type() == 'text/html':
                    html = str(html2text.html2text(part.get_payload(decode=True).decode('utf8')))

            if text is not None:
                return text.strip()
            elif html is not None:
                return html.strip()

            return "default error string"
        else:
            return str(html2text.html2text(email_message.get_payload(decode=True).decode('utf8'))).strip()

    except Exception as e:
        print('An error occurred: '+str(e))
    


def get_attachment(email_message):
    """
        
        Function to get attachment details in a email

        Parameters
        ----------
        email_message
            The email whose atachments needs to be extracted
        
        Returns
        -------
        image,pdf : tuple(boolean,boolean)
            returns a tuple (image,pdf) which returns the truth value ( 1 if present and 0 if absent) of image and pdf attachments

    """
    image=0
    pdf=0
    # go through all the parts of the email to check if any part has a pdf or image
    if email_message.is_multipart():
        for i in email_message.walk():
            ctype = i.get_content_type()
            if 'image' in ctype:
                image=1
            if 'pdf' in ctype:
                pdf=1

    return (image,pdf)

def get_cc(email_message):
    """
        
        Function to get CCed details in a email

        Parameters
        ----------
        email_message
            The email whose CCed email_ids needs to be extracted
        
        Returns
        -------
        CC_string : string
            returns a comma seperated string of all the CCed email_ids

    """
    if 'Cc' in email_message.keys():
        temp = re.findall('\<(.*?)\>', email_message['Cc']) 
        return ','.join(temp)
    return None

def get_email(email_address):
    """
        
        Function to get email_ids from a string

        Parameters
        ----------
        email_message
            The string from which all email_ids need to be extracted
        
        Returns
        -------
        email_id : string
            returns a string containing all the email_ids found in the string

    """
    temp = re.findall('\<(.*?)\>', email_address) 
    if temp==[]:
        return str(email_address)
    return ','.join(temp)


def convert_to_data(messages,message_ids,mail_base):
    """
        
        Function to convert a list of messages to a sql table

        Parameters
        ----------
        messages
            The list of all messages which need to be converted to a table
        messages_ids
            The list of all corresponding message ids of the messages in messages list
        mail_base
            The database object which contains the database connection to the database where the table has to be created
        
    """
    col_names =  ['ID','To_mail', 'From_mail', 'Subject','Message','CC','local_time','Time_Zone','utc_time','image','pdf']
    df  = pd.DataFrame(columns = col_names)
    # convert each message to a dataframe row by extracting the information according to the column name
    for i,j in zip(messages,message_ids):
        To=get_email(i['To'])
        From=get_email(i['From'])
        Subject=i['Subject']

        if i['Date'].find('+')!=-1:
            index=i['Date'].find('+')
        else:
            index=i['Date'].find('-')
        
        date=None
        timezone=None
        utc_time=None
        if index>-1:
            date=datetime.strptime((i['Date'][0:index-1]), "%a, %d %b %Y %H:%M:%S")
            timezone=i['Date'][index:index+5]
            utc_time=datetime.strptime((i['Date'][0:index+5]), "%a, %d %b %Y %H:%M:%S %z").astimezone(pytz.utc)

            if str(utc_time).find('+')!=-1:
                index_utc=str(utc_time).find('+')
            else:
                index_utc=str(utc_time).find('-')
                
            utc_time=str(utc_time)[0:index_utc-1]
            utc_time=datetime.strptime(utc_time, "%Y-%m-%d %H:%M:%S")

        message=get_message(i)
        message = re.sub(r'https?://\S+', '', message, flags=re.MULTILINE)
        message=''.join(e for e in message if e.isalnum() or e==' ')
        cc=get_cc(i)
        attachment=get_attachment(i)
        df.loc[len(df)] = [j['id'],To,From,Subject,message,cc,date,timezone,utc_time,attachment[0],attachment[1]]
    
    # convert the dataframe to sql table
    mail_base.create_table_from_df('gmail',df)

if __name__ == '__main__':
    auth=GMAIL_auth('../Storage/credentials.json')  # get credentials
    db=database('../Storage/Mail_base')             # establish db connectivity
    auth.gmail_auth_template()                      # get gmail_service object for the authenticated user
    gmail_api=GMAIL_endpoint(auth)                  # get a gmail_endpoint object
    messages,message_ids=gmail_api.fetch_messages(10) # fetch messages
    convert_to_data(messages,message_ids,db)          #convert messages to table