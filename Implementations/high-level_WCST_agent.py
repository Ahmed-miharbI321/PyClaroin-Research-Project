
# Introductory Comment: This is a hard-coded implementation of the high-level functions and roles of some of the different subsystems that make up the CLARION cognitive architecture. This implementation is a high-level representation of how a CLARION agent may engage with the tasks within the WCST and what each of its subsystems may be responsible for in that context. The WCST (Wisconsin Card Sorting Test) is a test where the testee must match a rule (color, shape, or number) with the current, unknown hidden rule set by the tester.

from pyClarion import Atom, Atoms # Import Atom and Atoms, which represent the smallest symbolic units of explicit knowledge in a CLARION agent.
from pyClarion.knowledge import * # For the PyClarion data stores (Buses, BusFamily, DataFamily, etc.).
import random, time # Import random for random choices, and time to pause between trials and simulate thinking time (time taken for the agent to think).

# This section is PyClarion's definition of the agent's context (as in its "world") also known as the "Keyspace Definition" section of the definition of a PyClarion simulation. This section represents all of the information the agent interacts with, internally or externally, to fulfill the simulation. Since we're simulating the WCST, the rules of the test (shape, color, and number), the feedback from the tester (correct or incorrect), and the actions to match with a particular rule (match with color, shape, or number) are all defined here.
# It's important to note that this is the only step of the PyClarion simulation definition "pipeline" that is followed in this implementation. The PyClarion simulation pipline uses the PyClarion library to eventually implement an agentic simulation of a described scenario. This implementation is not meant to be agentic, it is a hard-coded implementation of the high-level functions of the CLARION cognitive architecture in the particular scenario of the WCST. So, this section acts more like a convenient store for all the possible information that would need to be passed around and manipulated in the scenario of the WCST. The section defines bits of related information as "Atoms" which represent the smallest symbolic units of explicit knowledge in a CLARION agent. This section's function as an information reference/store could have been replicated with simple Strings, however, implementing it this way does not interfere with the project's overall purpose of creating a high-level implementation of a CLARION agent, while also accuratelly representing how information is stored in a CLARION agent. 

# Color Atoms for the possible color of shapes on the cards.
class Color(Atoms): 
# A card's shapes can have the colors red, green, or blue.
    red: Atom
    grn: Atom
    blu: Atom

# Shape Atoms for the possible shapes on the cards.
class Shape(Atoms): 
# A card can have the shapes circle, square, or triangle.
    circ: Atom
    squr: Atom
    tria: Atom

# Number Atoms for the possible number of shapes on the cards.
class Number(Atoms):
# There can be one to three shapes on a card.
    one: Atom
    two: Atom
    three: Atom

# The possible hidden rules in a trial.
class Rule(Atoms):
# color, shape, or number
    color: Atom
    shape: Atom
    number: Atom

# The possible feedback the testee can recieve
class Feedback(Atoms):
# A testee's choice can be correct or incorrect
    correct: Atom
    incorrect: Atom

# The possible actions a testee can take based on the rule they want to match with.
class Action(Atoms):
# The testee can match with color, number, or shape.
    match_color: Atom
    match_number: Atom
    match_shape: Atom
            
# Reference for the input to the agent, its output, and the defined target. Since part is only relevant for an agentic PyClarion implementation.
class Main(Buses):
    input: Bus
    output: Bus
    target: Bus

# Reference to the Buses.
class WCSTBuses(BusFamily):
    main: Main

# Reference to the data defined for the simulation. In our case, this is all the information relevant to the WCST.
class WCSTData(DataFamily):
    color: Color
    shape: Shape
    number: Number
    rule: Rule
    feedback: Feedback
    action: Action

# Reference to the WCSTData (and the Buses, which we're not using).
class WCSTRoot(Root):
    b: WCSTBuses
    d: WCSTData

# The context/world of the high-level agent is stored in the "root" variable
root = WCSTRoot()

