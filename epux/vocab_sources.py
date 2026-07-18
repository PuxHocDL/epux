"""Difficulty anchors and authentic source passages for vocabulary generation.

Two independent grounding tools for ``LLMClient.generate_vocab`` / ``suggest_topics``,
both meant to stop the LLM from defaulting to generic, already-known words:

* ``OXFORD_B2_WORDS`` / ``OXFORD_C1_WORDS`` — the expanded tier of the Oxford 5000
  (word 3001-5000), i.e. everything ABOVE the basic Oxford 3000 core. Verbatim word
  list transcribed from Oxford University Press's own free public PDF, published
  specifically for teachers/learners to reuse:
  https://www.oxfordlearnersdictionaries.com/external/pdf/wordlists/oxford-3000-5000/The_Oxford_5000_by_CEFR_level.pdf
  Sampled into prompts as a concrete "this rarity tier or harder" anchor.
* ``TOO_EASY_WORDS`` — a small hand-written blocklist of the specific words LLMs
  reach for by default (good/bad/big/important/problem/...). Not sourced from any
  list, just the obvious over-suggested set.
* ``PASSAGES`` — short extracts on classic IELTS Reading topic domains (environment,
  health, technology, archaeology, psychology, society...), adapted from Wikipedia
  article introductions (CC BY-SA 4.0, attribution below each entry) so the LLM can
  extract vocabulary that actually occurs in authentic academic-register text
  instead of inventing example sentences from scratch. Cambridge's own IELTS
  Reading passages are themselves adaptations of real magazine/encyclopedia
  articles, so this mirrors the genuine register without reproducing any
  copyrighted, commercially-sold test material (see the 2026-07-18 discussion
  with the user: Cambridge IELTS books are not freely licensed, so their
  passages are intentionally NOT stored here).
"""

from __future__ import annotations

import random
from typing import Any

# --------------------------------------------------------- Oxford 5000 (B2, C1)
# © Oxford University Press. "The Oxford 5000 by CEFR level" — free PDF, retrieved
# 2026-07-18. Only the B2 and C1 bands are kept (the harder half of the list); the
# Oxford 3000 (A1-B1 core, already assumed known) is intentionally not included.

