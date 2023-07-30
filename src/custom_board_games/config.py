import os
from dotenv import load_dotenv
import pathlib
load_dotenv()
# Our Host URL should not be prepended with "https" nor should it have a trailing slash.
os.environ['STABILITY_HOST'] = 'grpc.stability.ai:443'

ROOT = pathlib.Path(__file__).parent.resolve()

GAME_CONFIG_DIR = ROOT / 'game_configs'
os.makedirs(GAME_CONFIG_DIR, exist_ok=True)
TEXT_PROMPT_TEMPLATE_DIR = ROOT / 'text_prompt_templates'
os.makedirs(TEXT_PROMPT_TEMPLATE_DIR, exist_ok=True)
GENERATED_DIR = ROOT / "generated"
os.makedirs(GENERATED_DIR, exist_ok=True)
MESSAGE_CACHE_DIR = GENERATED_DIR / 'message_cache'
os.makedirs(MESSAGE_CACHE_DIR, exist_ok=True)
LLM_OUTPUT_DIR = GENERATED_DIR / "llm_output"
os.makedirs(LLM_OUTPUT_DIR, exist_ok=True)
GENERATED_OUTPUT_CONFIG_DIR = LLM_OUTPUT_DIR / 'game_configs'
os.makedirs(GENERATED_OUTPUT_CONFIG_DIR, exist_ok=True)
GENERATED_OUTPUT_STYLE_DIR = LLM_OUTPUT_DIR / 'game_styles'
os.makedirs(GENERATED_OUTPUT_STYLE_DIR, exist_ok=True)
GENERATED_IMAGE_DIR = GENERATED_DIR / "images"
os.makedirs(GENERATED_IMAGE_DIR, exist_ok=True)
UUID_NAME_MAP_FILENAME = GENERATED_DIR / 'uuid_name_map.yaml'
FONTS_DIR = ROOT / 'fonts'
os.makedirs(FONTS_DIR, exist_ok=True)
HTML_TEMPLATES_DIR = ROOT / 'html_templates'