# Define short handles for data sorts, so we can refer back to them in out "simulation".
color = root.d.color   
shape = root.d.shape  
number = root.d.number 
rule = root.d.rule
feedback = root.d.feedback
action = root.d.action


# Class represents WCST tester. The tester gives feedback (correct/incorrect) based on the testee's guess of the hidden rule and changes the hidden rule after a certain amount of trials (the amount of trials before changing the hidden rule is a random number between 5 and another predefined number).
class WCSTTester:

    # Initialize tester; the hidden rules available to choose from, how many trials before switching the rule, track the number of trials, the previous hidden rule, and the original number of trials before switching the hidden rule (The number of trials before switching the hidden rule will change throughout the test).
    def __init__(self, rules, switch_every):

        # List of rules atoms.
        self.rules = rules

        # Randomly choose hidden rule.
        self.hidden_rule = random.choice(self.rules)

        # Keep count of the current trial.
        self.trial = 0

        # To keep track of the previous hidden rule.
        self.previous_rule = None

        # Initialize number of trials before switching hidden rule.
        self.switch_every = switch_every

        # Keep track of original number of trials before switching hidden rule.
        self.original_switch_every = switch_every
    
    # Function to turn actions recieved from testee to strings for printing.
    def to_string(self, the_action):
        if the_action == action.match_color:
            return "matching with color"
        if the_action == action.match_shape:
            return "matching with shape"
        if the_action == action.match_number:
            return "matching with number"

    # Function to give feedback to testee. 
    def give_feedback(self, given_action):

        # Correct is a boolean which, based on the comparison between the testee's action (match with color, shape, or number) and the current hidden rule (shape, color, or number), will be true, indicating that the testee has chosen the correct rule which matches the hidden rule, or false, indicating that the testee has chosen the incorrect rule and didn't match the hidden rule.
        if self.hidden_rule == rule.color:
            correct = given_action == action.match_color

        elif self.hidden_rule == rule.shape:
            correct = given_action == action.match_shape

        elif self.hidden_rule == rule.number:
            correct = given_action == action.match_number
        
        # Increment to the current trial.
        self.trial += 1

        # If the current trial is the "switch_every"th trial, pick a random new hidden rule, making sure not to pick the one that is currently being used, and change the number of trials before switching the hidden rule to a number between 5, and the previously defined number of trials before switching the hidden rule.
        if self.trial % self.switch_every == 0:
            self.previous_rule = self.hidden_rule
            options = [r for r in self.rules if r != self.hidden_rule]
            self.hidden_rule = random.choice(options)
            self.switch_every = random.randint(5,self.original_switch_every)
        
        time.sleep(1) # Pause for a moment, for a more sequential representation of the testing process.

        # Give feedback to the testee, based on the result of their guess (correct or incorrect).
        if correct: # If the result of "correct" is true, then print a corresponding message, and return the "correct" Atom in the "Feedback" set of Atoms.
            print("Tester:", self.to_string(given_action), "was correct") 
            return feedback.correct
        else:
            print("Tester:", self.to_string(given_action), "was incorrect")
            return feedback.incorrect


