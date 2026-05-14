from pyClarion import * 
from pyClarion.knowledge import * 
import random

# Step 1 : Implement context of agent; shape, color, or number of card; Rule of current trial; Action agent can take; and Feedback from the tester.

class Color(Atoms): 
    red: Atom
    grn: Atom
    blu: Atom


class Shape(Atoms): 
    circ: Atom
    squr: Atom
    tria: Atom


class Number(Atoms):
    one: Atom
    two: Atom
    three: Atom


class Rule(Atoms):
    color: Atom
    shape: Atom
    number: Atom


class Feedback(Atoms):
    correct: Atom
    incorrect: Atom


class Action(Atoms):
    match_color: Atom
    match_number: Atom
    match_shape: Atom


class Main(Buses):
    input: Bus
    output: Bus
    target: Bus


class WCSTBuses(BusFamily):
    main: Main


class WCSTData(DataFamily):
    color: Color
    shape: Shape
    number: Number
    rule: Rule
    feedback: Feedback
    action: Action


class WCSTRoot(Root):
    b: WCSTBuses
    d: WCSTData

# Context of the environment is stored in "root" variable
root = WCSTRoot()

# Define short handles for data sorts
color = root.d.color   
shape = root.d.shape  
number = root.d.number 
rule = root.d.rule
feedback = root.d.feedback
action = root.d.action


# Class represents WCST tester
class WCSTTester:

    # Initialize tester; rules available and how many trials before rule switches.
    def __init__(self, rules, switch_every):

        # List of rules atoms
        self.rules = rules

        # Randomly choose hidden rule
        self.hidden_rule = random.choice(self.rules)

        # Trial has not started
        self.trial = 0

        # Keeping track of the previous rule 
        self.previous_rule = None

        # Initialize number before switching rule
        self.switch_every = switch_every

    # Function to give feedback to testee
    def give_feedback(self, given_action):

        # Compare the action of the testee to the tester's hidden rule
        if self.hidden_rule == rule.color:
            correct = given_action == action.match_color

        elif self.hidden_rule == rule.shape:
            correct = given_action == action.match_shape

        elif self.hidden_rule == rule.number:
            correct = given_action == action.match_number
        
        # Increment the number of trials after the testee has chosen.
        self.trial += 1

        # Every 10 trials, switch the hidden rule, and pick a random one not chosen before.
        if self.trial % self.switch_every == 0:
            self.previous_rule = self.hidden_rule
            options = [r for r in self.rules if r != self.hidden_rule]
            self.hidden_rule = random.choice(options)
            self.switch_every = random.randint(5,10)
        
        # Return the result of the testee's choice
        if correct:
            return feedback.correct
        else:
            return feedback.incorrect


# Class represents NACS, which is responsible for general knowledge and reasoning, and the motivational subsystem which provides motivations for cognition (in this case, why one choice over another).
class RuleChoice:

    # Initial probability of rules, rules and probability tuple initialization
    def __init__(self, rules):
        self.rules = rules
        self.init_probs = [1/3,1/3,1/3]
        self.rule_prob_comp = list(zip(self.rules,self.init_probs)) # A list of tuples of rules and their coresponding probability of being correct
        self.chosen_rule = None

    # Return the rule choice
    def choose_rule(self):
        # List of probabilities from tuple
        prob_list = [x[1] for x in self.rule_prob_comp]
        # List of rules from tuple
        rule_list = [x[0] for x in self.rule_prob_comp]

        # Pick the 
        self.chosen_rule = random.choices(rule_list, weights=prob_list, k =1)[0]

        return self.chosen_rule

    # Update the rule based on the feedback
    def update_rule(self, given_feedback):
        # If the chosen rule is incorrect
        if given_feedback == feedback.incorrect:
        
            # If the feedback was incorrect and there are no more choices to make
            if sum(prob == 1 for _,prob in self.rule_prob_comp) == 1:
                self.rule_prob_comp = [(rule, 1/3) for rule, _ in self.rule_prob_comp]

            # If the feedback was incorrect but there are two or three more choices to make
            else:
                # Turn the prob of the incorrect rule to 0
                self.rule_prob_comp = [(rule, 0) if rule == self.chosen_rule else (rule, prob) for rule, prob in self.rule_prob_comp ]

                # New total of probabilities
                total_prob = sum(prob for _,prob in self.rule_prob_comp)

                # Get new probability value of remaining rule choices
                self.rule_prob_comp = [(rule, prob / total_prob)for rule, prob in self.rule_prob_comp ]

        else:
            # If the chosen rule was correct, change it's probability of being correect to 100, and everything else to 0
            self.rule_prob_comp = [(rule, 1 if rule == self.chosen_rule else 0)for rule, _ in self.rule_prob_comp]

        # Choose a new rule with altered probs based on feedback
        self.current_rule = self.choose_rule()
        

# Class represents ACS, which is responsible for taking action based on a choice.
class MakeChoice:

    # Initialize with the context of environment
    def __init__(self, root):
        self.root = root

    # Methond for choosing action
    def choose_action(self, chosen_rule):
        # Color
        if chosen_rule == rule.color:
            return action.match_color
        # Shape
        if chosen_rule == rule.shape:
            return action.match_shape

        # Number 
        if chosen_rule == rule.number:
            return action.match_number

# Class is the WCST simulation
class WCSTModel:
    
    # Initialize context, and when to switch rule
    def __init__(self, switch_every):
        
        # Possible rules
        self.rules = [rule.color,rule.shape,rule.number]

        # Tester
        self.task = WCSTTester(self.rules, switch_every)
        # Testee NACS
        self.nacs = RuleChoice(self.rules)
        # Testee ACS
        self.acs = MakeChoice(root)

        # Total errors
        self.errors = 0
        # Perservation errors, which occur when the testee has picked a rule that was previously correct, but is now incorrect.
        self.perseveration_errors = 0
        # Total correct
        self.correct = 0

    # Function for running the trial
    def run_trial(self):
        chosen_rule = self.nacs.choose_rule()
        # Choose action based on assumed rule
        action = self.acs.choose_action(chosen_rule)

        # Keeping track of previous rule to measure perservation errors
        previous_rule = self.task.previous_rule
        
        # Give feedback to the action
        given_feedback = self.task.give_feedback(action)

        # if the feedback is incorrect
        if given_feedback == feedback.incorrect:
            # increase the total number of errors
            self.errors += 1

            # If the chosen rule is the same as the previous rule.
            if previous_rule is not None and chosen_rule == previous_rule:
                self.perseveration_errors += 1
        elif given_feedback == feedback.correct:
            self.correct += 1

        # update the rule based on feeback.
        self.nacs.update_rule(given_feedback)

# Testing
model = WCSTModel(10)

# Run 50 trials
for _ in range(50):
    model.run_trial()

# Print the total and perservation errors.
print("Errors:", model.errors)
print("Correct:", model.correct)
print("Perseveration errors:", model.perseveration_errors)







