import json
import os
import datetime
from get_data import database

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
            self.rule_cache[row[0]]=[]


def hash_dict(val):
    return json.dumps(val, sort_keys=True)

def check_single_rule(single_rule,rule_checker,email_id):
    if hash_dict(single_rule) not in rule_checker.rule_cache[email_id]:
        result=0
        field_name=single_rule['Field Name']
        predicate=single_rule['Predicate']
        value=single_rule['value']
        rule_checker.db.c.execute("SELECT "+ field_name +" FROM gmail WHERE ID=\""+str(email_id)+"\";")
        data=rule_checker.db.c.fetchall()
        data=data[0][0]

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
            if predicate=='less_than_days':
                if (data.find(value)>-1): 
                    result=1
            elif predicate==',greater_than_days':
                if (data.find(value)==-1): 
                    result=1
            elif predicate=='equals':
                if (data==value): 
                    result=1
            elif predicate=='less_than_months':
                if (data!=value): 
                    result=1
            elif predicate=='greater_than_months':
                if (data!=value): 
                    result=1
        
        elif field_name in numeric_type:
            if predicate=='present':
                if (data==1): 
                    result=1
            elif predicate=='absent':
                if (data==0): 
                    result=1
        

        


def check_rule(rule,rule_checker,email_id):
    if 'rule_list' not in rule:
            print("No rules available in this rule set")
            return
    for i in rule['rule_list']:
        check_single_rule(i,rule_checker,email_id)

if __name__ == '__main__':
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
                    for i in rules_arr:
                        check_rule(i,rule_checker,j)
        else:
            print("No rules available")