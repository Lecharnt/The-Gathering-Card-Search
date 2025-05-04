import streamlit as st
import requests
from collections import defaultdict
import time

# Streamlit app configuration
st.set_page_config(
    page_title="MTG Card Search",
    page_icon=":cards:",
    layout="wide"
)

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

def get_card_front_and_back(card):
    """Returns both faces of a transform card or just the single face"""
    if card.get('layout') in ['transform', 'modal_dfc'] and 'card_faces' in card:
        return card['card_faces'][0], card['card_faces'][1]
    return card, None

def categorize_by_color(cards):
    categories = defaultdict(list)
    for card in cards:
        front, back = get_card_front_and_back(card)
        front_color_identity = front.get('color_identity', [])
        card_type = front['type_line']
        
        # Check if back face exists and has different color identity
        if back and back.get('color_identity', []) != front_color_identity:
            # For transform cards, use the combined color identity
            combined_colors = list(set(front_color_identity + back.get('color_identity', [])))
            color_name = get_color_identity_name(combined_colors)
        else:
            color_name = get_color_identity_name(front_color_identity)
            
        if 'Land' in card_type:
            categories['Lands'].append(card)
        else:
            categories[color_name].append(card)
    return categories

def categorize_by_type(cards):
    categories = defaultdict(list)
    for card in cards:
        front, back = get_card_front_and_back(card)
        front_type = front['type_line']
        
        # Check both faces for transform cards
        types = [front_type]
        if back:
            types.append(back['type_line'])
        
        # Categorize based on all types from all faces
        if any('Creature' in t for t in types):
            categories['Creatures'].append(card)
        elif any('Artifact' in t for t in types):
            categories['Artifacts'].append(card)
        elif any('Enchantment' in t for t in types):
            categories['Enchantments'].append(card)
        elif any('Instant' in t for t in types):
            categories['Instants'].append(card)
        elif any('Sorcery' in t for t in types):
            categories['Sorceries'].append(card)
        elif any('Planeswalker' in t for t in types):
            categories['Planeswalkers'].append(card)
        elif any('Land' in t for t in types):
            categories['Lands'].append(card)
        elif any('Battle' in t for t in types):
            categories['Battles'].append(card)
        else:
            categories['Other'].append(card)
    return categories

def categorize_by_mana(cards):
    categories = defaultdict(list)
    for card in cards:
        front, back = get_card_front_and_back(card)
        front_cmc = front.get('cmc', 0)
        
        # For transform cards, use the highest CMC of either face
        if back:
            back_cmc = back.get('cmc', 0)
            cmc = max(front_cmc, back_cmc)
        else:
            cmc = front_cmc
        
        if cmc == 0:
            categories['0 Mana'].append(card)
        elif cmc == 1:
            categories['1 Mana'].append(card)
        elif cmc == 2:
            categories['2 Mana'].append(card)
        elif cmc == 3:
            categories['3 Mana'].append(card)
        elif cmc == 4:
            categories['4 Mana'].append(card)
        elif cmc == 5:
            categories['5 Mana'].append(card)
        elif cmc == 6:
            categories['6 Mana'].append(card)
        else:
            categories['7+ Mana'].append(card)
    return categories

def categorize_by_price(cards):
    categories = defaultdict(list)
    for card in cards:
        prices = card.get('prices', {})
        usd_price = prices.get('usd')
        
        # For transform cards, we'll use the card's overall price (not per face)
        price = float(usd_price or 0)
        
        if price == 0:
            categories['$0 (No Price)'].append(card)
        elif price <= 0.50:
            categories['$0.50 or less'].append(card)
        elif price <= 1.00:
            categories['$0.51 to $1.00'].append(card)
        elif price <= 5.00:
            categories['$1.01 to $5.00'].append(card)
        else:
            categories['$5.01 or more'].append(card)
    return categories
def safe_get(card, *keys, default=None):
    """Safely get nested dictionary values."""
    for key in keys:
        try:
            card = card[key]
        except (KeyError, TypeError):
            return default
    return card

def main():
    st.title("Magic The Gathering Card Search")
    
    with st.sidebar:
        st.header("Search Options")
        query = st.text_input("Search Oracle text", "")
        sort_by = st.selectbox(
            "Sort by",
            ["Type", "Color", "Mana Cost", "Price"],
            index=0
        )
    
    if query:
        with st.spinner("Searching for cards..."):
            cards = fetch_cards(query)
            time.sleep(0.5)
        
        if not cards:
            st.warning("No cards found matching your search.")
            return
            
        sort_methods = {
            "Type": categorize_by_type,
            "Color": categorize_by_color,
            "Mana Cost": categorize_by_mana,
            "Price": categorize_by_price
        }
        
        categories = sort_methods[sort_by](cards)
        
        st.success(f"Found {len(cards)} cards")
        st.subheader(f"Results sorted by: {sort_by}")
        
        for category, cards_in_category in categories.items():
            with st.expander(f"{category} ({len(cards_in_category)})", expanded=True):
                cols = st.columns(4)
                
                for i, card in enumerate(cards_in_category):
                    with cols[i % 4]:
                        # Safely get image URL
                        image_url = safe_get(card, 'image_uris', 'normal') or \
                                  safe_get(card, 'card_faces', 0, 'image_uris', 'normal')
                        
                        if image_url:
                            st.image(
                                image_url,
                                caption=f"{safe_get(card, 'name', default='Unknown')} ({safe_get(card, 'mana_cost', default='')})",
                                use_column_width=True
                            )
                        else:
                            st.write(f"No image for {safe_get(card, 'name', default='Unknown Card')}")
                        
                        with st.popover("Details"):
                            st.write(f"**Name:** {safe_get(card, 'name', default='Unknown')}")
                            st.write(f"**Type:** {safe_get(card, 'type_line', default='N/A')}")
                            st.write(f"**Mana Cost:** {safe_get(card, 'mana_cost', default='N/A')}")
                            st.write(f"**CMC:** {safe_get(card, 'cmc', default='N/A')}")
                            st.write(f"**Text:** {safe_get(card, 'oracle_text', default='N/A')}")
                            
                            # Safely get scryfall URI
                            scryfall_uri = safe_get(card, 'scryfall_uri')
                            if scryfall_uri:
                                st.write(f"[Scryfall Link]({scryfall_uri})")
                            else:
                                st.write("No Scryfall link available")

if __name__ == "__main__":
    main()
