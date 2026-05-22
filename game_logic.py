import random
import math

class SkillGameEngine:

    def __init__(self):
        self.status = "LOBBY"  # LOBBY, ACTIVE, ENDED
        self.players = []
        self.scores = {}
        self.wins = {}
        self.losses = {}
        self.deck = []
        self.discard_pile = []
        self.hands = {}
        self.history = []
        self.acting_joker = None
        self.current_turn_index = 0
        self.drawn_this_turn = False
        
        # New persistent round-robin tracking metrics
        self.last_match_starter = None
        
        self.preferences = {
            "bg_color": "bg-stone-100",
            "panel_color": "bg-white",
            "text_color": "text-slate-800",
            "accent_color": "border-emerald-600"
        }
        self.user_photos = {}
        self.custom_emotions = {}
        self.last_turn_dropped_cards = []
        self.last_show_declaration = None

    def add_player(self, username):
        if username not in self.players:
            self.players.append(username)
            if username not in self.scores:
                self.scores[username] = 0
            if username not in self.wins:
                self.wins[username] = 0
            if username not in self.losses:
                self.losses[username] = 0
            self.log_event(f"Player {username} joined the table matrix.")

    def shuffle_deck(self, triggered_by=None):
        """Builds and randomizes standard 52-card decks with natural jokers included.
        Dynamically adjusts deck counts to ensure a resilient stock pile."""
        suits = ['H', 'D', 'C', 'S']  # Hearts, Diamonds, Clubs, Spades
        values = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        
        num_players = max(len(self.players), 1)
        required_cards = (num_players * 5) + 2 + (num_players * 8)
        decks_needed = max(2, math.ceil(required_cards / 54))
        
        new_deck = []
        for _ in range(decks_needed):
            for suit in suits:
                for value in values:
                    new_deck.append({"suit": suit, "value": value, "is_joker": False})
            new_deck.append({"suit": "JOKER", "value": "JK", "is_joker": True})
            new_deck.append({"suit": "JOKER", "value": "JK", "is_joker": True})
            
        random.shuffle(new_deck)
        self.deck = new_deck
        self.status = "LOBBY"
        
        operator = triggered_by if triggered_by else "System"
        self.log_event(f"Decks successfully shuffled by {operator} using {decks_needed}-deck shoe format. Ready to deal.")

    def start_game(self):
        if len(self.players) < 2:
            return False, "Not enough players in the lobby matrix."
            
        # Clear out transient state caches from previous match rounds
        self.deck = []
        self.discard_pile = []
        self.hands = {}
        self.last_turn_dropped_cards = []
        self.last_show_declaration = None
        self.drawn_this_turn = False

        # --- ROUND-ROBIN TURN INITIALIZATION ROTATOR ---
        if self.last_match_starter is None or self.last_match_starter not in self.players:
            # First match or starter left? Default to the first player in the active index list
            starting_player = self.players[0]
        else:
            # Find index of previous match starter and shift it to the next index slot (+1)
            prev_index = self.players.index(self.last_match_starter)
            next_index = (prev_index + 1) % len(self.players)  # Wraps around smoothly to 0 using modulo
            starting_player = self.players[next_index]

        # Record this user as the current match's starter to preserve history context for the next restart
        self.last_match_starter = starting_player
        self.current_turn_index = self.players.index(starting_player)
        
        # --- RESUME SHUFFLE AND CARD DEALING ROUTINES ---
        self.shuffle_deck()
        
        # Select acting joker card value safely from randomized deck
        self.acting_joker = self.deck.pop(0)
        
        # Distribute 5 cards to each registered room player profile
        for p in self.players:
            self.hands[p] = [self.deck.pop(0) for _ in range(5)]
            
        # Seat the initial discard pile card element down onto layout stack
        self.discard_pile.append(self.deck.pop(0))
        
        self.status = "ACTIVE"
        self.log_event(f"Match started! Round-Robin selection nominated **{starting_player}** to go first.")
        return True, "Match successfully initialized."

    def get_current_turn_player(self):
        if not self.players or self.status != "ACTIVE":
            return None
        return self.players[self.current_turn_index % len(self.players)]

    def execute_turn_transaction(self, username, indices, picked_discard_card_raw=None):
        """Executes an atomic pre-play action: validates drop combinations, 
        picks up a replacement card from either the discard pile choice or the stock deck, 
        and updates hand states instantly."""
        if self.status != "ACTIVE" or self.get_current_turn_player() != username:
            return False, "Not your current execution context turn window."
        
        player_hand = self.hands.get(username, [])
        
        # 1. Gather dropped cards in normal ascending index order so they preserve sequence alignment
        natural_indices = sorted(list(set(indices)))
        dropped_cards = []
        for idx in natural_indices:
            if 0 <= idx < len(player_hand):
                dropped_cards.append(player_hand[idx])

        if not dropped_cards:
            return False, "You must select at least one card from your hand to drop."

        is_valid, error_msg = self._validate_discard_combination(dropped_cards)
        if not is_valid:
            return False, error_msg

        picked_card = None
        
        if picked_discard_card_raw and self.discard_pile:
            top_discard = self.discard_pile[-1]
            if (top_discard.get('value') == picked_discard_card_raw.get('value') and 
                top_discard.get('suit') == picked_discard_card_raw.get('suit')):
                picked_card = self.discard_pile.pop()
                self.log_event(f"{username} picked from discard pile.", {"source": "discard", "picked_card": picked_card})
            else:
                return False, "The highlighted discard card is no longer sitting at the top of the pile stack."
        
        if not picked_card:
            if self.deck:
                picked_card = self.deck.pop()
                self.log_event(f"{username} drew a card automatically from the stock deck pile.", {"source": "deck"})
            else:
                return False, "The undealt stock deck stack has been fully depleted."

        # 2. Pop elements from the hand using reverse descending indices to avoid shifting boundaries
        sorted_indices = sorted(list(set(indices)), reverse=True)
        for idx in sorted_indices:
            if 0 <= idx < len(player_hand):
                player_hand.pop(idx)
                
        if picked_card:
            player_hand.append(picked_card)
            
        self.last_turn_dropped_cards = dropped_cards
        for c in dropped_cards:
            self.discard_pile.append(c)
            
        card_descriptions = ", ".join([f"{c['value']}{c['suit']}" for c in dropped_cards])
        self.log_event(f"Player {username} dropped cards [{card_descriptions}] and advanced rotation stack.")
        
        self.current_turn_index += 1
        self.drawn_this_turn = False 
        return True, "Turn completed successfully."

    def _is_joker_type(self, card):
        """Helper to evaluate if an active object acts as a natural or acting wildcard joker."""
        if not card:
            return False
        if card.get('is_joker') or card.get('suit') == 'JOKER':
            return True
        if self.acting_joker and card.get('value') == self.acting_joker.get('value'):
            return True
        return False

    def _validate_discard_combination(self, cards):
        """Validates if dropped cards represent a Single, a valid Set, or a valid Sequence."""
        count = len(cards)
        
        if count == 1:
            return True, "Valid Single card drop."
            
        jokers = [c for c in cards if self._is_joker_type(c)]
        naturals = [c for c in cards if not self._is_joker_type(c)]

        if len(naturals) == 0:
            return True, "Valid combination (all Jokers)."

        # Strict Set Validation: natural cards must share identical face values
        target_value = naturals[0].get('value')
        is_valid_set = all(c.get('value') == target_value for c in naturals)
        
        if is_valid_set:
            return True, "Valid Set combination."

        # Strict Sequence Validation: requires minimum 3 cards, matching suits, consecutive order
        if count >= 3:
            target_suit = naturals[0].get('suit')
            if not all(c.get('suit') == target_suit for c in naturals):
                return False, "Invalid combination. Multi-card drops must match values for sets, or suits for sequences."

            rank_map = {'2':2, '3':3, '4':4, '5':5, '6':6, '7':7, '8':8, '9':9, '10':10, 'J':11, 'Q':12, 'K':13, 'A':14}
            natural_ranks = sorted([rank_map.get(c.get('value'), 0) for c in naturals])
            
            if len(natural_ranks) != len(set(natural_ranks)):
                return False, "Invalid Sequence. Natural cards cannot contain duplicates."

            total_span = natural_ranks[-1] - natural_ranks[0] + 1
            needed_jokers = total_span - len(natural_ranks)

            if len(jokers) >= needed_jokers:
                return True, "Valid Sequence combination."
            else:
                return False, "Invalid sequence."

        return False, "Invalid selection. Selection does not match a valid Single, Set, or Sequence."

    def declare_show(self, username, final_hand_dropped):
        """Concludes active matches by evaluating points and tracking score distributions."""
        if self.status != "ACTIVE":
            return False, "No active match operational framework running to terminate."

        # User modified code; Preserve it.
        player_scores_of_match = {}
        challenger = username

        for p in self.players:
            hand = self.hands.get(p, [])

            score_acc = 0

            for card in hand:
                val = card.get('value')
                if card.get('is_joker') or (self.acting_joker and val == self.acting_joker.get('value')):
                    score_acc += 0
                elif val in ['J', 'Q', 'K', 'A']:
                    score_acc += 10
                else:
                    try:
                        score_acc += int(val)
                    except ValueError:
                        score_acc += 5
            # self.scores[p] = self.scores.get(p, 0) + score_acc
            player_scores_of_match[p] = score_acc
            # self.log_event(f"PLAYER: {p} SCORE: {score_acc}")
            
            

        # winner = min(self.players, key=lambda p: self.scores.get(p, 0))
        challenger_score = player_scores_of_match[challenger]
        # self.log_event(f"Evaluating Challenge by {username} for score {challenger_score}")

        score_beater_count = 0
        for p in self.players:
            if p != challenger:
                # self.log_event(f"challenger is {challenger} and player is {p}")
                if player_scores_of_match[p]<=challenger_score:
                    score_beater_count += 1
                    #// score is 0 for all beaters
                else:
                    #// score counts for all non-beaters
                    self.scores[p] += player_scores_of_match[p]
                

        self.log_event(f"Player{challenger}'s score was beaten by {score_beater_count} players")
        self.log_event(f"Player Scores: {player_scores_of_match}")

        if score_beater_count == 0:
            self.wins[p] = self.wins.get(p, 0) + 1
            self.scores[challenger] -= (player_scores_of_match[challenger] + 25)
            
        else:
            self.losses[p] = self.losses.get(p, 0) + 1
            self.scores[challenger] += 50 + 25 * (score_beater_count - 1)

        self.status = "ENDED"
        self.last_show_declaration = {
            "username": username,
            "final_hand_dropped": final_hand_dropped
        }
        
        return True, "Show complete layout resolved."

    def log_event(self, message, metadata=None):
        from datetime import datetime
        log_entry = {
            "message": message,
            "timestamp": datetime.now().strftime("%I:%M:%S %p"),
            "metadata": metadata or {}
        }
        self.history.append(log_entry)
        if len(self.history) > 100:
            self.history.pop(0)

    def force_end(self):
        self.status = "ENDED"
        self.log_event("Match cycle forced to terminate early by Admin module routine.")

    def render_state_for_player(self, username):
        return {
            "status": self.status,
            "players": self.players,
            "scores": self.scores,
            "wins": self.wins,
            "losses": self.losses,
            "discard_pile": self.discard_pile,
            "your_hand": self.hands.get(username, []),
            "history": self.history,
            "deck_count": len(self.deck),
            "acting_joker": self.acting_joker,
            "current_turn": self.get_current_turn_player(),
            "drawn_this_turn": self.drawn_this_turn if self.get_current_turn_player() == username else False,
            "preferences": self.preferences,
            "user_photos": self.user_photos,
            "custom_emotions": self.custom_emotions,
            "last_turn_dropped_cards": self.last_turn_dropped_cards,
            "last_show_declaration": self.last_show_declaration
        }
