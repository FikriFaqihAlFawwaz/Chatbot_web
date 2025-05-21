import mysql.connector

# MySQL database connection
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",  # your MySQL username
        password="",  # your MySQL password
        database="chatbot"  # your MySQL database name
    )

# Function to save chat
def save_chat(user_message, bot_response):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("INSERT INTO chat_history (message, response) VALUES (%s, %s)", 
                       (user_message, bot_response))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error saving chat: {e}")

# Function to get chat history
def get_chat_history(user_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT message, response FROM chat_history WHERE user_id = %s ORDER BY created_at DESC", (user_id,))
        chat_history = cursor.fetchall()
        cursor.close()
        conn.close()
        return chat_history
    except Exception as e:
        print(f"Error retrieving chat history: {e}")
        return []

