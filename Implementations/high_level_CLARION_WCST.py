# Introductory comment: This is a non-agentic, Python implementation of the WCST (Wisconsin Card Sorting Test). The classes in this implmenetation represent a tester (WCSTTester), participant (ParticipantRuleChoice and ParticipantMakeChoice), and their interactions within a single trial (WCSTTrial). The WCST is a neuropsychological test which allows for the measure of cognitive flexibility, which essentially is the capacity of a cognitive agent to rapidly change their behaviour in response to external feedback in order to achieve a target goal. The WCST usually involves one or more target cards and a set of deck cards which are used by the participant. Each card contains a specific set of shapes which vary with respect to three categories; color of shape, type of shape, and number of shapes. In a single trial, the participant uses their deck cards to match the target card's correct category. The sorting rule (correct category) is not known by the participant. After each trial (matching attempt), the tester provides feedback (correct or incorrect) to the participant based on the current sorting rule. After a fixed number of continuous successful trials (trials where the pariticpant correctly matched the target card(s)), the tester changes the sorting rule in the trial following the final succesful trial without telling the participant, who then has to identify the new rule. Throughout the test, the participant must infer the correct sorting rule based on the feedback given by the tester.
# Distinctions from original WCST: The WCST reflected in this implementation differes from the version highlighted in the introductory comment. The notion of a physical card with identifiable features is not reflected here. In this implementation, an assumption is made where the pariticpant is aware of the three possible categories (shape, color, or number) it must match with the tester's sorting rule in a given trial. The test simply involves a declaration by the participant of the current sorting rule to which the tester then responds with feedback (correct or incorrect). The tester still changes the sorting rule after a fixed number of successive correct matches, a number which the participant is not aware of and must identify.
# Implementation goal: The goal of this implementation is to reflect a high-level representation of how a CLARION agent may interact with the WCST as a participant. The participant is defined in two classes; the ParticipantRuleChoice class and the MakeCoice class. The ParticipantRuleChoice class represents CLARION cognitive architecture's NACS (Non-Action Centered Subsystem), which is responsible for maintaining an agent's general knowledge and reasoning capabilties. The ParticipantMakeChoice class represents the CLARION cognitive architecture's ACS (Action-Centered Subsystem), which is responsible for an agent's physical actions. In the context of the altered WCST, the general knowledge of the model would be rules available in the test (color, shape, or number), their probabilities of matching the correct sorting rule in a given trial, the internally chosen rule for the trial, the number of correct matches in a row, and the number of trials before the sorting rule switches. It's reasoning capabilities are reflected in the choose_rule, update_rule and choose_next_rule functions. The actions available to the model reflect the rule it has chosen internally. For example, if the model chooses "color" (which in reality would be a declaration of the card chosen to the tester), the choice is passed through the ACS onto the tester. The CLARION cognitive architecture is composed of a total of four subclasses, including the ACS and NACS, which each interact with each other to emerge complex, human-like behaviour. For the purposes of the altered WCST, the ACS and NACS would be sufficient.

# Relevant imports

from pyClarion import Atom, Atoms # Atom and Atoms classes from PyClarion. In a true CLARION agent implemented using the PyClarion library, an Atom would represent the smallest symbolic unit of explicit knowledge. Atoms define a collection of Atom classes.
from pyClarion.knowledge import Root, DataFamily # Root and DataFamily from PyClarion. These classes are used to pass atoms to a CLARION agent. In this implementation, they are passed to a variable which the tester and participant class can access in their functions.
import random, time # Import random for random choices, and time to pause between trials, before feedback, and before choosing a rule.


# This would be the "Kesypace Definition" section of defining a CLARION agent through the PyClarion library. This section essentially represents the full context of a CLARION agent (or its "world") where it may be able to access the Atoms relevant to its simulation. In this implementation, this section is simply used as a convenient store for the elements of the altered WCST (rules available, feedback from the tester, and the actions from the participant). It also presents a more accurate depiction of how information is represented in a CLARION agent, than, say, groups of Strings. Despite using a facet of PyClarion agent definition, the implementation remains un-agentic.

# Class represents the possible sorting rules in a trial.
class Rule(Atoms):
# color, shape, or number
    color: Atom
    shape: Atom
    number: Atom

# Class represents the possible feedback the paritcipant can recieve.
class Feedback(Atoms):
# A participant's choice can be correct or incorrect
    correct: Atom
    incorrect: Atom

# Class represents the possible actions a participant can take based on the rule they want to match with.
class Action(Atoms):
# The participant can match with color, number, or shape.
    match_color: Atom
    match_number: Atom
    match_shape: Atom

