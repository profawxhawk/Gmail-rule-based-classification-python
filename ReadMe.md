---


---

<h1 id="gmail-rule-based-classification">GMAIL rule based classification</h1>
<p>A python module to take action on Gmail emails based upon some rules.</p>
<ol>
<li>For reading the HTML documentation traverse to docs/build/html/index.html</li>
<li>Please run the code in a linux environment with a python version==3.6 .</li>
</ol>
<h1 id="running-the-code">Running the Code</h1>
<ol>
<li>Pip install the requirements.txt file by running pip install -r requirements.txt</li>
<li>There are 3 python files to be run. Traverse to the Code folder.</li>
</ol>
<h2 id="get_data.py">get_data.py</h2>
<p>This module is to extract data from your gmail and store it in a table called gmail in a database called Mail_base.db in the storage folder.<br>
Once you run this file, you would have to authenticate your gmail account first which would then generate your credentials and they would be stored in the Storage folder. If you want to switch to a different account you would need to delete the credentials.json and token.pickle file from the Storage folder.</p>
<h2 id="generate_rules.py">generate_rules.py</h2>
<p>This module can be skipped if you do not want to add a new rule_set to the rules.json file. The function creates a new rule set from user input. Each rule_set has many rules and a set of actions and an any/all option. If any is choosen then if an email satisfies any one of the rules then the corresponding action would be performed else if all is choosen the email must satisfy all the rules in a rule_set for the action to be performed.<br>
Each rule has a field name, predicate and value.</p>
<ol>
<li>Field Name:
<ol>
<li>String type : [“To_mail”,“From_mail”,“Subject”,“Message”,“CC”,“Time_Zone”]</li>
<li>Date type :  [“local_time”,“utc_time”]</li>
<li>Numeric type : [“image”,“pdf”]</li>
</ol>
</li>
<li>Predicate
<ol>
<li>String type : [“contains”,“does_not_contain”,“equals”,“does_not_equal”]</li>
<li>Date type : [“less_than_days”,“greater_than_days”,“less_than_months”,“greater_than_months”,"equals]</li>
<li>Numeric type : [“present”,“absent”]</li>
</ol>
</li>
</ol>
<p>Value should comply with the choosen field name and predicate.<br>
Action can be choosen from one of the following : move,read,delete,starred,important or unread.</p>
<h2 id="apply_rules.py">apply_rules.py</h2>
<p>This module checks wether each mail stored in the database satisfies rule_sets defined in rules.json or not. It uses a hashmap cache of rules for optimizing repeated rules and hence makes the process faster.</p>

