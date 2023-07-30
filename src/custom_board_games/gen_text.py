from openai import ChatCompletion as OpenAIChatCompletion
from .utils.mock_gpt import ChatCompletion as MockChatCompletion
from .utils.redis import redis, save_game_config, load_game_config, ensure_redis_key_exists
import openai
import dataclasses
from dotenv import load_dotenv
import os
import uuid
import yaml
import json
from dataclasses import dataclass
import fire

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

from .config import GAME_CONFIG_DIR, TEXT_PROMPT_TEMPLATE_DIR

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")


if os.getenv("ENV", "test") == "test":
    ChatCompletion = MockChatCompletion
else:
    ChatCompletion = OpenAIChatCompletion


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
    # TODO: figure out this shit if i ever use functions
    # name: Union[str, None] = None
    # function_call: Union[str, None] = None




def serializable_messages(messages):
    return [dataclasses.asdict(msg) for msg in messages]


# TODO: COMBINE the two generated configs into one after text generation


def get_and_save_completion(game_run, prompt, chat_id=None, verbose=True):
    if chat_id is None:
        chat_id = str(uuid.uuid4())
        existing_messages = [
            Message(
                role="system",
                content="You are a board game designer. Your goal is to generate the content for new board games based on templates from existing games.",
            )
        ]
    else:
        existing_messages = load_chat(game_run, chat_id)

    if verbose:
        print("PROMPT:")
        print(prompt)

    existing_messages += [Message(role="user", content=prompt)]
    completion = ChatCompletion.create(model="gpt-4", messages=serializable_messages(existing_messages))

    message = Message(**completion.choices[0].message)
    # message = existing_messages[-1]
    if verbose:
        print("message content", message.content)
    parsed = json.loads(message.content)

    save_game_config(game_run, parsed)
    full_messages = existing_messages + [message]
    save_chat(game_run, chat_id, full_messages)
    return chat_id


def read_and_format_prompt(filename, **format_data):
    with open(filename) as f:
        return f.read().format(**format_data)


def save_chat(game_run, chat_id, messages):
    r = redis()
    ensure_redis_key_exists(game_run, "chats")
    r.json().set("game_runs", f".{game_run}.chats", {chat_id: serializable_messages(messages)})


def load_chat(game_run, chat_id):
    r = redis()
    msg_dict_list = r.json().get("game_runs", f".{game_run}.chats.{chat_id}")
    return [Message(**msg_dict) for msg_dict in msg_dict_list]


def load_name(game_run, verbose=True):
    config = load_game_config(game_run)
    name = config.get("name", None)
    if name is None:
        raise ValueError("Could not find name in generated message")
    if verbose:
        print("Generated Game Name:", name)
    return name


def load_story(game_run, verbose=True):
    config = load_game_config(game_run)
    story = config.get("story", None)
    if story is None and "text" not in story:
        raise ValueError("Could not find story.text in generated message")
    if verbose:
        print("Generated Game Story:", story["text"])
    return story["text"]


def gen_game_text(game_run, existing_game_name, theme, verbose=True):
    with open(os.path.join(GAME_CONFIG_DIR, f"{existing_game_name}/story.yaml"), "r") as f:
        story_template = yaml.load(f, Loader=Loader)
    story_template_str = json.dumps(story_template)
    with open(os.path.join(GAME_CONFIG_DIR, f"{existing_game_name}/action_characters.yaml"), "r") as f:
        action_characters_template = yaml.load(f, Loader=Loader)
    action_characters_template_str = json.dumps(action_characters_template)
    with open(os.path.join(GAME_CONFIG_DIR, f"{existing_game_name}/style.yaml"), "r") as f:
        style_template = yaml.load(f, Loader=Loader)
    style_template_str = json.dumps(style_template)

    save_game_config(game_run, story_template)
    save_game_config(game_run, action_characters_template)
    save_game_config(game_run, style_template)

    # TODO: this should only provide a minimal and easy template the LLM needs
    story_prompt = read_and_format_prompt(
        os.path.join(TEXT_PROMPT_TEMPLATE_DIR, "story.txt"),
        template_str=story_template_str,
        theme=theme,
        existing_game_name=existing_game_name,
    )

    # chat_id = "ec2c3a52-d44e-4669-9580-2696dae510e"
    chat_id = get_and_save_completion(
        game_run,
        story_prompt,
        verbose=verbose,
        # chat_id=chat_id
    )

    new_game_name = load_name(game_run, verbose=verbose)

    actions_and_characters_prompt = read_and_format_prompt(
        os.path.join(TEXT_PROMPT_TEMPLATE_DIR, "action_characters.txt"),
        template_str=action_characters_template_str,
        existing_game_name=existing_game_name,
        new_game_name=new_game_name,
    )

    get_and_save_completion(game_run, actions_and_characters_prompt, chat_id=chat_id, verbose=verbose)

    image_gen_prompt = read_and_format_prompt(
        os.path.join(TEXT_PROMPT_TEMPLATE_DIR, "style.txt"), template_str=style_template_str
    )
    get_and_save_completion(game_run, image_gen_prompt, chat_id=chat_id, verbose=verbose)
    return game_run


def main(existing_game_name, theme, game_run=None, verbose=True):
    if not game_run:
        game_run = str(uuid.uuid4())
    print("Game run", game_run)
    game_run = gen_game_text(game_run, existing_game_name, theme, verbose=verbose)
    print("Generated text for game run", game_run)


if __name__ == "__main__":
    fire.Fire(main)
