import random

ADJECTIVES = [
    'Quiet', 'Bold', 'Calm', 'Swift', 'Bright', 'Sharp', 'Wry',
    'Keen', 'Fierce', 'Nimble', 'Crisp', 'Iron', 'Steady', 'Sly'
]

NOUNS = [
    'Storm', 'Falcon', 'Ember', 'Harbor', 'Signal', 'Echo', 'Anchor',
    'Blaze', 'Spark', 'Wolf', 'Tide', 'Frost', 'River', 'Flare'
]

def generate_alias() -> str:
    """
    Generates a random alias containing an adjective, a noun, and a 2-digit number.
    Ensures the total length is <= 14 characters.
    """
    while True:
        adj = random.choice(ADJECTIVES)
        noun = random.choice(NOUNS)
        num = random.randint(10, 99)
        alias = f"{adj}{noun}{num}"
        if len(alias) <= 14:
            return alias
