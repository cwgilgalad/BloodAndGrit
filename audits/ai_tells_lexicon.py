"""Word lists and human baselines for audit_ai_tells.py.

Kept apart from the audit so the audit stays readable. Nothing here decides anything: the audit
counts these per thousand words and prints the rate beside the same count taken from writing
people did without a model. Each list says where it came from.
"""

# ---- Antislop ------------------------------------------------------------------------------------
# Paech et al., "Antislop", ICLR 2026, arXiv:2510.15061. The list is theirs, from
# github.com/sam-paech/antislop-sampler (slop_phrase_prob_adjustments.json, Apache License 2.0).
# They found some of these running over 1,000 times more often in model output than in human
# writing. Trimmed by hand for a western: dialogue tags ("nodded", "murmured"), plain adverbs, and
# words the books need ("depths", "unease", "peculiar", "shall") are left out.
ANTISLOP = [
    "symphony", "testament to", "kaleidoscope", "delve", "delves", "delving", "delved", "tapestry",
    "tapestries", "barely above a whisper", "barely a whisper", "orchestra of", "dance of",
    "maybe, just maybe", "perhaps, just perhaps", "was only just beginning", "bustling",
    "labyrinthine", "shivers down", "shivers up", "shiver down", "shiver up", "ministrations",
    "transcended", "thrummed", "bioluminescent", "moth to a flame", "eyes glinted", "camaraderie",
    "humble abode", "cold and calculating", "eyes never leaving", "palpable", "chuckles darkly",
    "they would face it together", "with a mixture of", "cacophony", "bore silent witness",
    "practiced ease", "ethereal", "life would never be the same", "for what seemed like an eternity",
    "little did he know", "threatens to consume", "meticulous", "meticulously", "complexities",
    "tailored", "underpins", "ever-evolving", "embark", "embarked", "daunting", "unleash",
    "reverberate", "reverberated", "revolutionize", "gossamer", "enigma", "indelible", "rivulets of",
    "reckless abandon", "newfound", "amidst", "serendipity", "serendipitous", "interconnectedness",
    "unbeknownst", "wafted", "etched", "intricate", "intricacies", "unwavering", "resonated", "solace",
    "awestruck", "wonderment", "quietude", "ominously", "precariously", "pulsated", "emboldened",
    "adorning", "brimming", "insurmountable", "unforeseen", "perseverance", "resilience",
    "captivating", "captivated", "empathetically", "transformative", "blossomed", "intertwine",
    "intertwined", "shimmered",
]

# Character and place names from the same list. A name here is not wrong, but a reader who has
# seen a lot of model-written fiction will notice it.
SLOP_NAMES_ANTISLOP = [
    "Elara", "Elysia", "Numeria", "Lyra", "Eira", "Eldoria", "Atheria", "Eluned", "Oakhaven",
    "Whisperwood", "Zephyria", "Elian", "Elias", "Elianore", "Aria", "Eitan", "Kael", "Jaxon",
    "Ravenswood", "Moonwhisper", "Lykos", "Seabrook", "Abernathy", "Eadric", "Aldric", "Maplewood",
    "Greenhaven", "Freydis", "Melodia", "Élise", "Claudette", "Marianne", "Amara", "Lila",
]

# Names that keep turning up in model-written fiction by writers' own reports rather than by any one
# study. Weaker evidence, so these are listed apart and only ever reported.
SLOP_NAMES_REPORTED = [
    "Silas", "Thorne", "Vance", "Aurelia", "Seraphina", "Isolde", "Quill", "Blackwood", "Hawthorne",
    "Ashford", "Whitmore", "Sterling", "Mercer", "Calloway", "Voss", "Kestrel", "Wren", "Sable",
]

# ---- Wikipedia's catalogue -----------------------------------------------------------------------
# "Wikipedia:Signs of AI writing", re-read 2026-09-16. Phrases from its sections on significance,
# promotional tone, superficial analysis and vague connection that audit_ai_tells.SOFT_WORDS did not
# already carry.
WIKI_PHRASES = [
    "enduring", "garner", "garnered", "interplay", "bolstered", "deep dive", "focal point",
    "indelible mark", "deeply rooted", "evolving landscape", "setting the stage for",
    "represents a shift", "marks a shift", "key turning point", "reflects broader", "symbolizing",
    "contributing to", "in the heart of", "renowned", "diverse array", "natural beauty",
    "valuable insights", "resonate with", "in connection with", "in association with",
    "is associated with", "encompassing", "cultivating",
]

# ---- Claude's own habits -------------------------------------------------------------------------
# Most of this project's prose was drafted with Claude, and Claude has tics of its own that the
# general lists above do not catch. These were collected from this repository's text on 2026-09-16.
# Each is an ordinary phrase once; the rate is the tell. Regular expressions, matched lowercase.
CLAUDE_REGISTER = [
    r"\bthe whole (?:of (?:it|the \w+|its \w+|their \w+|his \w+|her \w+)|point|shape|trick|horror|"
    r"secret|reason)\b",
    r"\bload-bearing\b",
    r"\bworth (?:keeping|knowing|noting|remembering|not re-deriving|not repeating|saying)\b",
    r"\b(?:that|this|which) is (?:the|exactly the) (?:point|tell|trick|job|difference)\b",
    r"\bthe tell\b",
    r"\bon purpose\b",
    r"\bdeliberately\b",
    r"\bquietly\b",
    r"\bgenuinely\b",
    r"\bin practice\b",
    r"\bit turns out\b",
    r"\bwhich is exactly\b",
    r"\bnone of (?:which|this|that)\b",
    r"\bdoing (?:the|a lot of|real) work\b",
    r"\bearns? (?:its|their|his|her) (?:place|keep)\b",
    r"\breads (?:as|like)\b",
    r"\bsits (?:beside|inside|next to|on top of|under|behind)\b",
    r"\bwhere it lands\b",
    r"\bthe shape of\b",
    r"\bthe honest (?:answer|version|reading)\b",
    r"\bin the same breath\b",
    r"\bnot a bug\b",
    r"\b(?:small|quiet) (?:grace|mercy|cruelty)\b",
]

