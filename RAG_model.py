from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ConversationHandler,
    CallbackQueryHandler, filters, CallbackContext
)
from swiggy_api import fetch_swiggy_data  # ✅ Import Swiggy API function
import json
from datetime import datetime
import logging
import os
import subprocess
from swiggydataretriver import SwiggyDataRetriever  

# ✅ Bot Token
TELEGRAM_BOT_TOKEN = "7244868035:AAE9ZdUb-pkVMos3BqN6Oj8QPQmRpd62bnQ"

# ✅ Conversation States
ENTER_NAME, ENTER_VEG_TYPE, CHOOSE_RECOMMENDATION, CHOOSE_MEAL, CHOOSE_MOOD, WAITING_FOR_LOCATION, SHOW_RECOMMENDATIONS = range(7)

# ✅ Setup Debug Logging
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.DEBUG
)

# ✅ Meal-Time Mapping
def get_meal_time():
    """Determine current meal time and return appropriate options."""
    current_time = datetime.now().hour
    if current_time < 11:
        return "breakfast", ["Idli","Dosa","Vada","Coffee","Tea"]
    elif current_time < 15:
        return "lunch", ["Biryani", "Thali", "Pizza", "Burger", "Pasta"]
    else:
        return "dinner", ["Roti", "Biryani", "Dosa", "Pizza", "Nachos"]

# ✅ Start Command
async def start(update: Update, context: CallbackContext) -> int:
    """Handles /start command and asks for user name."""
    await update.message.reply_text("🤖 Welcome! 👤 Please enter your name:")
    return ENTER_NAME  

