"""Coin shop, cosmetics, daily quests and AI-rival names for the Rapid Fire arena (earned coins only, no payments)."""
import random

SHOP = [
    {"id": "streak_freeze", "slot": "powerup", "title": "Streak Freeze", "body": "Protects your streak for one missed day.", "price": 120, "icon": "snowflake", "consumable": True},
    {"id": "frame_gold", "slot": "frame", "title": "Gold Frame", "body": "Shining gold ring around your avatar.", "price": 250, "icon": "circle-outline", "color": "gold"},
    {"id": "frame_neon", "slot": "frame", "title": "Neon Pulse", "body": "Cyan neon ring that pulses in duels.", "price": 400, "icon": "circle-double", "color": "cyan"},
    {"id": "frame_fire", "slot": "frame", "title": "Inferno Frame", "body": "Blazing orange fire ring.", "price": 650, "icon": "fire-circle", "color": "fire"},
    {"id": "frame_diamond", "slot": "frame", "title": "Diamond Crown", "body": "The rarest frame in the arena.", "price": 1200, "icon": "diamond-stone", "color": "diamond"},
    {"id": "entry_rocket", "slot": "entry", "title": "Rocket Launch", "body": "Blast into the duel on a rocket trail.", "price": 300, "icon": "rocket-launch"},
    {"id": "entry_lightning", "slot": "entry", "title": "Thunder Strike", "body": "Arrive with a lightning storm.", "price": 500, "icon": "lightning-bolt"},
    {"id": "entry_supercar", "slot": "entry", "title": "Supercar Drift", "body": "Drift in with speed lines and smoke.", "price": 800, "icon": "car-sports"},
    {"id": "entry_crown", "slot": "entry", "title": "Royal Parade", "body": "A golden crown descends with sparkles.", "price": 1500, "icon": "crown"},
    {"id": "entry_tornado", "slot": "entry", "title": "Cyclone Spin", "body": "Spin in on a roaring tornado.", "price": 600, "icon": "weather-tornado"},
    {"id": "entry_meteor", "slot": "entry", "title": "Meteor Crash", "body": "Smash down like a burning meteor.", "price": 900, "icon": "meteor"},
    {"id": "entry_dragon", "slot": "entry", "title": "Dragon Inferno", "body": "Ride in on dragon fire and embers.", "price": 1800, "icon": "fire"},
    {"id": "entry_phoenix", "slot": "entry", "title": "Phoenix Rise", "body": "Rise from flames on golden wings.", "price": 2000, "icon": "bird"},
    {"id": "entry_galaxy", "slot": "entry", "title": "Galaxy Warp", "body": "Warp in through a swirling galaxy.", "price": 2500, "icon": "orbit"},
    {"id": "entry_blackhole", "slot": "entry", "title": "Black Hole", "body": "Emerge from a black hole. Legendary.", "price": 3000, "icon": "atom-variant"},
    {"id": "theme_inferno", "slot": "theme", "title": "Inferno Arena", "body": "Red-orange battle arena.", "price": 350, "icon": "fire", "colors": ["#3B0A0A", "#070B18"]},
    {"id": "theme_ocean", "slot": "theme", "title": "Deep Ocean", "body": "Calm teal depths.", "price": 350, "icon": "waves", "colors": ["#032B3A", "#070B18"]},
    {"id": "theme_gold", "slot": "theme", "title": "Royal Gold", "body": "Champion’s gold arena.", "price": 900, "icon": "trophy", "colors": ["#3A2A05", "#070B18"]},
]
SHOP_BY_ID = {i["id"]: i for i in SHOP}
# 3D game-style hero avatars: 4 free starters, the rest bought with coins by rarity.
_AV = [
    ("av_topper", "Neon Topper", "common", 0, "a cheerful Indian teen boy student with headphones and a glowing cyan hoodie"),
    ("av_scholar", "Cyber Scholar", "common", 0, "a smart Indian teen girl with round glasses, ponytail and a purple tech jacket"),
    ("av_robo", "Robo Buddy", "common", 0, "a friendly round white-and-cyan robot with big glowing eyes"),
    ("av_panda", "Kung-Fu Panda", "common", 0, "a cute determined panda warrior with a red headband"),
    ("av_photon", "Photon Girl", "rare", 300, "a teen girl superhero made of light, golden visor, glowing yellow energy hair"),
    ("av_atom", "Atom Knight", "rare", 300, "a young knight in sleek blue armour with a glowing atom emblem on the chest"),
    ("av_ninja", "Quantum Ninja", "rare", 400, "a masked ninja with a glowing violet quantum blade aura and neon eyes"),
    ("av_rocket", "Rocket Ranger", "rare", 400, "a young astronaut ranger with an orange space helmet visor up, smiling boldly"),
    ("av_thunder", "Thunder Prince", "epic", 700, "a fierce young prince crackling with blue lightning, silver crown, storm aura"),
    ("av_crystal", "Crystal Mage", "epic", 700, "a mystical girl mage with floating pink crystals and glowing magenta eyes"),
    ("av_samurai", "Code Samurai", "epic", 800, "a cyberpunk samurai with a green digital-code glowing mask and katana on back"),
    ("av_ice", "Ice Titan", "epic", 800, "a powerful ice giant hero with frost armour and glowing icy blue eyes"),
    ("av_phoenix", "Phoenix Warrior", "legendary", 1500, "a heroic warrior girl with blazing phoenix fire wings and golden armour"),
    ("av_dragon", "Dragon Master", "legendary", 1500, "a confident young dragon master with a small red dragon on the shoulder, fiery glow"),
    ("av_galaxy", "Galaxy Queen", "legendary", 2000, "a regal cosmic queen with a starry galaxy cape, nebula hair and a glowing tiara"),
    ("av_einstein", "Professor Nova", "legendary", 2000, "a genius wild-white-haired scientist hero with glowing formula holograms around"),
]
AVATAR_ITEMS = [{"id": i, "slot": "avatar", "title": t, "rarity": r, "price": p, "prompt": pr} for i, t, r, p, pr in _AV]
AVATAR_BY_ID = {a["id"]: a for a in AVATAR_ITEMS}
FREE_AVATARS = [a["id"] for a in AVATAR_ITEMS if not a["price"]]
AVATARS = [a["id"] for a in AVATAR_ITEMS]
BUYABLE = {**SHOP_BY_ID, **{a["id"]: a for a in AVATAR_ITEMS if a["price"]}}


