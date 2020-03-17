import json
import os
import datetime
from get_data import database,GMAIL_auth,GMAIL_endpoint

string_type=["To_mail","From_mail","Subject","Message","CC","Time_Zone"]
date_type=["local_time","utc_time"]
numeric_type=["image","pdf"]
class email_rule_check:
    def __init__(self):
        self.db=database('Mail_base')
        self.rule_cache={}
    
    def generate_cache(self):
        self.db.c.execute("SELECT ID FROM gmail;")
        data = self.db.c.fetchall()
        for row in data:
            self.rule_cache[row[0]]={}


def hash_dict(val):
    return json.dumps(val, sort_keys=True)

def days(date1, date2): 
    return (date2-date1).days 

def days_to_months(days):
    return days/30

def check_single_rule(single_rule,rule_checker,email_id):
    if hash_dict(single_rule) not in rule_checker.rule_cache[email_id]:
        result=0
        field_name=single_rule['Field Name']
        predicate=single_rule['Predicate']
        value=single_rule['value']
        rule_checker.db.c.execute("SELECT "+ field_name +" FROM gmail WHERE ID=\""+str(email_id)+"\";")
        data=rule_checker.db.c.fetchall()
        data=data[0][0]

        if data!=None:
            if field_name in string_type:
                if predicate=='contains':
                    if (data.find(value)>-1): 
                        result=1
                elif predicate=='does_not_contain':
                    if (data.find(value)==-1): 
                        result=1
                elif predicate=='equals':
                    if (data==value): 
                        result=1
                elif predicate=='does_not_equal':
                    if (data!=value): 
                        result=1
                
            elif field_name in date_type:
                data=datetime.datetime.strptime(data, "%Y-%m-%d %H:%M:%S")
                cur_date=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cur_date=datetime.datetime.strptime(cur_date, "%Y-%m-%d %H:%M:%S")
                if predicate=='less_than_days':
                    if (days(data,cur_date)<=int(value)): 
                        result=1
                elif predicate=='greater_than_days':
                    if (days(data,datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))>int(value)): 
                        result=1
                elif predicate=='equals':
                    if (data==value): 
                        result=1
                elif predicate=='less_than_months':
                    if (days_to_months(days(data,datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))<=int(value)): 
                        result=1
                elif predicate=='greater_than_days':
                    if (days_to_months(days(data,datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))>int(value)): 
                        result=1
            
            elif field_name in numeric_type:
                if predicate=='present':
                    if (data==1): 
                        result=1
                elif predicate=='absent':
                    if (data==0): 
                        result=1

        rule_checker.rule_cache[email_id][hash_dict(single_rule)]=result
        return result
    else:
        return rule_checker.rule_cache[email_id][hash_dict(single_rule)]
        
        

def perform_action(email_id,action_list,gmail_api):
    message = gmail_api.gmail_service.users().messages().get(userId='me', id=email_id).execute()
    for i in action_list:
        if i['action']=="delete":
            gmail_api.gmail_service.users().messages().delete(userId='me', id=email_id).execute()
        elif i['action']=="read":
            if "UNREAD" in message['labelIds']:
                gmail_api.gmail_service.users().messages().modify(userId='me', id=email_id, body={'removeLabelIds': ['UNREAD']}).execute()
        elif i['action']=="important":
                if "IMPORTANT" not in message['labelIds']:
                    gmail_api.gmail_service.users().messages().modify(userId='me', id=email_id, body={'addLabelIds': ['IMPORTANT']}).execute()
        elif i['action']=="starred":
                if "STARRED" not in message['labelIds']:
                    gmail_api.gmail_service.users().messages().modify(userId='me', id=email_id, body={'addLabelIds': ['STARRED']}).execute()
        elif i['action']=="unread":
            if "UNREAD" not in message['labelIds']:
                gmail_api.gmail_service.users().messages().modify(userId='me', id=email_id, body={'addLabelIds': ['UNREAD']}).execute()
        elif i['action']=="move":
            if i['mailbox']=='trash':
                message = gmail_api.gmail_service.users().messages().trash(userId='me', id=email_id).execute()
            elif i['mailbox']=='inbox':
                if 'INBOX' not in message['labelIds']:
                    message = gmail_api.gmail_service.users().messages().modify(userId='me', id=email_id, body={'addLabelIds': ['INBOX']}).execute()
            elif i['mailbox']=='spam':
                if 'SPAM' not in message['labelIds']:
                    message = gmail_api.gmail_service.users().messages().modify(userId='me', id=email_id, body={'addLabelIds': ['SPAM']}).execute()
                



def check_rule(rule,rule_checker,email_id,gmail_api):
    if 'rule_list' not in rule:
            print("No rules available in this rule set")
            return
    if rule['Predicate']=='all':
        flag=1
        for i in rule['rule_list']:
            flag=check_single_rule(i,rule_checker,email_id)
            if flag==0:
                break
    elif rule['Predicate']=='any':
        flag=0
        for i in rule['rule_list']:
            flag=check_single_rule(i,rule_checker,email_id)
            if flag==1:
                break
    
    if flag==1:
        perform_action(email_id,rule['action_list'],gmail_api)
        print("Action successfully performed for email id "+str(email_id))
        return

    print("Email "+str(email_id)+" does not satisfy all the conditions")
    
    

if __name__ == '__main__':
    auth=GMAIL_auth('credentials.json')
    auth.gmail_auth_template()
    gmail_api=GMAIL_endpoint(auth)
    rule_checker=email_rule_check()
    rule_checker.generate_cache()
    with open("rules.json", "r") as file:
        if os.stat("rules.json").st_size > 0:
                rules = json.load(file) 
                if 'rule_set_arr' not in rules:
                    print("No rules available")
                    exit()
                rules_arr=rules['rule_set_arr']
                for j in rule_checker.rule_cache.keys():
                    for k,i in enumerate(rules_arr):
                        print("Checking rule "+str(k)+" for email id "+str(j))
                        check_rule(i,rule_checker,j,gmail_api)
        else:
            print("No rules available")