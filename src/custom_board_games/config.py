import os
from dotenv import load_dotenv
load_dotenv()
# Our Host URL should not be prepended with "https" nor should it have a trailing slash.
os.environ['STABILITY_HOST'] = 'grpc.stability.ai:443'

GAME_CONFIG_DIR = 'game_configs'
os.makedirs(GAME_CONFIG_DIR, exist_ok=True)
TEXT_PROMPT_TEMPLATE_DIR = 'text_prompt_templates'
os.makedirs(TEXT_PROMPT_TEMPLATE_DIR, exist_ok=True)
GENERATED_DIR = "generated"
os.makedirs(GENERATED_DIR, exist_ok=True)
MESSAGE_CACHE_DIR = os.path.join(GENERATED_DIR, 'message_cache')
os.makedirs(MESSAGE_CACHE_DIR, exist_ok=True)
LLM_OUTPUT_DIR = os.path.join(GENERATED_DIR, "llm_output")
os.makedirs(LLM_OUTPUT_DIR, exist_ok=True)
GENERATED_OUTPUT_CONFIG_DIR = os.path.join(LLM_OUTPUT_DIR, 'game_configs')
os.makedirs(GENERATED_OUTPUT_CONFIG_DIR, exist_ok=True)
GENERATED_OUTPUT_STYLE_DIR = os.path.join(LLM_OUTPUT_DIR, 'game_styles')
os.makedirs(GENERATED_OUTPUT_STYLE_DIR, exist_ok=True)
GENERATED_IMAGE_DIR = os.path.join(GENERATED_DIR, "images")
os.makedirs(GENERATED_IMAGE_DIR, exist_ok=True)
UUID_NAME_MAP_FILENAME = os.path.join(GENERATED_DIR, 'uuid_name_map.yaml')
FONTS_DIR = 'fonts'
os.makedirs(FONTS_DIR)
