# SkillGameEngine Framework (v2026.2.1)
An enterprise-grade, real-time multi-deck card game engine designed for strategic matching, sequential combinations, and social multiplayer synchronization over high-concurrency event loops.

---

## 🎮 Core Game Mechanics & System Requirements

### 1. Match Allocation & Structural Dimensions
* **Initial Hand Layout:** Every active player is dealt exactly **5 cards** upon round initialization.
* **Turn Lifecycle Sustainability:** The undealt stock deck size must dynamically adapt to scale across player counts to ensure that remaining spare cards can sustain **at least 8 full turn cycles** for all players without pile depletion.

### 2. Strategic Pre-Play Turn Model (Atomic Transactions)
The game utilizes a unified, simultaneous transaction model rather than individual sequential draw-and-discard phases.
* **Dual-Selection Configuration:** On their turn, a player selects card(s) to drop from their hand **and** chooses which card to pick up *before* executing the action.
* **Pickup Priority Rules:**
    1.  If the player explicitly highlights and selects the top card from the previous turn's **Discard Pile**, that card is extracted.
    2.  If no selection is made from the discard pile, the system's fallback strategy automatically deals the top card from the hidden **Undealt Stock Deck**.
* **The Execution Cycle ("Drop" Button):** Pressing the unified button triggers an atomic network transaction that simultaneously validates the dropped combinations, purges them from the player's hand, adds the picked card, updates the discard tracking metrics, and shifts the turn pointer forward.

### 3. Discard & Drop Validation Criteria
Every multi-card transaction must match one of three distinct mathematical structures to bypass engine rule constraints:
* **Sequence Rules:** Requires **3 or more cards** arranged in continuous sequential numeric value belonging to the *identical suit context* (e.g., 4♥-5♥-6♥). 
    * *Wildcards:* Can include **1 or more real printed Jokers or Acting Jokers** to fulfill the gaps.
* **Set Rules:** Requires **2 or more cards** sharing the *identical face numerical or letter value* regardless of suit (e.g., 7♠-7♦). 
    * *Wildcards:* Can include natural or acting jokers as wildcard substitutes.
* **Single Rules:** Exactly **1 card** of the user's choosing without restriction.

### 4. Dynamic Wildcard Engine (Acting Jokers)
* **Natural Wildcards:** Printed Jokers (`is_joker: True`) function universally as wildcards.
* **Acting Wildcards:** At game initialization, one card asset is flipped face-up from the deck to serve as the **Acting Joker** for that round. All cards matching its face value automatically function as jokers across all sequence and set check calculations.
* *Fallback Rule:* If a natural printed joker is selected as the round's acting joker, the system defaults the acting joker value to `"A"` (Aces).

### 5. Show Declarations & Round Evaluation Scoring
A player can call a "Show" during their turn matrix window to conclude the current match cycle and calculate scores.
* **The Winner's Immunity Rule:** When a player wins the round by declaring a valid show, **their current hand count adds exactly 0 points to their score balance.**
* **Opponent Penalty Calculations:** Remaining players accumulate penalty points based on unformed combinations left in their hand layout:
    * *Aces / Face Cards (J, Q, K, 10):* 10 points each.
    * *Numeric Cards (2-9):* Face value points.
    * *Unmapped elements:* Default to 5 points.
    * *Jokers (Natural or Acting):* 0 points.
* **Victory Metrics:** The player with the overall lowest accumulated point threshold across hands wins the tracking tournament workspace.

---

## 🎨 Interface & Experience Layout Requirements

### 1. Dual-Purpose Discard Tracking Component
* The system completely removes individual standalone "Cards Dropped In Previous Turn" modules.
* The unified **"Discard Pile Top"** visual component is extended into a horizontal preview rack that displays **every single card dropped during the immediate preceding turn cycle**. If no multi-card drop exists, it falls back to showing the absolute top element of the discard stack.

### 2. Multi-Tenant Role Privileges
* **Table Administrator (Admin):** The first user handle connecting to a newly spun-up game session workspace receives admin rights. Admins can configure theme styles, forcefully initialize or terminate matches early, purge history buffers, promote users, or register custom media emotes.
* **Standard Player:** Subsequent connecting accounts join as standard entities with standard deck actions.

### 3. Integrated Presentation Themes (Lighter Colored Options)
The layout engine supports an array of high-contrast light presentation canvases to optimize scannability, explicitly rejecting monotonic or dark-only default designs:
* **🍦 Cream Linen (System Default):** Soft stone backgrounds coupled with pure white panels.
* **☁️ Sky Pastel:** Relaxed ambient sky-blue textures.
* **🍇 Soft Lavender:** Gentle light-violet tracking layers.
* **🌱 Mint Crisp:** Vibrant soft-green canvas.
* **🏜️ Warm Desert Clay:** A light-colored, warm amber background combined with high-contrast sharp typography and orange-accented border dividers.
* **🌑 Dark Midnight:** Low-luminance cyber matrix option for low-light situations.

### 4. Social Stream Broadcasting Studio
* **Real-time Reaction Waves:** Players can dispatch quick text statuses or animated emojis that pop up over all screens.
* **YouTube Media Studio Integration:** Admins can save custom interaction tokens linking to active YouTube video streams. When triggered, the engine embeds a live synchronized video/audio overlay player across all connected player interfaces simultaneously.
