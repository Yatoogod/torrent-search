from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import logging
import requests
from bs4 import BeautifulSoup

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Function to search on 1337x
def search_1337x(query):
    search_url = f"https://1337x.to/search/{query}/1/"
    response = requests.get(search_url)
    soup = BeautifulSoup(response.text, 'html.parser')

    torrents = []
    for result in soup.find_all('tr')[1:]:
        title = result.find('td', class_='name').a.text
        seeders = result.find_all('td')[3].text
        leechers = result.find_all('td')[4].text
        magnet = result.find('a', href=True)['href']

        torrents.append({
            'title': title,
            'seeders': seeders,
            'leechers': leechers,
            'magnet': magnet
        })

        if len(torrents) >= 12:  # Fetch top 12 results
            break
    
    return torrents

# Function to search on YTS
def search_yts(query):
    search_url = f"https://yts.mx/api/v2/list_movies.json?query_term={query}&page=1"
    response = requests.get(search_url).json()
    
    torrents = []
    for movie in response['data']['movies']:
        title = movie['title']
        seeders = movie['torrents'][0]['seeds']
        leechers = movie['torrents'][0]['peers']
        magnet = movie['torrents'][0]['url']

        torrents.append({
            'title': title,
            'seeders': seeders,
            'leechers': leechers,
            'magnet': magnet
        })
        
        if len(torrents) >= 12:  # Fetch top 12 results
            break
    
    return torrents

# Function to search on Pirate Bay
def search_piratebay(query):
    search_url = f"https://thepiratebay.org/search/{query}/1/99/0"
    response = requests.get(search_url)
    soup = BeautifulSoup(response.text, 'html.parser')

    torrents = []
    for result in soup.find_all('tr')[1:]:
        title = result.find('a', class_='detLink').text
        seeders = result.find_all('td')[4].text
        leechers = result.find_all('td')[5].text
        magnet = result.find('a', href=True)['href']

        torrents.append({
            'title': title,
            'seeders': seeders,
            'leechers': leechers,
            'magnet': magnet
        })

        if len(torrents) >= 12:  # Fetch top 12 results
            break

    return torrents

# Function to search on RARBG
def search_rarbg(query):
    search_url = f"https://rarbg.to/torrents.php?search={query}&order=seeders"
    response = requests.get(search_url)
    soup = BeautifulSoup(response.text, 'html.parser')

    torrents = []
    for result in soup.find_all('tr')[1:]:
        title = result.find('a', class_='torrentname').text
        seeders = result.find_all('td')[3].text
        leechers = result.find_all('td')[4].text
        magnet = result.find('a', href=True)['href']

        torrents.append({
            'title': title,
            'seeders': seeders,
            'leechers': leechers,
            'magnet': magnet
        })

        if len(torrents) >= 12:  # Fetch top 12 results
            break

    return torrents

# Function to combine results from all websites
def search_torrent(query):
    torrents = []

    # Search on 1337x
    torrents += search_1337x(query)
    
    # Search on YTS
    torrents += search_yts(query)

    # Search on The Pirate Bay
    torrents += search_piratebay(query)

    # Search on RARBG
    torrents += search_rarbg(query)

    return torrents[:12]  # Limit to top 12 results

# Function to handle search command
async def search(update: Update, context: CallbackContext):
    query = ' '.join(update.message.text.split()[1:])  # User's search query, split the message after the command
    if not query:
        await update.message.reply_text("Please provide a search query.")
        return

    torrents = search_torrent(query)
    if torrents:
        message = ""
        for idx, torrent in enumerate(torrents, 1):
            message += f"{idx}. {torrent['title']} \n"
            message += f"Seeders: {torrent['seeders']} | Leechers: {torrent['leechers']} \n"
            message += f"/getlink_{idx} \n\n"

        await update.message.reply_text(message)
    else:
        await update.message.reply_text("No torrents found for your query.")

# Function to send magnet link
async def send_magnet(update: Update, context: CallbackContext):
    try:
        idx = int(update.message.text.split('_')[1]) - 1
        torrents = search_torrent(query=' '.join(context.args))  # Fetch torrents again for the latest search
        if 0 <= idx < len(torrents):
            magnet = torrents[idx]['magnet']
            await update.message.reply_text(f"Here is your magnet link:\n{magnet}")
        else:
            await update.message.reply_text("Invalid selection.")
    except (IndexError, ValueError):
        await update.message.reply_text("Invalid command. Please use /getlink_<number>.")

# Main function to run the bot
def main():
    application = Application.builder().token("6264504776:AAFPKj38UwNcA_ARSk0ZlLfc2nlJtxfPbGU").build()

    # Handlers
    application.add_handler(CommandHandler("start", lambda update, context: update.message.reply_text("Welcome to the Torrent Search Bot!")))
    application.add_handler(CommandHandler("search", search))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search))

    # Command to get magnet link
    application.add_handler(MessageHandler(filters.Regex(r'^/getlink_\d+$'), send_magnet))

    # Run the bot
    application.run_polling()

if __name__ == '__main__':
    main()
