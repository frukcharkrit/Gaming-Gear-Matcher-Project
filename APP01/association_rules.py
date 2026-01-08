"""
Association Rule Mining Module for Gaming Gear Matcher

This module implements Market Basket Analysis using the Apriori algorithm
to recommend gaming gear based on patterns in user preset data.
"""

import pandas as pd
from typing import List, Dict, Optional, Tuple
from django.core.cache import cache
from django.db.models import Q
from mlxtend.frequent_patterns import apriori, association_rules
from mlxtend.preprocessing import TransactionEncoder
import logging

from APP01.models import Preset, PresetGear, GamingGear

logger = logging.getLogger(__name__)


class AssociationRuleMiner:
    """
    Association Rule Mining engine for gear recommendations.
    
    Uses Apriori algorithm to find frequent itemsets and generate 
    association rules from user preset data.
    """
    
    CACHE_KEY_PREFIX = "association_rules"
    CACHE_TIMEOUT = 60 * 60 * 24  # 24 hours
    
    def __init__(self, min_support: float = 0.05, min_confidence: float = 0.3, min_lift: float = 1.0):
        """
        Initialize the association rule miner.
        
        Args:
            min_support: Minimum support threshold (0-1)
            min_confidence: Minimum confidence threshold (0-1)
            min_lift: Minimum lift threshold (typically >= 1.0)
        """
        self.min_support = min_support
        self.min_confidence = min_confidence
        self.min_lift = min_lift
    
    def build_transaction_data(self) -> pd.DataFrame:
        """
        Build transaction data from Preset model.
        
        Returns:
            DataFrame with transaction data in format suitable for Apriori
        """
        logger.info("Building transaction data from presets...")
        
        # Fetch all presets with their gears
        presets = Preset.objects.prefetch_related('presetgear_set__gear').all()
        
        if not presets.exists():
            logger.warning("No presets found in database")
            return pd.DataFrame()
        
        # Build transactions: each preset is a transaction containing gear IDs
        transactions = []
        for preset in presets:
            gear_ids = [
                str(pg.gear.gear_id) 
                for pg in preset.presetgear_set.all() 
                if pg.gear
            ]
            if gear_ids:  # Only add non-empty transactions
                transactions.append(gear_ids)
        
        if not transactions:
            logger.warning("No valid transactions found")
            return pd.DataFrame()
        
        # Convert to one-hot encoded DataFrame
        te = TransactionEncoder()
        te_ary = te.fit(transactions).transform(transactions)
        df = pd.DataFrame(te_ary, columns=te.columns_)
        
        logger.info(f"Built {len(df)} transactions with {len(df.columns)} unique gears")
        return df
    
    def mine_association_rules(self, transaction_df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """
        Mine association rules using Apriori algorithm.
        
        Args:
            transaction_df: Pre-built transaction DataFrame. If None, will build from database.
            
        Returns:
            DataFrame containing association rules with metrics (support, confidence, lift)
        """
        if transaction_df is None or transaction_df.empty:
            transaction_df = self.build_transaction_data()
        
        if transaction_df.empty:
            logger.warning("Empty transaction data, cannot mine rules")
            return pd.DataFrame()
        
        try:
            # Find frequent itemsets
            logger.info(f"Mining frequent itemsets with min_support={self.min_support}...")
            frequent_itemsets = apriori(
                transaction_df, 
                min_support=self.min_support, 
                use_colnames=True
            )
            
            if frequent_itemsets.empty:
                logger.warning("No frequent itemsets found. Try lowering min_support.")
                return pd.DataFrame()
            
            logger.info(f"Found {len(frequent_itemsets)} frequent itemsets")
            
            # Generate association rules
            logger.info(f"Generating rules with min_confidence={self.min_confidence}...")
            rules = association_rules(
                frequent_itemsets, 
                metric="confidence",
                min_threshold=self.min_confidence
            )
            
            if rules.empty:
                logger.warning("No rules found. Try lowering min_confidence.")
                return pd.DataFrame()
            
            # Filter by lift
            rules = rules[rules['lift'] >= self.min_lift]
            
            # Sort by confidence * lift for quality
            rules['score'] = rules['confidence'] * rules['lift']
            rules = rules.sort_values('score', ascending=False)
            
            logger.info(f"Generated {len(rules)} association rules")
            return rules
            
        except Exception as e:
            logger.error(f"Error mining association rules: {e}", exc_info=True)
            return pd.DataFrame()
    
    def get_recommendations(
        self, 
        gear_ids: List[int], 
        top_n: int = 5,
        exclude_types: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        Get gear recommendations based on selected gears using association rules.
        
        Args:
            gear_ids: List of gear IDs already selected
            top_n: Number of recommendations to return
            exclude_types: Gear types to exclude (e.g., types already in preset)
            
        Returns:
            List of dicts with keys: gear_id, gear, confidence, lift, score
        """
        # Try to get cached rules
        cache_key = f"{self.CACHE_KEY_PREFIX}_rules"
        rules = cache.get(cache_key)
        
        if rules is None or rules.empty:
            # Mine rules and cache them
            rules = self.mine_association_rules()
            if not rules.empty:
                cache.set(cache_key, rules, self.CACHE_TIMEOUT)
        
        if rules.empty:
            logger.warning("No association rules available for recommendations")
            return []
        
        # Convert gear_ids to string set (as stored in rules)
        selected_set = set(str(gid) for gid in gear_ids)
        
        # Find rules where antecedents match selected gears
        recommendations = []
        
        for _, rule in rules.iterrows():
            antecedents = rule['antecedents']
            consequents = rule['consequents']
            
            # Check if selected gears contain the antecedents
            if antecedents.issubset(selected_set):
                # Add consequents that are not already selected
                for gear_id_str in consequents:
                    if gear_id_str not in selected_set:
                        try:
                            gear_id = int(gear_id_str)
                            gear = GamingGear.objects.get(gear_id=gear_id)
                            
                            # Filter by type if needed
                            if exclude_types and gear.type in exclude_types:
                                continue
                            
                            recommendations.append({
                                'gear_id': gear_id,
                                'gear': gear,
                                'confidence': float(rule['confidence']),
                                'lift': float(rule['lift']),
                                'score': float(rule['score'])
                            })
                        except (GamingGear.DoesNotExist, ValueError):
                            continue
        
        # Remove duplicates (keep highest score)
        seen = {}
        for rec in recommendations:
            gid = rec['gear_id']
            if gid not in seen or rec['score'] > seen[gid]['score']:
                seen[gid] = rec
        
        # Sort by score and return top N
        final_recs = sorted(seen.values(), key=lambda x: x['score'], reverse=True)
        return final_recs[:top_n]
    
    def refresh_cache(self) -> bool:
        """
        Refresh the cached association rules.
        
        Returns:
            True if successful, False otherwise
        """
        logger.info("Refreshing association rules cache...")
        try:
            rules = self.mine_association_rules()
            if not rules.empty:
                cache_key = f"{self.CACHE_KEY_PREFIX}_rules"
                cache.set(cache_key, rules, self.CACHE_TIMEOUT)
                logger.info("Successfully refreshed association rules cache")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to refresh cache: {e}", exc_info=True)
            return False


# Global instance
_miner_instance = None

def get_miner() -> AssociationRuleMiner:
    """Get singleton instance of AssociationRuleMiner"""
    global _miner_instance
    if _miner_instance is None:
        _miner_instance = AssociationRuleMiner()
    return _miner_instance


def get_gear_recommendations(gear_ids: List[int], top_n: int = 5, exclude_types: Optional[List[str]] = None) -> List[Dict]:
    """
    Convenience function to get gear recommendations.
    
    Args:
        gear_ids: List of gear IDs already selected
        top_n: Number of recommendations to return
        exclude_types: Gear types to exclude
        
    Returns:
        List of recommendation dicts
    """
    miner = get_miner()
    return miner.get_recommendations(gear_ids, top_n, exclude_types)


def refresh_association_rules() -> bool:
    """
    Convenience function to refresh association rules cache.
    
    Returns:
        True if successful
    """
    miner = get_miner()
    return miner.refresh_cache()