# Class which holds the data defined to represent the  simulation. In our case, this is all the information relevant to the WCST (rules, feedback, and actions).
class WCSTData(DataFamily):
    rule: Rule
    feedback: Feedback
    action: Action

# Class represents the root, a reference to the information relevant to the WCST.
class WCSTRoot(Root):
    d: WCSTData

# The WCST information can be accessed from the root variable.
root = WCSTRoot()

# handles for rules, feedback, and actions to be accessed by the participant and tester classes.
rule = root.d.rule
feedback = root.d.feedback
action = root.d.action

# Tester Class. Represents the WCST tester. In this implementation, we are not modelling the tester as an agentic architecture, so all of its capacities are contained in this single class, as opposed to splitting them between different classes which may represent the ACS, NACS, or other needed CLARION subsystems to accurately reflect a high-level implementation of an agentic tester.
class WCSTTester:

    # Initialize WCSTTester; recieves the possible sorting rules and the fixed number of correct guesses by the participant before switching the sorting rule.
    def __init__(self, rules, switch_every):

        self.rules = rules # List of rules atoms.
        self.sorting_rule = random.choice(self.rules) # Randomly choose initial sorting rule.
        self.previous_rule = None # To keep track of the previous sorting rule (So the same rule is not picked after switching).
        self.switch_every = switch_every # Number of correct guesses before switching sorting rule.
        self.correct_guesses = 0 # Number of correct guesses by the participant (To know when to switch).
    
    # Turn participant actions to strings for message printing.
    def to_string(self, the_action):
        if the_action == action.match_color:
            return "matching with color"
        if the_action == action.match_shape:
            return "matching with shape"
        if the_action == action.match_number:
            return "matching with number"

    # Function to give feedback to participant. Receives the participant's action and returns the feedback (correct or incorrect).
    def give_feedback(self, given_action):

        # Correct is a boolean which, based on the comparison between the participant's action (match with color, shape, or number) and the current sorting rule (shape, color, or number), could be true, indicating that the participant has chosen the correct rule which matches the sorting rule, or false, indicating that the participant has chosen the incorrect rule and failed to match the sorting rule.
        if self.sorting_rule == rule.color:
            correct = given_action == action.match_color

        elif self.sorting_rule == rule.shape:
            correct = given_action == action.match_shape

        elif self.sorting_rule == rule.number:
            correct = given_action == action.match_number
       
        time.sleep(1) # Pausing to simulate response time.

        # Give feedback to the participant based on the result of their guess (correct or incorrect) and change the sorting rule if the participant has correctly guessed it the initialized fixed number of correct guesses (self.switch_every variable).
        if correct: # If the result of "correct" is true, increment the number of correct guesses by the participant and print a message that the participant's action was correct. At the end of the block, return a "correct" Atom from the set of feedback Atoms.
            self.correct_guesses += 1
            print("Tester:", self.to_string(given_action), "was correct")
            if self.correct_guesses > 0 and self.correct_guesses % self.switch_every == 0: # Then, if the number of correct guesses is greater than 0 (so if switch_every is set to 10, the rule doesnt switch after the first trial), and the current successive correct guess by the participant is at the "self.switch_every"th iteration, set the current sorting rule to become the previous one (so it is not immediately picked again), create a new set with the remaining options, and pick a new, random rule between the two remaining ones.
                self.previous_rule = self.sorting_rule
                options = [r for r in self.rules if r != self.sorting_rule]
                self.sorting_rule = random.choice(options)
            return feedback.correct
        else: # Otherwise, if the result of correct is false, print a message that the participant's action was incorrect and return a "correct" Atom from the set of feedback Atoms.
            print("Tester:", self.to_string(given_action), "was incorrect")
            return feedback.incorrect


