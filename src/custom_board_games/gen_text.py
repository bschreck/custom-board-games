import openai
from dotenv import load_dotenv
import os
import sys
import uuid
import pickle
import yaml
from dataclasses import dataclass

try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper
    
from config import (
    GAME_CONFIG_DIR,
    TEXT_PROMPT_TEMPLATE_DIR,
    MESSAGE_CACHE_DIR,
    GENERATED_OUTPUT_CONFIG_DIR,
    GENERATED_OUTPUT_STYLE_DIR,
    UUID_NAME_MAP_FILENAME
)

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")




# Build full pipeline from prompt with one command
# Find true sizes of images I need, and exactly which parts to buy
# Build functions to combine sets of images (e.g. place logos on top, make the card art with text, make the box art with text)
# Build function to output the final PDF and images
# Allow optional user images as seeds
# Build webpage that has input fields for story, theme, user-provided images
# While AI is running, dynamically populate the webpage with text and the generated images
# Calls to Stability AI should be done in parallel, so that the user doesn't have to wait for each image to be generated
# Each image should be able to be regenerated (with access to existing ones), up to N times to prevent spam and wasting my api key
# Potentially need to generate a mock visualization of the actual board game, but only do that if people say it's necessary
# Build react website, add Stripe integration, deploy somewhere
# Connect to my phone number & email, so that I get a text when someone buys a game
# Add randomness/uniqueness slider, which will require rewriting LLM prompts and allowing for different numbers of characters
# Add additional game templates


# new image/config architecture:
# image names & some form of description are inline where they exist in the main config used for jinja template
# write a program that (bidirectionally) maps each of these to a flat list of image prompts
# generate images from the prompts
# save image along with a unique key, mapping to path on disk, to DB
# save unique key alongside original location in config
# for composite images, indicate they are composite in the original config,
#   along with the associated keys in the original config that make them up.
#   some more thought is needed here, because we will need loops (for all char/logos, for all components)
# in the generation step, if a composite image already exists in DB, just fetch it from disk
# otherwise, find the images that make it up, combine them, save using a new key to DB along with keys to components
# using key/value store DB will make all this stuff simpler. Perhaps Redis

@dataclass
class Message:
    role: str
    content: str
    name: str | None = None
    function_call: str | None = None

    def parse_yaml(self):
        # TODO: add handling for if AI leaves out quotej
        try:
            return yaml.load(self.content, Loader=Loader)
        except Exception:
            print("could not parse LLM message: " + self.content)
            
    def save_content_as_yaml(self, out_f):
        parsed = self.parse_yaml()
        with open(out_f, "w") as f:
            yaml.dump(parsed, f, Dumper=Dumper)


# TODO: COMBINE the two generated configs into one after text generation

def get_and_save_completion_as_yaml(prompt, out_f, chat_pickle_file, existing_messages=None, verbose=True):
    if verbose:
        print("PROMPT:")
        print(prompt)
    if existing_messages is None:
        existing_messages = [
            Message(role="system", content="You are a board game designer. Your goal is to generate the content for new board games based on templates from existing games.")
        ]
    existing_messages += [
        Message(role="user", content=prompt)
    ]
    completion = openai.ChatCompletion.create(
      model="gpt-4",
      messages=existing_messages
    )
    
    message = Message(**completion.choices[0].message)
    if verbose:
        print("message content", message.content)
    try:
        message.save_content_as_yaml(out_f)
    except Exception as e:
        print(e)
    full_messages = existing_messages + [message]
    save_chat(full_messages, chat_pickle_file)
    return full_messages


def read_and_format_prompt(filename, **format_data):
    with open(filename) as f:
        return f.read().format(**format_data)


def save_chat(messages, out_f):
    with open(out_f, "wb") as f:
        pickle.dump(messages, f)


def save_uuid_to_name_map(map_filename, id, name):
    with open(map_filename) as f:
        uuid_to_name = yaml.load(f, Loader=Loader)
        uuid_to_name[id] = name
    uuid_to_name_str = yaml.dump(uuid_to_name, Dumper=Dumper)
    with open(map_filename, 'w') as f:
        f.write(uuid_to_name_str)


def load_name_and_story(name_and_story_file, verbose=True):
    with open(name_and_story_file) as f:
        generated_game = yaml.load(f, Loader=Loader)
        if 'name' not in generated_game:
            raise ValueError('Could not find name in generated game')
        if 'story' not in generated_game and 'text' not in generated_game['story']:
            raise ValueError('Could not find story.text in generated game')
    if verbose:
        print("Generated Game Name:", generated_game['name'])
        print("Generated Game Story:", generated_game['story']['text'])
    return generated_game['name'], generated_game['story']['text']

    
def gen_game_text(game_run, existing_game_name, theme, verbose=True):
    with open(os.path.join(GAME_CONFIG_DIR, f'{existing_game_name}.yaml'), "r") as f:
        template = yaml.load(f, Loader=Loader)
        
    template_str = yaml.dump(template, Dumper=Dumper)
    
    story_prompt = read_and_format_prompt(
        os.path.join(TEXT_PROMPT_TEMPLATE_DIR, 'story.txt'),
        template_str=template_str,
        theme=theme,
        existing_game_name=existing_game_name
    )

    name_and_story_file = os.path.join(
        GENERATED_OUTPUT_CONFIG_DIR, game_run, 'name_and_story.yaml'
    )
    name_and_story_pickle_file = os.path.join(
        MESSAGE_CACHE_DIR, game_run, 'name_and_story.p'
    )
    existing_messages = get_and_save_completion_as_yaml(
        story_prompt, 
        name_and_story_file, 
        name_and_story_pickle_file,
        verbose=verbose
    )

    new_game_name, _ = load_name_and_story(name_and_story_file, verbose=verbose)

    save_uuid_to_name_map(UUID_NAME_MAP_FILENAME, game_run, new_game_name)

    actions_and_characters_prompt = read_and_format_prompt(
        os.path.join(TEXT_PROMPT_TEMPLATE_DIR, 'action_characters.txt'),
        existing_game_name=existing_game_name,
        new_game_name=new_game_name,
    )

    generated_game_config_file = os.path.join(GENERATED_OUTPUT_CONFIG_DIR, game_run, 'game_config.yaml')
    generated_game_pickle_file = os.path.join(MESSAGE_CACHE_DIR, game_run, 'game_config.p')
    existing_messages = get_and_save_completion_as_yaml(
        actions_and_characters_prompt, 
        generated_game_config_file, 
        generated_game_pickle_file, 
        existing_messages=existing_messages,
        verbose=verbose
    )
    
    image_gen_prompt = read_and_format_prompt(
        os.path.join(TEXT_PROMPT_TEMPLATE_DIR, 'style.txt'),
    )
    generated_art_text_file = os.path.join(GENERATED_OUTPUT_STYLE_DIR, game_run, 'art_text.yaml')
    generated_art_pickle_file = os.path.join(MESSAGE_CACHE_DIR, game_run, 'art_text.p')
    existing_messages = get_and_save_completion_as_yaml(
        image_gen_prompt, 
        generated_art_text_file, 
        generated_art_pickle_file, 
        existing_messages=existing_messages,
        verbose=verbose
    )
    return game_run


if __name__ == '__main__':
    existing_game_name = sys.argv[1]
    theme = sys.argv[2]
    game_run = str(uuid.uuid4())
    game_run = gen_game_text(game_run, existing_game_name, theme, verbose=True)
    print("Generated text for game run", game_run)
