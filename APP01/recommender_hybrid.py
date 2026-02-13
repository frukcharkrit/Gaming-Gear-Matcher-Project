import json
from .models import GamingGear

class HybridRecommender:
    def __init__(self):
        pass

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
            try:
                specs = json.loads(gear.specs)
            except:
                continue
                
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
                    score += min(float(sentiment) * 2, 30)
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
                specs = json.loads(gear_entry['gear'].specs)
                return specs.get(key, default)
            except:
                return default

        # ======================================================
        # 1. Performance (Best Spec Match) -> Index 0
        # ======================================================
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
        perf_cons.append("Premium gear may be harder to find in some regions")
        if not any('comfort' in p.lower() for p in perf_pros):
            perf_cons.append("Spec-focused — comfort and ergonomics may be secondary")

        variants['Performance'] = {
            'Mouse': mice[0] if mice else None,
            'Keyboard': keyboards[0] if keyboards else None,
            'Headset': headsets[0] if headsets else None,
            'Monitor': monitors[0] if monitors else None,
            'Chair': chairs[0] if chairs else None,
            'desc': 'Top-tier specs matched to your playstyle.',
            'analysis': perf_analysis,
            'pros': perf_pros,
            'cons': perf_cons,
            'badge': 'Best Match'
        }

        # ======================================================
        # 2. Balanced / Value -> Index 1
        # ======================================================
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
            'Mouse': mice[1] if len(mice) > 1 else (mice[0] if mice else None),
            'Keyboard': keyboards[1] if len(keyboards) > 1 else (keyboards[0] if keyboards else None),
            'Headset': headsets[1] if len(headsets) > 1 else (headsets[0] if headsets else None),
            'Monitor': monitors[1] if len(monitors) > 1 else (monitors[0] if monitors else None),
            'Chair': chairs[1] if len(chairs) > 1 else (chairs[0] if chairs else None),
            'desc': 'Great performance with alternative features.',
            'analysis': bal_analysis,
            'pros': bal_pros,
            'cons': bal_cons,
            'badge': 'Value Pick'
        }

        # ======================================================
        # 3. Pro Choice (High Sentiment/Usage)
        # ======================================================
        def get_pro_choice(candidates):
            if not candidates:
                return None
            sorted_cands = sorted(candidates, key=lambda x: float(x.get('sentiment', 0) or 0), reverse=True)
            return sorted_cands[0]

        pro_analysis = (
            "🏆 The 'Meta' setup — these are the products most loved by pro players and reviewers. "
            "Regardless of specific specs, this gear has earned its reputation through "
            "real-world performance and community trust."
        )

        pro_pros = ["Highest user satisfaction and review scores", "Battle-tested by professional players"]
        pro_cons = []

        pro_mouse = get_pro_choice(mice)
        if pro_mouse:
            sent = float(pro_mouse.get('sentiment', 0) or 0)
            if sent > 7:
                pro_pros.append(f"Mouse has exceptional review sentiment ({sent:.1f}/10)")
            elif sent > 4:
                pro_pros.append(f"Mouse has strong positive reviews ({sent:.1f}/10)")

        if pro_mouse and mice:
            if pro_mouse['gear'].gear_id != mice[0]['gear'].gear_id:
                pro_cons.append("May not be the absolute best spec match for your preferences")
            else:
                pro_pros.append("Also happens to be the best spec match — a clear winner!")

        pro_cons.append("Popular gear may have higher demand and limited stock")
        pro_cons.append("'Popular' doesn't always mean 'perfect for you' — personal fit matters")

        variants['Pro'] = {
            'Mouse': pro_mouse,
            'Keyboard': get_pro_choice(keyboards),
            'Headset': get_pro_choice(headsets),
            'Monitor': get_pro_choice(monitors),
            'Chair': get_pro_choice(chairs),
            'desc': 'Most loved by reviewers and pros.',
            'analysis': pro_analysis,
            'pros': pro_pros,
            'cons': pro_cons,
            'badge': 'Pro Choice'
        }

        return variants

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
            try:
                specs = json.loads(gear.specs)
            except:
                continue
                
            # Content-Based Logic
            length = float(specs.get('L (cm)', 0))
            if hand_size == 'Small' and length < 12.0:
                score += 20
                reasons.append("Fits Small Hands")
            elif hand_size == 'Large' and length > 12.5:
                score += 20
                reasons.append("Fits Large Hands")
            elif hand_size == 'Medium':
                score += 10 # Fits most
                
            # Grip Match
            shape = specs.get('Shape', 'Ambidextrous')
            if grip == 'Palm' and 'Ergonomic' in shape:
                score += 15
                reasons.append("Ergonomic shape for Palm Grip")
            elif grip == 'Fingertip' and length < 12.0:
                score += 15
                reasons.append("Compact for Fingertip Grip")
                
            # Genre Match (Weight & Shape)
            weight = float(specs.get('W (g)', 999))
            
            if genre == 'FPS':
                if weight < 75:
                    score += 25
                    reasons.append("Lightweight for FPS flicks")
            elif genre == 'MOBA':
                if 60 <= weight <= 90:
                    score += 20
                    reasons.append("Balanced weight for MOBA")
                elif weight < 60:
                     # Penalize ultra-light for MOBA (preference for control)
                    score -= 5
            elif genre == 'MMO' or genre == 'RPG':
                # MMO players often prefer heavier, more stable mice with more buttons (which adds weight)
                if weight > 80:
                    score += 25
                    reasons.append("Stable weight for MMO/RPG")
                elif weight < 60:
                    # Penalize ultra-light heavily as they lack buttons/stability
                    score -= 20
                
                if 'Ergonomic' in specs.get('Shape', ''):
                    score += 15
                    reasons.append("Comfortable for long raids")

            # NLP Sentiment Boost (Capped to prevent overpowering)
            sentiment = specs.get('sentiment_score', 0)
            if sentiment:
                try:
                    sent_val = float(sentiment)
                    # Max boost reduced from 30 to 20 to let Genre logic win
                    boost = min(sent_val * 2, 20) 
                    score += boost
                    if sent_val > 5:
                        reasons.append("High reviewer sentiment")
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
            try:
                specs = json.loads(gear.specs)
            except:
                continue
            
            form_factor = specs.get('Form Factor', '')
            
            # Genre Logic
            if genre == 'FPS':
                if any(x in form_factor for x in ['60%', '65%', '75%', 'TKL']):
                    score += 30
                    reasons.append(f"Compact {form_factor} for more mouse space")
            elif genre == 'MOBA':
                if 'TKL' in form_factor:
                    score += 20
                    reasons.append("TKL balance for MOBA")
            elif genre == 'MMO':
                if 'Full Size' in form_factor:
                    score += 30
                    reasons.append("Full Size keys for MMO macros")
            
            # Sentiment
            sentiment = specs.get('sentiment_score', 0)
            if sentiment:
                try:
                    score += min(float(sentiment) * 2, 30)
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
            try:
                specs = json.loads(gear.specs)
            except:
                continue
                
            audio_type = specs.get('Audio Output', '')
            
            if genre == 'FPS':
                # Prefer Surround or good imaging 
                score += 10 
                reasons.append("Optimized for footsteps")
            
            # Sentiment is king for headsets
            sentiment = specs.get('sentiment_score', 0)
            if sentiment:
                try:
                    score += min(float(sentiment) * 3, 40)
                    if float(sentiment) > 5:
                        reasons.append("Excellent Sound/Comfort reviews")
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
            try:
                specs = json.loads(gear.specs)
            except:
                 continue
                 
            try:
                hz = float(specs.get('Refresh Rate', '60').replace('Hz',''))
            except:
                hz = 60
                
            res = specs.get('Resolution', '')
            
            if genre == 'FPS':
                if hz >= 240:
                    score += 40
                    reasons.append(f"Pro-level {hz}Hz Refresh Rate")
                elif hz >= 144:
                    score += 20
                
                if 'TN' in specs.get('Panel Tech', ''):
                    score += 5 
                    
            elif genre in ['MOBA', 'MMO']:
                if '1440' in res or '2160' in res:
                    score += 30
                    reasons.append("High Resolution for Visuals")
                if 'IPS' in specs.get('Panel Tech', '') or 'OLED' in specs.get('Panel Tech', ''):
                    score += 20
                    reasons.append("Vibrant Panel Colors")

            # Sentiment
            sentiment = specs.get('sentiment_score', 0)
            if sentiment:
                try:
                    score += min(float(sentiment) * 2, 30)
                except: pass
                
            scores.append({'gear': gear, 'score': score, 'reasons': reasons, 'sentiment': sentiment})
            
        scores.sort(key=lambda x: x['score'], reverse=True)
        return scores[:5]
