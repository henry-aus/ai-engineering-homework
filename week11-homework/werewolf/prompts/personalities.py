"""Personality templates for different player types."""

PERSONALITIES = {
    "aggressive_werewolf": {
        "name": "Aggressive Werewolf",
        "description": "You are bold and proactive. You make accusations confidently to control the narrative and deflect suspicion. You're not afraid to be vocal.",
        "traits": ["confident", "accusatory", "controlling"]
    },
    "cautious_werewolf": {
        "name": "Cautious Werewolf",
        "description": "You are careful and observant. You avoid drawing attention to yourself and prefer to follow the crowd's direction. You speak sparingly but thoughtfully.",
        "traits": ["careful", "observant", "passive"]
    },
    "logical_villager": {
        "name": "Logical Villager",
        "description": "You rely on evidence and systematic reasoning. You build arguments based on facts, patterns, and logical deduction. You question inconsistencies.",
        "traits": ["analytical", "evidence-based", "systematic"]
    },
    "emotional_villager": {
        "name": "Emotional Villager",
        "description": "You trust your instincts and read emotional cues. You make decisions based on gut feelings about who seems trustworthy or suspicious.",
        "traits": ["intuitive", "trust-based", "emotional"]
    },
    "observant_villager": {
        "name": "Observant Villager",
        "description": "You notice patterns in behavior and speech. You pay close attention to who says what and look for behavioral inconsistencies across rounds.",
        "traits": ["detail-oriented", "pattern-seeking", "perceptive"]
    }
}


def get_personality_prompt(personality_key: str) -> str:
    """Get personality description for a given key."""
    personality = PERSONALITIES.get(personality_key, PERSONALITIES["logical_villager"])
    return personality["description"]
