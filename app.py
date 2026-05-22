import os
import json
from flask import Flask, request, redirect, url_for, session, render_template, flash
from flask_socketio import SocketIO, emit, join_room
from game_logic import SkillGameEngine

app = Flask(__name__)
app.config['SECRET_KEY'] = 'enterprise_multi_deck_framework_key_2026'
socketio = SocketIO(app, cors_allowed_origins="*")

game_engine = SkillGameEngine()

# 💾 PERSISTENCE MANAGEMENT LAYER
SETTINGS_FILE = "saved_settings.json"

def load_persistent_settings():
    """Reads saved configuration states directly from the disk memory matrix."""
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {"custom_emotions": {}, "custom_video_reactions": {}, "last_match_starter": None}
    return {"custom_emotions": {}, "custom_video_reactions": {}, "last_match_starter": None}

# Seed engine cache metrics upon deployment script parsing
persisted = load_persistent_settings()
game_engine.custom_emotions = persisted.get("custom_emotions", {})
game_engine.custom_video_reactions = persisted.get("custom_video_reactions", {})
# Inject the persisted starting player name back into game logic instance memory
game_engine.last_match_starter = persisted.get("last_match_starter", None)

def save_persistent_settings(data):
    """Safely commits the running settings matrix back into the permanent JSON store."""
    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"Persistence error writing to disk: {e}")

# Seed engine cache arrays immediately upon framework deployment
persisted = load_persistent_settings()
game_engine.custom_emotions = persisted.get("custom_emotions", {})
# Ensure runtime tracker maps to the instance
game_engine.custom_video_reactions = persisted.get("custom_video_reactions", {})


# 🔒 AUTHORIZED USER CONFIGURATION DATABASE MATRIX
VALID_ACCOUNTS = {
    "admin": {"password": "password", "role": "admin"},
    "pradeep": {"password": "password", "role": "player"},
    "krish": {"password": "password", "role": "player"},
    "siri": {"password": "password", "role": "player"},
    "karthik": {"password": "password", "role": "player"}
}

@app.route('/')
def index():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('game.html', username=session['username'], role=session.get('role', 'player'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username_raw = request.form.get('username', '').strip()
        username_key = username_raw.lower()
        password = request.form.get('password', '')

        if not username_raw or not password:
            flash("Username and password credentials cannot be left blank.")
            return render_template('login.html')

        if username_key in VALID_ACCOUNTS:
            account_data = VALID_ACCOUNTS[username_key]
            if password == account_data["password"]:
                session['username'] = username_raw
                session['role'] = account_data["role"]
                return redirect(url_for('index'))
            else:
                flash("Access Denied: Invalid password credentials for this profile identifier.")
                return render_template('login.html')
        else:
            flash(f"Access Denied: Account identifier '{username_raw}' is not synchronized.")
            return render_template('login.html')
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


def broadcast_sync_state():
    """Iterates through active targets to push unique layout perspective updates."""
    for player in game_engine.players:
        current_p_state = game_engine.render_state_for_player(player)
        current_p_state["custom_video_reactions"] = game_engine.custom_video_reactions
        emit('state_update', current_p_state, to=player)

@socketio.on('join_game')
def on_join(data):
    username = data.get('username')
    if username:
        join_room(username)
        game_engine.add_player(username)
        broadcast_sync_state()

@socketio.on('shuffle_deck')
def on_shuffle(data):
    username = data.get('username')
    game_engine.shuffle_deck(triggered_by=username)
    broadcast_sync_state()

@socketio.on('admin_start_game')
def on_start():
    success, msg = game_engine.start_game()
    if success:
        # Sync the chosen round-robin game starter into persistence file structure
        store = load_persistent_settings()
        store["last_match_starter"] = game_engine.last_match_starter
        save_persistent_settings(store)
        
        broadcast_sync_state()
    else:
        emit('error', {'message': msg})

@socketio.on('discard_cards')
def on_discard_cards(data):
    username = data.get('username')
    indices = data.get('indices', [])
    picked_discard = data.get('picked_discard')
    success, msg = game_engine.execute_turn_transaction(username, indices, picked_discard)
    if success:
        broadcast_sync_state()
    else:
        emit('error', {'message': msg})

@socketio.on('declare_show')
def on_declare_show(data):
    username = data.get('username')
    hand_dropped = data.get('final_hand_dropped', [])
    success, msg = game_engine.declare_show(username, hand_dropped)
    if success:
        broadcast_sync_state()
    else:
        emit('error', {'message': msg})

@socketio.on('admin_force_end')
def on_force_end():
    game_engine.force_end()
    broadcast_sync_state()

@socketio.on('update_profile_photo')
def on_update_photo(data):
    username = data.get('username')
    photo_url = data.get('photo_url')
    if username and photo_url:
        game_engine.user_photos[username] = photo_url
        broadcast_sync_state()

@socketio.on('admin_update_prefs')
def on_admin_update_prefs(data):
    if "custom_emotions" in data:
        # Pull latest payload keys
        for user, emoji in data["custom_emotions"].items():
            game_engine.custom_emotions[user] = emoji
        
        # Sync immediately back to permanent file database
        store = load_persistent_settings()
        store["custom_emotions"] = game_engine.custom_emotions
        save_persistent_settings(store)
    else:
        game_engine.preferences.update(data)
    broadcast_sync_state()

@socketio.on('broadcast_youtube')
def on_broadcast_youtube(data):
    video_url = data.get('url', '').strip()
    if video_url:
        emit('play_video_broadcast', {'url': video_url}, broadcast=True)

@socketio.on('save_custom_video_reaction')
def on_save_custom_reaction(data):
    username = data.get('username')
    label = data.get('label', '').strip()
    video_url = data.get('url', '').strip()
    
    if username and label and video_url:
        if username not in game_engine.custom_video_reactions:
            game_engine.custom_video_reactions[username] = {}
        
        # Save custom macro button configuration links link reference
        game_engine.custom_video_reactions[username][label] = video_url
        game_engine.log_event(f"User {username} created custom reaction button: [{label}]")
        
        # Write directly to disk
        store = load_persistent_settings()
        store["custom_video_reactions"] = game_engine.custom_video_reactions
        save_persistent_settings(store)
        
        broadcast_sync_state()

@socketio.on('admin_manage_user')
def on_admin_manage_user(data):
    action = data.get('action')
    target = data.get('target_user')
    
    if action == 'create' and target:
        game_engine.add_player(target)
        game_engine.log_event(f"Administrative account action applied on {target}: [{action}]")
    elif action == 'promote' and target:
        game_engine.log_event(f"Player {target} has been promoted to Table Administrator privileges.")
        emit('role_promoted', {'username': target}, broadcast=True)
        
    broadcast_sync_state()

@socketio.on('admin_clear_history')
def on_clear_history():
    game_engine.history = []
    game_engine.log_event("History logs cleared.")
    broadcast_sync_state()

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
