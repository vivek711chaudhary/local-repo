import logging
import requests
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
    CallbackContext,
    CallbackQueryHandler
)
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import asyncio
from telegram import Update
from telegram.ext import ContextTypes
import json
# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Telegram bot token
BOT_TOKEN = "7606681330:AAHNUpi_k1tfUIKyBeFGn1HusWDahrnUxMw"

# Backend API URL
BASE_URL = "http://localhost:5000"

# Command: /start
# async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     """Sends a welcome message."""
#     await update.message.reply_text("Welcome to the Music Battle Bot! 🎶\nType /help to see available commands.")

# Command: /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Lists all available commands."""
    help_text = (
        "/start - Start the bot\n"
        "/help - List commands\n"
        "/startbattle <track1> <track2> - Start a music battle\n"
        "/votetrack <battleId> <trackNumber> - Vote for a track\n"
        "/battlevotes <battleId> - Get current votes for a battle\n"
        "/battledetails <battleId> - Get details of a battle\n"
        "/battlevoters <battleId> - Get total voters for a battle\n"
        "/leaderboard Get the top voters \n"
        "/get_voters_list <battleId> \n"
        "/get_contract_Balance - Get the balance hold by the contract \n"
        "/close_battle <battleId> - Close the battle with specific battleId \n" 
        "/transfer_to_owner <amount> <userAddress> <senderAddress> Send the money from contract to the senderAdress : Only Owner\n"
    )
    await update.message.reply_text(help_text)

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# Predefined mappings
GENRES = {
    "Pop": 5,  # Payment amount for Pop genre
    "Rock": 10,
    "Hip-Hop": 15,
    "Classical": 3,
}

CREATOR_NAME_MAPPING = {
    "0x14dC79964da2C08b23698B3D3cc7Ca32193d9955": "Creator A",
    "0x23618e81E3f5cdF7f54C3d65f7FBc0aBf5B21E8f": "Creator B",
    "0xa0Ee7A142d267C1f36714E4a8F75612F20a79720": "Creator C",
    "0xBcd4042DE499D14e55001CcbB24a551F3b954096": "Creator D",
    "0x71bE63f3384f5fb98995898A86B02Fb2426c5788": "Creator E",
    "0x1CBd3b2770909D4e10f157cABC84C7264073C9Ec": "Creator F",
    "0xdF3e18d64BC6A983f673Ab319CCaE4f1a57C7097": "Creator G",
    "0xcd3B766CCDd6AE721141F452C550Ca635964ce71": "Creator H",
}

SONG_CREATOR_MAPPING = {
    "Pop": [
        {"song": "Pop Song 1", "creator": "0x14dC79964da2C08b23698B3D3cc7Ca32193d9955"},
        {"song": "Pop Song 2", "creator": "0x23618e81E3f5cdF7f54C3d65f7FBc0aBf5B21E8f"},
    ],
    "Rock": [
        {"song": "Rock Song 1", "creator": "0xa0Ee7A142d267C1f36714E4a8F75612F20a79720"},
        {"song": "Rock Song 2", "creator": "0xBcd4042DE499D14e55001CcbB24a551F3b954096"},
    ],
    "Hip-Hop": [
        {"song": "Hip-Hop Song 1", "creator": "0x71bE63f3384f5fb98995898A86B02Fb2426c5788"},
        {"song": "Hip-Hop Song 2", "creator": "0x1CBd3b2770909D4e10f157cABC84C7264073C9Ec"},
    ],
    "Classical": [
        {"song": "Classical Song 1", "creator": "0xdF3e18d64BC6A983f673Ab319CCaE4f1a57C7097"},
        {"song": "Classical Song 2", "creator": "0xcd3B766CCDd6AE721141F452C550Ca635964ce71"},
    ],
}

# Global variable to store votes
VOTES = {"track1": 0, "track2": 0}


