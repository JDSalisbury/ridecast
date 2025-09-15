"""Enhanced fun facts storage and management system."""

import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, asdict
import random


@dataclass
class FunFact:
    """Represents a single fun fact with metadata."""
    content: str
    content_hash: str
    user_name: str
    date_used: str
    category: str = "general"
    
    @classmethod
    def create(cls, content: str, user_name: str, category: str = "general") -> 'FunFact':
        """Create a new FunFact with auto-generated hash and current date."""
        content_hash = hashlib.md5(content.lower().strip().encode()).hexdigest()
        date_used = datetime.now().isoformat()
        return cls(content, content_hash, user_name, date_used, category)


class FunFactsDB:
    """Manages fun facts storage with intelligent deduplication."""
    
    def __init__(self, db_path: str = "fun_facts_db.json"):
        self.script_dir = Path(__file__).resolve().parent
        self.db_path = self.script_dir / db_path
        self.facts_by_user: Dict[str, List[FunFact]] = {}
        self.load_database()
        
        # Categories for diverse fact generation
        self.categories = [
            "quotes", "safety_tips", "motorcycle_history", 
            "technical_facts", "riding_tips", "inspiration"
        ]
    
    def load_database(self) -> None:
        """Load existing database or create empty one."""
        if self.db_path.exists():
            try:
                with open(self.db_path, 'r') as f:
                    data = json.load(f)
                    
                # Convert dict back to FunFact objects
                for user_name, facts_data in data.items():
                    self.facts_by_user[user_name] = [
                        FunFact(**fact_data) for fact_data in facts_data
                    ]
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Error loading fun facts database: {e}. Starting fresh.")
                self.facts_by_user = {}
        else:
            self.facts_by_user = {}
    
    def save_database(self) -> None:
        """Save current database to disk."""
        # Convert FunFact objects to dicts for JSON serialization
        data = {
            user_name: [asdict(fact) for fact in facts]
            for user_name, facts in self.facts_by_user.items()
        }
        
        with open(self.db_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def add_fun_fact(self, content: str, user_name: str, category: str = "general") -> bool:
        """Add a new fun fact if it's not a duplicate. Returns True if added."""
        fact = FunFact.create(content, user_name, category)
        
        # Check for duplicates
        if self.is_duplicate(fact.content_hash, user_name):
            return False
        
        # Initialize user list if needed
        if user_name not in self.facts_by_user:
            self.facts_by_user[user_name] = []
        
        # Add fact and save
        self.facts_by_user[user_name].append(fact)
        self.save_database()
        return True
    
    def is_duplicate(self, content_hash: str, user_name: str, recent_days: int = 30) -> bool:
        """Check if content hash exists for user within recent days."""
        if user_name not in self.facts_by_user:
            return False
        
        cutoff_date = datetime.now() - timedelta(days=recent_days)
        
        for fact in self.facts_by_user[user_name]:
            # Check if this hash was used recently
            if fact.content_hash == content_hash:
                fact_date = datetime.fromisoformat(fact.date_used)
                if fact_date > cutoff_date:
                    return True
        
        return False
    
    def get_recent_facts_summary(self, user_name: str, limit: int = 10) -> str:
        """Get a summary of recent facts for context (not the full facts)."""
        if user_name not in self.facts_by_user:
            return "No previous facts found."
        
        # Get recent facts
        recent_facts = sorted(
            self.facts_by_user[user_name],
            key=lambda x: x.date_used,
            reverse=True
        )[:limit]
        
        if not recent_facts:
            return "No previous facts found."
        
        # Create summary with themes/categories instead of full content
        categories_used = [fact.category for fact in recent_facts]
        category_counts = {}
        for cat in categories_used:
            category_counts[cat] = category_counts.get(cat, 0) + 1
        
        summary_lines = [
            f"Recent fact categories used: {', '.join(category_counts.keys())}",
            f"Total recent facts: {len(recent_facts)}"
        ]
        
        # Add some key phrases to avoid (extracted from content)
        key_phrases = []
        for fact in recent_facts[:5]:  # Only check last 5 for key phrases
            content = fact.content.lower()
            if "valentino rossi" in content:
                key_phrases.append("Valentino Rossi quotes")
            elif "guy martin" in content:
                key_phrases.append("Guy Martin quotes")
            elif "evel knievel" in content:
                key_phrases.append("Evel Knievel quotes")
            elif "hunter s. thompson" in content:
                key_phrases.append("Hunter S. Thompson quotes")
        
        if key_phrases:
            summary_lines.append(f"Recently used personalities: {', '.join(set(key_phrases))}")
        
        return " | ".join(summary_lines)
    
    def get_unused_category(self, user_name: str, recent_days: int = 7) -> str:
        """Get a category that hasn't been used recently."""
        if user_name not in self.facts_by_user:
            return random.choice(self.categories)
        
        cutoff_date = datetime.now() - timedelta(days=recent_days)
        
        # Get recently used categories
        recent_categories = set()
        for fact in self.facts_by_user[user_name]:
            fact_date = datetime.fromisoformat(fact.date_used)
            if fact_date > cutoff_date:
                recent_categories.add(fact.category)
        
        # Return a category not used recently
        unused_categories = [cat for cat in self.categories if cat not in recent_categories]
        
        if unused_categories:
            return random.choice(unused_categories)
        else:
            # All categories used recently, pick least used
            category_counts = {}
            for fact in self.facts_by_user[user_name]:
                fact_date = datetime.fromisoformat(fact.date_used)
                if fact_date > cutoff_date:
                    cat = fact.category
                    category_counts[cat] = category_counts.get(cat, 0) + 1
            
            # Return category with minimum count
            if category_counts:
                return min(category_counts.items(), key=lambda x: x[1])[0]
            else:
                return random.choice(self.categories)
    
    def cleanup_old_facts(self, days_to_keep: int = 90) -> int:
        """Remove facts older than specified days. Returns count removed."""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        removed_count = 0
        
        for user_name in self.facts_by_user:
            original_count = len(self.facts_by_user[user_name])
            self.facts_by_user[user_name] = [
                fact for fact in self.facts_by_user[user_name]
                if datetime.fromisoformat(fact.date_used) > cutoff_date
            ]
            removed_count += original_count - len(self.facts_by_user[user_name])
        
        if removed_count > 0:
            self.save_database()
        
        return removed_count
    
    def get_stats(self, user_name: str) -> Dict[str, int]:
        """Get statistics for a user's fun facts."""
        if user_name not in self.facts_by_user:
            return {"total_facts": 0, "unique_categories": 0}
        
        facts = self.facts_by_user[user_name]
        categories = set(fact.category for fact in facts)
        
        return {
            "total_facts": len(facts),
            "unique_categories": len(categories),
            "facts_last_30_days": len([
                f for f in facts 
                if datetime.fromisoformat(f.date_used) > datetime.now() - timedelta(days=30)
            ])
        }