# This is the first class which represents the Testee. Since the implementation is meant to be a high-level representation of a CLARION agent, each class is a hard-coded representation of some of the subsystems that make up a CLARION agent but only the ones relevant to this specific task. This class represents the NACS (Non-Action-Centered Subsystem) and the MS (Motivational Subsystem). The NACS is responsible for an agent's general knowledge and reasoning and the motivational subsystem creates incentives for cognition (in this case, it helps to decide between choices). Both of these aspects are roughly represented in the "update_rule" function. The testee guesses the hidden rule based on a list of probabilities that it manipulates throughout the trials.
# This class is also where the abstract concepts are modelled. The concepts of frustration and uncertainty are modelled here through printed messages which are triggered after certain conditions are met during the trials. Frustration is triggered after the testee chooses the incorrect rule two or more times in a row, and is represented through a printed message where all the words are fully capitalised. Uncertainty is triggered when the testee has to pick between rules of equal probability, and is represented through a "hmmm" prefix before a printed message. If neither of the conditions are triggered, a simple message will be printed where the testee will declare their chosen rule.
class RuleChoice:

    # Initialize RuleChoice; the hidden rules to guess, the probability that each one of the rules is the correct one, a composition between the rules and their corresponding probability of being correct, the picked rule (chosen randomly in the beginning), and how many times in a row the rule chosen was incorrect.
    def __init__(self, rules):
        self.rules = rules
        self.init_probs = [1/3,1/3,1/3] # Probability of each rule being correct, equal at the beginning.
        self.rule_prob_comp = list(zip(self.rules,self.init_probs)) # A list of tuples of rules and their coresponding probability of being correct.
        self.chosen_rule = random.choice(self.rules) # Tracking the chosen rule, a random one is picked at the beginniing.
        self.incorrect_counter = 0 # Keeping track of incorrect answers in a row to model frustration (2 or more incorrect answers in a row result in frustration).

    # Turning rules to strings for printing.
    def to_string(self, the_rule):
        if the_rule == rule.color:
            return "color"
        if the_rule == rule.shape:
            return "shape"
        if the_rule == rule.number:
            return "number"
    
    # Function to return the chosen rule and print a corresponding message.
    def choose_rule(self):
        time.sleep(1) # Pause for a moment to simulate "though time".

        # Model frustration.
        if self.incorrect_counter >=2: # If the testee has two or more incorrect answers in a row
            print("Model (Frustrated): I WILL MATCH WITH",self.to_string(self.chosen_rule).upper() + "!") # Print a "frustrated" message declaring the chosen rule.
        
        # Model certainty.
        elif any(1 in tup for tup in self.rule_prob_comp): # If any one of the probabilities in the rule, probability tuple has a 100% probability of being correct
            print("Model (Certain): I will match with", self.to_string(self.chosen_rule)) # Print a message declaring that rule will be chosen (the logic in "update_rule" ensures that this rule will be chosen so this lines up).
        
        # Model uncertainty.
        elif  all(prob == self.rule_prob_comp[0][1] for _,prob in self.rule_prob_comp) or len({prob for _, prob in self.rule_prob_comp}) == 2: # if two or more rules have the same probability in the rule probability tuple list.
            print("Model (Uncertain): Hmmm... I will match with", self.to_string(self.chosen_rule) + "...") # Print an "uncertain" message declaring the chosen rule.

        return self.chosen_rule # Return the chosen rule so a corresponding action is picked and passed to the tester.

    # Function to update the chosen rule based on the feedback recieved from the tester.
    def update_rule(self, given_feedback):

        # If the chosen rule is incorrect.
        if given_feedback == feedback.incorrect:
        
            # If the feedback was incorrect and all the rules have already been chosen (hidden rule probably switched as the testee was cycling through the rules).
            if sum(prob == 1 for _,prob in self.rule_prob_comp) == 1:
                self.rule_prob_comp = [(rule, 0 if rule == self.chosen_rule else 1/3) for rule, _ in self.rule_prob_comp ] # Reset the proabilities for the rules, make it so that they are all equal since the hidden rule most likely switched.

            # If the feedback was incorrect but there are two or three more choices to make
            else:
                self.rule_prob_comp = [(rule, 0) if rule == self.chosen_rule else (rule, prob) for rule, prob in self.rule_prob_comp ] # Turn the prob of the chosen rule to 0 since it was incorrect.

                total_prob = sum(prob for _,prob in self.rule_prob_comp) # Get the new total of the probabilities.

                self.rule_prob_comp = [(rule, prob / total_prob)for rule, prob in self.rule_prob_comp ] # Get the new probability values for each of the remaining values.

            self.incorrect_counter += 1

        # If the chosen rule was correct.
        else:
            self.rule_prob_comp = [(rule, 1 if rule == self.chosen_rule else 0)for rule, _ in self.rule_prob_comp] # Change it's probability of being correect to 100, and everything else to 0. The testee assumes that the hidden rule will not change right after they have picked the correct answer.

            self.incorrect_counter = 0 # Reset the incorrect rules guessed in a row to 0.

        # List of probabilities from tuple
        prob_list = [x[1] for x in self.rule_prob_comp]
        # List of rules from tuple
        rule_list = [x[0] for x in self.rule_prob_comp]

        self.chosen_rule = random.choices(rule_list, weights=prob_list, k =1)[0] # Pick the hidden rule with the highest probability of being correct or a random hidden rule if the probabilities are equal.


