from flask import Flask, render_template, request
import requests
from collections import defaultdict

app = Flask(__name__)
SCRYFALL_SEARCH_URL = "https://api.scryfall.com/cards/search"

def fetch_cards(query):
    url = f"{SCRYFALL_SEARCH_URL}?q=o:{query}&unique=cards"
    all_cards = []
    while url:
        response = requests.get(url)
        data = response.json()
        all_cards.extend(data.get("data", []))
        url = data.get("next_page")
    return all_cards

def get_color_identity_name(color_identity):
    color_map = {
        'W': 'White',
        'U': 'Blue',
        'B': 'Black',
        'R': 'Red',
        'G': 'Green'
    }
    
    colors = [color_map.get(c, c) for c in color_identity]
    
    if len(colors) == 0:
        return "Colorless"
    elif len(colors) == 1:
        return colors[0]
    elif len(colors) == 2:
        color_pair = tuple(sorted(color_identity))
        two_color_names = {
            ('W', 'U'): "Azorius (White/Blue)",
            ('U', 'B'): "Dimir (Blue/Black)",
            ('U', 'R'): "Izzet (Blue/Red)",
            ('U', 'G'): "Simic (Blue/Green)",
            ('B', 'R'): "Rakdos (Black/Red)",
            ('B', 'G'): "Golgari (Black/Green)",
            ('W', 'B'): "Orzhov (White/Black)",
            ('W', 'R'): "Boros (White/Red)",
            ('W', 'G'): "Selesnya (White/Green)",
            ('R', 'G'): "Gruul (Red/Green)"
        }
        return two_color_names.get(color_pair, "/".join(colors))
    elif len(colors) == 3:
        color_triple = tuple(sorted(color_identity))
        three_color_names = {
            ('W', 'U', 'B'): "Esper (White/Blue/Black)",
            ('U', 'B', 'R'): "Grixis (Blue/Black/Red)",
            ('B', 'R', 'G'): "Jund (Black/Red/Green)",
            ('W', 'R', 'G'): "Naya (White/Red/Green)",
            ('W', 'U', 'G'): "Bant (White/Blue/Green)",
            ('W', 'B', 'G'): "Abzan (White/Black/Green)",
            ('W', 'U', 'R'): "Jeskai (White/Blue/Red)",
            ('W', 'B', 'R'): "Mardu (White/Black/Red)",
            ('U', 'B', 'G'): "Sultai (Blue/Black/Green)",
            ('U', 'R', 'G'): "Temur (Blue/Red/Green)"
        }
        return three_color_names.get(color_triple, "/".join(colors))
    elif len(colors) == 4:
        return "Four-Color (" + "/".join(colors) + ")"
    else:
        return "Five-Color (WUBRG)"

def categorize_by_color(cards):
    categories = defaultdict(list)
    for card in cards:
        front = card['card_faces'][0] if card.get('layout') == 'transform' else card
        color_identity = front.get('color_identity', [])
        card_type = front['type_line']
        
        if 'Land' in card_type:
            categories['Lands'].append(front)
        else:
            color_name = get_color_identity_name(color_identity)
            categories[color_name].append(front)
    return categories

def categorize_by_type(cards):
    categories = defaultdict(list)
    for card in cards:
        front = card['card_faces'][0] if card.get('layout') == 'transform' else card
        card_type = front['type_line']
        
        # Simplify type categories
        if 'Creature' in card_type:
            categories['Creatures'].append(front)
        elif 'Artifact' in card_type:
            categories['Artifacts'].append(front)
        elif 'Enchantment' in card_type:
            categories['Enchantments'].append(front)
        elif 'Instant' in card_type:
            categories['Instants'].append(front)
        elif 'Sorcery' in card_type:
            categories['Sorceries'].append(front)
        elif 'Planeswalker' in card_type:
            categories['Planeswalkers'].append(front)
        elif 'Land' in card_type:
            categories['Lands'].append(front)
        elif 'Battle' in card_type:
            categories['Battles'].append(front)
        else:
            categories['Other'].append(front)
    return categories

def categorize_by_mana(cards):
    categories = defaultdict(list)
    for card in cards:
        front = card['card_faces'][0] if card.get('layout') == 'transform' else card
        cmc = front.get('cmc', 0)
        
        if cmc == 0:
            categories['0 Mana'].append(front)
        elif cmc == 1:
            categories['1 Mana'].append(front)
        elif cmc == 2:
            categories['2 Mana'].append(front)
        elif cmc == 3:
            categories['3 Mana'].append(front)
        elif cmc == 4:
            categories['4 Mana'].append(front)
        elif cmc == 5:
            categories['5 Mana'].append(front)
        elif cmc == 6:
            categories['6 Mana'].append(front)
        else:
            categories['7+ Mana'].append(front)
    return categories

def categorize_by_price(cards):
    categories = defaultdict(list)
    for card in cards:
        front = card['card_faces'][0] if card.get('layout') == 'transform' else card
        price = float(front.get('prices', {}).get('usd', 0) or 0)
        
        if price == 0:
            categories['$0 (No Price)'].append(front)
        elif price <= 0.50:
            categories['$0.50 or less'].append(front)
        elif price <= 1.00:
            categories['$0.51 to $1.00'].append(front)
        elif price <= 5.00:
            categories['$1.01 to $5.00'].append(front)
        else:
            categories['$5.01 or more'].append(front)
    return categories

@app.route("/", methods=["GET", "POST"])
def index():
    categories = {}
    query = ""
    sort_by = "type"
    sort_label = "Type"
    has_categories = False
    loaded = False  # Add this flag

    if request.method == "POST":
        query = request.form.get("query", "").strip()
        sort_by = request.form.get("sort_by", "type")
        
        # Show loading state when fetching cards
        cards = fetch_cards(query)

        sort_labels = {
            "type": "Type",
            "color": "Color",
            "mana": "Mana Cost",
            "price": "Price"
        }
        sort_label = sort_labels.get(sort_by, "Type")

        # Sorting and categorization logic remains the same
        if sort_by == "type":
            cards.sort(key=lambda x: x['type_line'])
            categories = categorize_by_type(cards)
        elif sort_by == "color":
            cards.sort(key=lambda x: get_color_identity_name(x.get('color_identity', [])))
            categories = categorize_by_color(cards)
        elif sort_by == "mana":
            cards.sort(key=lambda x: x.get('cmc', 0))
            categories = categorize_by_mana(cards)
        elif sort_by == "price":
            cards.sort(key=lambda x: float(x.get('prices', {}).get('usd', 0) or 0))
            categories = categorize_by_price(cards)
        
        has_categories = bool(categories)
        loaded = True  # Set to True after data is loaded

    return render_template(
        "index.html", 
        categories=categories,
        has_categories=has_categories,
        query=query, 
        sort_by=sort_by,
        sort_label=sort_label,
        loaded=loaded  # Pass the loaded flag to template
    )
# Add this at the bottom of your app.py
if __name__ == "__main__":
    app.run()