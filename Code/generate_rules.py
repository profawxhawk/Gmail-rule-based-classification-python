import json
import os
import datetime
class my_dictionary(dict): # reference https://www.geeksforgeeks.org/python-add-new-keys-to-a-dictionary/

    """A dictionary class to do basic dict operations """
    # __init__ function 
    def __init__(self): 
        """
        
        Constructor for dictionary class

        """
        self = dict() 

    # Function to add key:value 
    def add(self, key, value): 
        """
        
        Function to add key:value pair

        Parameters
        ----------
        key
            A key to be hashed in the dictionary
        value:
            The value for the corresponding key


        """
        self[key] = value 

def get_input(cond_string,cond_arr):
    """
        
        Function to get input till some conditions match

        Parameters
        ----------
        cond_string
            The display message to be printed while taking input
        cond_arr
            The array of allowed values for the input

        
        Returns
        -------
        ans:string
            The input value in accordance with the given conditions

        """
    print(cond_string)
    ans=input()
    while(ans not in cond_arr):
        print("Input does not match any allowed values.Please enter again")
        ans=input()
    return ans

def get_rule():
    """
        
        Function to get a single rule dictionary
        
        Returns
        -------
        Action :dictionary
            Rule contains field name, predicate and value as keys.
            

        """

    # choosing field name type
    value=None
    rule_type=get_input("choose rule type as string,date or numeric",["string","date","numeric"])
    if rule_type=='string':
        field_name=get_input("choose field name as To_mail,From_mail,Subject,Message,CC or Time_Zone",["To_mail","From_mail","Subject","Message","CC","Time_Zone"])
        rule_predicate=get_input("choose predicate as contains,does_not_contain,equals or does_not_equal",["contains","does_not_contain","equals","does_not_equal"])
        print("Input a string value")
        value=input()

    # get field name for different types 
    if rule_type=='date':
        field_name=get_input("choose field name as local_time or utc_time",["local_time","utc_time"])
        rule_predicate=get_input("choose predicate as less_than_days,greater_than_days,less_than_months,greater_than_months,equals",["less_than_days","greater_than_days","less_than_months","greater_than_months","equals"])
        
        if rule_predicate=='equals':
            print("Input date in the year-month-date hour:minute:second format")
            value=input()
            while True:
                try:
                    value=datetime.datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
                    break
                except:    
                    pass
                print("Incorrect format, try again")
                value=input()

        else:
            print("Input a numeric integer value")
            value=input()
            while(value.isdigit()==0):
                print("Please enter numeric value")
                value=input()

    if rule_type=='numeric':
        field_name=get_input("choose field name as image or pdf",["image","pdf"])
        rule_predicate=get_input("choose predicate as present or absent",["present","absent"])

    return {'Field Name':field_name,'Predicate':rule_predicate,'value':value}


def get_action():
    """
    
    Function to get a single action dictionary
    
    Returns
    -------
    Action :dictionary
        Action contains action and mailbox as keys
        

    """
    action=get_input("choose action as move,read,delete,starred,important or unread",["move","read","unread","delete","starred","important"])
    mailbox=None
    if action=="move":
        mailbox=get_input("choose place to move as inbox,trash or spam",["inbox","spam","trash"])
    return {'action':action,'mailbox':mailbox}




if __name__ == '__main__':
    print("1) Add a rule set ( would be added to rules.json) ")
    print("2) Exit")
    ans=input()
    rules={}
    while ans!='2':
        if ans=='1':
            with open("../Storage/rules.json", "w+") as file: 
                if os.stat("../Storage/rules.json").st_size > 0:
                    json_object = json.load(file) 
                    rules = json.loads(json_object)
                temp=my_dictionary()
                print("Enter rule set name")
                name=input()
                temp.add('Name',name)
                rule_set_predicate=get_input("Enter rule set predicate as either any or all",["ANY","ALL","any","all"])
                temp.add('Predicate',rule_set_predicate)
                print("1) Enter a single rule")
                print("Done ( any other key )")
                rule_limit=input()
                rule_arr=[]
                while(rule_limit=='1'):
                    rule_arr.append(get_rule())
                    print("1) Enter a single rule")
                    print("Done ( any other key )")
                    rule_limit=input()
                
                temp.add('rule_list',rule_arr)

                print("1) Enter a action")
                print("Done ( any other key )")
                action_limit=input()
                action_arr=[]
                while(action_limit=='1'):
                    action_arr.append(get_action())
                    print("1) Enter a action")
                    print("Done ( any other key )")
                    action_limit=input()
                
                temp.add('action_list',action_arr)
                if 'rule_set_arr' not in rules:
                    rules['rule_set_arr']=[temp]
                else:
                    rules['rule_set_arr'].append(temp)
                
                json.dump(rules,file)
        print("1) Add a rule set ( would be added to rules.json) ")
        print("2) Exit")
        ans=input()
    print("Exiting...")
        

            



            

            