async def start_battle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Starts a new music battle with genre selection."""
    if len(context.args) != 0:
        await update.message.reply_text(
            "Usage: /startbattle "
        )
        return

    # Step 1: Create Inline Keyboard for Genre Selection
    buttons = [
        [InlineKeyboardButton(genre, callback_data=f"genre|{genre}")] for genre in GENRES.keys()
    ]
    keyboard = InlineKeyboardMarkup(buttons)

    await update.message.reply_text(
        "🎶 Select a music genre for the battle:",
        reply_markup=keyboard,
    )


# Callback handler for genre selection
async def handle_genre_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles genre selection, starts the battle, and sets up voting UI."""
    query = update.callback_query
    await query.answer()

    # Extract selected genre
    _, genre = query.data.split("|")

    # Step 2: Allocate two songs and their creators from the selected genre
    songs = SONG_CREATOR_MAPPING.get(genre, [])
    if len(songs) < 2:
        await query.edit_message_text("❌ Not enough songs in the selected genre.")
        return

    track1, track2 = songs[0]["song"], songs[1]["song"]
    creator1, creator2 = songs[0]["creator"], songs[1]["creator"]

    # Step 3: Get payment amount for the selected genre
    payment_amount = GENRES.get(genre, 0)

    # Retrieve the wallet address
    try:
        group_id = query.message.chat.id  # Correct access to group_id
        user_id = query.from_user.id

        # Check wallet mapping
        if group_id not in wallet_mapping or user_id not in wallet_mapping[group_id]:
            await query.edit_message_text("❌ You haven't set your wallet address yet. Use /setwallet to set it.")
            return

        wallet = wallet_mapping[group_id][user_id]["wallet"]
    except Exception as e:
        logger.error(f"Exception occurred: {e}")
        await query.edit_message_text("❌ Failed to retrieve wallet address.")
        return

    # Step 4: Prepare payload
    payload = {
        "track1": track1,
        "track2": track2,
        "creatorTrack1": creator1,
        "creatorTrack2": creator2,
        "userAddress": wallet,
        "paymentAmount": payment_amount,
    }

    # Step 5: Send payload to the backend
    try:
        response = requests.post(f"{BASE_URL}/startbattle", json=payload)
        data = response.json()

        if response.status_code == 200:
            battleId = data.get("battleId", "N/A")
            if battleId == "N/A":
                await query.edit_message_text("❌ Battle creation failed.")
                return

            message = (
                f"🎵 {data['message']}\n"
                f"Battle ID: {battleId}\n"
                f"Balance Before: {data['balanceBefore']}\n"
                f"Balance After: {data['balanceAfter']}\n"
                f"Transaction Hash: {data['transactionHash']}"
            )
            await query.edit_message_text(message)
        else:
            await query.edit_message_text(f"❌ Error: {data.get('error', 'Unknown error occurred.')}")
            return
    except Exception as e:
        logger.error(e)
        await query.edit_message_text("❌ Failed to connect to the backend.")
        return

    # Step 6: Set up the voting UI
    buttons = [
        [
            InlineKeyboardButton(
                f"🎵 Vote Track 1 (0 votes)",
                callback_data=f"vote|track1|{battleId}|{payment_amount}",
            ),
            InlineKeyboardButton(
                f"🎵 Vote Track 2 (0 votes)",
                callback_data=f"vote|track2|{battleId}|{payment_amount}",
            ),
        ]
    ]
    voting_keyboard = InlineKeyboardMarkup(buttons)

    await query.message.reply_text(
        f"Vote for your favorite track below:\n\n"
        f"Track 1: {track1} by {creator1}\n"
        f"Track 2: {track2} by {creator2}\n",
        reply_markup=voting_keyboard,
    )


