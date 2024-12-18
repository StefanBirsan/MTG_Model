import requests
import pandas as pd
import os
import re
from PIL import Image, ImageEnhance, ImageOps

annotations = []
processed_ids = set()  

# API URL to fetch a random card
api_url = "https://api.scryfall.com/cards/random"

# sanitize card names for use in file and directory names
def sanitize_name(name):
    return re.sub(r'[<>:"/\\|?*]', '', name)

def fetch_cards(url, max_images=10000):
    image_count = 0  

    while image_count < max_images:
        response = requests.get(url)
        card = response.json()
        
        card_id = card['id']
        if card_id in processed_ids:
            continue 
        
        if 'image_uris' in card: 
            image_url = card['image_uris']['normal']
            image_response = requests.get(image_url)
            image_path = os.path.join('data', 'raw', 'images', f"{card_id}.jpg")
            
            os.makedirs(os.path.dirname(image_path), exist_ok=True)
            
            with open(image_path, 'wb') as f:
                f.write(image_response.content)
            
            name = sanitize_name(card['name'])
            mana_color = card['colors'] if 'colors' in card else ['Colorless']
            rarity = card['rarity']
            set_name = card['set_name']
            
            mana_cost = card.get('mana_cost', '')
            total_mana = sum(int(x) if x.isdigit() else 1 for x in re.findall(r'\{(\w+)\}', mana_cost))
            generic_mana = sum(int(x) for x in re.findall(r'\{(\d+)\}', mana_cost))
            mana_count = {color: mana_cost.count(color) for color in ['W', 'U', 'B', 'R', 'G']}
            
            annotations.append([image_path, name, mana_color, rarity, set_name, total_mana, generic_mana, mana_count])
            
            card_folder = os.path.join('data', 'raw', 'images', name)
            os.makedirs(card_folder, exist_ok=True)
            
            original_image_path = os.path.join(card_folder, f"{card_id}.jpg")
            os.rename(image_path, original_image_path)

            original_image = Image.open(original_image_path)
            
            for i in range(1, 6):
                variation = original_image.copy()
            
                if i == 1:
                    variation = ImageEnhance.Brightness(variation).enhance(1.5)
                elif i == 2:
                    variation = ImageEnhance.Contrast(variation).enhance(1.5)
                elif i == 3:
                    variation = ImageEnhance.Color(variation).enhance(1.5)
                elif i == 4:
                    variation = ImageOps.grayscale(variation)
                elif i == 5:
                    variation = ImageOps.invert(variation)
                
                variation_path = os.path.join(card_folder, f"{card_id}_variation_{i}.jpg")
                variation.save(variation_path)
            
            processed_ids.add(card_id) 
            image_count += 1 

fetch_cards(api_url)

annotations_df = pd.DataFrame(annotations, columns=['image_path', 'name', 'mana_color', 'rarity', 'set_name', 'total_mana', 'generic_mana', 'mana_count'])
annotations_df.to_csv('data/annotations.csv', index=False)

print("Data collection complete. Images and annotations saved.")