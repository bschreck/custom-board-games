import openai
from dotenv import load_dotenv
import os
import yaml
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper
load_dotenv()


# TODO make namedtuple for Message
#namedtuple MessageDict
# role # system, user, assistant, function
# content
# name
# function_call

if __name__ == '__main__':
    #settings = OpenAIProvider.default_settings
    #logger = logging.getLogger("Custom Board Games GPT Logger")
    #provider = OpenAIProvider(settings, logger)
    #completion: OpenAIObject = openai.ChatCompletion.create(
    #    messages=messages,
    #    model="model",
    #    n=1,
    #    temperature=1, # 0-2
    #    top_p=1, # 0-1
    #    functions=[], # name, description, params
    #    function_call="none", #"auto"
    #    api_key=openai_api_key,
    #    api_base=openai_api_base,
    #    organization=openai_organization,
    #)
    openai.api_key = os.getenv("OPENAI_API_KEY")

    with open('templates/coup_template_config.yaml', "r") as f:
        template = yaml.load(f, Loader=Loader)
        
    template_str = yaml.dump(template, Dumper=Dumper)
    
    theme = "teenage mutant ninja turtles"
    prompt = f'''
Generate the name and narrative storyline of a new board game.
This name and story will be used to automatically replace the fields in the YAML template provided below.
You should output only the "name" and "story.text" fields in a way that is parseable by YAML. Include quotes around strings in case you use reserved keywords by YAML.
This board game should be based on the following theme: {theme}.

Example output:

name: "Teenage Mutant Ninja Turtles Game"
story:
  text:
   - "my story paragraph 1"
   - "my story paragraph 2"


{template_str}
'''

    completion = openai.ChatCompletion.create(
      #model="gpt-4",
      model="gpt-4",
      messages=[
        {"role": "system", "content": "You are an automated board game designer. Your goal is to generate the content for new board games based on templates from existing games."},
        {"role": "user", "content": prompt}
      ]
    )

    message = completion.choices[0].message
    print("message content", message['content'])
    # TODO: add handling for if AI leaves out quotej
    try:
        generated = yaml.load(message["content"], Loader=Loader)
    except Exception:
        raise ValueError("could not parse LLM output: " + message["content"])
    if 'name' in generated:
        template['name'] = generated['name']
    else:
        raise ValueError("could not find name in LLM output: " + generated)
    if 'story' in generated and 'text' in generated['story']:
        template['story']['text'] = generated['story']['text']
    else:
        raise ValueError("could not find story.text in LLM output: " + generated)
    with open('generated_game.yaml', "w") as f:
        yaml.dump(template, f, Dumper=Dumper)
        