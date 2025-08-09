# Kosha - Your Personal AI Journal Bot

**Kosha** is a smart, conversational Telegram bot designed to be your personal digital assistant. It helps you track your life, thoughts, and tasks through journaling, reminders, and AI-powered summaries, all within the convenience of Telegram.

## Key Features

-   **📝 Daily Journaling:** Seamlessly log your thoughts, activities, and notes anytime.
-   **🤖 AI-Powered Summaries:** Get daily summaries of your journal entries, powered by Google's Gemini AI.
-   **💬 Conversational AI Chat:** Chat directly with Gemini for brainstorming, asking questions, or just for fun.
-   **✅ Interactive TODO Lists:** Manage your daily tasks with an easy-to-use, interactive to-do list.
-   **🔔 Smart Reminders:** Set reminders using natural language (e.g., "remind me in 2 hours to call mom").
-   **🗓️ Scheduled Check-ins:** Receive hourly check-ins to help you stay on track with your tasks.
-   **🔒 Secure & Private:** The bot can be configured to respond only to your personal Telegram account.

## How It Works

Kosha is built with Python and leverages several powerful libraries:

-   **[python-telegram-bot](https://python-telegram-bot.org/):** For interacting with the Telegram Bot API.
-   **[Google Gemini API](https://ai.google.dev/):** For all AI-powered features, including summaries and chat.
-   **[APScheduler](https://apscheduler.readthedocs.io/):** For scheduling reminders, daily summaries, and check-ins.
-   **[Dateparser](https://dateparser.readthedocs.io/):** For parsing natural language dates and times.
-   **SQLite:** For all data storage.

## Getting Started

To run your own instance of Kosha, follow these steps:

### Prerequisites

-   Python 3.9+
-   A Telegram Bot Token (get one from [BotFather](https://t.me/botfather))
-   A Google Gemini API Key (get one from [Google AI Studio](https://ai.google.dev/))

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/sairaghavendragan/Kosha.git
    cd Kosha
    ```

2.  **Install the required packages:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Set up your environment variables:**
    -   Copy the example `.env.example` file to a new `.env` file:
        ```bash
        cp .env.example .env
        ```
    -   Open the `.env` file and add your credentials.
    -   To make the bot private, you **must** add your `MY_CHAT_ID`. To get your ID, send a message to the Telegram bot **[@raw_info_bot](https://t.me/raw_info_bot)**.
        ```
        BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN
        GEMINI_API_KEY=YOUR_GEMINI_API_KEY
        TIMEZONE=Your/Timezone # e.g., America/New_York
        MY_CHAT_ID=YOUR_TELEGRAM_CHAT_ID
        ```

4.  **Initialize the database:**
    The bot will automatically create the `database.db` file on its first run.

5.  **Run the bot:**
    ```bash
    python main.py
    ```

Your bot should now be running and responding only to you!

## Commands & Usage

-   **Any Text Message:** Any message that is not a command will be saved as a journal entry for the day.
-   `/todo [task]`: Add a new task to your daily TODO list.
-   `/todos`: Show your interactive TODO list for the day.
-   `/remind [when] [what]`: Set a reminder.
    -   *Example:* `/remind in 1 hour to check the oven`
-   `/summary [date]`: Get the AI-generated summary for a specific date.
    -   *Example:* `/summary yesterday` or `/summary 2025-08-10`
-   `/logs`: Show all your journal entries for today.
-   `/gemini [optional query]`: Start a conversation with the Gemini AI. If you provide a query, it will be a single-turn conversation.
-   `/endgemini`: End the current Gemini chat session.

## License

This project is licensed under the MIT License.