# ---- StoryScope ----------------------------------------------------------------------------------
# "StoryScope: Investigating idiosyncrasies in AI fiction", arXiv:2604.03136 (2026). Model-written
# fiction used smell imagery in 82% of stories against 57% of human ones, showed emotion through the
# body in 81% against 38%, and stated its theme outright in 77% against 52%. These lists are this
# audit's stand-ins for those three findings; the study coded whole stories by hand.
SMELL = [
    r"\bsmell(?:s|ed|ing)?\b", r"\bsmelt\b", r"\bscent(?:s|ed)?\b", r"\bstink(?:s|ing)?\b",
    r"\bstank\b", r"\bstench\b", r"\breek(?:s|ed|ing)?\b", r"\bodou?rs?\b", r"\baroma\b",
    r"\bwhiff\b",
]
BODY_EMOTION = [
    r"\b(?:chest|throat|jaw|gut|stomach) (?:tightened|clenched|knotted|dropped|turned|lurched)\b",
    r"\bheart (?:pounded|hammered|raced|thudded|skipped|lurched)\b",
    r"\bpulse (?:quickened|raced|jumped)\b",
    r"\bbreath (?:caught|hitched)\b",
    r"\b(?:a )?chill (?:ran|crept|went) (?:down|up|through)\b",
    r"\bshivers? (?:ran )?(?:down|up) (?:his|her|their|my|your) spine\b",
    r"\bblood ran cold\b",
    r"\bskin crawled\b",
    r"\bhairs? on the back of (?:his|her|their|my|your) neck\b",
    r"\bknuckles (?:went|turned) white\b",
    r"\ba lump in (?:his|her|their|my|your) throat\b",
    r"\bbile rose\b",
]
THEME_STATEMENT = [
    r"\bthis is a story about\b",
    r"\bthe story is (?:really )?about\b",
    r"\bthe (?:lesson|moral) (?:here |of (?:it|this|the story) )?is\b",
    r"\bwhat (?:it|this) (?:all )?(?:really )?means is\b",
    r"\bat (?:its|the) heart,",
    r"\bis really about\b",
    r"\bwhat (?:truly|really) matters is\b",
]

# ---- plain English -------------------------------------------------------------------------------
# Function words, for lexical density (the share of words that carry content). arXiv:2606.04177
# found lexical richness the strongest single signal that holds across domains and models.
FUNCTION_WORDS = set("""
a about above across after afterwards again against all almost alone along already also although
always am among amongst an and another any anybody anyhow anyone anything anyway anywhere are around
as at be became because become becomes been before beforehand behind being below beside besides
between beyond both but by can cannot could did do does doing done down during each either else
elsewhere enough even ever every everybody everyone everything everywhere except few for from
further had has have having he hence her here hereafter hereby herein hers herself him himself his
how however i if in indeed into is it its itself just last latter least less many may me meanwhile
might mine more moreover most mostly much must my myself neither never nevertheless next no nobody
none noone nor not nothing now nowhere of off often on once one only onto or other others otherwise
our ours ourselves out over own per perhaps rather same seem seemed seeming seems several shall she
should since so some somebody somehow someone something sometime sometimes somewhere still such than
that the their theirs them themselves then thence there thereafter thereby therefore therein these
they this those though through throughout thru thus to together too toward towards under until up
upon us very via was we well were what whatever when whence whenever where whereafter whereas whereby
wherein whereupon wherever whether which while whither who whoever whole whom whose why will with
within without would yet you your yours yourself yourselves
""".split())

# Words ending in -ing that are nouns, so a comma before them is not a participial clause.
ING_NOUNS = set("""
thing nothing something anything everything morning evening building ceiling clothing feeling king
ring spring string wing sling swing sting bring during offering blessing darling farthing shilling
wedding bedding pudding lightning warning meaning beginning ending wording sibling duckling
gelding stocking wing lodging dwelling reckoning working workings bearing bearings footing
opening landing crossing clearing hanging killing shooting casting
including according regarding concerning considering excluding following pending
""".split())

# Stops for the repeated-head check: a head made only of these is grammar, not rhetoric.
HEAD_STOPS = set("""
a an the of in on at to for by with from as and or but nor yet so that this these those it its
is was are were be been am he she they we you i his her their our your my me him them us
""".split())

# ---- human baselines -----------------------------------------------------------------------------
# The same measures, run with this audit's own code over writing done without a model:
#   srd5      the 5e System Reference Document (Wizards of the Coast, 2016), a rules text. Markdown
#             from github.com/BTMorton/dnd-5e-srd, 5esrd.md.
#   virginian Owen Wister, The Virginian (1902), Project Gutenberg #1298. Western prose.
# Recompute with:  python audits/audit_ai_tells.py --calibrate FILE
# Filled in by the calibration run of 2026-09-16; see BASELINES in audit_ai_tells.py.
