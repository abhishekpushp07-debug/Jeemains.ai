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
    {"id": "theme_inferno", "slot": "theme", "title": "Inferno Arena", "body": "Red-orange battle arena.", "price": 350, "icon": "fire", "colors": ["#3B0A0A", "#070B18"]},
    {"id": "theme_ocean", "slot": "theme", "title": "Deep Ocean", "body": "Calm teal depths.", "price": 350, "icon": "waves", "colors": ["#032B3A", "#070B18"]},
    {"id": "theme_gold", "slot": "theme", "title": "Royal Gold", "body": "Champion’s gold arena.", "price": 900, "icon": "trophy", "colors": ["#3A2A05", "#070B18"]},
]
SHOP_BY_ID = {i["id"]: i for i in SHOP}
AVATARS = ["robot-happy", "account-circle", "ninja", "account-cowboy-hat", "alien", "owl", "panda", "cat", "dog", "account-tie", "face-woman-shimmer", "face-man-shimmer"]

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
            "entry": random.choice(["entry_rocket", "entry_lightning", None])}