def safe_avatar(a):
    return a if a in AVATAR_BY_ID else FREE_AVATARS[2]

QUESTS = [
    {"id": "q_sprint", "title": "Finish 1 Solo Sprint", "goal": 1, "stat": "sprints", "coins": 30},
    {"id": "q_correct", "title": "Get 25 cards correct", "goal": 25, "stat": "correct", "coins": 40},
    {"id": "q_duel", "title": "Win 1 duel", "goal": 1, "stat": "wins", "coins": 50},
]

_FIRST = ("Aarav Vivaan Aditya Arjun Sai Reyansh Krishna Ishaan Shaurya Atharv Kabir Rudra Ayaan Dhruv Kian Advik Arnav Vihaan Yash Rohan "
          "Ananya Diya Aadhya Saanvi Myra Ira Anika Navya Pari Riya Kiara Sara Aanya Meera Tara Nisha Kavya Siya Avni Ishita "
          "Rahul Karan Nikhil Varun Aman Harsh Dev Parth Om Laksh Neha Pooja Sneha Shreya Tanvi Isha Mahi Zoya Aisha Fatima "
          "Imran Zaid Arham Rehan Faiz Simran Harleen Jaspreet Gurleen Manav Tejas Pranav Shiv Aryan Ritvik Lavanya Pallavi Trisha Ritika Bhavya "
          "Ganesh Murali Karthik Vignesh Lakshmi Divya Keerthi Abhinav Siddharth Anirudh").split()
_LAST = "S. K. M. R. P. A. V. D. G. N.".split()
RIVAL_NAMES = [f"{f} {l}" for f in _FIRST for l in _LAST][:1000]


def rival_profile():
    return {"name": random.choice(RIVAL_NAMES), "avatar": random.choice(AVATARS), "frame": random.choice([None, "frame_gold", "frame_neon"]),
            "entry": random.choice([i["id"] for i in SHOP if i["slot"] == "entry"])}
