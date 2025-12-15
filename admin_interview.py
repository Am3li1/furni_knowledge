# admin_interview.py - Admin interview system to learn about furniture offerings
from flask import Flask, request, jsonify, session, render_template_string
from flask_cors import CORS
import os
from dotenv import load_dotenv
import json
from datetime import datetime
from database import get_db_connection
import hashlib

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'admin-secret-key-123')
CORS(app)  # Enable CORS for all routes

# Simple password hashing
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Check admin password from .env
ADMIN_HASHED_PASSWORD = hash_password(os.getenv('ADMIN_PASSWORD', 'admin123'))

# HTML template for admin interface
ADMIN_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Admin - Teach Ella About Your Furniture</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #111;
            color: #f5f5f5;
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 900px;
            margin: 0 auto;
            display: flex;
            flex-direction: column;
            height: 95vh;
        }
        .header {
            text-align: center;
            padding: 20px 0;
            border-bottom: 1px solid #444;
            margin-bottom: 20px;
        }
        .header h1 {
            color: #8B7355;
            margin-bottom: 10px;
        }
        .chat-container {
            flex: 1;
            overflow-y: auto;
            background: #1a1a1a;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            border: 1px solid #444;
        }
        .message {
            margin-bottom: 15px;
            padding: 12px 16px;
            border-radius: 10px;
            max-width: 80%;
            word-wrap: break-word;
        }
        .bot-message {
            background: #333;
            color: #f5f5f5;
            border: 1px solid #444;
            margin-right: auto;
        }
        .admin-message {
            background: #8B7355;
            color: white;
            border: 1px solid #7a6345;
            margin-left: auto;
        }
        .input-container {
            display: flex;
            gap: 10px;
        }
        input[type="text"] {
            flex: 1;
            padding: 12px 16px;
            background: #1a1a1a;
            color: #f5f5f5;
            border: 1px solid #444;
            border-radius: 8px;
            font-size: 16px;
        }
        button {
            padding: 12px 24px;
            background: #8B7355;
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
            font-size: 16px;
        }
        button:hover {
            background: #7a6345;
        }
        .progress {
            margin-top: 10px;
            color: #ccc;
            font-size: 14px;
        }
        .login-container {
            max-width: 400px;
            margin: 100px auto;
            text-align: center;
        }
        .login-container input {
            width: 100%;
            margin: 10px 0;
        }
        .error {
            color: #ff6b6b;
            margin: 10px 0;
        }
    </style>
