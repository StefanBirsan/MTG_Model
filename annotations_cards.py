import requests
import pandas as pd
import os
import re
from PIL import Image, ImageEnhance, ImageOps

annotations = []

# Base API URL to fetch cards from all sets
api_url = "https://api.scryfall.com/cards/search?q=game:paper"

# Function to fetch cards and handle pagination
def fetch_cards(url, max_images=10000):
    image_count = 0  

    while url and image_count < max_images:
        response = requests.get(url)
        data = response.json()
        cards = data['data']
        
        for card in cards:
            if 'image_uris' in card: 
                image_url = card['image_uris']['normal']
                image_response = requests.get(image_url)
                image_path = os.path.join('data', 'raw', 'images', f"{card['id']}.jpg")
                
                # Ensure the directory exists before writing the file
                os.makedirs(os.path.dirname(image_path), exist_ok=True)
                
                with open(image_path, 'wb') as f:
                    f.write(image_response.content)
                
                name = card['name']
                mana_color = card['colors'] if 'colors' in card else ['Colorless']
                rarity = card['rarity']
                set_name = card['set_name']
                
                # Extract mana cost information
                mana_cost = card.get('mana_cost', '')
                total_mana = sum(int(x) if x.isdigit() else 1 for x in re.findall(r'\{(\w+)\}', mana_cost))
                generic_mana = sum(int(x) for x in re.findall(r'\{(\d+)\}', mana_cost))
                mana_count = {color: mana_cost.count(color) for color in ['W', 'U', 'B', 'R', 'G']}
                
                annotations.append([image_path, name, mana_color, rarity, set_name, total_mana, generic_mana, mana_count])
                
                
                card_folder = os.path.join('data', 'raw', 'images', name)
                os.makedirs(card_folder, exist_ok=True)
                
        
                original_image_path = os.path.join(card_folder, f"{card['id']}.jpg")
                os.rename(image_path, original_image_path)
                
                
                original_image = Image.open(original_image_path)
                
                # Create 5 variations of the image
                for i in range(1, 6):
                    variation = original_image.copy()
                    
                    # Apply different transformations for each variation
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
                    
                    variation_path = os.path.join(card_folder, f"{card['id']}_variation_{i}.jpg")
                    variation.save(variation_path)
                
                image_count += 1  
                
                if image_count >= max_images:
                    break  
        
        if image_count < max_images:
            url = data.get('next_page')
        else:
            break

fetch_cards(api_url)


annotations_df = pd.DataFrame(annotations, columns=['image_path', 'name', 'mana_color', 'rarity', 'set_name', 'total_mana', 'generic_mana', 'mana_count'])
annotations_df.to_csv('data/annotations.csv', index=False)

print("Data collection complete. Images and annotations saved.")