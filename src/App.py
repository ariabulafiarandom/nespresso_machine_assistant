import os
import time
from flask import Flask, request, jsonify
from flask_cors import CORS
import secrets
import psycopg2
import psycopg2.extras
from openai import OpenAI


threads = {}  # Global variable to store thread IDs

app = Flask(__name__)
app.secret_key = secrets.token_urlsafe(16)
CORS(app)

# OpenAI setup
api_key = os.environ['OPENAI_API_KEY']
client = OpenAI(api_key=api_key)
assistant_id = os.environ['OPENAI_ASSISTANT_ID'] 

# Database connection
def get_db_connection():
    conn = psycopg2.connect(
        host=os.environ['DB_HOST'],
        database=os.environ['DB_DATABASE_NAME'],
        user=os.environ['DB_USER'],
        password=os.environ['DB_PASSWORD']
    )
    return conn

# Utility function to get chat history
def get_chat_history(thread_id):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # Retrieve chat history from the database
    cur.execute('SELECT * FROM message WHERE thread_id = %s ORDER BY uploaded_at', (thread_id,))
    chat_history = cur.fetchall()

    cur.close()
    conn.close()
    return chat_history

def format_chat_history(chat_history_raw):
    formatted_history = []
    for item in chat_history_raw:
        # Extract the necessary fields
        role, message = item[2], item[4]
        formatted_history.append({
            'role': role.capitalize(),
            'message': message
        })
    return formatted_history

# Start a new chat session
@app.route('/start_chat', methods=['POST'])
def start_chat():
    try:
        thread = client.beta.threads.create()
        thread_id = thread.id
        threads[thread_id] = thread_id

        # Insert a new record for the chat session in the database
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
                INSERT INTO chat_session (thread_id) VALUES (%s)
            """, (thread_id,)
        )
        conn.commit()
        cur.close()
        conn.close()

        return jsonify({'status': 'Session started', 'thread_id': thread_id})
    except Exception as e:
        print(f"Error starting chat: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/send_message', methods=['POST'])
def send_message():
    try:
        if request.is_json:
            data = request.get_json()
            session_id = data.get('session_id')
            user_input = data.get('message')
        else:
            session_id = request.form.get('session_id')
            user_input = request.form.get('message')

        print('Session ID:', session_id)  # Debugging
        print('User Input:', user_input)  # Debugging

        if session_id in threads:
            print('Session found in threads')
            thread_id = threads[session_id]
            

            message = client.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=user_input
            )

            message_id = message.id
            message_role = message.role

            conn = get_db_connection()
            cur = conn.cursor()
            # Log the user's message
            
            cur.execute(
                """
                    INSERT INTO message (role, message_id, message, thread_id, assistant_id) 
                    VALUES (%s, %s, %s, %s, %s)
                """,
                (message_role, message_id, user_input, thread_id, assistant_id)
            )
            conn.commit()

            run = client.beta.threads.runs.create(
                thread_id=thread_id,
                assistant_id=assistant_id
            )
            print('Run created')
            while True:
                run = client.beta.threads.runs.retrieve(
                    thread_id=thread_id,
                    run_id=run.id
                )

                time.sleep(1)

                if run.status=="completed":
                    print('Run completed.')
                    messages = client.beta.threads.messages.list(thread_id=thread_id)
                    print(f'messages: {messages}')
                    latest_message = messages.data[0]
                    print(f'latest_message:{latest_message}')
                    message_id = latest_message.id
                    message_role = latest_message.role
                    print(f'new role {message_role}')
                    response_message = latest_message.content[0].text.value
                    print(response_message)
                    # Log the GPT response
                    cur.execute(
                        """
                            INSERT INTO message (role, message_id, message, thread_id, assistant_id) 
                            VALUES (%s, %s, %s, %s, %s)
                        """,
                        (message_role, message_id, response_message, thread_id, assistant_id)
                    )
                    conn.commit()
                    cur.close()
                    conn.close()

                    # Now fetch the updated chat history
                    chat_history_raw = get_chat_history(thread_id)
                    formatted_chat_history = format_chat_history(chat_history_raw)
                    
                    print('Got chat history')
                    print(formatted_chat_history)

                    return jsonify({'chatHistory': formatted_chat_history})

        else:
            print('Session ID not found in threads')
            return jsonify({'error': 'Invalid session ID'})
    
    except Exception as e:
        print('Error:', e)
        return jsonify({'error': str(e)})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