# Participant class. Represents the participant high-level agent's NACS (Non-Action-centered Subsystem) Which is responsible for general knowledge and reasoning.
# This class also models some emotions and their possible triggers at high level. When the participant makes a choice, they declare their answer to the tester. Each declaration highlights an emotion the participant is feeling. This implementation models frustration when the participant gets the sorting rule wrong two or more times, uncertainty when the participant has to pick between rules with equalling probabilities, and certainty when the participant has found the correct sorting rule.  
class ParticipantRuleChoice:

    # Initialize ParticipantRuleChoice; recieves the set of possible rules (color, shape, number).
    def __init__(self, rules):
        # General knowledge.
        self.rules = rules # List of rules atoms.
        self.init_probs = [1/3, 1/3, 1/3] # List of the probabilities for each rule being the correct sorting rule. At the beginning of the test, before any feedback from the tester, all three rules would have the same probability of being the correct sorting rule.
        self.rule_prob_comp = list(zip(self.rules, self.init_probs)) # A list of tuples of the rules and their corresponding probability of being the correct sorting rule.
        self.chosen_rule = random.choice(self.rules) # Choose a random rule at the beggining of the test, since they all have the same probability of being the correct sorting rule.
        self.incorrect_counter = 0 # Keep track of the number of incorrect guesses to later model frustration (which triggers after two or more incorrect guesses).
        self.correct_streak = 0 # Keep track of the number of correct streaks, to eventually discover the maximum, to which then the participant discovers the number of correct guesses before the sorting rule switches.
        self.learned_switch_every = None # The number of correct guesses before the sorting rule switches.

    # Function turns rules to strings to print participant messages.
    def to_string(self, the_rule):
        if the_rule == rule.color:
            return "color"
        if the_rule == rule.shape:
            return "shape"
        if the_rule == rule.number:
            return "number"
        
    # Function to choose a rule.
    def choose_next_rule(self):
        rule_list = self.rules # The list of rules (structurally the same to the one in rule_prob_comp)
        prob_list = [p for _, p in self.rule_prob_comp] # The list of probabilities for each rule.
        self.chosen_rule = random.choices(rule_list, weights=prob_list, k=1)[0] # Pick the rule with the largest weight (probability of being correct), or a random one if they are all the same.

    # Function to return the chosen rule (passed to the ACS) and print choice declaration. High-level emotion and speech component.
    def choose_rule(self):
        time.sleep(1)

        # Model frustration. Frustrated declaration of rule choice.
        if self.incorrect_counter >= 2: # Print this message if the participant guesses the sorting rule incorrectly 2 or more times.
            print("Model (Frustrated): I WILL MATCH WITH", self.to_string(self.chosen_rule).upper() + "!")

        # Model uncertainty after sorting rule switch. Declare that the sorting rule has switched, and the new rule picked on that basis.
        elif self.learned_switch_every is not None and self.correct_streak == 0: # Print this message once the participant has learned the number of correct guesses.
            print("Model (Learned): The rule probably switched. Hmmm... I will match with", self.to_string(self.chosen_rule) + "...")

        # Model certainty. Certain declaration of rule choice (Participant is 100% that this is the correct rule).
        elif any(prob == 1 for _, prob in self.rule_prob_comp):
            print("Model (Certain): I will match with", self.to_string(self.chosen_rule))

        # Model uncertainty. Uncertain declaration of rule choice (Participant has 2 or more rules to choose with equal probability and is not certain which one may be correct).
        else:
            print("Model (Uncertain): Hmmm... I will match with", self.to_string(self.chosen_rule) + "...")

        return self.chosen_rule # Return the chosen rule

    # Function to update the chosen rule based on the feedback recieved from the tester.
    def update_rule(self, given_feedback):

        if given_feedback == feedback.incorrect: # If the chosen rule is incorrect.

            if self.correct_streak > 0 and self.learned_switch_every is None: # If we had a streak of correct guesses in row and we have not yet learned the number of correct guesses before the rule switches.
                self.learned_switch_every = self.correct_streak # Set the number of correct guesses before sorting rule switch to the streak of correct guesses.
                print("Model (Learned): I think the rule switches after", self.learned_switch_every, "correct guesses.") # Print initial learning message.

            self.correct_streak = 0 # Reset the correct streak.
            self.incorrect_counter += 1 # Increment the number of incorrect guesses.
        
            self.rule_prob_comp = [(r, 0 if r == self.chosen_rule else p) for r, p in self.rule_prob_comp] # Set the prob of the incorrectly chosen rule to 0.
            total_prob = sum(p for _, p in self.rule_prob_comp) # Find total prob of the remaining rules.

            if total_prob == 0: # If all three rules were picked (none of the were correct).
                self.rule_prob_comp = [(r, 1/3) for r, _ in self.rule_prob_comp] # Reset the probability of the rules.

            else: # Otherwise, if it's not 0 (indiciating that there are more choices to make).
                self.rule_prob_comp = [(r, p / total_prob) for r, p in self.rule_prob_comp] # Update the probabilities of the remaining rueles. 

        # If the chosen rule was correct.
        else:
            self.correct_streak += 1 # Increment the streak of correct guesses
            self.incorrect_counter = 0 # Reset the number of incorrcet answers to 0.

            if self.learned_switch_every is not None and self.correct_streak >= self.learned_switch_every: # If we already know the number of successive correct guesses before the sorting rule switches and we reached a corresponding number of correct streaks.
                print("Model (Prediction): I reached", self.learned_switch_every, "correct guesses, so the rule should switch now.") # Print declaration of new choice, since max number of correct guesses was reached and the rule has swaped.
                self.correct_streak = 0 # Reset the streak of correct guesses.
                self.rule_prob_comp = [(r, 1/3) for r,_ in self.rule_prob_comp] # Reset the probabilities of all the rules again to pick a random rule.

            else: # Otherwise, if we have learned the maximum number of correct guesses, but we have not reached that number yet.
                self.rule_prob_comp = [(r, 1 if r == self.chosen_rule else 0)for r,_ in self.rule_prob_comp] # Set the probability of the correctly chosen rule to 100 (continue choosing it).

        self.choose_next_rule() # Choose new rule based on probability updates.


