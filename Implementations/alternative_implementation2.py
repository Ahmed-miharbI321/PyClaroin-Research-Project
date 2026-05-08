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

# Context of environment is stored in "root" variable
root = WCSTRoot()

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
    def give_feedback(self, action):

        # Compare the action of the testee to the tester's hidden rule
        if self.hidden_rule == root.d.rule.color:
            correct = action == root.d.action.match_color

        elif self.hidden_rule == root.d.rule.shape:
            correct = action == root.d.action.match_shape

        elif self.hidden_rule == root.d.rule.number:
            correct = action == root.d.action.match_number
        
        # Increment the number of trials after the testee has chosen.
        self.trial += 1

        # Every 10 trials, switch the hidden rule, and pick a random one not chosen before.
        if self.trial % self.switch_every == 0:
            self.previous_rule = self.hidden_rule
            options = [r for r in self.rules if r != self.hidden_rule]
            self.hidden_rule = random.choice(options)
        
        # Return the result of the testee's choice
        if correct:
            return root.d.feedback.correct
        else:
            return root.d.feedback.incorrect


# Class represents NACS, which is responsible for general knowledge and reasoning
class RuleChoice:

    # Initialize with a random rule
    def __init__(self, rules):
        self.rules = rules
        self.current_rule = random.choice(self.rules)

    # Return the rule choice
    def choose_rule(self):
        return self.current_rule

    # Update the rule based on the feedback
    def update_rule(self, feedback):
        if feedback == root.d.feedback.incorrect:
            options = [r for r in self.rules if r != self.current_rule]
            self.current_rule = random.choice(options)

# Class represents ACS, which is responsible for taking action based on a choice.
class MakeChoice:

    # Initialize with the context of environment
    def __init__(self, root):
        self.root = root

    # Methond for choosing action
    def choose_action(self, chosen_rule):
        # Color
        if chosen_rule == root.d.rule.color:
            return root.d.action.match_color
        # Shape
        if chosen_rule == root.d.rule.shape:
            return root.d.action.match_shape

        # Number 
        if chosen_rule == root.d.rule.number:
            return root.d.action.match_number

# Class is the WCST simulation
class WCSTModel:
    
    # Initialize context, and when to switch rule
    def __init__(self, switch_every):
        
        # Possible rules
        self.rules = [root.d.rule.color,root.d.rule.shape,root.d.rule.number]

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

    # Function for running the trial
    def run_trial(self):
        chosen_rule = self.nacs.choose_rule()
        # Choose action based on assumed rule
        action = self.acs.choose_action(chosen_rule)

        # Keeping track of previous rule to measure perservation errors
        previous_rule = self.task.previous_rule
        
        # Give feedback to the action
        feedback = self.task.give_feedback(action)

        # if the feedback is incorrect
        if feedback == root.d.feedback.incorrect:
            # increase the total number of errors
            self.errors += 1

            # If the chosen rule is the same as the previous rule.
            if previous_rule is not None and chosen_rule == previous_rule:
                self.perseveration_errors += 1

        # update the rule based on feeback.
        self.nacs.update_rule(feedback)


# Testing
model = WCSTModel(10)

# Run 50 trials
for _ in range(50):
    model.run_trial()

# Print the total and perservation errors.
print("Errors:", model.errors)
print("Perseveration errors:", model.perseveration_errors)