# Callback handler for voting (handles both UI updates and functionality)
async def handle_voting(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles voting for tracks and updates the user with a separate message."""
    query = update.callback_query
    await query.answer()

    # Extract the data from the callback_data
    try:
        # Unpack the data based on the updated structure
        _, voted_track, battle_id, payment_amount = query.data.split("|")
    except ValueError:
        await query.message.reply_text("❌ Invalid voting data received. Please try again.")
        return

    # Convert `battle_id` and `payment_amount` to appropriate types
    try:
        battle_id = int(battle_id)  # Convert to integer if necessary
        payment_amount = float(payment_amount)  # Convert to float for numeric operations
    except ValueError:
        await query.message.reply_text("❌ Invalid data format in voting information.")
        return

    # Determine the track number (1 or 2) based on the vote
    track_number = 1 if voted_track == "track1" else 2

    user_address = ""
    try:
        group_id = query.message.chat.id  # Correct access to group_id
        user_id = query.from_user.id

        # Check wallet mapping
        if group_id not in wallet_mapping or user_id not in wallet_mapping[group_id]:
            await query.edit_message_text("❌ You haven't set your wallet address yet. Use /setwallet to set it.")
            return

        user_address = wallet_mapping[group_id][user_id]["wallet"]
    except Exception as e:
        logger.error(f"Exception occurred: {e}")
        await query.edit_message_text("❌ Failed to retrieve wallet address.")
        return

    # Prepare the payload to send to the backend
    if not battle_id or not user_address or not payment_amount:
        await query.message.reply_text("❌ Missing required information to process your vote.")
        return

    payload = {
        "battleId": battle_id,
        "trackNumber": track_number,
        "userAddress": user_address,
        "paymentAmount": payment_amount,
    }

    transaction_hash = ""
    try:
        # Step 1: Make API request to process the vote
        print("YOUR PAYLOAD IS THIS:")
        print(payload)
        response = requests.post(f"{BASE_URL}/votetrack", json=payload)

    # Try to parse the JSON response
        data = response.json() if response.status_code == 200 else {}

    # Step 2: Handle response status codes
        if response.status_code == 200:
            transaction_hash = data.get("transactionHash", "N/A")
            message_from_backend = data.get("message", "Vote recorded successfully.")

            if "already" not in message_from_backend.lower():
                message = (
                f"✅ Your vote for Track {track_number} has been recorded!\n"
                f"Transaction Hash: {transaction_hash}"
            )
            else:
                message = "❌ You have already voted in this battle."
        else:
        # Handle non-200 status codes
            message = f"❌ Error: {data.get('error', 'Unknown error occurred.')}"
    except requests.exceptions.RequestException as e:
    # Catch network-related exceptions
        message = f"❌ Failed to connect to the backend. {str(e)}"

    # Send the user a separate response message
    await query.message.reply_text(message)

    # Step 2: Update the voting UI with backend vote counts
    if transaction_hash != "N/A":
        try:
            # Fetch updated vote counts from the backend
            response = requests.get(f"{BASE_URL}/battle/{battle_id}/votes")
            data = response.json()

            if response.status_code == 200:
                buttons = [
                    [
                        InlineKeyboardButton(
                            f"🎵 Vote Track 1 ({data['track1Votes']} votes)",
                            callback_data=f"vote|track1|{battle_id}|{payment_amount}",
                        ),
                        InlineKeyboardButton(
                            f"🎵 Vote Track 2 ({data['track2Votes']} votes)",
                            callback_data=f"vote|track2|{battle_id}|{payment_amount}",
                        ),
                    ]
                ]
                voting_keyboard = InlineKeyboardMarkup(buttons)

                # Update the voting UI with current vote counts
                await query.edit_message_text(
                    f"Vote for your favorite track below:\n\n"
                    f"Track 1: {SONG_CREATOR_MAPPING['Pop'][0]['song']} by {CREATOR_NAME_MAPPING[SONG_CREATOR_MAPPING['Pop'][0]['creator']]}\n"
                    f"Track 2: {SONG_CREATOR_MAPPING['Pop'][1]['song']} by {CREATOR_NAME_MAPPING[SONG_CREATOR_MAPPING['Pop'][1]['creator']]}\n",
                    reply_markup=voting_keyboard,
                )
            else:
                await query.message.reply_text(
                    f"❌ Failed to fetch updated votes. Error: {data.get('error', 'Unknown error.')}"
                )
        except Exception as e:
            logger.error(f"Exception occurred while updating UI: {e}")
            await query.message.reply_text("❌ Failed to update the voting UI.")


# Command: /votetrack
async def vote_track(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Votes for a track in a battle."""
    if len(context.args) != 4:
        await update.message.reply_text("Usage: /votetrack <battleId> <trackNumber> <userAddress> <paymentAmount>")
        return

    try:
        # Extracting arguments
        battleId, trackNumber, userAddress, paymentAmount = context.args
        payload = {
            "battleId": int(battleId),
            "trackNumber": int(trackNumber),
            "userAddress": userAddress,
            "paymentAmount": paymentAmount,
        }

        # Making API request
        response = requests.post(f"{BASE_URL}/votetrack", json=payload)
        data = response.json()

        if response.status_code == 200:
            message = (
                f"✅ {data['message']} \n"
                f"Transaction Hash: {data.get('transactionHash', 'N/A')}"
            )
        else:
            message = f"❌ Error: {data.get('error', 'Unknown error')}"
    except ValueError:
        message = "❌ Invalid input. Ensure that <battleId> and <trackNumber> are numbers."
    except Exception as e:
        logger.error(f"Exception occurred: {e}")
        message = "❌ Failed to connect to the backend."

    await update.message.reply_text(message)

# Command: /battlevotes
async def get_votes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Fetches current votes for a battle."""
    if len(context.args) != 1:
        await update.message.reply_text("Usage: /battlevotes <battleId>")
        return

    battleId = context.args[0]

    try:
        response = requests.get(f"{BASE_URL}/battle/{battleId}/votes")
        data = response.json()

        if response.status_code == 200:
            message = (
                f"🎶 Battle ID: {data['battleId']}\n"
                f"Track 1 Votes: {data['track1Votes']}\n"
                f"Track 2 Votes: {data['track2Votes']}"
            )
        else:
            message = f"❌ Error: {data['error']}"
    except Exception as e:
        logger.error(e)
        message = "❌ Failed to connect to the backend."

    await update.message.reply_text(message)

# Command: /battledetails
async def get_battle_details(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Fetches details of a battle."""
    if len(context.args) != 1:
        await update.message.reply_text("Usage: /battledetails <battleId>")
        return

    battleId = context.args[0]

    try:
        response = requests.get(f"{BASE_URL}/battle/{battleId}/details")
        data = response.json()

        if response.status_code == 200:
            message = (
                f"🎶 Battle ID: {data['battleId']}\n"
                f"Track 1: {data['track1']} (Votes: {data['votesTrack1']})\n"
                f"Track 2: {data['track2']} (Votes: {data['votesTrack2']})\n"
                f"Timestamp: {data['timestamp']}"
                f"Active: {'Yes' if data['isActive'] else 'No'}\n"
            )
        else:
            message = f"❌ Error: {data['error']}"
    except Exception as e:
        logger.error(e)
        message = "❌ Failed to connect to the backend."

    await update.message.reply_text(message)

# Command: /battlevoters
async def get_total_voters(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Fetches total voters for a battle."""
    if len(context.args) != 1:
        await update.message.reply_text("Usage: /battlevoters <battleId>")
        return

    battleId = context.args[0]

    try:
        response = requests.get(f"{BASE_URL}/battle/{battleId}/voters")
        data = response.json()

        if response.status_code == 200:
            message = f"🎶 Total Voters for Battle {data['battleId']}: {data['totalVoters']}"
        else:
            message = f"❌ Error: {data['error']}"
    except Exception as e:
        logger.error(e)
        message = "❌ Failed to connect to the backend."

    await update.message.reply_text(message)

# Command: /leaderboard
async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Fetches the leaderboard for top tracks."""
    try:
        response = requests.get(f"{BASE_URL}/leaderboard")
        data = response.json()

        if response.status_code == 200:
            leaderboard_text = "🎶 Leaderboard\n"
            for idx, entry in enumerate(data['leaderboard']):
                leaderboard_text += f"{idx+1}. {entry['track']} - {entry['votes']} votes\n"
        else:
            leaderboard_text = f"❌ Error: {data['error']}"
    except Exception as e:
        logger.error(e)
        leaderboard_text = "❌ Failed to connect to the backend."

    await update.message.reply_text(leaderboard_text)

# Command: /closebattle
async def close_battle(update: Update, context: ContextTypes.DEFAULT_TYPE, battleId: int) -> None:
    """Closes a battle and retrieves the winner."""
    try:
        # Making API request to get the winner after battle is closed
        response = requests.get(f"http://localhost:5000/battle/{battleId}/winner")
        data = response.json()

        if response.status_code == 200:
            if data.get("winner") and data["winner"].get("_length_", 0) > 0:
                winner_info = data["winner"]
                message = (
                    f"🎉 Battle {data['battleId']} has been closed!\n"
                    f"Winner Details: {winner_info}"
                )
            else:
                message = (
                    f"⚠ Battle {data['battleId']} has been closed, but no winner was found."
                )
        else:
            message = f"❌ Error: {data.get('error', 'Unknown error')}"

    except Exception as e:
        logger.error(f"Exception occurred: {e}")
        message = "❌ Failed to connect to the backend."

    await update.message.reply_text(message)

# Command: /balance
async def get_balance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Fetches and displays the current balance."""
    try:
        # Making API request
        response = requests.get("http://localhost:5000/balance")
        data = response.json()

        if response.status_code == 200:
            balance = data.get("balance", "Unknown")
            message = f"💰 Current Balance: {balance}"
        else:
            message = f"❌ Error: {data.get('error', 'Unable to fetch balance')}"
    except Exception as e:
        logger.error(f"Exception occurred: {e}")
        message = "❌ Failed to connect to the backend."

    await update.message.reply_text(message)

# Command: /voterslist
async def get_voters_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Fetches and displays the voters list for a specific battle."""
    if len(context.args) != 1:
        await update.message.reply_text("Usage: /voterslist <battleId>")
        return

    battle_id = context.args[0]

    try:
        # Making API request
        response = requests.get(f"http://localhost:5000/battle/{battle_id}/votersList")
        data = response.json()

        if response.status_code == 200:
            battle_id = data.get("battleId", "Unknown")
            voters_list = data.get("votersList", [])
            if voters_list:
                voters = "\n".join(voters_list)
                message = f"👥 Voters for Battle ID {battle_id}:\n{voters}"
            else:
                message = f"👥 No voters yet for Battle ID {battle_id}."
        else:
            message = f"❌ Error: {data.get('error', 'Unable to fetch voters list')}"
    except Exception as e:
        logger.error(f"Exception occurred: {e}")
        message = "❌ Failed to connect to the backend."

    await update.message.reply_text(message)

# Command: /transfertouser
async def transfer_to_owner(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Transfers money from the contract to the specified user address."""
    if len(context.args) != 1:
        await update.message.reply_text("Usage: /transfertouser <userAddress>")
        return

    user_address = context.args[0]
    payload = {"userAddress": user_address}

    try:
        # Making POST request
        response = requests.post("http://localhost:5000/transferToOwner", json=payload)
        data = response.json()

        if response.status_code == 200 and data.get("success"):
            message = f"✅ Transfer successful to address: {user_address}"
        else:
            message = f"❌ Transfer failed: {data.get('error', 'Unknown error occurred')}"
    except Exception as e:
        logger.error(f"Exception occurred: {e}")
        message = "❌ Failed to connect to the backend."

    await update.message.reply_text(message)


# In-memory mapping {group_id: {user_id: wallet_address}}
wallet_mapping = {}

# Load wallet data from a file
def load_data():
    global wallet_mapping
    try:
        with open("wallets.json", "r") as f:
            wallet_mapping = json.load(f)
    except FileNotFoundError:
        wallet_mapping = {}

# Save wallet data to a file
def save_data():
    with open("wallets.json", "w") as f:
        json.dump(wallet_mapping, f)

# Start command
async def start(update: Update, context: CallbackContext):
    """Sends a welcome message."""
    await update.message.reply_text("Welcome to the Music Battle Bot! 🎶\nType /help to see available commands.")
    await update.message.reply_text("Welcome! Use /setwallet <wallet> to link your wallet address.")

async def set_wallet(update: Update, context: CallbackContext):
    # Get the wallet address (previously set, if any)
    tempAddress = get_wallet(update, context)

    # If the user already has a wallet address set, notify them
    if tempAddress != "":
        print(f"You have already set the wallet address.\n Your wallet address is {tempAddress}")
        await update.message.reply_text(f"You have already set the wallet address\n Your wallet address is {tempAddress}")
        return  # Exit the function if the wallet is already set

    # Get group ID, user ID, and username
    group_id = update.message.chat_id
    user_id = update.message.from_user.id
    username = update.message.from_user.username

    # Check if the user has provided a wallet address
    if not context.args:
        await update.message.reply_text("Please provide a wallet address, e.g., /setwallet 0xABC123...")
        return

    # Join the arguments to form the wallet address
    wallet = " ".join(context.args)

    # Initialize the group in the mapping if it doesn't exist
    if group_id not in wallet_mapping:
        wallet_mapping[group_id] = {}

    # Store the wallet address for the user
    wallet_mapping[group_id][user_id] = {
        "wallet": wallet,
        "username": username,
    }

    try:
        save_data()  # Save the updated data
    except Exception as e:
        print(f"Problem in storing data: {e}")

    # Confirm the wallet address has been set
    await update.message.reply_text(f"Wallet address for @{username} set to {wallet}.")

async def get_wallet(update: Update, context: CallbackContext):
    group_id = update.message.chat_id
    user_id = update.message.from_user.id

    if group_id not in wallet_mapping or user_id not in wallet_mapping[group_id]:
        await update.message.reply_text("You haven't set your wallet address yet.")
        return ""

    wallet = wallet_mapping[group_id][user_id]["wallet"]
    await update.message.reply_text(f"Your wallet address is {wallet}.")

async def list_wallets(update: Update, context: CallbackContext):
    group_id = update.message.chat_id

    if group_id not in wallet_mapping or not wallet_mapping[group_id]:
        await update.message.reply_text("No wallet addresses found for this group.")
        return

    wallets = wallet_mapping[group_id]
    response = "Wallet mappings:\n"
    for user_id, info in wallets.items():
        response += f"@{info['username']}: {info['wallet']}\n"

    await update.message.reply_text(response)


# Main function to run the bot
def main():
    """Run the bot."""
    application = Application.builder().token(BOT_TOKEN).build()

    # Register commands
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("startbattle", start_battle))
    application.add_handler(CommandHandler("votetrack", vote_track))
    application.add_handler(CommandHandler("battlevotes", get_votes))
    application.add_handler(CommandHandler("battledetails", get_battle_details))
    application.add_handler(CommandHandler("battlevoters", get_total_voters))
    application.add_handler(CommandHandler("leaderboard", leaderboard))
    application.add_handler(CommandHandler("transfer_to_owner", transfer_to_owner))
    application.add_handler(CommandHandler("get_voters_list", get_voters_list))
    application.add_handler(CommandHandler("get_contract_Balance", get_balance))
    application.add_handler(CommandHandler("close_battle", close_battle))

    application.add_handler(CallbackQueryHandler(handle_voting, pattern=r"^vote\|"))
    application.add_handler(CallbackQueryHandler(handle_genre_selection, pattern=r"^genre\|"))

    # Add wallet-related commands
    application.add_handler(CommandHandler("setwallet", set_wallet))
    application.add_handler(CommandHandler("getwallet", get_wallet))
    application.add_handler(CommandHandler("listwallets", list_wallets))

    # Start the bot
    logger.info("Bot started...")
    application.run_polling()
    load_data()

if __name__ == "__main__":
    main()