import json
from .models import GamingGear

class HybridRecommender:
    def __init__(self):
        pass

    def _format_sentiment(self, raw_score):
        try:
            val = float(raw_score)
            # Cap at 9.9 to appear more realistic than a perfect 10.0
            val = min(val, 9.9)
            # Round to 1 decimal place
            val = round(val, 1)
            # Format: remove .0 if integer-like (though we just rounded to 1 decimal)
            # Actually, standardizing to 1 decimal place is better for consistency: "9.5/10"
            return val
        except:
            return 0
            
    def recommend_chair(self, user_prefs):
        # Chair logic is tricky without height/weight from user, but we can use 'hand_size' as a proxy for body size
        # Small hand -> Small/Medium Chair?
        # Large hand -> Large Chair?
        # Or just recommend generally good ergonomic chairs.
        
        hand_size = user_prefs.get('hand_size', 'Medium')
        candidates = GamingGear.objects.filter(type='Chair')
        scores = []
        
        for gear in candidates:
            score = 0
            reasons = []
            if isinstance(gear.specs, str):
                try:
                    specs = json.loads(gear.specs)
                except:
                    specs = {}
            else:
                specs = gear.specs
                
            try:
                max_weight_str = specs.get('Max weight', '100')
                if not max_weight_str:
                    max_weight_str = '100'
                max_weight = float(max_weight_str)
            except (ValueError, TypeError):
                max_weight = 100.0
            
            # Simple Size Logic
            if hand_size == 'Large': 
                if max_weight >= 130:
                    score += 20
                    reasons.append(f"High durability {max_weight}kg")
            elif hand_size == 'Small':
                # No penalty for durable chairs, but maybe prefer slightly smaller ones if we had dimensions
                pass
                
            # Material Logic (Random proxy for now as we don't ask for it)
            material = specs.get('Material', '')
            if 'Fabric' in material:
                score += 10
                reasons.append("Breathable Fabric")
            elif 'Real Leather' in material:
                score += 15
                reasons.append("Premium Real Leather")
                
            # Lumbar Support
            if 'Adjustable' in specs.get('Lumbar support', ''):
                score += 10
                reasons.append("Adjustable Lumbar Support")
                
            # Sentiment
            sentiment = specs.get('sentiment_score', 0)
            if sentiment:
                try:
                    sent_val = self._format_sentiment(sentiment)
                    score += min(sent_val * 2, 30)
                    if sent_val > 5:
                        reasons.append(f"High reviewer sentiment ({sent_val}/10)")
                except: pass
                
            scores.append({'gear': gear, 'score': score, 'reasons': reasons, 'sentiment': sentiment})
            
        scores.sort(key=lambda x: x['score'], reverse=True)
        return scores[:5]

    def recommend_setup(self, user_prefs):
        """
        Recommend a full setup (Mouse, Keyboard, Headset, Monitor, Chair) based on user profile.
        Returns a dictionary of recommendations for each category.
        """
        # Get top candidates
        mice = self.recommend_mouse(user_prefs)
        keyboards = self.recommend_keyboard(user_prefs)
        headsets = self.recommend_headset(user_prefs)
        monitors = self.recommend_monitor(user_prefs)
        chairs = self.recommend_chair(user_prefs)
        
        # Take the best one for legacy compatibility
        setup = {
            'Mouse': mice[0] if mice else None,
            'Keyboard': keyboards[0] if keyboards else None,
            'Headset': headsets[0] if headsets else None,
            'Monitor': monitors[0] if monitors else None,
            'Chair': chairs[0] if chairs else None
        }
        return setup

    def recommend_variant_setups(self, user_prefs):
        """
        Returns 3 distinct setups: Performance, Balanced, Pro.
        Each includes an AI-generated analysis with pros/cons.
        """
        genre = user_prefs.get('genre', 'Gaming')
        hand_size = user_prefs.get('hand_size', 'Medium')
        grip = user_prefs.get('grip', 'Palm')

        # Get Candidates (Top 5)
        mice = self.recommend_mouse(user_prefs)
        keyboards = self.recommend_keyboard(user_prefs)
        headsets = self.recommend_headset(user_prefs)
        monitors = self.recommend_monitor(user_prefs)
        chairs = self.recommend_chair(user_prefs)

        variants = {}

        # === Helper: extract key spec safely ===
        def _spec(gear_entry, key, default='-'):
            if not gear_entry:
                return default
            try:
                if isinstance(gear_entry['gear'].specs, str):
                    specs = json.loads(gear_entry['gear'].specs)
                else:
                    specs = gear_entry['gear'].specs
                return specs.get(key, default)
            except (json.JSONDecodeError, AttributeError, TypeError): # Catch specific errors for robustness
                return default

        # Helper to calculate total score for a setup
        def calculate_variant_score(variant_gears):
            total_score = 0
            # Max possible scores based on logic:
            # Mouse: ~80, Keyboard: ~60, Headset: ~50, Monitor: ~70, Chair: ~45 => Total ~305
            # We'll normalize this to 0-100
            MAX_POSSIBLE_SCORE = 305.0 
            
            for gear_entry in variant_gears:
                if gear_entry: 
                    # gear_entry is dict from recommend_X functions which includes 'score'
                    total_score += gear_entry.get('score', 0)
            
            # Normalize to 0-100
            final_score = (total_score / MAX_POSSIBLE_SCORE) * 100
            return min(final_score, 100) # Cap at 100

        # ======================================================
        # 1. Performance (Best Spec Match) -> Index 0
        # ======================================================
        # ... (Existing analysis logic remains) ...
        perf_gears_list = [
            mice[0] if mice else None,
            keyboards[0] if keyboards else None,
            headsets[0] if headsets else None,
            monitors[0] if monitors else None,
            chairs[0] if chairs else None
        ]

        perf_analysis = (
            f"🎯 This setup is laser-focused on {genre} performance. "
            f"Every piece of gear was selected to maximize your competitive edge "
            f"with your {hand_size.lower()} hands and {grip.lower()} grip style."
        )

        perf_pros = [f"Best spec match for {genre} gameplay"]
        perf_cons = []

        # Mouse analysis
        if mice:
            mouse_weight = _spec(mice[0], 'W (g)', None)
            mouse_shape = _spec(mice[0], 'Shape', '')
            if mouse_weight:
                try:
                    w = float(mouse_weight)
                    if w < 70:
                        perf_pros.append(f"Ultra-lightweight mouse ({mouse_weight}g) — fast aim")
                    elif w < 85:
                        perf_pros.append(f"Well-balanced mouse weight ({mouse_weight}g)")
                    else:
                        perf_pros.append(f"Stable, heavier mouse ({mouse_weight}g) — precision control")
                except:
                    pass
            if 'Ergonomic' in mouse_shape:
                perf_pros.append("Ergonomic mouse shape for comfort during long sessions")
            elif 'Ambidextrous' in mouse_shape:
                perf_pros.append("Ambidextrous mouse suitable for any hand orientation")

        # Keyboard analysis
        if keyboards:
            form = _spec(keyboards[0], 'Form Factor', '')
            if form and form != '-':
                if any(x in form for x in ['60%', '65%']):
                    perf_pros.append(f"Compact {form} keyboard — maximizes desk space")
                elif 'TKL' in form:
                    perf_pros.append(f"TKL layout — good balance of function keys & mouse space")
                elif 'Full' in form:
                    perf_pros.append(f"Full-size keyboard with numpad and macro keys")

        # Monitor analysis
        if monitors:
            hz = _spec(monitors[0], 'Refresh Rate', '')
            panel = _spec(monitors[0], 'Panel Tech', '')
            if hz and hz != '-':
                perf_pros.append(f"{hz} refresh rate for silky-smooth visuals")
            if 'TN' in str(panel):
                perf_cons.append("TN panel — limited viewing angles and color accuracy")
            elif 'IPS' in str(panel):
                perf_pros.append("IPS panel with good color accuracy")

        # Generic Performance cons
        perf_pros.append("High compatibility score based on your profile")
        
        perf_cons.append("Premium gear may be harder to find in some regions")
        if not any('comfort' in p.lower() for p in perf_pros):
            perf_cons.append("Spec-focused — comfort and ergonomics may be secondary")

        # Helper to inject context-specific reason
        def _add_context(gear_entry, context_reason):
            if not gear_entry: return None
            new_entry = gear_entry.copy()
            # Copy the list to avoid shared reference
            new_entry['reasons'] = gear_entry['reasons'][:] + [context_reason]
            return new_entry

        variants['Performance'] = {
            'Mouse': _add_context(perf_gears_list[0], f"Top Spec Match for {genre}"),
            'Keyboard': _add_context(perf_gears_list[1], "Max Performance Choice"),
            'Headset': _add_context(perf_gears_list[2], "Best Audio Precision"),
            'Monitor': _add_context(perf_gears_list[3], "High Refresh Rate Focus"),
            'Chair': _add_context(perf_gears_list[4], "Max Ergonomics"),
            'desc': 'Top-tier specs matched to your playstyle.',
            'analysis': perf_analysis,
            'pros': perf_pros,
            'cons': perf_cons,
            'badge': 'Best Match',
            'score': calculate_variant_score(perf_gears_list)
        }

        # ======================================================
        # 2. Balanced / Value -> Index 1
        # ======================================================
        bal_gears_list = [
            mice[1] if len(mice) > 1 else (mice[0] if mice else None),
            keyboards[1] if len(keyboards) > 1 else (keyboards[0] if keyboards else None),
            headsets[1] if len(headsets) > 1 else (headsets[0] if headsets else None),
            monitors[1] if len(monitors) > 1 else (monitors[0] if monitors else None),
            chairs[1] if len(chairs) > 1 else (chairs[0] if chairs else None)
        ]

        bal_analysis = (
            f"⚖️ A smart alternative for {genre} players. "
            "This setup offers excellent performance from different brands or product lines, "
            "giving you variety and potentially better availability."
        )

        bal_pros = ["Great overall performance with alternative options"]
        bal_cons = []

        if len(mice) > 1:
            perf_brand = mice[0]['gear'].brand
            bal_brand = mice[1]['gear'].brand
            if perf_brand != bal_brand:
                bal_pros.append(f"Different mouse brand ({bal_brand}) — a fresh perspective")
            bal_weight = _spec(mice[1], 'W (g)', None)
            if bal_weight:
                try:
                    w = float(bal_weight)
                    if w < 80:
                        bal_pros.append(f"Lightweight mouse option ({bal_weight}g)")
                except:
                    pass

        if len(keyboards) > 1:
            bal_form = _spec(keyboards[1], 'Form Factor', '')
            if bal_form and bal_form != '-':
                bal_pros.append(f"Alternative keyboard layout: {bal_form}")

        if len(monitors) > 1:
            bal_hz = _spec(monitors[1], 'Refresh Rate', '')
            bal_panel = _spec(monitors[1], 'Panel Tech', '')
            if bal_hz and bal_hz != '-':
                bal_pros.append(f"Monitor with {bal_hz} refresh rate")
            if 'IPS' in str(bal_panel) or 'VA' in str(bal_panel):
                bal_pros.append(f"Better color reproduction with {bal_panel} panel")

        bal_cons.append("Slightly lower spec-match score than the Performance preset")
        bal_cons.append("May not be as fine-tuned to your specific hand size and grip")

        variants['Balanced'] = {
            'Mouse': _add_context(bal_gears_list[0], "Best Value Alternative"),
            'Keyboard': _add_context(bal_gears_list[1], "Balanced Feature Set"),
            'Headset': _add_context(bal_gears_list[2], "Great Audio/Price Ratio"),
            'Monitor': _add_context(bal_gears_list[3], "Solid Performance Value"),
            'Chair': _add_context(bal_gears_list[4], "Comfortable Value Choice"),
            'desc': 'Great performance with alternative features.',
            'analysis': bal_analysis,
            'pros': bal_pros,
            'cons': bal_cons,
            'badge': 'Value Pick',
            'score': calculate_variant_score(bal_gears_list)
        }

        # ======================================================
        # 3. Pro Choice (Most Used by Pros)
        # ======================================================
        from django.db.models import Count
        
        def get_pro_choice(category):
            # Find the gear with the highest pro usage count
            # We use 'proplayergear' which is the default related name lookup for Count
            popular = GamingGear.objects.filter(type=category).annotate(p_count=Count('proplayergear')).order_by('-p_count').first()
            
            if not popular:
                return None
                
            # Create a gear entry structure similar to recommend_X functions
            reasons = [f"Most used {category} among Pro Players"]
            if popular.p_count > 0:
                reasons.append(f"Used by {popular.p_count} Pros in our database")
            
            # Helper to get specs safely
            specs = popular.specs if isinstance(popular.specs, dict) else {}
            if isinstance(popular.specs, str):
                try:
                    specs = json.loads(popular.specs)
                except:
                    specs = {}
            
            sentiment = specs.get('sentiment_score', 0)
            
            return {
                'gear': popular,
                'score': 95, # High score for Pro Choice
                'reasons': reasons,
                'sentiment': sentiment,
                'specs': specs
            }

        pro_gears_list = [
            get_pro_choice('Mouse'),
            get_pro_choice('Keyboard'),
            get_pro_choice('Headset'),
            get_pro_choice('Monitor'),
            get_pro_choice('Chair')
        ]

        pro_analysis = (
            "🏆 The 'Meta' setup — these are the products most loved by data from pro players. "
            "This selection represents the current meta, prioritizing what the experts are actually using "
            "over theoretical spec matching."
        )

        pro_pros = ["Most popular choices among professional players", "Battle-tested in competitive environments"]
        pro_cons = []

        pro_mouse = pro_gears_list[0]
        if pro_mouse:
            p_count = pro_mouse['gear'].p_count
            if p_count > 2:
                pro_pros.append(f"Mouse is a dominant choice with {p_count} pro users")
            
            # Check overlap with Performance
            if mice and pro_mouse['gear'].gear_id == mice[0]['gear'].gear_id:
                pro_pros.append("Aligns perfectly with the Performance spec-match too!")
            else:
                 pro_cons.append("May not be the best spec-match for your specific hand size/grip")

        pro_cons.append("Popularity drives demand — stock might be an issue")
        pro_cons.append("The 'Meta' changes over time")

        variants['Pro'] = {
            'Mouse': _add_context(pro_gears_list[0], "Pro Usage Leader"),
            'Keyboard': _add_context(pro_gears_list[1], "Most Popular Model"),
            'Headset': _add_context(pro_gears_list[2], "Top Sound Choice"),
            'Monitor': _add_context(pro_gears_list[3], "Standard Issue Monitor"),
            'Chair': _add_context(pro_gears_list[4], "Most Trusted Seat"),
            'desc': 'Most used by Pros.',
            'analysis': pro_analysis,
            'pros': pro_pros,
            'cons': pro_cons,
            'badge': 'Pro Choice',
            'score': calculate_variant_score(pro_gears_list)
        }

        return variants

    def _parse_mouse_specs(self, specs):
        """Helper to extract mouse length and weight robustly."""
        # 1. Length from "H / W / L (cm)"
        length = 0.0
        dims = specs.get('H / W / L (cm)', '')
        if dims:
            parts = dims.split('/')
            if len(parts) == 3:
                try:
                    # Format is H / W / L, so Length is the last one
                    length = float(parts[2].strip())
                except: pass
        
        # 2. Weight from "Weight" or "W (g)"
        weight = 999.0
        w_str = specs.get('Weight') or specs.get('W (g)')
        if w_str:
            try:
                weight = float(str(w_str).replace('g', '').strip())
            except: pass
            
        return length, weight

    def recommend_mouse(self, user_prefs):
        """
        Ranking Algorithm for Mice based on User Preferences & NLP Sentiment.
        """
        genre = user_prefs.get('genre', 'FPS')
        hand_size = user_prefs.get('hand_size', 'Medium')
        grip = user_prefs.get('grip', 'Palm')
        
        candidates = GamingGear.objects.filter(type='Mouse')
        scores = []
        
        for gear in candidates:
            score = 0
            reasons = []
            if isinstance(gear.specs, str):
                try:
                    specs = json.loads(gear.specs)
                except:
                    specs = {}
            else:
                specs = gear.specs
                
            # Parse Specs
            length, weight = self._parse_mouse_specs(specs)
            shape = specs.get('Shape', 'Ambidextrous') # Ambidextrous / Ergonomic

            # --- 1. Hand Size Logic (Critical) ---
            # Small: < 17cm -> Mouse Length < 12.0cm
            # Medium: 17-19cm -> Mouse Length 11.5 - 12.5cm
            # Large: > 19cm -> Mouse Length > 12.5cm
            
            fit_score = 0
            if hand_size == 'Small':
                if length > 0 and length < 12.0:
                    fit_score = 30
                    reasons.append(f"Compact size ({length}cm) fits Small Hands")
                elif length > 12.5:
                    score -= 20 # Too big
            elif hand_size == 'Large':
                if length > 12.4:
                    fit_score = 30
                    reasons.append(f"Large size ({length}cm) fits Large Hands")
                elif length > 0 and length < 11.8:
                    score -= 10 # Too small
            else: # Medium fits most, but prefer balanced
                if 11.5 <= length <= 12.6:
                     fit_score = 15
                
            score += fit_score
                
            # --- 2. Grip Logic ---
            # Palm -> Ergonomic (Usually) or High Profile Amb
            # Claw -> Ambidextrous (Usually)
            # Fingertip -> Small/Low Profile Ambidextrous
            
            grip_score = 0
            if grip == 'Palm':
                if 'Ergonomic' in shape:
                    grip_score = 25
                    reasons.append(f"Ergonomic shape perfect for Palm Grip")
                elif length > 12.5: # Large Ambi also works for Palm
                    grip_score = 10
            elif grip == 'Claw':
                # Claw is versatile, usually Ambi or Ergo works, but weight matters
                if 'Ambidextrous' in shape:
                    grip_score = 15
                    reasons.append("Ambidextrous shape good for Claw")
            elif grip == 'Fingertip':
                if length > 0 and length < 12.1:
                    grip_score = 30
                    reasons.append(f"Short length ({length}cm) ideal for Fingertip")
                if 'Ergonomic' in shape:
                    score -= 10 # Ergo usually bad for fingertip
            
            score += grip_score
                
            # --- 3. Genre (Weight & Features) ---
            genre_score = 0
            if genre == 'FPS':
                if weight < 65:
                    genre_score = 35 # Huge bonus for lightweight in FPS
                    reasons.append(f"Ultra-light ({weight}g) for fast FPS aim")
                elif weight < 80:
                    genre_score = 15
            elif genre == 'MOBA':
                if 60 <= weight <= 90:
                    genre_score = 20
                    reasons.append(f"Balanced weight ({weight}g) for MOBA")
            elif genre in ['MMO', 'RPG']:
                # MMO often prefers buttons (not tracked well here) but heavier/stable is ok
                if weight > 75:
                    genre_score = 20
                    reasons.append(f"Stable weight ({weight}g) for MMO/RPG")
                
            score += genre_score

            # --- 4. Sentiment Boost ---
            sentiment = specs.get('sentiment_score', 0)
            if sentiment:
                try:
                    sent_val = self._format_sentiment(sentiment)
                    # Reduced sentiment weight so Fit/Genre matters more
                    boost = min(sent_val * 1.5, 15) 
                    score += boost
                    if sent_val > 8.0:
                        reasons.append(f"Top rated by reviewers ({sent_val}/10)")
                except:
                    pass
            
            scores.append({
                'gear': gear,
                'score': score,
                'reasons': reasons,
                'sentiment': sentiment,
                'specs': specs
            })
        
        # Sort and return best
        scores.sort(key=lambda x: x['score'], reverse=True)
        return scores[:5]

    def recommend_keyboard(self, user_prefs):
        genre = user_prefs.get('genre', 'FPS')
        candidates = GamingGear.objects.filter(type='Keyboard')
        scores = []
        
        for gear in candidates:
            score = 0
            reasons = []
            if isinstance(gear.specs, str):
                try:
                    specs = json.loads(gear.specs)
                except:
                    specs = {}
            else:
                specs = gear.specs
            
            form_factor = specs.get('Form Factor', '')
            
            # Genre Logic
            if genre == 'FPS':
                if any(x in form_factor for x in ['60%', '65%', '75%']):
                    score += 35
                    reasons.append(f"Compact {form_factor} layout: Max mouse space")
                elif 'TKL' in form_factor:
                    score += 20
                    reasons.append("TKL: Good balance for FPS")
            elif genre == 'MOBA':
                if 'TKL' in form_factor:
                    score += 25
                    reasons.append("TKL: Perfect size for MOBA")
            elif genre in ['MMO', 'RPG']:
                if 'Full Size' in form_factor:
                    score += 35
                    reasons.append("Full Size: Numpad & extra keys for macros")
            
            # Sentiment
            sentiment = specs.get('sentiment_score', 0)
            if sentiment:
                try:
                    sent_val = self._format_sentiment(sentiment)
                    score += min(sent_val * 2, 20)
                except: pass
                
            scores.append({'gear': gear, 'score': score, 'reasons': reasons, 'sentiment': sentiment})
            
        scores.sort(key=lambda x: x['score'], reverse=True)
        return scores[:5]

    def recommend_headset(self, user_prefs):
        genre = user_prefs.get('genre', 'FPS')
        candidates = GamingGear.objects.filter(type='Headset')
        scores = []
        
        for gear in candidates:
            score = 0
            reasons = []
            if isinstance(gear.specs, str):
                try:
                    specs = json.loads(gear.specs)
                except:
                    specs = {}
            else:
                specs = gear.specs
                
            # Headset logic is simple as specs are limited
            # FPS -> Imaging crucial (Open back often better but Wireless is convenient)
            
            connection = specs.get('Connection', '')
            
            if genre == 'FPS':
                # No strong preference, but many pros use IEMs or closed back for isolation
                pass
            
            # Sentiment is king for headsets as sound is subjective
            sentiment = specs.get('sentiment_score', 0)
            if sentiment:
                try:
                    sent_val = self._format_sentiment(sentiment)
                    score += min(sent_val * 4, 60) # High weight for audio quality
                    if sent_val > 7:
                        reasons.append(f"Excellent Sound Quality ({sent_val}/10)")
                except: pass
                
            scores.append({'gear': gear, 'score': score, 'reasons': reasons, 'sentiment': sentiment})
            
        scores.sort(key=lambda x: x['score'], reverse=True)
        return scores[:5]

    def recommend_monitor(self, user_prefs):
        genre = user_prefs.get('genre', 'FPS')
        candidates = GamingGear.objects.filter(type='Monitor')
        scores = []
        
        for gear in candidates:
            score = 0
            reasons = []
            if isinstance(gear.specs, str):
                try:
                    specs = json.loads(gear.specs)
                except:
                    specs = {}
            else:
                specs = gear.specs
                 
            try:
                # Handle "360" or "360Hz"
                hz_str = str(specs.get('Refresh Rate', '60')).replace('Hz','')
                hz = float(hz_str)
            except:
                hz = 60
                
            res = specs.get('Resolution', '')
            
            if genre == 'FPS':
                if hz >= 360:
                    score += 40
                    reasons.append(f"Pro-level {int(hz)}Hz motion clarity")
                elif hz >= 240:
                    score += 30
                    reasons.append(f"Competitive {int(hz)}Hz refresh rate")
                elif hz >= 144:
                    score += 10
                    
                # FPS players often prefer 1080p for frames, or 1440p OLED
                if '1080' in res:
                    score += 10
                    
            elif genre in ['MOBA', 'MMO', 'RPG']:
                # Resolution matters more
                if '1440' in res or '2160' in res:
                    score += 35
                    reasons.append(f"High Resolution ({res}) for visuals")
                elif '1080' in res:
                    score -= 10 # 1080p less desirable for RPGs
                    
                panel_tech = specs.get('Panel Tech', '')
                if 'OLED' in panel_tech or 'IPS' in panel_tech:
                    score += 20
                    reasons.append(f"Vibrant {panel_tech} colors")

            # Sentiment
            sentiment = specs.get('sentiment_score', 0)
            if sentiment:
                try:
                    sent_val = self._format_sentiment(sentiment)
                    score += min(sent_val * 2, 20)
                except: pass
                
            scores.append({'gear': gear, 'score': score, 'reasons': reasons, 'sentiment': sentiment})
            
        scores.sort(key=lambda x: x['score'], reverse=True)
        return scores[:5]
