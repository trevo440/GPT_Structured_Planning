# ------------------------------------------------------------
# IMPORTS
# ------------------------------------------------------------

from openai import OpenAI
from dataclasses import dataclass, field
from typing import List
import json

# ------------------------------------------------------------
# Error Handling
# ------------------------------------------------------------

class FirstInstruct(Exception):
    pass

# ------------------------------------------------------------
# CONTEXT STORAGE
# ------------------------------------------------------------

@dataclass
class ResponseStore:
    text: str = field(default_factory=str)
    html: str = field(default_factory=str)
    css:  str = field(default_factory=str)
    js:   str = field(default_factory=str)

# ------------------------------------------------------------
# INSTRUCTION SETS
# ------------------------------------------------------------

@dataclass
class Instruct:
    iset:  List[dict] = field(default_factory=list)
    first: List[dict] = field(default_factory=list)
    last:  List[dict] = field(default_factory=list)
    comps: int = 0

    def __post_init__(self):
        if not isinstance(self.iset, list):
            raise ValueError("iset field must be a list")
        if not isinstance(self.first, list):
            raise ValueError("first field must be a list")
        if not isinstance(self.last, list):
            raise ValueError("last field must be a list")

# ------------------------------------------------------------
# PROMPT(S)
# ------------------------------------------------------------

@dataclass
class PromptManager:
    OpenAIclient : OpenAI

    def __post_init__(self):
        # Post initialization, generate the instruction set from ChatGPT
      
        if not ModelInstruct.first:
             raise FirstInstruct("You did not provide the ModelInstruct a first instruction")

        first_instruct = json.dumps(ModelInstruct.first)

        completion = self.OpenAIclient.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": first_instruct},
            ]
        )

        response = completion.choices[0].message.content 
        response = response.strip("```python").strip("```")
        
        try:
            instruct_set = json.loads(response)
            ModelInstruct.iset += instruct_set
        except:
            print("GPT Failed format (Create Instruct): ", response)
        
    def run_instruct(self, 
                     iter_agent: bool = False, 
                     iter_method: str = '', 
                     new_client: OpenAI = None, 
                     response_store: tuple = ('text', False),
                     revise_instruct = True, 
                     rev_instruct: List = [
                        {
                        "task": "GPT Instruction set Recursion",
                        "details": "Using the last output, update the items above."
                        },

                        {
                        "task": "GPT Response to be usable in programming loop",
                        "details": "Return the list-of-python-dictionaries only and NOTHING ELSE."
                        }
                    ]):
        
        '''
        iter_agent: for sending iset instructions back & forth instead of as a appended single packet | not implemented
        iter_method ('pre'|'post'): where to place the first iset Agent instruction before iteration  | not implemented
        new_client: pass to reset the existing context & pass in bare min info from ResponseStore     | partial
        response_store[0]: attribute of response_store to use in current instruction call             | implemented
        response_store[1]: replace OR what to concat existing stored responses with                   | implemented
        revise_instruct: whether or not to use existing stored context to update instruction set      | implemented
        rev_instruct: appended to end of existing instruction set, passed with context for revision   | implemented
        
        '''
        
        if new_client:
            self.OpenAIclient = new_client

        if not ModelInstruct.iset:
            return "0 Tasks remaining in queue"
        
        if not iter_agent:
            prompts = [AgentInstruct.first + [ModelInstruct.iset[0]] + AgentInstruct.last]

        if iter_method == "pre":
            pass

        if iter_method == "post":
            pass

        for prompt in prompts:
            completion = self.OpenAIclient.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": json.dumps(prompt)},
                ]
            )
            response = completion.choices[0].message.content
            
            if response_store[1] == False:
                setattr(TempResponseStore, response_store[0], response)
            else:
                setattr(TempResponseStore, response_store[0], getattr(TempResponseStore, response_store[0]) + response_store[1] + response)

            if len(ModelInstruct.iset) != 1:
                ModelInstruct.iset = ModelInstruct.iset[1:]
            else:
                print("All instructions Completed. Total Instruction Count: ", ModelInstruct.comps + 1)
                return
                
            if revise_instruct:
                init_context = getattr(TempResponseStore, response_store[0]) + "\n"
                revision = ModelInstruct.iset + rev_instruct

                completion = self.OpenAIclient.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": init_context + json.dumps(revision)},
                    ]
                )

                response = completion.choices[0].message.content 
                response = response.strip("```python").strip("```")
                
                try:
                    instruct_set = json.loads(response)
                    ModelInstruct.iset = instruct_set
                except:
                    print("GPT Failed format (Revise Instruct): ", response)

        ModelInstruct.comps += 1

# GLOBAL
TempResponseStore: ResponseStore = ResponseStore()
ModelInstruct: Instruct = Instruct(
    '''
    Currently no execution of LAST instruction exists
    '''
  
    first = [
        {
            "task": "Create Outline of research paper",
            "details": "Then create a plan to write outline a research paper on machine learning, following the list-of-python-dictionaries structure this response came in as, with each section/subsection getting it's own task & details. Please be as specific as possible, while remaining concise. Maximum 5 Dictionaries." 
        },
        {
            "task": "GPT Response to be usable in programming loop",
            "details": "Return the list-of-python-dictionaries only and NOTHING ELSE."
        }
    ]
)

AgentInstruct: Instruct = Instruct(
    '''
    Desired structure for Agent Instructions: First + Current instruction set; + Iterations in iset (if exist); last. If no iset, all instructions sent in one packet.
    '''
  
    first = [
        {
            "task": "Response Selection",
            "details": "Return ONLY the outcome of performing the "details" item in the next dictionary, as text for use in a research paper. Do not include any additional details, or explanation." 
        },  
    ]
)

PM = PromptManager(
    OpenAI(api_key='ENTER_YOUR_KEY_HERE'),
)

# Output Examples
print("INITIAL INSTRUCTION SET:")
print(ModelInstruct.iset)
print()

# Running through instruction set (generator mimic)
PM.run_instruct()

# Current State Output Examples
print("POST-RUN STATE:")
print("Instructions Completed: ", ModelInstruct.comps, "\n")
print("CURRENT INSTRUCT SET: \n", ModelInstruct.iset, "\n")
print("IN STORAGE: \n", TempResponseStore.text)