OXFORD_B2_WORDS: list[str] = [
    "absorb", "abstract", "accent", "accidentally", "accommodate", "accomplish",
    "accountant", "accuracy", "accurately", "acid", "activate", "addiction",
    "additionally", "adequate", "adequately", "adjust", "affordable", "agriculture",
    "alien", "alongside", "altogether", "ambulance", "amusing", "analyst",
    "ancestor", "animation", "annually", "anticipate", "anxiety", "apology",
    "applicant", "appropriately", "arrow", "artwork", "aside", "asset", "assign",
    "assistance", "assumption", "assure", "astonishing", "attachment", "auction",
    "audio", "automatic", "automatically", "awareness", "awkward", "badge",
    "balanced", "ballet", "balloon", "barely", "bargain", "basement", "basket",
    "beneficial", "beside", "besides", "bias", "bid", "biological", "blanket",
    "blow", "bold", "bombing", "booking", "boost", "bound", "brick", "briefly",
    "broadcaster", "broadly", "bug", "cabin", "canal", "candle", "carbon",
    "casual", "cave", "certainty", "certificate", "challenging", "championship",
    "charming", "chase", "cheek", "cheer", "choir", "chop", "circuit",
    "civilization", "clarify", "classify", "clerk", "cliff", "clinic", "clip",
    "coincidence", "collector", "colony", "colourful", "comic", "commander",
    "comparative", "completion", "compose", "composer", "compound",
    "comprehensive", "comprise", "compulsory", "concrete", "confess",
    "confusion", "consequently", "conservation", "considerable", "considerably",
    "consistently", "conspiracy", "consult", "consultant", "consumption",
    "controversial", "controversy", "convenience", "convention", "conventional",
    "convey", "convincing", "cope", "corporation", "corridor", "counter",
    "coverage", "crack", "craft", "creativity", "critically", "cruise", "cue",
    "curious", "curriculum", "cute", "dairy", "dare", "darkness", "database",
    "deadline", "deadly", "dealer", "deck", "defender", "delete", "democracy",
    "democratic", "demonstration", "depart", "dependent", "deposit",
    "depression", "derive", "desperately", "destruction", "determination",
    "devote", "differ", "disability", "disabled", "disagreement", "disappoint",
    "disappointment", "discourage", "disorder", "distant", "distinct",
    "distinguish", "distract", "disturb", "dive", "diverse", "diversity",
    "divorce", "dominant", "donation", "dot", "downtown", "dramatically",
    "drought", "dull", "dump", "duration", "dynamic", "economics", "economist",
    "editorial", "efficiently", "elbow", "electronics", "elegant", "elementary",
    "eliminate", "embrace", "emission", "emotionally", "empire", "enjoyable",
    "entertaining", "entrepreneur", "envelope", "equip", "equivalent", "era",
    "erupt", "essentially", "ethic", "ethnic", "evaluation", "evident",
    "evolution", "evolve", "exceed", "exception", "excessive", "exclude",
    "exhibit", "exit", "exotic", "expansion", "expertise", "exploit",
    "exposure", "extension", "extensive", "extensively", "extract", "fabric",
    "fabulous", "failed", "fake", "fame", "fantasy", "fare", "federal", "fever",
    "firefighter", "firework", "firm", "firmly", "flavour", "fond", "fool",
    "forbid", "forecast", "format", "formation", "formerly", "fortunate",
    "forum", "fossil", "foundation", "founder", "fraction", "fragment",
    "framework", "fraud", "freely", "frequent", "fulfil", "full-time",
    "fundamentally", "furious", "gaming", "gender", "gene", "genetic", "genius",
    "genuine", "genuinely", "gesture", "gig", "globalization", "globe",
    "golden", "goodness", "gorgeous", "governor", "graphic", "graphics",
    "greatly", "greenhouse", "grocery", "guideline", "habitat", "harbour",
    "headquarters", "heal", "healthcare", "helmet", "hence", "herb", "hidden",
    "highway", "hilarious", "historian", "homeless", "honesty", "hook",
    "hopefully", "hunger", "hypothesis", "icon", "identical", "illusion",
    "immigration", "immune", "implement", "implication", "incentive",
    "incorporate", "incorrect", "independence", "index", "indication",
    "inevitable", "inevitably", "infer", "inflation", "infrastructure",
    "inhabitant", "inherit", "innovation", "innovative", "input", "insert",
    "inspector", "installation", "instant", "instantly", "integrate",
    "intellectual", "interact", "interaction", "interpretation", "interval",
    "invade", "invasion", "investor", "isolate", "isolated", "jail", "jet",
    "joint", "journalism", "jury", "ladder", "landing", "lane", "lately",
    "leaflet", "legend", "lens", "lifetime", "lighting", "likewise",
    "limitation", "literally", "literary", "litre", "litter", "logo",
    "lottery", "loyal", "lyric", "magnificent", "make-up", "manufacture",
    "manufacturing", "marathon", "margin", "marker", "martial", "mate",
    "mayor", "mechanic", "mechanical", "mechanism", "medal", "medication",
    "membership", "memorable", "metaphor", "miner", "miserable", "mode",
    "modest", "monster", "monthly", "monument", "moreover", "mortgage",
    "mosque", "motion", "motivate", "motivation", "moving", "myth", "naked",
    "nasty", "navigation", "nearby", "necessity", "negotiate", "negotiation",
    "neutral", "newly", "norm", "notebook", "novelist", "nowadays", "nursing",
    "nutrition", "obesity", "observer", "obstacle", "occupation", "occupy",
    "offender", "ongoing", "openly", "opera", "operator", "optimistic",
    "orchestra", "organic", "outfit", "output", "outstanding", "overcome",
    "overnight", "overseas", "ownership", "oxygen", "packet", "palm", "panic",
    "parade", "parallel", "participation", "partnership", "part-time",
    "passionate", "password", "patience", "pause", "peer", "penalty",
    "perceive", "perception", "permanently", "pity", "placement", "portion",
    "potentially", "precede", "precious", "precise", "precisely",
    "predictable", "preference", "pride", "primarily", "principal", "prior",
    "probability", "probable", "proceed", "programming", "progressive",
    "prohibit", "promising", "promotion", "prompt", "proportion", "protein",
    "protester", "psychological", "publicity", "publishing", "purely",
    "pursuit", "puzzle", "questionnaire", "racial", "racism", "racist",
    "radiation", "random", "rating", "reasonably", "rebuild", "receiver",
    "recession", "reckon", "recognition", "recovery", "recruit", "recruitment",
    "referee", "refugee", "registration", "regulate", "reinforce", "relieve",
    "relieved", "remarkable", "remarkably", "reporting", "resign",
    "resolution", "restore", "restrict", "restriction", "retail",
    "retirement", "revenue", "revision", "ridiculous", "risky", "rival",
    "rob", "robbery", "rocket", "romance", "roughly", "ruin", "satisfaction",
    "scandal", "scare", "scenario", "scholar", "scholarship", "screening",
    "seeker", "seminar", "settler", "severely", "shaped", "shocking", "shore",
    "shortage", "shortly", "short-term", "sibling", "signature",
    "significance", "skilled", "slogan", "so-called", "somehow", "sophisticated",
    "spare", "specialize", "specify", "spectacular", "spectator", "speculate",
    "speculation", "spice", "spill", "spoil", "spokesman", "spokesperson",
    "spokeswoman", "sponsorship", "sporting", "stall", "stance", "starve",
    "steadily", "stimulate", "strengthen", "strictly", "stroke", "stunning",
    "subsequent", "subsequently", "suburb", "suffering", "sufficient",
    "sufficiently", "surgeon", "survival", "survivor", "suspend",
    "sustainable", "swallow", "sympathetic", "tackle", "technological",
    "temporarily", "tendency", "tension", "terminal", "terribly", "terrify",
    "territory", "terror", "terrorism", "terrorist", "textbook", "theft",
    "therapist", "thesis", "thorough", "thoroughly", "timing", "tissue",
    "tournament", "trace", "trading", "tragedy", "tragic", "trait", "transmit",
    "transportation", "trap", "treasure", "tribe", "trigger", "trillion",
    "troop", "tsunami", "ultimate", "unacceptable", "uncertainty", "undergo",
    "undertake", "unfold", "unfortunate", "unite", "unity", "universal",
    "urgent", "usage", "useless", "valid", "variation", "vertical",
    "viewpoint", "visible", "voluntary", "voting", "wander", "warming",
    "weird", "welfare", "widespread", "wisdom", "withdraw", "workforce",
    "workplace", "workshop",
]

