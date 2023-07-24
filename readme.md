# README

## MVP Inputs

1. Theme or story
1. Base template (e.g. Coup)
1. Generate new rules?
1. Upload images to use in artwork (they will be modified)
1. Number of board games to make
1. Payment
1. Shipping address

## MVP Desired Outputs

1. pdf containining text instructions along with images for print gameplay
1. Each image needed to upload to board game manufacturer to print

## TODO:

- layout of PDF
  - create html using jinja, convert to PDF
  - install wkhtmltopdf, pdfkit, jinja2
  - Images on PDF:
    - character on background with title
    - photo of some of the components (box, cards, one card reversed, arranged slightly diagonally)
    - photo of all coins, each card, a reference card, a reversed card, and the reversed instruction page
    - 30ish degree tilted picture of each character card with a corresponding action, with logo superimposed but mostly to the right
    - additional one for contessa in counteractions
    - additional one with both ambassador+captain and both logos. The one on top is even more tilted, perhaps 45 deg
- exactly how to generate text from which prompts
  - maybe provide full original transcript in memory
  - generate each part separately, and include a template for GPT to fill out
- exactly which components I will buy from manufacturer for each game (and save in a spreadsheet or config file)
- sizes of each image
- template prompt(s) for each image
- prompt to identify font
- code to generate necessary stylized text images with font
- code to create final images from stable diffusion imgs + stylized text
- squarespace website to accept inputs and send me a text+email
- generate a full Coup-type board game and have it printed
- launch website
- market it to friends
- add survey if they regenerate the response.
  - did it not make sense (logically or narratively)
  * did you just want to try it again
  * did the newly generated one fix the issue if there was on

high level main image background, with the name of the game, and one of the characters

name of the game

4 sides of the box
bottom of the box

each character card

logo for each character
token logo

two reverse game names for back of each card
simple background for each card

fontface
