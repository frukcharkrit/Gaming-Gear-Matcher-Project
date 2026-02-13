import os
import json
import shutil
from django.core.management.base import BaseCommand
from django.core.files import File
from django.conf import settings
from APP01.models import ProPlayer, GamingGear, ProPlayerGear

class Command(BaseCommand):
    help = 'Import real data from JSON files'

    def handle(self, *args, **options):
        self.stdout.write("Starting data import...")
        
        base_data_dir = os.path.join(settings.BASE_DIR, 'data')
        
        # 1. Import Gaming Gear
        self.import_gear(base_data_dir)
        
        # 2. Import Pro Players
        self.import_pro_players(base_data_dir)
        
        self.stdout.write(self.style.SUCCESS("Data import completed successfully!"))
    
    def generate_description(self, category, item):
        """สร้างคำอธิบายจาก specs"""
        name = item.get('Name', 'Unknown Gear')
        
        if category == 'Mouse':
            sensor = item.get('Sensor', 'High-performance optical sensor')
            dpi = item.get('Max DPI', '20000')
            weight = item.get('Weight', 'lightweight')
            shape = item.get('Shape', 'ergonomic')
            return f"Professional gaming mouse featuring {sensor} sensor with up to {dpi} DPI. " \
                   f"Designed with a {shape.lower()} shape and weighing only {weight}g, " \
                   f"this mouse delivers precision and comfort for competitive gaming."
        
        elif category == 'Keyboard':
            switches = item.get('Switches', 'mechanical switches')
            return f"High-performance gaming keyboard equipped with {switches}. " \
                   f"Built for esports professionals, offering fast response times and durability for intense gaming sessions."
        
        elif category == 'Headset':
            driver = item.get('Driver Size (mm)', 'premium drivers')
            connection = item.get('Connection', 'multi-platform')
            return f"Premium gaming headset with {driver}mm drivers delivering immersive audio. " \
                   f"Features {connection} connectivity for versatile gaming setups."
        
        elif category == 'Monitor':
            refresh = item.get('Max Refresh Rate (Hz)', 'high refresh rate')
            resolution = item.get('Resolution', 'high resolution')
            panel = item.get('Panel Type', 'gaming-grade panel')
            return f"Professional gaming monitor with {refresh}Hz refresh rate and {resolution} {panel}. " \
                   f"Engineered for competitive gaming with fast response times and smooth visuals."
        
        elif category == 'Mousepad':
            surface = item.get('Surface', 'optimized gaming surface')
            size = item.get('Size', 'large')
            return f"Professional gaming mousepad with {surface.lower()}. " \
                   f"{size} size provides ample space for low-sensitivity gaming."
        
        elif category == 'Chair':
            material = item.get('Material', 'premium materials')
            return f"Ergonomic gaming chair crafted with {material.lower()}. " \
                   f"Designed for extended gaming sessions with optimal support and comfort."
        
        else:
            return f"Professional {category.lower()} designed for competitive gaming. " \
                   f"Features high-quality components and construction for peak performance."

    def load_reviews(self, base_data_dir):
        """Loads all review data and calculates sentiment scores."""
        reviews = {}
        review_files = {
            'Mouse': 'mice_reviews_data.json',
            'Keyboard': 'keyboards_reviews_data.json',
            'Headset': 'headsets_reviews_data.json',
            'Monitor': 'monitors_reviews_data.json',
            'Mousepad': 'mousepads_reviews_data.json',
            'Chair': 'chairs_reviews_data.json'
        }

        for category, filename in review_files.items():
            filepath = os.path.join(base_data_dir, filename)
            if not os.path.exists(filepath):
                continue
            
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            reviews[category] = {}
            for item in data:
                name = item.get('name')
                if not name:
                    continue
                # Clean name: remove " Review" suffix for matching
                clean_name = name.replace(' Review', '').strip()
                
                pros = item.get('pros', [])
                cons = item.get('cons', [])
                
                # Simple NLP Sentiment Algorithm
                # Pros are weighted more positively (1.5), Cons negatively (1.0)
                score = (len(pros) * 1.5) - (len(cons) * 1.0)
                
                reviews[category][clean_name] = {
                    'pros': pros,
                    'cons': cons,
                    'sentiment_score': score
                }
        return reviews

    def import_gear(self, base_data_dir):
        # 1. Load Reviews Metadata
        reviews_data = self.load_reviews(base_data_dir)
        
        gear_files = {
            'Mouse': 'mice_data.json',
            'Keyboard': 'keyboards_data.json',
            'Headset': 'headsets_data.json',
            'Monitor': 'monitors_data.json',
            'Mousepad': 'mousepads_data.json',
            'Chair': 'chairs_data.json'
        }

        for category, filename in gear_files.items():
            filepath = os.path.join(base_data_dir, filename)
            if not os.path.exists(filepath):
                self.stdout.write(self.style.WARNING(f"File not found: {filename}"))
                continue
            
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            self.stdout.write(f"Importing {category} from {filename} with Sentiment Analysis...")
            
            for item in data:
                # Name key might vary slightly or be 'Name'
                name = item.get('Name') or item.get('name')
                if not name:
                    continue
                
                # Generate description
                description = self.generate_description(category, item)
                
                # Merge Review Data (NLP)
                specs_data = item.copy()
                review_info = reviews_data.get(category, {}).get(name)
                
                # Try fuzzy match if exact match fails
                if not review_info:
                    for r_name, r_data in reviews_data.get(category, {}).items():
                        if name in r_name or r_name in name:
                            review_info = r_data
                            break
                
                if review_info:
                    specs_data['pros'] = review_info['pros']
                    specs_data['cons'] = review_info['cons']
                    specs_data['sentiment_score'] = review_info['sentiment_score']
                
                # Try to find existing gear or create
                gear, created = GamingGear.objects.get_or_create(
                    name=name,
                    defaults={
                        'type': category,
                        'brand': name.split(' ')[0], # Simple guess
                        'description': description,
                        'specs': json.dumps(specs_data) # Store all raw data + sentiment in specs
                    }
                )
                
                # Update description if gear already exists but has no description
                if not created:
                    needs_save = False
                    if not gear.description:
                        gear.description = description
                        needs_save = True
                    
                    # Update specs with new review data if available
                    if review_info:
                        current_specs = json.loads(gear.specs) if gear.specs else {}
                        # Only update if sentiment is missing or different
                        if 'sentiment_score' not in current_specs:
                            current_specs.update({
                                'pros': review_info['pros'],
                                'cons': review_info['cons'],
                                'sentiment_score': review_info['sentiment_score']
                            })
                            gear.specs = json.dumps(current_specs)
                            needs_save = True
                    
                    if needs_save:
                        gear.save()
                
                # Image handling
                # Images are in "Gaming Gear Pictures/{Category}/{Name}.png/jpg/etc"
                # We need to find the file.
                image_dir = os.path.join(base_data_dir, 'Gaming Gear Pictures', category)
                image_path = self.find_image(image_dir, name)
                
                if image_path and (created or not gear.image):
                    with open(image_path, 'rb') as img_f:
                        gear.image.save(os.path.basename(image_path), File(img_f), save=True)
                        
    def import_pro_players(self, base_data_dir):
        filepath = os.path.join(base_data_dir, 'pro_player_data.json')
        if not os.path.exists(filepath):
            return

        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.stdout.write(f"Importing Pro Players...")
        
        for item in data:
            name = item.get('player_name')
            if not name:
                continue
                
            details = item.get('details', {})
            
            player, created = ProPlayer.objects.get_or_create(
                name=name,
                defaults={
                    'game': details.get('game', 'Unknown'),
                    'bio': details.get('bio', ''),
                    'settings': json.dumps({
                        'mouse_settings': item.get('mouse_settings', {}),
                        'setup': item.get('setup', [])
                    })
                }
            )
            
            # Image handling
            image_dir = os.path.join(base_data_dir, 'Pro Player Pictures')
            image_path = self.find_image(image_dir, name)
            
            if image_path and (created or not player.image):
                with open(image_path, 'rb') as img_f:
                    player.image.save(os.path.basename(image_path), File(img_f), save=True)

            # Link Gear
            if 'gear' in item:
                for gear_item in item['gear']:
                    gear_name = gear_item.get('name')
                    gear_cat = gear_item.get('category')
                    
                    # Try to find the gear in DB
                    # Fuzzy match might be needed but for now exact or contains
                    gear_obj = GamingGear.objects.filter(name__icontains=gear_name).first()
                    
                    if gear_obj:
                        ProPlayerGear.objects.get_or_create(player=player, gear=gear_obj)

    def find_image(self, directory, start_name):
        if not os.path.exists(directory):
            return None
        
        # Clean name for filename matching if needed
        # But simpler is to list dir and find matching start
        
        # remove special chars from start_name for filename comparison if needed
        # For now, simplistic search
        
        safe_name = start_name.replace(' ', '_').replace('"', '').replace("'", "")
        
        for f in os.listdir(directory):
            if f.lower().startswith(start_name.lower()) or f.lower().startswith(safe_name.lower()):
                 return os.path.join(directory, f)
        
        return None