OXFORD_C1_WORDS: list[str] = [
    "abolish", "abortion", "absence", "absent", "absurd", "abundance", "abuse",
    "academy", "accelerate", "acceptance", "accessible", "accomplishment",
    "accordance", "accordingly", "accountability", "accountable", "accumulate",
    "accumulation", "accusation", "accused", "acquisition", "activation",
    "activist", "acute", "adaptation", "adhere", "adjacent", "adjustment",
    "administer", "administrative", "administrator", "admission", "adolescent",
    "adoption", "adverse", "advocate", "aesthetic", "affection", "aftermath",
    "aggression", "agricultural", "aide", "albeit", "alert", "align",
    "alignment", "alike", "allegation", "allege", "allegedly", "alliance",
    "allocate", "allocation", "allowance", "ally", "amateur", "ambassador",
    "amend", "amendment", "amid", "analogy", "anchor", "anonymous",
    "apparatus", "appealing", "appetite", "applaud", "applicable", "appoint",
    "appreciation", "arbitrary", "architectural", "archive", "arena",
    "arguably", "array", "articulate", "aspiration", "aspire", "assassination",
    "assault", "assemble", "assembly", "assert", "assertion", "assurance",
    "asylum", "atrocity", "attain", "attendance", "attorney", "attribute",
    "audit", "authentic", "authorize", "autonomy", "availability", "await",
    "backdrop", "backing", "backup", "bail", "ballot", "banner", "bare",
    "barrel", "battlefield", "bay", "beam", "beast", "behalf", "beloved",
    "bench", "benchmark", "beneath", "beneficiary", "betray", "bind",
    "biography", "bishop", "bizarre", "blade", "blast", "bleed", "blend",
    "bless", "blessing", "boast", "bonus", "boom", "bounce", "boundary",
    "breach", "breakdown", "breakthrough", "breed", "broadband", "browser",
    "brutal", "buddy", "buffer", "bulk", "burden", "bureaucracy", "burial",
    "burst", "cabinet", "calculation", "canvas", "capability", "capitalism",
    "capitalist", "cargo", "carriage", "carve", "casino", "casualty",
    "catalogue", "cater", "cattle", "caution", "cautious", "cease", "cemetery",
    "chamber", "chaos", "characterize", "charm", "charter", "chronic", "chunk",
    "circulate", "circulation", "citizenship", "civic", "civilian", "clarity",
    "clash", "classification", "cling", "clinical", "closure", "cluster",
    "coalition", "coastal", "cognitive", "coincide", "collaborate",
    "collaboration", "collective", "collision", "colonial", "columnist",
    "combat", "commence", "commentary", "commentator", "commerce",
    "commissioner", "commodity", "communist", "companion", "comparable",
    "compassion", "compel", "compelling", "compensate", "compensation",
    "competence", "competent", "compile", "complement", "complexity",
    "compliance", "complication", "comply", "composition", "compromise",
    "compute", "conceal", "concede", "conceive", "conception", "concession",
    "condemn", "confer", "confession", "configuration", "confine",
    "confirmation", "confront", "confrontation", "congregation",
    "congressional", "conquer", "conscience", "consciousness", "consecutive",
    "consensus", "consent", "conserve", "consistency", "consolidate",
    "constituency", "constitute", "constitution", "constitutional",
    "constraint", "consultation", "contemplate", "contempt", "contend",
    "contender", "contention", "continually", "contractor", "contradiction",
    "contrary", "contributor", "conversion", "convict", "conviction",
    "cooperate", "cooperative", "coordinate", "coordination", "coordinator",
    "copper", "copyright", "correction", "correlate", "correlation",
    "correspond", "correspondence", "correspondent", "corresponding",
    "corrupt", "corruption", "costly", "councillor", "counselling",
    "counsellor", "counterpart", "countless", "coup", "courtesy", "crawl",
    "creator", "credibility", "credible", "creep", "critique", "crown",
    "crude", "crush", "crystal", "cult", "cultivate", "curiosity", "custody",
    "cynical", "dam", "damaging", "dawn", "debris", "debut", "decisive",
    "declaration", "dedicated", "dedication", "deem", "default", "defect",
    "defensive", "deficiency", "deficit", "defy", "delegate", "delegation",
    "delicate", "denial", "denounce", "dense", "density", "dependence",
    "depict", "deploy", "deployment", "deprive", "deputy", "descend",
    "descent", "designate", "desirable", "desktop", "destructive", "detain",
    "detection", "detention", "deteriorate", "devastate", "devise",
    "diagnose", "diagnosis", "dictate", "dictator", "differentiate",
    "dignity", "dilemma", "dimension", "diminish", "diplomat", "diplomatic",
    "directory", "disastrous", "discard", "discharge", "disclose",
    "disclosure", "discourse", "discretion", "discrimination", "dismissal",
    "displace", "disposal", "dispose", "dispute", "disrupt", "disruption",
    "dissolve", "distinction", "distinctive", "distort", "distress",
    "disturbing", "divert", "divine", "doctrine", "documentation", "domain",
    "dominance", "donor", "dose", "drain", "drift", "driving", "drown",
    "dual", "duo", "eager", "earnings", "ease", "echo", "ecological",
    "educator", "effectiveness", "efficiency", "elaborate", "electoral",
    "elevate", "eligible", "elite", "embark", "embarrassment", "embassy",
    "embed", "embody", "emergence", "empirical", "empower", "enact",
    "encompass", "encouragement", "encouraging", "endeavour", "endless",
    "endorse", "endorsement", "endure", "enforce", "enforcement",
    "engagement", "engaging", "enquire", "enrich", "enrol", "ensue",
    "enterprise", "enthusiast", "entitle", "entity", "epidemic", "equality",
    "equation", "erect", "escalate", "essence", "establishment", "eternal",
    "evacuate", "evoke", "evolutionary", "exaggerate", "excellence",
    "exceptional", "excess", "exclusion", "exclusive", "exclusively",
    "execute", "execution", "exert", "exile", "expenditure", "experimental",
    "expire", "explicit", "explicitly", "exploitation", "explosive",
    "extremist", "facilitate", "faction", "faculty", "fade", "fairness",
    "fatal", "fate", "favourable", "feat", "feminist", "fibre", "fierce",
    "filter", "firearm", "fixture", "flaw", "flawed", "flee", "fleet",
    "flesh", "flexibility", "flourish", "fluid", "footage", "foreigner",
    "forge", "formula", "formulate", "forthcoming", "foster", "fragile",
    "franchise", "frankly", "frustrated", "frustrating", "frustration",
    "functional", "fundraising", "funeral", "gambling", "gathering", "gaze",
    "generic", "genocide", "glance", "glimpse", "glorious", "glory",
    "governance", "grace", "grasp", "grave", "gravity", "grief", "grin",
    "grind", "grip", "gross", "guerrilla", "guidance", "guilt", "hail",
    "halt", "handful", "handling", "harassment", "hardware", "harmony",
    "harsh", "harvest", "hatred", "haunt", "hazard", "heighten", "heritage",
    "hierarchy", "high-profile", "hint", "homeland", "hopeful", "horizon",
    "hostage", "hostile", "hostility", "humanitarian", "humanity", "humble",
    "identification", "ideological", "ideology", "ignorance", "imagery",
    "immense", "imminent", "implementation", "imprison", "imprisonment",
    "inability", "inadequate", "inappropriate", "incidence", "inclined",
    "inclusion", "incur", "indicator", "indigenous", "induce", "indulge",
    "inequality", "infamous", "infant", "infect", "inflict", "influential",
    "inherent", "inhibit", "initiate", "inject", "injustice", "inmate",
    "insider", "inspect", "inspection", "inspiration", "instinct",
    "institutional", "instruct", "instrumental", "insufficient", "insult",
    "intact", "intake", "integral", "integrated", "integration", "integrity",
    "intensify", "intensity", "intensive", "intent", "interactive",
    "interface", "interfere", "interference", "interim", "interior",
    "intermediate", "intervene", "intervention", "intimate", "intriguing",
    "investigator", "invisible", "invoke", "involvement", "ironic",
    "ironically", "irony", "irrelevant", "isolation", "judicial", "junction",
    "jurisdiction", "justification", "kidnap", "kidney", "kingdom",
    "landlord", "landmark", "large-scale", "laser", "latter", "lawsuit",
    "layout", "leak", "leap", "legacy", "legendary", "legislation",
    "legislative", "legislature", "legitimate", "lengthy", "lesser",
    "lethal", "liable", "liberal", "liberation", "liberty", "lifelong",
    "likelihood", "linear", "linger", "literacy", "lobby", "logic",
    "long-standing", "loop", "loyalty", "machinery", "magistrate",
    "magnetic", "magnitude", "mainland", "mainstream", "maintenance",
    "mandate", "mandatory", "manifest", "manipulate", "manipulation",
    "manuscript", "marginal", "marine", "marketplace", "massacre",
    "mathematical", "mature", "maximize", "meaningful", "medieval",
    "meditation", "melody", "memoir", "memorial", "mentor", "merchant",
    "mercy", "mere", "merely", "merge", "merger", "merit", "methodology",
    "midst", "migration", "militant", "militia", "minimal", "minimize",
    "mining", "ministry", "miracle", "misery", "misleading", "missile",
    "mobility", "mobilize", "moderate", "modification", "momentum",
    "monopoly", "morality", "motive", "municipal", "mutual", "namely",
    "nationwide", "naval", "neglect", "neighbouring", "niche", "noble",
    "nominate", "nomination", "nominee", "nonetheless", "non-profit",
    "notable", "notably", "notify", "notorious", "novel", "nursery",
    "objection", "oblige", "obsess", "obsession", "occasional", "occurrence",
    "offspring", "operational", "opt", "optical", "optimism", "oral",
    "organizational", "orientation", "originate", "outbreak", "outlet",
    "outlook", "outrage", "outsider", "overlook", "overly", "oversee",
    "overturn", "overwhelm", "overwhelming", "parameter", "parental",
    "parliamentary", "partial", "partially", "passive", "patch", "patent",
    "pathway", "patrol", "patron", "peak", "peculiar", "persist",
    "persistent", "personnel", "petition", "philosopher", "philosophical",
    "physician", "pioneer", "pipeline", "plea", "plead", "pledge", "plunge",
    "poll", "portfolio", "portray", "postpone", "practitioner", "precedent",
    "precision", "predator", "predecessor", "predominantly", "pregnancy",
    "prejudice", "preliminary", "premise", "premium", "prescribe",
    "prescription", "presently", "preservation", "preside", "presidency",
    "presidential", "prestigious", "presumably", "presume", "prevail",
    "prevalence", "prevention", "prey", "principal", "privatization",
    "privilege", "probe", "problematic", "proceedings", "proceeds",
    "processing", "proclaim", "productive", "productivity", "profitable",
    "profound", "projection", "prominent", "pronounced", "propaganda",
    "proposition", "prosecute", "prosecution", "prosecutor", "prospective",
    "prosperity", "protective", "protocol", "province", "provincial",
    "provision", "provoke", "psychiatric", "pulse", "query", "quest",
    "quota", "radical", "rage", "raid", "rally", "ranking", "ratio",
    "rational", "readily", "realization", "realm", "reasoning", "reassure",
    "rebel", "rebellion", "recipient", "reconstruction", "referendum",
    "reflection", "reform", "refuge", "refusal", "regain", "regardless",
    "regime", "regulator", "regulatory", "rehabilitation", "reign",
    "rejection", "relevance", "reliability", "reluctant", "remainder",
    "remains", "remedy", "reminder", "removal", "render", "renew",
    "renowned", "rental", "replacement", "reportedly", "representation",
    "reproduce", "reproduction", "republic", "resemble", "reside",
    "residence", "residential", "residue", "resignation", "resistance",
    "respective", "respectively", "restoration", "restraint", "resume",
    "retreat", "retrieve", "revelation", "revenge", "reverse", "revival",
    "revive", "revolutionary", "rhetoric", "riot", "ritual", "robust",
    "rotate", "rotation", "ruling", "rumour", "sacred", "sacrifice", "sake",
    "sanction", "sceptical", "scope", "scrutiny", "secular", "seemingly",
    "segment", "seize", "seldom", "selective", "senator", "sensation",
    "sensitivity", "sentiment", "separation", "settlement", "sexuality",
    "shareholder", "shatter", "sheer", "shipping", "shrink", "sigh",
    "simulate", "simulation", "simultaneously", "situated", "skip", "slam",
    "slavery", "smash", "soak", "soar", "socialist", "sole", "solely",
    "solidarity", "sovereignty", "span", "spark", "specification",
    "specimen", "spectacle", "spectrum", "sphere", "spine", "spotlight",
    "spouse", "squad", "squeeze", "stability", "stabilize", "stake",
    "stark", "statistical", "steer", "stem", "stereotype", "stimulus",
    "storage", "straightforward", "strain", "strategic", "striking",
    "strive", "structural", "stumble", "stun", "submission", "subscriber",
    "subscription", "subsidy", "substantial", "substantially", "substitute",
    "subtle", "suburban", "succession", "successive", "successor", "sue",
    "suicide", "summit", "superb", "superior", "supervise", "supervision",
    "supervisor", "supplement", "supportive", "supposedly", "suppress",
    "supreme", "surge", "surgical", "surplus", "surrender", "surveillance",
    "suspicion", "suspicious", "sustain", "symbolic", "syndrome",
    "synthesis", "systematic", "tactic", "tactical", "taxpayer", "tempt",
    "tenant", "tender", "tenure", "terminate", "terrain", "testify",
    "testimony", "texture", "theatrical", "theology", "theoretical",
    "thereafter", "thereby", "thoughtful", "thought-provoking", "threshold",
    "thrilled", "thrive", "tighten", "timely", "tobacco", "tolerance",
    "tolerate", "toxic", "trademark", "trail", "transaction", "transcript",
    "transformation", "transit", "transmission", "transparency",
    "transparent", "trauma", "treaty", "tremendous", "tribal", "tribunal",
    "tribute", "triumph", "trophy", "troubled", "trustee", "tuition",
    "turnout", "turnover", "undergraduate", "underlying", "undermine",
    "undoubtedly", "unify", "unprecedented", "unveil", "upcoming",
    "upgrade", "uphold", "utility", "utilize", "utterly", "vague",
    "validity", "vanish", "variable", "varied", "venture", "verbal",
    "verdict", "verify", "versus", "vessel", "veteran", "viable", "vibrant",
    "vicious", "villager", "violate", "violation", "virtue", "vocal", "vow",
    "vulnerability", "vulnerable", "warehouse", "warfare", "warrant",
    "warrior", "weaken", "well-being", "whatsoever", "whereby", "whilst",
    "widen", "width", "willingness", "withdrawal", "worship", "worthwhile",
    "worthy", "yield", "youngster",
]