</head>
<body>
    <div class="container" id="app">
        {% if not logged_in %}
        <div class="login-container">
            <h1>Admin Login</h1>
            <p>Teach Ella about your furniture offerings</p>
            <input type="password" id="password" placeholder="Enter admin password">
            <button onclick="login()">Login</button>
            <div id="login-error" class="error"></div>
        </div>
        {% else %}
        <div class="header">
            <h1>🛋️ Teach Ella About Your Furniture</h1>
            <p>I'll ask questions about what your company offers</p>
            <div class="progress" id="progress">Starting interview...</div>
        </div>
        
        <div class="chat-container" id="chat">
            <!-- Messages will appear here -->
        </div>
        
        <div class="input-container">
            <input type="text" id="message-input" placeholder="Type your answer..." onkeypress="handleKeyPress(event)">
            <button onclick="sendMessage()">Send</button>
        </div>
        {% endif %}
    </div>

    <script>
        {% if logged_in %}
        let currentSessionId = null;
        
        function addMessage(text, isAdmin = false) {
            const chat = document.getElementById('chat');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${isAdmin ? 'admin-message' : 'bot-message'}`;
            messageDiv.textContent = text;
            chat.appendChild(messageDiv);
            chat.scrollTop = chat.scrollHeight;
        }
        
        function updateProgress(text) {
            document.getElementById('progress').textContent = text;
        }
        
        function sendMessage() {
            const input = document.getElementById('message-input');
            const message = input.value.trim();
            
            if (!message) return;
            
            // Add admin message to chat
            addMessage(message, true);
            input.value = '';
            
            // Send to backend
            fetch('/admin/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    session_id: currentSessionId
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    addMessage(data.reply);
                    updateProgress(data.progress || '');
                    
                    if (data.session_id) {
                        currentSessionId = data.session_id;
                    }
                    
                    // Check if interview is complete
                    if (data.complete) {
                        document.getElementById('message-input').disabled = true;
                        document.querySelector('button').disabled = true;
                        document.querySelector('button').textContent = 'Interview Complete';
                    }
                } else {
                    addMessage("Error: " + data.error);
                }
            })
            .catch(error => {
                addMessage("Network error. Please try again.");
                console.error('Error:', error);
            });
        }
        
        function handleKeyPress(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        }
        
        // Start the interview when page loads
        window.onload = function() {
            fetch('/admin/start', {
                method: 'POST'
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    addMessage(data.greeting);
                    currentSessionId = data.session_id;
                    updateProgress(data.progress || 'Starting interview...');
                }
            });
        };
        {% else %}
        function login() {
            const password = document.getElementById('password').value;
            const errorDiv = document.getElementById('login-error');
            
            fetch('/admin/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ password: password })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    window.location.reload();
                } else {
                    errorDiv.textContent = data.error || 'Invalid password';
                }
            });
        }
        
        // Allow Enter key to submit login
        document.getElementById('password').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                login();
            }
        });
        {% endif %}
    </script>
</body>
</html>
'''

# Routes
@app.route('/admin')
def admin_index():
    """Admin main page"""
    logged_in = session.get('admin_logged_in', False)
    return render_template_string(ADMIN_HTML, logged_in=logged_in)

@app.route('/admin/login', methods=['POST'])
def admin_login():
    """Admin login endpoint"""
    data = request.json
    password = data.get('password', '')
    
    if hash_password(password) == ADMIN_HASHED_PASSWORD:
        session['admin_logged_in'] = True
        return jsonify({"success": True})
    else:
        return jsonify({"success": False, "error": "Invalid password"})

@app.route('/admin/start', methods=['POST'])
def start_interview():
    """Start a new interview session"""
    if not session.get('admin_logged_in'):
        return jsonify({"success": False, "error": "Not logged in"})
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Create a new session
        session_data = {
            "step": "welcome",
            "learned_data": {},
            "current_room": None,
            "current_furniture": None
        }
        
        cursor.execute(
            "INSERT INTO admin_sessions (session_data) VALUES (%s) RETURNING id",
            (json.dumps(session_data),)
        )
        session_id = cursor.fetchone()[0]
        conn.commit()
        
        greeting = """🛋️ Hello! I'm Ella, your furniture teaching assistant.

I'll help you teach me about all the furniture your company offers. 
Let's start with the basics:

What rooms do you furnish? (e.g., Living Room, Bedroom, Dining Room, Office)

Please list them separated by commas."""
        
        return jsonify({
            "success": True,
            "greeting": greeting,
            "session_id": session_id,
            "progress": "Step 1: Teaching me about rooms"
        })
        
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "error": str(e)})
    finally:
        cursor.close()
        conn.close()

@app.route('/admin/chat', methods=['POST'])
def admin_chat():
    """Process admin's teaching responses"""
    if not session.get('admin_logged_in'):
        return jsonify({"success": False, "error": "Not logged in"})
    
    data = request.json
    user_message = data.get('message', '').strip()
    session_id = data.get('session_id')
    
    if not user_message:
        return jsonify({"success": False, "error": "Empty message"})
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get current session
        cursor.execute("SELECT session_data FROM admin_sessions WHERE id = %s", (session_id,))
        result = cursor.fetchone()
        
        if not result:
            return jsonify({"success": False, "error": "Session not found"})
        
        session_data = result[0]
        current_step = session_data.get('step', 'welcome')
        
        # Process based on current step
        response = ""
        next_step = current_step
        
        if current_step == "welcome":
            # Admin listed rooms
            rooms = [room.strip() for room in user_message.split(',')]
            rooms = [room for room in rooms if room]
            
            if not rooms:
                response = "Please provide at least one room. Example: Living Room, Bedroom, Dining Room"
            else:
                # Save rooms to database
                for room in rooms:
                    cursor.execute(
                        "INSERT INTO rooms (name) VALUES (%s) ON CONFLICT (name) DO NOTHING",
                        (room,)
                    )
                
                session_data['learned_data']['rooms'] = rooms
                session_data['step'] = 'room_selection'
                next_step = 'room_selection'
                
                response = f"""Great! I've noted that you furnish: {', '.join(rooms)}

Now let's explore each room. Which room should we start with?

Please type the room name: {', '.join(rooms)}"""
        
        elif current_step == "room_selection":
            # Admin selected a room to explore
            selected_room = user_message.strip()
            
            # Check if it's a valid room
            cursor.execute("SELECT id FROM rooms WHERE LOWER(name) = LOWER(%s)", (selected_room,))
            room_result = cursor.fetchone()
            
            if not room_result:
                response = f"I don't see '{selected_room}' in your room list. Please choose from: {', '.join(session_data['learned_data'].get('rooms', []))}"
            else:
                room_id = room_result[0]
                session_data['current_room'] = selected_room
                session_data['current_room_id'] = room_id
                session_data['step'] = 'furniture_types'
                next_step = 'furniture_types'
                
                response = f"""Perfect! Let's explore **{selected_room}**.

What types of furniture do you offer for the {selected_room}?
(e.g., for Living Room: Sofa, TV Unit, Center Table, Bookshelf)

Please list furniture types separated by commas:"""
        
        elif current_step == "furniture_types":
            # Admin listed furniture types for current room
            furniture_types = [ft.strip() for ft in user_message.split(',')]
            furniture_types = [ft for ft in furniture_types if ft]
            
            if not furniture_types:
                response = "Please provide at least one furniture type."
            else:
                room_id = session_data.get('current_room_id')
                room_name = session_data.get('current_room')
                
                # Save furniture types to database
                for furniture in furniture_types:
                    cursor.execute(
                        """INSERT INTO furniture_types (room_id, name) 
                           VALUES (%s, %s) 
                           ON CONFLICT (room_id, name) DO NOTHING
                           RETURNING id""",
                        (room_id, furniture)
                    )
                
                # Store in session
                if 'furniture_by_room' not in session_data['learned_data']:
                    session_data['learned_data']['furniture_by_room'] = {}
                session_data['learned_data']['furniture_by_room'][room_name] = furniture_types
                
                session_data['step'] = 'furniture_selection'
                next_step = 'furniture_selection'
                
                response = f"""Excellent! For {room_name}, you offer: {', '.join(furniture_types)}

Now let's detail each furniture type. Which one should we start with?

Type the furniture name: {', '.join(furniture_types)}"""
        
        elif current_step == "furniture_selection":
            # Admin selected a furniture type to detail
            selected_furniture = user_message.strip()
            room_name = session_data.get('current_room')
            furniture_list = session_data['learned_data']['furniture_by_room'].get(room_name, [])
            
            if selected_furniture not in furniture_list:
                response = f"I don't see '{selected_furniture}' in your list for {room_name}. Please choose from: {', '.join(furniture_list)}"
            else:
                session_data['current_furniture'] = selected_furniture
                session_data['step'] = 'furniture_details'
                next_step = 'furniture_details'
                
                response = f"""Let's detail **{selected_furniture}** for {room_name}.

Please describe this furniture item. Include:
1. Available sizes/variants (e.g., 2-seater, 3-seater, king size, queen size)
2. Material options (e.g., fabric, leather, wood types)
3. Color options
4. Any special features or add-ons
5. Price range
6. Delivery time

Example: "3-seater fabric sofas available in 5 colors (grey, blue, beige, maroon, black) with optional storage. Price: ₹25,000-45,000. Delivery: 3-4 weeks."

Please describe your {selected_furniture}:"""
        
        elif current_step == "furniture_details":
            # Admin provided detailed furniture description
            room_name = session_data.get('current_room')
            furniture_name = session_data.get('current_furniture')
            
            # Get furniture_type_id
            cursor.execute("""
                SELECT ft.id 
                FROM furniture_types ft 
                JOIN rooms r ON ft.room_id = r.id 
                WHERE r.name = %s AND ft.name = %s
            """, (room_name, furniture_name))
            furniture_type_result = cursor.fetchone()
            
            if furniture_type_result:
                furniture_type_id = furniture_type_result[0]
                
                # For now, store the raw description
                # In a more advanced version, you'd parse this into structured data
                config_data = {
                    "description": user_message,
                    "room": room_name,
                    "furniture_type": furniture_name,
                    "timestamp": datetime.now().isoformat()
                }
                
                cursor.execute("""
                    INSERT INTO product_configs 
                    (furniture_type_id, config_name, attributes, options, price_range, delivery_time)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    furniture_type_id,
                    f"{room_name} - {furniture_name}",
                    json.dumps({"raw_description": user_message}),
                    json.dumps({}),
                    "To be extracted",
                    "To be extracted"
                ))
                
                response = f"""✅ Great! I've saved details for {furniture_name} in {room_name}.

What would you like to do next?
1. Detail another furniture type in {room_name}
2. Move to another room
3. Finish interview

Type your choice (1, 2, or 3):"""
                
                session_data['step'] = 'next_action'
                next_step = 'next_action'
        
        elif current_step == "next_action":
            # Admin chooses next action
            choice = user_message.strip()
            
            if choice == "1":
                # Detail another furniture in same room
                room_name = session_data.get('current_room')
                furniture_list = session_data['learned_data']['furniture_by_room'].get(room_name, [])
                
                response = f"""Which other furniture in {room_name} would you like to detail?

Available: {', '.join(furniture_list)}

Type the furniture name:"""
                session_data['step'] = 'furniture_selection'
                next_step = 'furniture_selection'
                session_data['current_furniture'] = None
            
            elif choice == "2":
                # Move to another room
                rooms = session_data['learned_data'].get('rooms', [])
                current_room = session_data.get('current_room')
                remaining_rooms = [r for r in rooms if r != current_room]
                
                if remaining_rooms:
                    response = f"""Which room would you like to explore next?

Available rooms: {', '.join(remaining_rooms)}

Type the room name:"""
                    session_data['step'] = 'room_selection'
                    next_step = 'room_selection'
                    session_data['current_room'] = None
                    session_data['current_furniture'] = None
                else:
                    response = "You've covered all rooms! Would you like to finish? (yes/no)"
                    session_data['step'] = 'finish_confirmation'
                    next_step = 'finish_confirmation'
            
            elif choice == "3":
                response = "Are you sure you want to finish the interview? (yes/no)"
                session_data['step'] = 'finish_confirmation'
                next_step = 'finish_confirmation'
            
            else:
                response = "Please choose 1, 2, or 3."
        
        elif current_step == "finish_confirmation":
            if user_message.lower() in ['yes', 'y', 'finish']:
                # Mark session as complete
                cursor.execute(
                    "UPDATE admin_sessions SET is_completed = TRUE WHERE id = %s",
                    (session_id,)
                )
                
                # Generate summary
                summary = generate_interview_summary(session_data['learned_data'])
                
                response = f"""🎉 Interview Complete!

Here's what I learned about your company:
{summary}

Your furniture knowledge has been saved to the database.
Customers can now use this information through the customer chat.

You can:
1. Start a new interview session to add more details
2. Access the customer chat to test the system
3. View the database to see stored information

Thank you for teaching me!"""
                
                conn.commit()
                return jsonify({
                    "success": True,
                    "reply": response,
                    "complete": True,
                    "progress": "Interview complete - Knowledge saved!"
                })
            else:
                response = "Let's continue. What would you like to do next?\n1. Detail another furniture\n2. Move to another room\n3. Finish interview"
                session_data['step'] = 'next_action'
                next_step = 'next_action'
        
        # Update session data
        session_data['step'] = next_step
        cursor.execute(
            "UPDATE admin_sessions SET session_data = %s WHERE id = %s",
            (json.dumps(session_data), session_id)
        )
        
        conn.commit()
        
        progress_text = get_progress_text(next_step, session_data)
        
        return jsonify({
            "success": True,
            "reply": response,
            "session_id": session_id,
            "progress": progress_text,
            "complete": False
        })
        
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "error": str(e)})
    finally:
        cursor.close()
        conn.close()

def get_progress_text(step, session_data):
    """Generate progress text based on current step"""
    if step == "welcome":
        return "Step 1: Teaching me about rooms"
    elif step == "room_selection":
        return f"Step 2: Selecting a room to explore"
    elif step == "furniture_types":
        room = session_data.get('current_room', 'a room')
        return f"Step 3: Listing furniture for {room}"
    elif step == "furniture_selection":
        room = session_data.get('current_room', 'current room')
        return f"Step 4: Selecting furniture in {room} to detail"
    elif step == "furniture_details":
        furniture = session_data.get('current_furniture', 'selected furniture')
        return f"Step 5: Detailing {furniture}"
    elif step == "next_action":
        return "Step 6: Choosing next action"
    elif step == "finish_confirmation":
        return "Final step: Completing interview"
    return "Teaching in progress..."

def generate_interview_summary(learned_data):
    """Generate a summary of what was learned"""
    summary = []
    
    if 'rooms' in learned_data:
        summary.append(f"• Rooms furnished: {', '.join(learned_data['rooms'])}")
    
    if 'furniture_by_room' in learned_data:
        for room, furniture_list in learned_data['furniture_by_room'].items():
            summary.append(f"• {room}: {', '.join(furniture_list)}")
    
    if not summary:
        summary.append("• Basic room information collected")
    
    return '\n'.join(summary)

@app.route('/admin/logout')
def admin_logout():
    """Admin logout"""
    session.pop('admin_logged_in', None)
    return jsonify({"success": True})

if __name__ == '__main__':
    # Initialize database if not already
    from database import init_database
    init_database()
    
    print("🚀 Starting Admin Interview System...")
    print("📝 Admin interface: http://localhost:5001/admin")
    print("🔒 Password from .env file")
    print("=" * 50)
    
    app.run(debug=True, port=5001)