# This class represents the ACS (Action-Centered Subsystem), which is responsible for making an action based on the choice retrieved from the NACS, which is influenced by the MS. The testee takes an action (matching with color, shape, or number) based on the choice it made.
class MakeChoice:

    # Function returns the corresponding action based on the chosen rule.
    def choose_action(self, chosen_rule):
        # If chosen color, match with color.
        if chosen_rule == rule.color:
            return action.match_color
        # If chosen shape, match with shape.
        if chosen_rule == rule.shape:
            return action.match_shape

        # If chosen number, match with number. 
        if chosen_rule == rule.number:
            return action.match_number
        

# This class models the whole WCST simulation.
class WCSTModel:
    
    # Create the high-level CLARION subsystems (ACS, NACS, and MS), which collectively represent a high-level implementation of a CLARION agent (the testee), create the tester, keep track of the total errors of the testee, its perseverative errors (when the testee picks an incorrect rule that was previously correct), and the total number of correctly matched rules.
    def __init__(self, switch_every):
        
        # List of rule Atoms.
        self.rules = [rule.color,rule.shape,rule.number]
        # Tester.
        self.tester = WCSTTester(self.rules, switch_every)
        # Testee NACS and MS. 
        self.nacs_ms = RuleChoice(self.rules)
        # Testee ACS.
        self.acs = MakeChoice()
        # Tracking total errors of testee.
        self.errors = 0
        # Tracking testee perseverative errors.
        self.perseverative_errors = 0
        # Tracking total correctly matched rules from testee.
        self.correct = 0

    # Function to run a single trial.
    def run_trial(self):
        chosen_rule = self.nacs_ms.choose_rule() # First the testee chooses a rule.

        action = self.acs.choose_action(chosen_rule) # Then, the testee makes an action based on the chosen rule.

        previous_rule = self.tester.previous_rule # Keeping track of the previous hidden rule to measure perseverative errors.
        
        given_feedback = self.tester.give_feedback(action) # The testeer gives feedback to the testee's chosen rule based on the action they made.

        # If the tester's feedback is "incorrect".
        if given_feedback == feedback.incorrect:
            # Increment the total number of errors
            self.errors += 1

            # If the feedback is "incorrect" and chosen rule is the same as the previous rule (perseverative error).
            if previous_rule is not None and chosen_rule == previous_rule:
                self.perseverative_errors += 1 # Increment the number of perseverative errors.
        # If the tester's feedback is "correct".
        elif given_feedback == feedback.correct: 
            self.correct += 1 # increment the number of correct asnwers

        self.nacs_ms.update_rule(given_feedback) # Based on the feedback, the testee updates the rule.

# Running the test

# WCST model object. Initially, the testee switches the hidden rule after 10 trials.
model = WCSTModel(10)

# Run 50 trials.
for i in range(50):
    time.sleep(1) # Pause between each trial.
    print("-" * 50)
    print(" " * 15, "Trial -",i+1, "\n") # Print current trial number.
    model.run_trial() # Run the model.

# Print the total number of errors, the number of perseverative errors, and the number of correctly matched rules.
print("-" * 50)
print("Model errors:", model.errors)
print("Model correct answers:", model.correct)
print("Model perseverative errors:", model.perseverative_errors)
print("-" * 50)