# Hand-written, not sourced from any list — the specific over-suggested basics
# that LLMs default to when a difficulty floor isn't enforced.
TOO_EASY_WORDS: list[str] = [
    "good", "bad", "big", "small", "happy", "sad", "nice", "beautiful",
    "important", "interesting", "difficult", "easy", "fast", "slow", "new",
    "old", "young", "strong", "weak", "rich", "poor", "clean", "safe",
    "dangerous", "healthy", "busy", "cheap", "expensive", "high", "low",
    "long", "short", "early", "late", "open", "full", "empty", "right",
    "wrong", "real", "simple", "necessary", "useful", "problem", "change",
    "help", "work", "money", "time", "people", "thing", "way", "idea",
    "world", "life", "family", "friend", "food", "weather",
]


def sample_target_words(count: int = 40, tier: str = "mixed") -> list[str]:
    """A fresh random sample of Oxford 5000 B2/C1 words, as a concrete rarity anchor.

    Not a list of words the LLM must use verbatim — just inspiration for "this is
    roughly the register/frequency band to aim for", re-sampled each call so
    repeated generations don't converge on the same handful of words.
    """
    pool = {
        "b2": OXFORD_B2_WORDS,
        "c1": OXFORD_C1_WORDS,
        "mixed": OXFORD_B2_WORDS + OXFORD_C1_WORDS,
    }.get(tier, OXFORD_B2_WORDS + OXFORD_C1_WORDS)
    return random.sample(pool, min(count, len(pool)))