async def receive_name(update: Update, context: CallbackContext) -> int:
    """Receive and store user's name, then ask for food preference or show change option if already set."""
    user_name = update.message.text.strip()
    
    # ✅ Store or update the user's name
    context.user_data["name"] = user_name
    keyboard = [
        [InlineKeyboardButton("🥦 Veg", callback_data="veg"), InlineKeyboardButton("🍗 Non-Veg", callback_data="non-veg")],
        [InlineKeyboardButton("🥗 Both", callback_data="both")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(f"Great, {user_name}! 🍽️ What type of food do you prefer?", reply_markup=reply_markup)
    return ENTER_VEG_TYPE

async def enter_veg_type(update: Update, context: CallbackContext) -> int:
    """Save user food preference or proceed if they already have one."""
    query = update.callback_query
    await query.answer()

    # ✅ If user wants to change preference, ask again
    if query.data == "change_preference":
        keyboard = [
            [InlineKeyboardButton("🥦 Veg", callback_data="veg"), InlineKeyboardButton("🍗 Non-Veg", callback_data="non-veg")],
            [InlineKeyboardButton("🥗 Both", callback_data="both")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.message.reply_text("🔄 Please select your new food preference:", reply_markup=reply_markup)
        return ENTER_VEG_TYPE  # Stay in the same state to reselect preference

    # ✅ If user selects "Proceed", directly call `choose_recommendation()`
    if query.data == "proceed":
        return await choose_recommendation(update, context)  # Proceed to recommendation choice

    # ✅ If user is selecting a new preference, store it
    context.user_data["food_type"] = query.data

    keyboard = [
        [InlineKeyboardButton("⏳ Time-Based", callback_data="time_based"), InlineKeyboardButton("😊 Mood-Based", callback_data="mood_based")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.reply_text("How would you like food recommendations?", reply_markup=reply_markup)
    return CHOOSE_RECOMMENDATION



async def choose_meal(update: Update, context: CallbackContext) -> int:
    """Ask user to select a meal based on the current time of the day."""
    query = update.callback_query
    await query.answer()

    # ✅ Get current meal time & options
    meal_time, options = get_meal_time()
    context.user_data["meal_time"] = meal_time

    # ✅ Create buttons for available meal options
    keyboard = [[InlineKeyboardButton(item, callback_data=f"food_{item.lower()}")] for item in options]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.reply_text(f"🍽️ It's *{meal_time}* time! What would you like to eat?", reply_markup=reply_markup)
    
    return SHOW_RECOMMENDATIONS  # ✅ Move to the next step to fetch recommendations

# ✅ Handle Recommendation Type Selection
async def choose_recommendation(update: Update, context: CallbackContext) -> int:
    """Handle whether the user wants time-based or mood-based recommendations."""
    query = update.callback_query
    await query.answer()

    recommendation_type = query.data
    context.user_data["recommendation_type"] = recommendation_type

    if recommendation_type == "time_based":
        return await choose_meal(update, context)  

    elif recommendation_type == "mood_based":
        keyboard = [
            [InlineKeyboardButton("😊 Happy", callback_data="mood_happy")],
            [InlineKeyboardButton("😢 Sad", callback_data="mood_sad")],
            [InlineKeyboardButton("😡 Angry", callback_data="mood_angry")],
            [InlineKeyboardButton("😴 Tired", callback_data="mood_tired")],
            [InlineKeyboardButton("😐 Bored", callback_data="mood_bored")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.message.reply_text("😊 How are you feeling today?", reply_markup=reply_markup)
        return CHOOSE_MOOD  

# ✅ Handle Mood Selection
async def choose_mood(update: Update, context: CallbackContext) -> int:
    """Handle user's mood selection and show food options based on the selected mood."""
    query = update.callback_query
    await query.answer()

    user_mood = query.data.replace("mood_", "")  
    context.user_data["selected_mood"] = user_mood

    mood_food_map = {
        "happy": ["Ice Cream", "Cake", "Cold Drinks"],
        "sad": ["Biryani","Nachos"],
        "tired": ["Coffee", "Tea"],
        "angry": ["Biryani", "Pizza"],
        "bored": ["Noodles", "Frankie"],
    }

    if user_mood not in mood_food_map:
        await query.message.reply_text("❌ Invalid mood selection. Please try again.")
        return CHOOSE_MOOD  

    food_options = mood_food_map[user_mood]  
    keyboard = [[InlineKeyboardButton(food, callback_data=f"food_{food.lower()}")] for food in food_options]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.reply_text(f"🍽️ Since you're feeling *{user_mood}*, how about these foods?", reply_markup=reply_markup)
    return SHOW_RECOMMENDATIONS  

# ✅ Request Location
async def request_location(update: Update, context: CallbackContext) -> int:
    """Request the user to share their location for recommendations."""
    
    keyboard = [[KeyboardButton("📍 Share Location", request_location=True)]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

    # ✅ Check if update is from a button click (callback_query) or a message
    if update.message:  
        await update.message.reply_text("📍 Please share your location for better recommendations.", reply_markup=reply_markup)
    elif update.callback_query:  
        await update.callback_query.message.reply_text("📍 Please share your location for better recommendations.", reply_markup=reply_markup)

    return WAITING_FOR_LOCATION  # ✅ Correct state transition


    return SHOW_RECOMMENDATIONS  # ✅ Now waits for user input (handled in fallback)'''
async def receive_location(update: Update, context: CallbackContext) -> int:
    """Receive user location and store coordinates, then call `show_restaurants()`."""
    user_location = update.message.location

    if not user_location:
        print("❌ DEBUG: Location was not received!")  # ✅ Debugging
        await update.message.reply_text("❌ Location not received. Please try again.")
        return WAITING_FOR_LOCATION  

    # ✅ Store location in context
    context.user_data["lat"] = user_location.latitude
    context.user_data["lng"] = user_location.longitude
    print(f"✅ DEBUG: Location received - Lat: {context.user_data['lat']}, Lng: {context.user_data['lng']}")

    # ✅ Immediately call `show_restaurants()` after receiving location
    return await show_restaurants(update, context)

async def show_restaurants(update: Update, context: CallbackContext) -> int:
    """Fetch restaurant data and display to the user, then prompt them to ask a question."""
    
    print("🔍 DEBUG: show_restaurants() called.")  # ✅ Debugging log

    selected_food = context.user_data.get("selected_food", "Dosa")
    lat, lng = context.user_data.get("lat"), context.user_data.get("lng")
    food_type = context.user_data.get("food_type", "both")

    print(f"📡 DEBUG: Fetching restaurant data for {selected_food} at ({lat}, {lng}), Food Type: {food_type}")

    # ✅ Fetch restaurant data
    results = fetch_swiggy_data(lat, lng, selected_food, food_type)

    # ✅ Store results in context
    context.user_data["restaurants"] = results  

    if not results:
        print("❌ DEBUG: No restaurants found.")
        await update.effective_message.reply_text(
            f"❌ No restaurants found for *{selected_food}*. Try another selection.", parse_mode="Markdown"
        )
        return SHOW_RECOMMENDATIONS  

    print(f"✅ DEBUG: {len(results)} restaurants found. Proceeding to user query phase...")

    # ✅ Ask the user to type their query
    await update.message.reply_text(
        "✅ Location received & restaurant data fetched!\n"
        "Now, ask me anything about food recommendations. 🍽️\n"
        "For example:\n"
        "👉 *Which restaurant serves the best biryani?*\n"
        "👉 *Show me the top-rated pizza places nearby.*",
        parse_mode="Markdown"
    )

    return SHOW_RECOMMENDATIONS  # ✅ Move to user query phase

async def fetch_additional_info(update: Update, context: CallbackContext) -> int:
    """Process user questions and fetch AI-powered restaurant recommendations."""
    
    message = update.effective_message  
    user_query = message.text.strip()  # ✅ Get user's typed question
    
    if not user_query:
        await message.reply_text("❌ Please type a question about restaurants!", parse_mode="Markdown")
        return SHOW_RECOMMENDATIONS  

    print(f"🔍 DEBUG: Processing user query - {user_query}")  # ✅ Debug user query

    try:
        google_api_key = "AIzaSyBgJDRTkjwujipEvegv6Le7U9DeprzcPGg"  
        json_file = "rag_results.json"  

        retriever = SwiggyDataRetriever(json_file, google_api_key)
        retriever.setup()

        result = retriever.run_query(user_query)  # ✅ Use user's query

        if not result:
            print("❌ DEBUG: No relevant results found.")
            await message.reply_text("❌ No relevant results found. Try asking differently!", parse_mode="Markdown")
            return SHOW_RECOMMENDATIONS  

        print(f"✅ DEBUG: AI-powered response: {result}")

        await message.reply_text(f"📊 *AI-powered Answer:*\n{result}", parse_mode="Markdown")

    except Exception as e:
        print(f"❌ ERROR: {e}")
        await message.reply_text(f"❌ Error processing your question: {str(e)}", parse_mode="Markdown")

    return SHOW_RECOMMENDATIONS  # ✅ Wait for more user queries

async def fetch_recommendations(update: Update, context: CallbackContext) -> int:
    """Fetch recommendations after receiving location or food selection."""
    
    query = update.callback_query
    if query:
        await query.answer()
        selected_food = query.data.replace("food_", "")  # Extract food name
        context.user_data["selected_food"] = selected_food

    elif update.message:
        pass  # Location was already stored, proceed to fetching

    lat, lng = context.user_data.get("lat"), context.user_data.get("lng")
    if lat is None or lng is None:
        return await request_location(update, context)  # ✅ Ask for location first

    return await show_restaurants(update, context)  # ✅ Fetch restaurants and move to AI-based recommendations

def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],  
    states={
        ENTER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_name)],
        ENTER_VEG_TYPE: [CallbackQueryHandler(enter_veg_type)],  
        CHOOSE_RECOMMENDATION: [CallbackQueryHandler(choose_recommendation)],  
        CHOOSE_MOOD: [CallbackQueryHandler(choose_mood, pattern="^mood_.*$")],  
        WAITING_FOR_LOCATION: [MessageHandler(filters.LOCATION, receive_location)],
        SHOW_RECOMMENDATIONS: [
            CallbackQueryHandler(fetch_recommendations, pattern="^food_.*$"),  
            MessageHandler(filters.TEXT & ~filters.COMMAND, fetch_additional_info),  # ✅ Handle user queries after fetching data
        ],
    },
    fallbacks=[MessageHandler(filters.TEXT & ~filters.COMMAND, fetch_additional_info)],  # ✅ Fallback for unexpected queries
)

    app.add_handler(conv_handler)
    print("🤖 Bot is running... Waiting for input...")
    app.run_polling()

    '''app.add_handler(conv_handler)
    print("🤖 Bot is running... Waiting for input...")
    app.run_polling()'''

if __name__ == "__main__":
    main()












from sklearn.metrics import precision_score, recall_score, f1_score
import numpy as np

def evaluate_retrieval(recommended_items, ground_truth_items, k=5):
    """
    Evaluate retrieval performance at top-k recommendations.
    
    Args:
        recommended_items (list): List of recommended food/restaurant names.
        ground_truth_items (list): List of actual preferred food/restaurant names (user likes).
        k (int): Number of top recommendations to evaluate (default is 5).

    Returns:
        dict: Dictionary containing Precision@k, Recall@k, F1@k scores.
    """
    # Trim to top-k
    recommended_top_k = recommended_items[:k]

    # Create binary vectors
    y_true = [1 if item in ground_truth_items else 0 for item in recommended_top_k]
    y_pred = [1] * len(recommended_top_k)  # We predict 1 for all recommended

    # Calculate metrics
    precision = precision_score(y_true, y_pred, zero_division=0)
    recall = recall_score(y_true, y_pred, zero_division=0)
    if precision + recall == 0:
        f1 = 0.0
    else:
        f1 = 2 * (precision * recall) / (precision + recall)

    return {
        "Precision@{}".format(k): round(precision, 3),
        "Recall@{}".format(k): round(recall, 3),
        "F1@{}".format(k): round(f1, 3)
    }
