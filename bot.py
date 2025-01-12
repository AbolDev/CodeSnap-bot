import telebot
from telebot.types import Message
from config import TOKEN

from pygments import highlight
from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.formatters import ImageFormatter
from PIL import Image
from io import BytesIO

# ['dracula', 'github-dark', 'gruvbox-dark', 'monokai', 'native', 'nord-darker', 'one-dark', 'paraiso-dark', 'solarized-dark', 'stata-dark']

def generate_code_image(code: str, language: str = None) -> bytes:
    """Convert code to syntax highlighted image"""
    try:
        # Get the appropriate lexer
        if language:
            lexer = get_lexer_by_name(language, stripall=True)
        else:
            try:
                lexer = guess_lexer(code)
            except:
                lexer = get_lexer_by_name("text")

        # Configure the image formatter
        formatter = ImageFormatter(
            style="nord-darker", # paraiso-dark, dracula
            font_name="Courier New",
            font_size=24,
            image_width=2200,
            image_height=1600,
            line_numbers=True,
            line_number_bg="#272823",
            line_number_fg="#6b6b6b",
            line_number_separator=True,
            line_number_pad=5,
            image_pad=10,
        )
        
        # Generate the highlighted code image
        highlighted_code = highlight(code, lexer, formatter)
        
        # Process the image
        image = Image.open(BytesIO(highlighted_code))
        image = image.resize((image.width, image.height), Image.LANCZOS)
        
        # Convert to bytes
        image_bytes = BytesIO()
        image.save(image_bytes, format="PNG")
        image_bytes.seek(0)
        
        return image_bytes.getvalue()
    except Exception as e:
        print(f"Error generating image: {e}")
        return None

# Initialize bot
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message: Message):
    """Handle /start command"""
    welcome_text = "Hi! Send me code and I'll convert it to a beautiful image."
    if message.chat.type in ['group', 'supergroup']:
        welcome_text += f"\nMention me (@{bot.user.username}) with the code or reply to a message containing code."
    bot.reply_to(message, welcome_text)

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message: Message):
    """Handle all messages containing code"""
    # Only process messages that mention the bot in groups
    if message.chat.type in ['group', 'supergroup'] and f'@{bot.user.username}' not in message.text:
        return

    codes = []

    # Check for reply
    if message.reply_to_message:
        if message.reply_to_message.entities:
            for entity in message.reply_to_message.entities:
                if entity.type == "pre":
                    code = message.reply_to_message.text[entity.offset:entity.offset + entity.length]
                    codes.append({'content': code, 'language': entity.language})
        # If no code blocks found, use entire text
        if not codes and message.reply_to_message.text:
            cleaned_text = message.reply_to_message.text.replace(f'@{bot.user.username}', '').strip()
            if cleaned_text:
                codes.append({'content': cleaned_text, 'language': None})

    # Check current message
    if message.entities:
        for entity in message.entities:
            if entity.type == "pre":
                code = message.text[entity.offset:entity.offset + entity.length]
                codes.append({'content': code, 'language': entity.language})
    
    # If no code blocks found, use entire message
    if not codes and message.text:
        cleaned_text = message.text.replace(f'@{bot.user.username}', '').strip()
        if cleaned_text:
            codes.append({'content': cleaned_text, 'language': None})

    # Generate and send images
    media = []
    for code in codes:
        image_bytes = generate_code_image(code['content'], code['language'])
        if image_bytes:
            media.append(telebot.types.InputMediaPhoto(image_bytes))

    if media:
        try:
            if len(media) == 1:
                bot.send_photo(message.chat.id, media[0].media)
            else:
                bot.send_media_group(message.chat.id, media)
        except Exception as e:
            print(f"Error sending message: {e}")
            bot.reply_to(message, "Sorry, I couldn't process that code. Please try again.")

if __name__ == "__main__":
    print("Bot is running...")
    while True:
        try:
            bot.infinity_polling()
        except Exception as e:
            print(f"Bot error: {e}")
            continue