# --------------------------------------------------------------------- passages
# Adapted from Wikipedia article introductions (CC BY-SA 4.0), retrieved 2026-07-18.
# Kept short (a few paragraphs) and attributed. These stand in for authentic
# academic-register source text the way real IELTS Reading passages themselves are
# adaptations of real magazine/encyclopedia articles — without touching any
# copyrighted, commercially-sold Cambridge test material.

PASSAGES: list[dict[str, Any]] = [
    {
        "id": "coral-reef",
        "topic": "marine biology / coral reefs",
        "keywords": ["coral", "reef", "marine", "ocean life", "sea life"],
        "title": "Coral Reef",
        "source_url": "https://en.wikipedia.org/wiki/Coral_reef",
        "license": "CC BY-SA 4.0, adapted from Wikipedia",
        "text": (
            "A coral reef is characterized by reef-building corals and forms from "
            "colonies of coral polyps held together by calcium carbonate. Most "
            "coral reefs are built from stony corals whose polyps cluster in "
            "groups. Coral belongs to the class Anthozoa in the phylum Cnidaria, "
            "which includes sea anemones and jellyfish. Unlike sea anemones, "
            "corals secrete hard carbonate exoskeletons. Most reefs grow best in "
            "warm, shallow, clear, sunny, and agitated water. Coral reefs first "
            "appeared 485 million years ago at the Early Ordovician, displacing "
            "microbial and sponge reefs.\n\n"
            "Sometimes called rainforests of the sea, shallow coral reefs form "
            "some of Earth's most diverse ecosystems. Though occupying less than "
            "0.1% of ocean area, they provide habitat for at least 25% of all "
            "marine species, including fish, mollusks, worms, crustaceans, "
            "echinoderms, sponges, tunicates and other cnidarians. Coral reefs "
            "flourish in nutrient-poor waters, most commonly at shallow tropical "
            "depths, though deep water and cold water coral reefs exist elsewhere "
            "at smaller scales."
        ),
    },
    {
        "id": "urban-heat-island",
        "topic": "urbanization / cities",
        "keywords": ["urban", "city", "cities", "urbanization", "urban heat"],
        "title": "Urban Heat Island",
        "source_url": "https://en.wikipedia.org/wiki/Urban_heat_island",
        "license": "CC BY-SA 4.0, adapted from Wikipedia",
        "text": (
            "The urban heat island (UHI) effect is a meteorological and "
            "climatological phenomenon in which urban areas experience "
            "significantly warmer temperatures than surrounding rural areas. The "
            "temperature difference is usually larger at night than during the "
            "day, and is most apparent when winds are weak, under clear-sky "
            "conditions, noticeably during the summer and winter. The main cause "
            "of the UHI effect is the modification of land surfaces, while waste "
            "heat generated by energy usage is a secondary contributor. Urban "
            "areas occupy about 0.5% of the Earth's land surface but host more "
            "than half of the world's population.\n\n"
            "Increases in heat within urban centres lengthen growing seasons, "
            "decrease air quality by increasing the production of pollutants "
            "such as ozone, and decrease water quality as warmer waters flow "
            "into area streams and put stress on their ecosystems. Not all "
            "cities have a distinct urban heat island, and the heat island "
            "characteristics depend strongly on the background climate of the "
            "area where the city is located. Heat can be reduced by tree cover "
            "and green space, which act as sources of shade and promote "
            "evaporative cooling. Other options include green roofs, passive "
            "daytime radiative cooling applications, ventilation corridors, and "
            "the use of lighter-coloured surfaces that reflect more sunlight and "
            "absorb less heat."
        ),
    },
    {
        "id": "sleep",
        "topic": "health / sleep science",
        "keywords": ["sleep", "health", "rest"],
        "title": "Sleep",
        "source_url": "https://en.wikipedia.org/wiki/Sleep",
        "license": "CC BY-SA 4.0, adapted from Wikipedia",
        "text": (
            "Sleep is a state of reduced mental and physical activity in which "
            "consciousness is altered and certain sensory activity is inhibited. "
            "During sleep, muscle activity drops significantly and environmental "
            "interaction decreases. Though sleep differs from wakefulness in "
            "responsiveness to stimuli, the brain remains actively engaged, "
            "making it distinctly different from comas or disorders of "
            "consciousness.\n\n"
            "The body cycles through two primary sleep modes: rapid eye movement "
            "sleep (REM) and non-REM sleep. REM sleep involves not just rapid eye "
            "movements but also near-total body paralysis. Human rest activates "
            "restorative processes across multiple bodily systems, including "
            "immune, nervous, skeletal, and muscular functions. These processes "
            "maintain emotional stability, cognitive performance, and "
            "endocrine and immune system health. An internal circadian clock "
            "naturally prompts sleep when darkness arrives. Sleep behaviour is "
            "evolutionarily ancient and conserved across species, likely "
            "originating as a brain-cleansing mechanism; research increasingly "
            "suggests that metabolic waste removal represents a fundamental "
            "sleep function."
        ),
    },
    {
        "id": "food-security",
        "topic": "society / food security",
        "keywords": ["food security", "hunger", "famine", "agriculture policy"],
        "title": "Food Security",
        "source_url": "https://en.wikipedia.org/wiki/Food_security",
        "license": "CC BY-SA 4.0, adapted from Wikipedia",
        "text": (
            "Food security is defined as the state of having reliable access to "
            "a sufficient quantity of affordable, healthy food. The concept "
            "encompasses availability for people of all backgrounds, and at the "
            "household level, all members of a family having consistent access "
            "to enough food for an active, healthy life. Food-secure individuals "
            "avoid living in hunger or fear of starvation. The definition "
            "includes resilience against future disruptions from droughts, "
            "floods, shipping problems, fuel shortages, economic instability, "
            "and conflicts. Its opposite, food insecurity, represents limited or "
            "uncertain availability of suitable food.\n\n"
            "The understanding of food security has evolved significantly. "
            "Today's framework recognizes six key dimensions: availability, "
            "access, utilization, stability, agency, and sustainability. The "
            "1996 World Food Summit established that food should not be used as "
            "an instrument for political and economic pressure."
        ),
    },
    {
        "id": "archaeology",
        "topic": "history / archaeology",
        "keywords": ["archaeology", "ancient", "history", "excavation", "artefact", "artifact"],
        "title": "Archaeology",
        "source_url": "https://en.wikipedia.org/wiki/Archaeology",
        "license": "CC BY-SA 4.0, adapted from Wikipedia",
        "text": (
            "Archaeology is the study of human activity through the recovery "
            "and analysis of material culture. The archaeological record "
            "consists of artifacts, architecture, biofacts or ecofacts, sites, "
            "and cultural landscapes. Archaeology can be considered both a "
            "social science and a branch of the humanities. The discipline "
            "involves surveying, excavation, and eventually analysis of data "
            "collected, to learn more about the past.\n\n"
            "Archaeologists study human prehistory and history, from the "
            "development of the first stone tools 3.3 million years ago up "
            "until recent decades. Archaeology is distinct from palaeontology, "
            "which is the study of fossil remains. Archaeology is particularly "
            "important for learning about prehistoric societies, for which, by "
            "definition, there are no written records. Archaeology developed "
            "out of antiquarianism in Europe during the 19th century and has "
            "since become a discipline practised worldwide. Nonetheless, today, "
            "archaeologists face many problems, such as dealing with "
            "pseudoarchaeology, the looting of artifacts, a lack of public "
            "interest, and opposition to the excavation of human remains."
        ),
    },
    {
        "id": "artificial-intelligence",
        "topic": "technology / artificial intelligence",
        "keywords": ["artificial intelligence", "ai", "machine learning", "automation", "robot"],
        "title": "Artificial Intelligence",
        "source_url": "https://en.wikipedia.org/wiki/Artificial_intelligence",
        "license": "CC BY-SA 4.0, adapted from Wikipedia",
        "text": (
            "Artificial intelligence (AI) is the capability of computational "
            "systems to perform tasks typically associated with human "
            "intelligence, such as learning, reasoning, problem-solving, "
            "perception, and decision-making. It is a field of research in "
            "engineering, mathematics, and computer science that develops and "
            "studies methods and software that enable machines to perceive "
            "their environment and use learning and intelligence to take "
            "actions that maximize their chances of achieving defined goals.\n\n"
            "High-profile applications of AI include advanced web search "
            "engines, chatbots, virtual assistants, autonomous vehicles, and "
            "play and analysis in strategy games. Since the 2020s, generative "
            "AI has become widely available to generate images, audio, and "
            "videos from text prompts. The traditional goals of AI research "
            "include learning, reasoning, knowledge representation, planning, "
            "natural language processing, and perception, as well as support "
            "for robotics. AI also draws upon psychology, linguistics, "
            "philosophy, and neuroscience."
        ),
    },
    {
        "id": "renewable-energy",
        "topic": "environment / renewable energy",
        "keywords": ["renewable energy", "solar", "wind power", "green energy", "clean energy"],
        "title": "Renewable Energy",
        "source_url": "https://en.wikipedia.org/wiki/Renewable_energy",
        "license": "CC BY-SA 4.0, adapted from Wikipedia",
        "text": (
            "Renewable energy, also called green energy, is energy made from "
            "renewable natural resources that are replenished on a human "
            "timescale. The most prevalent forms include solar energy, wind "
            "power, and hydropower, with bioenergy and geothermal power playing "
            "significant roles in certain regions. These installations function "
            "effectively in both urban and rural settings at various scales.\n\n"
            "The sector has undergone dramatic transformation. Renewable energy "
            "systems have rapidly become more efficient and cheaper over the "
            "past 30 years. A substantial majority of newly installed global "
            "electricity generation capacity now comes from renewable sources, "
            "with solar and wind experiencing particularly dramatic cost "
            "declines over the past decade that have made them competitive "
            "with conventional fossil fuels. Between 2011 and 2021, renewable "
            "energy's share of global electricity supply grew from 20% to 28%, "
            "with solar and wind accounting for most gains."
        ),
    },
    {
        "id": "cognitive-development",
        "topic": "psychology / child development",
        "keywords": ["cognitive development", "child psychology", "children learning", "brain development"],
        "title": "Cognitive Development",
        "source_url": "https://en.wikipedia.org/wiki/Cognitive_development",
        "license": "CC BY-SA 4.0, adapted from Wikipedia",
        "text": (
            "Cognitive development is a field of study in neuroscience and "
            "psychology focusing on a child's development in terms of "
            "information processing, conceptual resources, perceptual skill, "
            "language learning, and other aspects of the developed adult "
            "brain and cognitive psychology. Qualitative distinctions exist "
            "between how children and adults process experiences, with "
            "concepts like object permanence and cause-effect reasoning "
            "differing developmentally.\n\n"
            "Cognitive development can be defined as the emergence of the "
            "ability to consciously cognize, understand, and articulate one's "
            "understanding in adult terms. Four key components — reasoning, "
            "intelligence, language, and memory — begin developing around 18 "
            "months as infants engage with their surroundings through toys, "
            "parental interaction, and environmental stimuli."
        ),
    },
    {
        "id": "human-migration",
        "topic": "society / migration",
        "keywords": ["migration", "immigrant", "immigration", "emigration", "移民"],
        "title": "Human Migration",
        "source_url": "https://en.wikipedia.org/wiki/Human_migration",
        "license": "CC BY-SA 4.0, adapted from Wikipedia",
        "text": (
            "Human migration is the movement of people from one place to "
            "another, with intentions of settling, permanently or temporarily, "
            "at a new location. The movement frequently happens across "
            "considerable distances and between nations, though internal "
            "migration, within a single country, is the dominant form of "
            "human migration globally.\n\n"
            "Migration tends to associate with improved human capital at "
            "individual and household levels, along with better access to "
            "migration networks that may enable subsequent relocations. "
            "Research suggests this movement holds substantial potential for "
            "advancing human development, with evidence indicating migration "
            "is one of the most direct routes out of poverty. Demographics "
            "matter significantly: age influences both employment-related and "
            "other types of relocation. People may relocate as individuals, "
            "family groups, or larger collectives."
        ),
    },
    {
        "id": "biodiversity-loss",
        "topic": "environment / biodiversity and conservation",
        "keywords": ["biodiversity", "extinction", "conservation", "endangered species", "habitat loss"],
        "title": "Biodiversity Loss",
        "source_url": "https://en.wikipedia.org/wiki/Biodiversity_loss",
        "license": "CC BY-SA 4.0, adapted from Wikipedia",
        "text": (
            "Biodiversity loss happens when species disappear completely from "
            "Earth (extinction) or when there is a decrease or disappearance "
            "of species in a specific area. The reduction in biological "
            "diversity within a given location can be either temporary or "
            "permanent, depending on whether the underlying damage can be "
            "reversed through ecological restoration efforts.\n\n"
            "The primary drivers of contemporary species decline stem from "
            "human activities that exceed planetary boundaries. These "
            "activities encompass habitat destruction through deforestation, "
            "intensive land use practices such as monoculture farming, "
            "various forms of pollution affecting air and water systems, "
            "unsustainable resource extraction, invasive species introduction, "
            "and climate change impacts. Some researchers argue that habitat "
            "loss driven by commodity production for export markets, rather "
            "than population size alone, is the more significant factor, "
            "noting that wealth disparities between nations correlate more "
            "closely with environmental degradation than demographic data."
        ),
    },
    {
        "id": "space-exploration",
        "topic": "science / space exploration",
        "keywords": ["space exploration", "astronaut", "nasa", "rocket", "mars", "moon landing"],
        "title": "Space Exploration",
        "source_url": "https://en.wikipedia.org/wiki/Space_exploration",
        "license": "CC BY-SA 4.0, adapted from Wikipedia",
        "text": (
            "Space exploration is the physical investigation of outer space by "
            "uncrewed robotic space probes and through human spaceflight. "
            "While observation of celestial objects, known as astronomy, "
            "predates recorded history, the development of efficient rockets "
            "during the mid-twentieth century made physical space exploration "
            "achievable. Common motivations for exploring space include "
            "advancing scientific research, demonstrating national prestige, "
            "fostering international cooperation, ensuring humanity's "
            "long-term survival, and gaining military advantages.\n\n"
            "The early space era was characterized by competition between "
            "superpowers. The Soviet Union achieved numerous firsts, including "
            "launching Sputnik 1 on October 4, 1957, the first human-made "
            "object in orbit, and Yuri Gagarin's crewed flight in 1961. The "
            "United States achieved the first human Moon landing with "
            "Apollo 11 in 1969."
        ),
    },
    {
        "id": "nutrition",
        "topic": "health / nutrition",
        "keywords": ["nutrition", "diet", "food and health", "malnutrition"],
        "title": "Nutrition",
        "source_url": "https://en.wikipedia.org/wiki/Nutrition",
        "license": "CC BY-SA 4.0, adapted from Wikipedia",
        "text": (
            "Nutrition is the biochemical and physiological process by which "
            "an organism uses food and water to support its life. The intake "
            "of these substances provides organisms with nutrients, divided "
            "into macro- and micronutrients, which can be metabolized to "
            "create energy and chemical structures; too much or too little of "
            "an essential nutrient can cause malnutrition.\n\n"
            "The type of organism determines what nutrients it needs and how "
            "it obtains them. Some organisms can produce nutrients internally "
            "by consuming basic elements, while others must consume other "
            "organisms to obtain pre-existing nutrients. All forms of life "
            "require carbon, energy, and water, as well as various other "
            "molecules. Animals require complex nutrients such as "
            "carbohydrates, lipids, and proteins, obtaining them by consuming "
            "other organisms. Humans have developed agriculture and cooking to "
            "replace foraging and advance human nutrition."
        ),
    },
    {
        "id": "remote-work",
        "topic": "work / remote work and technology",
        "keywords": ["remote work", "telecommute", "work from home", "hybrid work", "office culture"],
        "title": "Remote Work",
        "source_url": "https://en.wikipedia.org/wiki/Telecommuting",
        "license": "CC BY-SA 4.0, adapted from Wikipedia",
        "text": (
            "Remote work involves the practice of working at or from one's "
            "home or another space rather than from an office or workplace. "
            "The practice of working at home has been documented for "
            "centuries, with management relying on trust and detailed "
            "record-keeping.\n\n"
            "Modern remote work emerged during the 1970s when technology "
            "first enabled satellite offices to connect with downtown "
            "mainframes. The terms telecommuting and telework were "
            "established by Jack Nilles in 1973. By the 1980s and 1990s, this "
            "arrangement became increasingly common through collaborative "
            "software, cloud computing, and video calling. The COVID-19 "
            "pandemic then catalyzed a rapid transition to remote work for "
            "white-collar workers around the world, with this shift largely "
            "persisting afterward."
        ),
    },
]

_PASSAGE_BY_ID: dict[str, dict[str, Any]] = {p["id"]: p for p in PASSAGES}


def find_passage(topic: str) -> dict[str, Any] | None:
    """Fuzzy-match a free-text topic string against the curated passage bank."""
    needle = topic.strip().lower()
    if not needle:
        return None
    for passage in PASSAGES:
        haystacks = [passage["topic"], passage["title"], *passage["keywords"]]
        if any(needle in h.lower() or h.lower() in needle for h in haystacks):
            return passage
    return None


def passage_public() -> list[dict[str, Any]]:
    """Passage list without full text, for browsing/attribution display."""
    return [
        {"id": p["id"], "topic": p["topic"], "title": p["title"],
         "source_url": p["source_url"], "license": p["license"]}
        for p in PASSAGES
    ]