# Participant class. Represents the participant high-level agent's ACS (Action-centered Subsystem) Which is responsible for physical actions. This is where the tester receieves the participant's actions. So, this is a representation of the participant expressing their guess in what would be the physical world.
class ParticipantMakeChoice:

    # Function returns the corresponding action based on the chosen rule.
    def choose_action(self, chosen_rule):

        # If color was chosen, match with color.
        if chosen_rule == rule.color:
            return action.match_color
        # If shape was chosen, match with shape.
        if chosen_rule == rule.shape:
            return action.match_shape
        # If number was chosen, match with number. 
        if chosen_rule == rule.number:
            return action.match_number
        

# WCST trial class. Models an interacting tester and participant (one sends feedback, the other sends actions), models the pariticipant as a set of interacting CLARION subsystems (each belonging to a respective class), and models the tester as a single class which sets a random sorting rules, switches them after certain number of correct guesses, and sends feedback based on the participant's answer.
class WCSTTrial:
    
    # Initialize WCSTModel; Recieves a number which represents the number of correct guesses before switching the hidden rule.
    def __init__(self, switch_every):
        
        self.rules = [rule.color,rule.shape,rule.number] # List of rule Atoms.
        self.tester = WCSTTester(self.rules, switch_every) # The tester, recieves the rules (to choose the sorting rule from) and the number of correect guesses before the sorting rule must be switched.
        self.nacs = ParticipantRuleChoice(self.rules) # The participant's ParticipantRuleChoice system (The system which makes a choice of rules, updates the choice based on feedback, and identifies maximum number of correct guesses before the sorting rule switches). This would be the NACS in an agentic implementation of the participant, hence the name.
        self.acs = ParticipantMakeChoice() # The ParticipantMakeChoice system (the system which returns an action based on the choice of rule). This would be the ACS in an agentic implementation of the participant, hence the name. 
        # The metrics to measure the performance of the participant.
        self.errors = 0 # The total incorrect guesses.
        self.perseverative_errors = 0 # The perseverative errors (When the participant picks the incorrect sorting rule which was the previously correct sorting rule).
        self.correct = 0 # The total correct guesss.

    # Function to run a single trial.
    def run_trial(self):
        chosen_rule = self.nacs.choose_rule() # First the participant chooses a rule (initially a random rule).
        action = self.acs.choose_action(chosen_rule) # The returned action based on the chosen rule.
        previous_sorting_rule = self.tester.previous_rule # Variable to identify whether a perseverative error has happened.
        given_feedback = self.tester.give_feedback(action) # The feedback from the tester based on the participant's answer.

        if given_feedback == feedback.incorrect: # If the participant guessed incorrectly for this trial.
            self.errors += 1 # Increment the total number of errors
            if previous_sorting_rule is not None and chosen_rule == previous_sorting_rule: # If the participant picked a rule that was previously correct (perseverative error).
                self.perseverative_errors += 1 # Increment the number of perseverative errors.

        elif given_feedback == feedback.correct: # Otherwise, if the tester's feedback is "correct".
            self.correct += 1 # Increment the total number of correct answers.

        self.nacs.update_rule(given_feedback) # The participant updates the rule based on the tester's feedback.


# Running the test

model = WCSTTrial(10) # The model of a WCST trial. The number of correct guesses before a sorting rule switch is set to 10.
for i in range(50): # Run 50 trials.
    time.sleep(1) # Pause between each trial.
    print("-" * 50) # Seperators between each trial
    print(" " * 15, "Trial -",i+1, "\n") # Print current trial number.
    model.run_trial() # Run the model.

# Print the total number of errors, the number of perseverative errors, and the number of correctly matched rules.
print("-" * 50) # Seperators.
print("Model errors:", model.errors)
print("Model correct answers:", model.correct)
print("Model perseverative errors:", model.perseverative_errors)
print("-" * 50) # Seperators.









