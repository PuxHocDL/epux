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
import re
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

# ------------------------------------------------------- Oxford 3000 (A1, A2)
# (c) Oxford University Press. "The Oxford 3000 by CEFR level" -- free PDF, retrieved
# 2026-07-18: https://www.oxfordlearnersdictionaries.com/external/pdf/wordlists/oxford-3000-5000/The_Oxford_3000_by_CEFR_level.pdf
# Only the A1+A2 tiers are kept -- the B1/B2 tiers of THIS list are a separate,
# harder set of "core" words that a B2+ learner is still actively learning, so they
# don't belong in a "definitely already known" exclude set. Real, authoritative,
# and far larger than a hand-written blocklist could be -- used as a deterministic
# backstop in generate_vocab (see llm.py) as well as a prompt-level anchor.

OXFORD_3000_A1: list[str] = [
    "a", "an", "about", "above", "across", "action", "activity", "actor", "actress",
    "add", "address", "adult", "advice", "afraid", "after", "afternoon", "again",
    "age", "ago", "agree", "air", "airport", "all", "also", "always", "amazing",
    "and", "angry", "animal", "another", "answer", "any", "anyone", "anything",
    "apartment", "apple", "april", "area", "arm", "around", "arrive", "art",
    "article", "artist", "as", "ask", "at", "august", "aunt", "autumn", "away",
    "baby", "back", "bad", "bag", "ball", "banana", "band", "bank", "bath",
    "bathroom", "be", "beach", "beautiful", "because", "become", "bed", "bedroom",
    "beer", "before", "begin", "beginning", "behind", "believe", "below", "best",
    "better", "between", "bicycle", "big", "bike", "bill", "bird", "birthday",
    "black", "blog", "blonde", "blue", "boat", "body", "book", "boot", "bored",
    "boring", "born", "both", "bottle", "box", "boy", "boyfriend", "bread",
    "break", "breakfast", "bring", "brother", "brown", "build", "building", "bus",
    "business", "busy", "but", "butter", "buy", "by", "bye", "cafe", "cake",
    "call", "camera", "can", "cannot", "capital", "car", "card", "career",
    "carrot", "carry", "cat", "cd", "cent", "centre", "century", "chair",
    "change", "cheap", "check", "cheese", "chicken", "child", "chocolate",
    "choose", "cinema", "city", "class", "classroom", "clean", "climb", "clock",
    "close", "clothes", "club", "coat", "coffee", "cold", "college", "colour",
    "come", "common", "company", "compare", "complete", "computer", "concert",
    "conversation", "cook", "cooking", "cool", "correct", "cost", "could",
    "country", "course", "cousin", "cow", "cream", "create", "culture", "cup",
    "customer", "cut", "dad", "dance", "dancer", "dancing", "dangerous", "dark",
    "date", "daughter", "day", "dear", "december", "decide", "delicious",
    "describe", "description", "desk", "detail", "dialogue", "dictionary", "die",
    "diet", "difference", "different", "difficult", "dinner", "dirty", "discuss",
    "dish", "do", "doctor", "dog", "dollar", "door", "down", "downstairs", "draw",
    "dress", "drink", "drive", "driver", "during", "dvd", "each", "ear", "early",
    "east", "easy", "eat", "egg", "eight", "eighteen", "eighty", "elephant",
    "else", "email", "end", "enjoy", "enough", "euro", "even", "evening", "event",
    "ever", "every", "everybody", "everyone", "everything", "exam", "example",
    "excited", "exciting", "exercise", "expensive", "explain", "extra", "eye",
    "face", "fact", "fall", "false", "family", "famous", "fantastic", "far",
    "farm", "farmer", "fast", "fat", "father", "favourite", "february", "feel",
    "feeling", "festival", "few", "fifteen", "fifth", "fifty", "fill", "film",
    "final", "find", "fine", "finish", "fire", "first", "fish", "five", "flat",
    "flight", "floor", "flower", "fly", "food", "foot", "football", "for",
    "forget", "form", "forty", "four", "fourteen", "fourth", "free", "friday",
    "friend", "friendly", "from", "front", "fruit", "full", "fun", "funny",
    "future", "game", "garden", "geography", "get", "girl", "girlfriend", "give",
    "glass", "go", "goodbye", "grandfather", "grandmother", "grandparent",
    "great", "green", "grey", "group", "grow", "guess", "guitar", "gym", "hair",
    "half", "hand", "happen", "happy", "hard", "hat", "hate", "have", "he",
    "head", "health", "healthy", "hear", "hello", "help", "her", "here", "hey",
    "hi", "high", "him", "his", "history", "hobby", "holiday", "home", "homework",
    "hope", "horse", "hospital", "hot", "hotel", "hour", "house", "how",
    "however", "hundred", "hungry", "husband", "i", "ice", "idea", "if",
    "imagine", "important", "improve", "in", "include", "information",
    "interest", "interested", "interesting", "internet", "interview", "into",
    "introduce", "island", "it", "its", "jacket", "january", "jeans", "job",
    "join", "journey", "juice", "july", "june", "just", "keep", "key", "kind",
    "kitchen", "kilometre", "know", "land", "language", "large", "last", "late",
    "later", "laugh", "learn", "leave", "left", "leg", "lesson", "let", "letter",
    "library", "lie", "life", "light", "like", "line", "lion", "list", "listen",
    "little", "live", "local", "long", "look", "lose", "lot", "love", "lunch",
    "machine", "magazine", "main", "make", "man", "many", "map", "march",
    "market", "married", "match", "may", "maybe", "me", "meal", "mean",
    "meaning", "meat", "meet", "meeting", "member", "menu", "message", "metre",
    "midnight", "mile", "milk", "million", "minute", "miss", "mistake", "model",
    "modern", "moment", "monday", "money", "month", "more", "morning", "most",
    "mother", "mountain", "mouse", "mouth", "move", "movie", "much", "mum",
    "museum", "music", "must", "my", "name", "natural", "near", "need",
    "negative", "neighbour", "never", "new", "news", "newspaper", "next", "nice",
    "night", "nine", "nineteen", "ninety", "no", "nobody", "north", "nose",
    "not", "note", "nothing", "november", "now", "number", "nurse", "object",
    "october", "of", "off", "office", "often", "oh", "ok", "old", "on", "once",
    "one", "onion", "online", "only", "open", "opinion", "opposite", "or",
    "orange", "order", "other", "our", "out", "outside", "over", "own", "page",
    "paint", "painting", "pair", "paper", "paragraph", "parent", "park", "part",
    "partner", "party", "passport", "past", "pay", "pen", "pencil", "people",
    "pepper", "perfect", "period", "person", "personal", "phone", "photo",
    "photograph", "phrase", "piano", "picture", "piece", "pig", "pink", "place",
    "plan", "plane", "plant", "play", "player", "please", "point", "police",
    "policeman", "pool", "poor", "popular", "positive", "possible", "post",
    "potato", "pound", "practice", "practise", "prefer", "prepare", "present",
    "pretty", "price", "probably", "problem", "product", "programme", "project",
    "purple", "put", "quarter", "question", "quick", "quickly", "quiet", "quite",
    "radio", "rain", "read", "reader", "reading", "ready", "real", "really",
    "reason", "red", "relax", "remember", "repeat", "report", "restaurant",
    "result", "return", "rice", "rich", "ride", "right", "river", "road", "room",
    "routine", "rule", "run", "sad", "salad", "salt", "same", "sandwich",
    "saturday", "say", "school", "science", "scientist", "sea", "second",
    "section", "see", "sell", "send", "sentence", "september", "seven",
    "seventeen", "seventy", "share", "she", "sheep", "shirt", "shoe", "shop",
    "shopping", "short", "should", "show", "shower", "sick", "similar", "sing",
    "singer", "sister", "sit", "situation", "six", "sixteen", "sixty", "skill",
    "skirt", "sleep", "slow", "small", "snake", "snow", "so", "somebody",
    "someone", "something", "sometimes", "son", "song", "soon", "sorry",
    "sound", "soup", "south", "space", "speak", "special", "spell", "spelling",
    "spend", "sport", "spring", "stand", "star", "start", "statement",
    "station", "stay", "still", "stop", "story", "street", "strong", "student",
    "study", "style", "subject", "success", "sugar", "summer", "sun", "sunday",
    "supermarket", "sure", "sweater", "swim", "swimming", "table", "take",
    "talk", "tall", "taxi", "tea", "teach", "teacher", "team", "teenager",
    "telephone", "television", "tell", "ten", "tennis", "terrible", "test",
    "text", "than", "thank", "thanks", "that", "the", "theatre", "their",
    "them", "then", "there", "they", "thing", "think", "third", "thirsty",
    "thirteen", "thirty", "this", "though", "thousand", "three", "through",
    "thursday", "ticket", "time", "tired", "title", "to", "today", "together",
    "toilet", "tomato", "tomorrow", "tonight", "too", "tooth", "topic",
    "tourist", "town", "traffic", "train", "travel", "tree", "trip", "trousers",
    "true", "try", "t-shirt", "tuesday", "turn", "tv", "twelve", "twenty",
    "twice", "two", "type", "umbrella", "uncle", "under", "understand",
    "university", "until", "up", "upstairs", "us", "use", "useful", "usually",
    "vacation", "vegetable", "very", "video", "village", "visit", "visitor",
    "wait", "waiter", "wake", "walk", "wall", "want", "warm", "wash", "watch",
    "water", "way", "we", "wear", "weather", "website", "wednesday", "week",
    "weekend", "welcome", "well", "west", "what", "when", "where", "which",
    "while", "white", "who", "why", "wife", "will", "win", "window", "wine",
    "winter", "with", "without", "woman", "wonderful", "word", "work", "worker",
    "world", "would", "write", "writer", "writing", "wrong", "year", "yes",
    "yesterday", "yet", "you", "young", "your", "yourself",
]

OXFORD_3000_A2: list[str] = [
    "ability", "able", "abroad", "accept", "accident", "according to", "achieve",
    "act", "active", "actually", "advantage", "adventure", "advertise",
    "advertisement", "advertising", "affect", "against", "airline", "alive",
    "all right", "allow", "almost", "alone", "along", "already", "alternative",
    "although", "among", "amount", "ancient", "ankle", "any more", "anybody",
    "anyway", "anywhere", "app", "appear", "appearance", "apply", "architect",
    "architecture", "argue", "argument", "army", "arrange", "arrangement",
    "asleep", "assistant", "athlete", "attack", "attend", "attention",
    "attractive", "audience", "author", "available", "average", "avoid",
    "award", "awful", "background", "badly", "bar", "baseball", "based",
    "basketball", "bean", "bear", "beat", "beef", "behave", "behaviour",
    "belong", "belt", "benefit", "billion", "bin", "biology", "birth",
    "biscuit", "bit", "blank", "blood", "blow", "board", "boil", "bone", "book",
    "borrow", "boss", "bottom", "bowl", "brain", "bridge", "bright", "brilliant",
    "broken", "brush", "burn", "businessman", "button", "camp", "camping",
    "care", "careful", "carefully", "carpet", "cartoon", "case", "cash",
    "catch", "cause", "celebrate", "celebrity", "certain", "certainly",
    "chance", "character", "charity", "chat", "check", "chef", "chemistry",
    "chip", "choice", "church", "cigarette", "circle", "classical", "clear",
    "clearly", "clever", "climate", "clothing", "cloud", "coach", "coast",
    "code", "colleague", "collect", "column", "comedy", "comfortable",
    "comment", "communicate", "community", "compete", "competition", "complain",
    "completely", "condition", "conference", "connect", "connected", "consider",
    "contain", "context", "continent", "continue", "control", "cooker", "copy",
    "corner", "correctly", "count", "couple", "cover", "crazy", "creative",
    "credit", "crime", "criminal", "cross", "crowd", "crowded", "cry",
    "cupboard", "curly", "cycle", "daily", "danger", "data", "dead", "deal",
    "death", "decision", "deep", "definitely", "degree", "dentist",
    "department", "depend", "desert", "designer", "destroy", "detective",
    "develop", "device", "diary", "differently", "digital", "direct",
    "direction", "director", "disagree", "disappear", "disaster", "discovery",
    "discussion", "disease", "distance", "divorced", "document", "double",
    "download", "downstairs", "drama", "drawing", "dream", "drive", "driving",
    "drop", "drug", "dry", "earn", "earth", "easily", "education", "effect",
    "either", "electric", "electrical", "electricity", "electronic", "employ",
    "employee", "employer", "empty", "ending", "energy", "engine", "engineer",
    "enormous", "enter", "environment", "equipment", "error", "especially",
    "essay", "everyday", "everywhere", "evidence", "exact", "exactly",
    "excellent", "except", "exist", "expect", "experience", "experiment",
    "expert", "explanation", "expression", "extreme", "extremely", "factor",
    "factory", "fail", "fair", "fan", "farming", "fashion", "fear", "feature",
    "feed", "female", "fiction", "field", "fight", "figure", "final",
    "finally", "finish", "first", "firstly", "fit", "fix", "flat", "flu",
    "fly", "flying", "focus", "following", "foreign", "forest", "fork",
    "formal", "fortunately", "forward", "fresh", "fridge", "frog", "fun",
    "furniture", "further", "future", "gallery", "gap", "gas", "gate",
    "general", "generally", "gift", "goal", "god", "gold", "golf",
    "government", "grass", "greet", "ground", "guest", "guide", "gun", "guy",
    "habit", "half", "hall", "happily", "hard", "headache", "heart", "heat",
    "heavy", "height", "helpful", "hero", "hide", "hill", "himself", "his",
    "historic", "historical", "honest", "horrible", "horror", "host", "hunt",
    "hurricane", "hurry", "identity", "ignore", "illegal", "illness", "image",
    "imaginary", "imagination", "immediately", "immigrant", "impact", "import",
    "importance", "impression", "impressive", "improvement", "incredibly",
    "indeed", "indicate", "indirect", "indoor", "indoors", "influence",
    "ingredient", "injure", "injured", "innocent", "insect", "inside",
    "instead", "instruction", "instructor", "instrument", "intelligent",
    "international", "introduction", "invent", "invention", "invitation",
    "invite", "involve", "item", "itself", "jam", "jazz", "jewellery", "joke",
    "journalist", "jump", "kid", "kill", "killing", "kiss", "knee", "knife",
    "knock", "knowledge", "lab", "laboratory", "lack", "lady", "lake", "lamp",
    "land", "laptop", "last", "later", "laughter", "law", "lawyer", "lazy",
    "lead", "leader", "leading", "learning", "least", "lecture", "lemon",
    "lend", "less", "level", "lift", "likely", "limit", "line", "link",
    "listener", "little", "lock", "look", "lorry", "lost", "loud", "loudly",
    "lovely", "low", "luck", "lucky", "mail", "major", "male", "manage",
    "manager", "manner", "mark", "marry", "material", "mathematics", "maths",
    "matter", "may", "media", "medical", "medicine", "memory", "mention",
    "metal", "method", "middle", "might", "mind", "mirror", "missing",
    "mobile", "monkey", "moon", "mostly", "motorcycle", "movement", "musical",
    "musician", "myself", "narrow", "national", "nature", "nearly",
    "necessary", "neck", "neither", "nervous", "network", "noise", "noisy",
    "none", "normal", "normally", "notice", "novel", "nowhere", "nut", "ocean",
    "offer", "officer", "oil", "onto", "opportunity", "option", "ordinary",
    "organization", "organize", "original", "ourselves", "outside", "oven",
    "own", "owner", "pack", "pain", "painter", "palace", "pants", "parking",
    "particular", "pass", "passenger", "past", "patient", "pattern", "pay",
    "peace", "penny", "per", "per cent", "perform", "perhaps", "permission",
    "personality", "pet", "petrol", "physical", "physics", "pick", "pilot",
    "planet", "plastic", "plate", "platform", "pleased", "pocket", "polite",
    "politician", "politics", "pollution", "population", "position",
    "possession", "possibility", "possibly", "poster", "power", "predict",
    "prediction", "prepared", "presentation", "press", "pressure", "pretend",
    "previous", "previously", "priest", "primary", "prince", "princess",
    "printing", "prisoner", "private", "producer", "production", "profession",
    "professional", "profit", "program", "programmer", "programme", "progress",
    "promise", "pronounce", "protect", "provide", "pub", "public", "publish",
    "pull", "purpose", "push", "quality", "quantity", "queen", "quietly",
    "race", "railway", "raise", "rate", "rather", "reach", "react", "realize",
    "receive", "recent", "recently", "reception", "recipe", "recognize",
    "recommend", "record", "recording", "recycle", "reduce", "refer", "region",
    "regular", "relationship", "remove", "repair", "replace", "reply",
    "report", "reporter", "request", "research", "researcher", "respond",
    "response", "rest", "review", "ride", "ring", "rise", "rock", "role",
    "roof", "round", "route", "rubbish", "rude", "run", "sadly", "safe",
    "sail", "sailing", "salary", "sale", "sauce", "save", "scared", "scary",
    "scene", "schedule", "score", "screen", "search", "season", "seat",
    "secondly", "secret", "secretary", "seem", "sense", "separate", "series",
    "serious", "serve", "service", "several", "shake", "shall", "shape",
    "share", "sheet", "ship", "shoulder", "shout", "shut", "side", "sign",
    "silver", "simple", "since", "singing", "single", "sir", "site", "size",
    "ski", "skiing", "skin", "sky", "slowly", "smartphone", "smell", "smile",
    "smoke", "smoking", "soap", "soccer", "social", "society", "sock", "soft",
    "soldier", "solution", "solve", "somewhere", "sort", "source", "speaker",
    "specific", "speech", "speed", "spider", "spoon", "square", "stage",
    "stair", "stamp", "star", "start", "state", "stay", "steal", "step",
    "stomach", "stone", "store", "storm", "straight", "strange", "strategy",
    "stress", "structure", "stupid", "succeed", "successful", "suddenly",
    "suggest", "suggestion", "suit", "support", "suppose", "sure", "surprise",
    "surprised", "surprising", "survey", "sweet", "symbol", "system", "tablet",
    "talk", "target", "task", "taste", "teaching", "teenage", "temperature",
    "term", "themselves", "thick", "thief", "thin", "thinking", "third",
    "thought", "throw", "tidy", "tie", "tip", "tool", "top", "tour", "tourism",
    "towards",
]

# ------------------------------------------------------ Academic Word List (AWL)
# Averil Coxhead, "Headwords of the Academic Word List" (2000), Victoria University
# of Wellington -- free PDF, retrieved 2026-07-18:
# https://www.wgtn.ac.nz/lals/resources/academicwordlist/awl-headwords/Headwords-of-the-Academic-Word-List.pdf
# 570 word families that occur frequently across academic writing regardless of
# subject, split into the 10 official sublists (most to least frequent). Kept here
# as two tiers: AWL_CORE (sublists 1-5, the most common academic vocabulary -- the
# words that show up constantly in IELTS/TOEFL-style writing) and AWL_ADVANCED
# (sublists 6-10, rarer). This is a distinct, complementary anchor to the Oxford
# 5000: Oxford is general-register frequency, AWL is specifically the vocabulary of
# formal academic writing, which is exactly the register IELTS Task 2 rewards.

AWL_CORE: list[str] = [
    "academy", "access", "achieve", "acquire", "adequate", "adjust",
    "administration", "affect", "alter", "alternative", "amend", "analyse",
    "annual", "apparent", "approach", "appropriate", "approximate", "area",
    "aspect", "assess", "assist", "assume", "attitude", "attribute",
    "authority", "available", "aware", "benefit", "capacity", "category",
    "challenge", "chapter", "circumstance", "civil", "clause", "code",
    "comment", "commission", "commit", "communicate", "community", "compensate",
    "complex", "component", "compound", "compute", "concentrate", "concept",
    "conclude", "conduct", "confer", "conflict", "consent", "consequent",
    "considerable", "consist", "constant", "constitute", "constrain",
    "construct", "consult", "consume", "contact", "context", "contract",
    "contrast", "contribute", "convene", "coordinate", "core", "corporate",
    "correspond", "create", "credit", "criteria", "culture", "cycle", "data",
    "debate", "decline", "deduce", "define", "demonstrate", "derive", "design",
    "despite", "dimension", "discrete", "distinct", "distribute", "document",
    "domestic", "dominate", "draft", "economy", "element", "emerge",
    "emphasis", "enable", "energy", "enforce", "ensure", "entity",
    "environment", "equate", "equivalent", "error", "establish", "estimate",
    "ethnic", "evaluate", "evident", "evolve", "exclude", "expand", "export",
    "expose", "external", "facilitate", "factor", "feature", "final",
    "finance", "focus", "formula", "framework", "function", "fund",
    "fundamental", "generate", "generation", "goal", "grant", "hence",
    "hypothesis", "identify", "illustrate", "image", "immigrate", "impact",
    "implement", "implicate", "imply", "impose", "income", "indicate",
    "individual", "initial", "injure", "instance", "institute", "integrate",
    "interact", "internal", "interpret", "invest", "investigate", "involve",
    "issue", "item", "job", "journal", "justify", "label", "labour", "layer",
    "legal", "legislate", "liberal", "licence", "link", "locate", "logic",
    "maintain", "major", "margin", "maximise", "mechanism", "medical",
    "mental", "method", "minor", "modify", "monitor", "negate", "network",
    "normal", "notion", "objective", "obtain", "obvious", "occupy", "occur",
    "option", "orient", "outcome", "output", "overall", "parallel",
    "parameter", "participate", "partner", "perceive", "percent", "period",
    "perspective", "phase", "philosophy", "physical", "policy", "positive",
    "potential", "precise", "predict", "previous", "primary", "prime",
    "principal", "principle", "prior", "proceed", "process", "professional",
    "project", "promote", "proportion", "psychology", "publish", "purchase",
    "pursue", "range", "ratio", "react", "regime", "region", "register",
    "regulate", "reject", "relevant", "rely", "remove", "require", "research",
    "reside", "resolve", "resource", "respond", "restrict", "retain",
    "revenue", "role", "scheme", "section", "sector", "secure", "seek",
    "select", "sequence", "series", "sex", "shift", "significant", "similar",
    "site", "source", "specific", "specify", "stable", "statistic", "status",
    "strategy", "stress", "structure", "style", "subsequent", "substitute",
    "sufficient", "sum", "summary", "survey", "sustain", "symbol", "target",
    "task", "technical", "technique", "technology", "text", "theory",
    "tradition", "transfer", "transit", "trend", "undertake", "valid", "vary",
    "version", "volume", "welfare", "whereas",
]

AWL_ADVANCED: list[str] = [
    "abandon", "abstract", "accommodate", "accompany", "accumulate", "accurate",
    "acknowledge", "adapt", "adult", "advocate", "aggregate", "aid", "albeit",
    "allocate", "ambiguous", "analogy", "anticipate", "append", "appreciate",
    "arbitrary", "assemble", "assign", "assure", "attach", "attain", "author",
    "automate", "behalf", "bias", "bond", "brief", "bulk", "capable", "cease",
    "channel", "chart", "chemical", "cite", "clarify", "classic", "coherent",
    "coincide", "collapse", "colleague", "commence", "commodity", "compatible",
    "compile", "complement", "comprehensive", "comprise", "conceive",
    "concurrent", "confine", "confirm", "conform", "contemporary",
    "contradict", "contrary", "controversy", "converse", "convert",
    "convince", "cooperate", "couple", "crucial", "currency", "decade",
    "definite", "denote", "deny", "depress", "detect", "deviate", "device",
    "devote", "differentiate", "diminish", "discriminate", "displace",
    "display", "dispose", "distort", "diverse", "domain", "drama", "duration",
    "dynamic", "edit", "eliminate", "empirical", "encounter", "enhance",
    "enormous", "equip", "erode", "estate", "ethic", "eventual", "exceed",
    "exhibit", "expert", "explicit", "exploit", "extract", "federal", "fee",
    "file", "finite", "flexible", "fluctuate", "format", "forthcoming",
    "foundation", "found", "furthermore", "gender", "globe", "grade",
    "guarantee", "guideline", "hierarchy", "highlight", "identical",
    "ideology", "ignorance", "implicit", "incentive", "incidence", "incline",
    "incorporate", "index", "induce", "inevitable", "infer", "infrastructure",
    "inherent", "inhibit", "initiate", "innovate", "input", "insert",
    "insight", "inspect", "integral", "integrity", "intelligence", "intense",
    "intermediate", "interval", "intervene", "intrinsic", "invoke", "isolate",
    "lecture", "levy", "likewise", "manipulate", "manual", "mature", "media",
    "mediate", "medium", "migrate", "military", "minimal", "minimise",
    "minimum", "ministry", "mode", "motive", "mutual", "neutral",
    "nevertheless", "nonetheless", "norm", "notwithstanding", "nuclear",
    "odd", "offset", "ongoing", "overlap", "overseas", "panel", "paradigm",
    "paragraph", "passive", "persist", "phenomenon", "plus", "portion",
    "pose", "practitioner", "precede", "predominant", "preliminary",
    "presume", "priority", "prohibit", "prospect", "protocol", "publication",
    "qualitative", "quote", "radical", "random", "rational", "recover",
    "refine", "reinforce", "relax", "release", "reluctance", "restore",
    "restrain", "reveal", "reverse", "revise", "revolution", "rigid",
    "route", "scenario", "schedule", "scope", "simulate", "so-called",
    "sole", "somewhat", "sphere", "straightforward", "submit", "subordinate",
    "subsidy", "successor", "supplement", "survive", "suspend", "tape",
    "team", "tense", "terminate", "theme", "thereby", "thesis", "topic",
    "trace", "transform", "transmit", "transport", "trigger", "ultimate",
    "undergo", "underlie", "uniform", "unify", "unique", "utilise",
    "vehicle", "via", "violate", "virtual", "visible", "vision", "visual",
    "voluntary", "whereby", "widespread",
]


def known_baseline_words(tier: str = "b2") -> set[str]:
    """Words a learner at this target tier can be assumed to already know.

    Used as a deterministic backstop in generate_vocab: after the LLM returns
    words, drop any whose entire term is one of these (case-insensitive) instead
    of just hoping the prompt-level instruction was followed. A1+A2 for a B2
    target, A1+A2+B1-equivalent caution is intentionally NOT extended further
    (see OXFORD_3000_A1/A2 module docstring for why B1/B2 core stays out of this
    set), so this only ever removes genuinely basic words, never legitimate
    B1/B2 vocabulary a learner is still building.
    """
    if tier in ("a1", "a2", "b1"):
        return set()
    return {w.lower() for w in OXFORD_3000_A1 + OXFORD_3000_A2}


def sample_academic_words(count: int = 10, tier: str = "mixed") -> list[str]:
    """A fresh random sample of Academic Word List items -- formal-essay register,
    distinct from (and complementary to) the general-frequency Oxford 5000 sample.
    """
    pool = {
        "core": AWL_CORE,
        "advanced": AWL_ADVANCED,
        "mixed": AWL_CORE + AWL_ADVANCED,
    }.get(tier, AWL_CORE + AWL_ADVANCED)
    return random.sample(pool, min(count, len(pool)))


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
        "keywords": ["sleep", "insomnia", "rem sleep", "circadian"],
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
        "keywords": ["archaeology", "archaeological", "excavation", "artefact", "artifact"],
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
    {
        "id": "photosynthesis",
        "topic": "biology / photosynthesis",
        "keywords": ["photosynthesis", "plants", "chlorophyll"],
        "title": "Photosynthesis",
        "source_url": "https://en.wikipedia.org/wiki/Photosynthesis",
        "license": "CC BY-SA 4.0, adapted from Wikipedia",
        "text": (
            "Photosynthesis is the biological process by which photopigment-bearing "
            "organisms — most plants, algae and cyanobacteria — convert light "
            "energy, typically from sunlight, into the chemical energy needed to "
            "fuel their metabolism. The term usually refers to oxygenic "
            "photosynthesis, which splits water and releases oxygen as a "
            "byproduct; the resulting energy is stored in organic compounds such "
            "as carbohydrates.\n\n"
            "Some bacteria perform anoxygenic photosynthesis instead, splitting "
            "hydrogen sulfide rather than water and releasing sulfur instead of "
            "oxygen. Photosynthesis plays a critical role in maintaining Earth's "
            "oxygen levels and supplies the biological energy that fuels complex "
            "life. It was first properly understood in 1779, when Jan Ingenhousz "
            "demonstrated that plants require light, not merely soil and water, "
            "in order to grow."
        ),
    },
    {
        "id": "evolution",
        "topic": "biology / evolution and natural selection",
        "keywords": ["evolution", "natural selection", "darwin", "adaptation"],
        "title": "Evolution",
        "source_url": "https://en.wikipedia.org/wiki/Evolution",
        "license": "CC BY-SA 4.0, adapted from Wikipedia",
        "text": (
            "Evolution is the change in the heritable characteristics of "
            "biological populations over successive generations. It occurs "
            "through mechanisms such as natural selection and genetic drift "
            "acting on genetic variation, making certain traits progressively "
            "more or less common within a population over time.\n\n"
            "The scientific theory of evolution by natural selection was "
            "developed independently by two British naturalists, Charles Darwin "
            "and Alfred Russel Wallace, in the mid-19th century, as an "
            "explanation for why organisms are so well adapted to their physical "
            "and biological environments. Darwin set out this theory in detail "
            "in his landmark book On the Origin of Species, which established "
            "the framework still used today for understanding how species "
            "change over time."
        ),
    },
    {
        "id": "genetics",
        "topic": "biology / genetics and heredity",
        "keywords": ["genetics", "genes", "dna", "heredity", "mendel"],
        "title": "Genetics",
        "source_url": "https://en.wikipedia.org/wiki/Genetics",
        "license": "CC BY-SA 4.0, adapted from Wikipedia",
        "text": (
            "Genetics is the study of genes, genetic variation, and heredity in "
            "organisms. It is an important branch of biology because heredity is "
            "central to how organisms evolve. Gregor Mendel, a 19th-century "
            "Augustinian friar, is considered the founder of the science: by "
            "studying how traits were inherited in pea plants, he discovered "
            "that organisms pass on characteristics through discrete units of "
            "inheritance — what are now called genes.\n\n"
            "Modern genetics has expanded well beyond Mendel's original work, "
            "and now covers the function and behaviour of genes at the "
            "cellular, organismal and population level. Genes interact with "
            "environmental factors to shape how an organism develops and "
            "behaves, a relationship often summed up as 'nature versus nurture'. "
            "Two genetically identical seeds, for example, can grow to very "
            "different heights if one is planted in an arid climate and the "
            "other in a temperate one."
        ),
    },
    {
        "id": "volcano",
        "topic": "geography / volcanoes",
        "keywords": ["volcano", "eruption", "lava", "magma"],
        "title": "Volcano",
        "source_url": "https://en.wikipedia.org/wiki/Volcano",
        "license": "CC BY-SA 4.0, adapted from Wikipedia",
        "text": (
            "A volcano is a vent or fissure in a planet's crust that allows hot "
            "lava, volcanic ash and gases to escape from a magma chamber below "
            "the surface. On Earth, volcanoes occur mainly where tectonic plates "
            "diverge or converge; most are actually underwater, since most plate "
            "boundaries lie beneath the ocean. The Mid-Atlantic Ridge is a "
            "classic example of divergent volcanic activity, while the Pacific "
            "'Ring of Fire' is dominated by convergent activity — divergent "
            "volcanism tends to be gentle, while convergent volcanism tends to "
            "produce violent eruptions.\n\n"
            "Volcanoes are usually classified by how often they erupt: active "
            "volcanoes have a recent history of eruption and may erupt again, "
            "dormant volcanoes have not erupted since roughly 12,000 years ago "
            "but remain capable of future activity, and extinct volcanoes have "
            "no remaining magma source at all. Large eruptions can noticeably "
            "cool the planet, since ash and sulfuric acid droplets in the "
            "atmosphere block sunlight — historically triggering 'volcanic "
            "winters' and severe famines."
        ),
    },
    {
        "id": "earthquake",
        "topic": "geography / earthquakes",
        "keywords": ["earthquake", "seismic", "tremor", "fault line"],
        "title": "Earthquake",
        "source_url": "https://en.wikipedia.org/wiki/Earthquake",
        "license": "CC BY-SA 4.0, adapted from Wikipedia",
        "text": (
            "An earthquake, also called a quake or a tremor, is the shaking of "
            "the Earth's surface caused by a sudden release of energy in the "
            "lithosphere that generates seismic waves. Earthquakes vary "
            "enormously in severity, from tremors too small to notice to "
            "violent events capable of destroying entire cities. Seismicity at "
            "a given location describes the average rate of seismic energy "
            "released there over time.\n\n"
            "In its broadest sense, the term covers any event that produces "
            "seismic waves, whether natural or triggered by human activity such "
            "as mining, fracking or underground nuclear tests. The point where "
            "an earthquake originates underground is called the hypocentre, and "
            "the point on the surface directly above it is the epicentre. Most "
            "earthquakes are caused by geological faults, though volcanic "
            "activity and landslides can also trigger them."
        ),
    },
    {
        "id": "black-hole",
        "topic": "astronomy / black holes",
        "keywords": ["black hole", "astronomy", "event horizon", "gravity", "einstein"],
        "title": "Black Hole",
        "source_url": "https://en.wikipedia.org/wiki/Black_hole",
        "license": "CC BY-SA 4.0, adapted from Wikipedia",
        "text": (
            "A black hole is an astronomical object so compact that its gravity "
            "prevents anything, including light, from escaping. Albert "
            "Einstein's theory of general relativity predicts that any "
            "sufficiently dense mass will collapse into such an object; the "
            "boundary beyond which nothing can escape is called the event "
            "horizon.\n\n"
            "Objects whose gravity might be strong enough to trap light were "
            "first proposed as early as the 18th century, but it was not until "
            "1916 that the first mathematical solution describing a black hole "
            "was derived from general relativity. For decades black holes "
            "remained a largely theoretical curiosity, until the 1960s showed "
            "they were a natural and unavoidable prediction of Einstein's "
            "theory. Cygnus X-1 became the first object widely accepted by "
            "astronomers as an actual black hole, in 1971."
        ),
    },
    {
        "id": "industrial-revolution",
        "topic": "history / the industrial revolution",
        "keywords": ["industrial revolution", "industrialisation", "factories", "manufacturing history"],
        "title": "Industrial Revolution",
        "source_url": "https://en.wikipedia.org/wiki/Industrial_Revolution",
        "license": "CC BY-SA 4.0, adapted from Wikipedia",
        "text": (
            "The Industrial Revolution was a period in which the global economy "
            "shifted towards more widespread, efficient and stable "
            "manufacturing, moving away from hand production and towards "
            "machines, new methods of chemical manufacturing and iron "
            "production, the growing use of water and steam power, and the "
            "rise of the mechanised factory. It began in Great Britain around "
            "1760 and had spread to continental Europe and the United States by "
            "about 1840; many economic historians regard its onset as one of "
            "the most significant events in human history, comparable only to "
            "the adoption of agriculture in terms of material progress.\n\n"
            "Output increased dramatically as a result, driving an "
            "unprecedented rise in population. Britain led much of the early "
            "innovation and, by the mid-18th century, had become the world's "
            "leading commercial nation. The textile industry was the first to "
            "adopt modern production methods and became the dominant industry "
            "of the period in terms of employment, output and capital invested."
        ),
    },
    {
        "id": "ancient-egypt",
        "topic": "history / ancient Egypt",
        "keywords": ["ancient egypt", "pharaoh", "nile", "pyramids"],
        "title": "Ancient Egypt",
        "source_url": "https://en.wikipedia.org/wiki/Ancient_Egypt",
        "license": "CC BY-SA 4.0, adapted from Wikipedia",
        "text": (
            "Ancient Egypt was a cradle of civilisation that developed along the "
            "lower reaches of the Nile River in north-eastern Africa. It "
            "emerged as a unified state around 3150 BC, when Upper and Lower "
            "Egypt were brought together under a single ruler, traditionally "
            "identified as Narmer.\n\n"
            "Egyptian history unfolded through alternating periods of stability "
            "and upheaval. Three major stable eras — the Old Kingdom, the "
            "Middle Kingdom and the New Kingdom — represent the peaks of "
            "Egyptian power and cultural achievement, each separated by an "
            "intermediate period of relative decline. The New Kingdom marked "
            "the height of Egypt's influence, extending its control over much "
            "of Nubia and large parts of the Levant."
        ),
    },
    {
        "id": "ancient-rome",
        "topic": "history / ancient Rome",
        "keywords": ["ancient rome", "roman empire", "roman republic"],
        "title": "Ancient Rome",
        "source_url": "https://en.wikipedia.org/wiki/Ancient_Rome",
        "license": "CC BY-SA 4.0, adapted from Wikipedia",
        "text": (
            "In modern historiography, ancient Rome refers to Roman "
            "civilisation from the founding of the city of Rome in the 8th "
            "century BC to the collapse of the Western Roman Empire in the 5th "
            "century AD — an era of roughly 1,200 years, traditionally divided "
            "into three periods: the Kingdom, the Republic and the Empire.\n\n"
            "The city began as a small Italic settlement, traditionally dated "
            "to 753 BC, on the banks of the River Tiber. From this modest "
            "beginning, Rome grew through military conquest and strategic "
            "alliances into the dominant power of the Mediterranean. At its "
            "height, around 117 AD, the empire controlled roughly five million "
            "square kilometres and an estimated 50 to 90 million people — about "
            "a fifth of the world's population at the time."
        ),
    },
    {
        "id": "printing-press",
        "topic": "history / the printing press",
        "keywords": ["printing press", "gutenberg", "printing revolution"],
        "title": "Printing Press",
        "source_url": "https://en.wikipedia.org/wiki/Printing_press",
        "license": "CC BY-SA 4.0, adapted from Wikipedia",
        "text": (
            "A printing press is a mechanical device that transfers ink onto "
            "paper or cloth by applying pressure to an inked surface. It "
            "replaced the far slower method of rubbing paper by hand against a "
            "printing surface, and its invention fundamentally reshaped how "
            "books were produced and how information spread through society.\n\n"
            "Around 1440, the goldsmith Johannes Gutenberg developed a method "
            "for mass-producing movable metal type, launching what is now "
            "called the Printing Revolution. Building on the screw presses "
            "already used in Europe, a printing press of around 1600 could "
            "produce roughly 3,600 impressions in a 15-hour working day, far "
            "more than earlier woodblock methods. The technology spread "
            "rapidly outward from Gutenberg's workshop in Mainz, reaching about "
            "270 European cities within a few decades; by 1500, presses across "
            "Western Europe had already produced more than twenty million "
            "copies of printed works."
        ),
    },
    {
        "id": "second-language-acquisition",
        "topic": "linguistics / learning a second language",
        "keywords": ["second language", "language learning", "bilingualism", "language acquisition"],
        "title": "Second-Language Acquisition",
        "source_url": "https://en.wikipedia.org/wiki/Second-language_acquisition",
        "license": "CC BY-SA 4.0, adapted from Wikipedia",
        "text": (
            "Second-language acquisition (SLA) is the process by which people "
            "learn a language other than their native language. Researchers in "
            "the field study how learners build up their knowledge of a second "
            "language, drawing on cognitive, social and linguistic "
            "perspectives: cognitive approaches examine memory and attention, "
            "sociocultural theories emphasise the role of social interaction "
            "and immersion, and linguistic approaches look at which parts of "
            "language ability are innate and which are learned.\n\n"
            "Individual factors such as age, motivation and personality also "
            "shape how successfully someone acquires a second language, which "
            "is part of why researchers study ideas like the critical period "
            "hypothesis and different learning strategies. Beyond acquisition "
            "itself, the field also studies language loss — known as "
            "second-language attrition — and how much formal classroom "
            "instruction actually improves learning outcomes."
        ),
    },
    {
        "id": "endangered-languages",
        "topic": "linguistics / endangered languages",
        "keywords": ["endangered language", "language death", "linguistic diversity"],
        "title": "Endangered Languages",
        "source_url": "https://en.wikipedia.org/wiki/Endangered_language",
        "license": "CC BY-SA 4.0, adapted from Wikipedia",
        "text": (
            "An endangered or moribund language is one at risk of "
            "disappearing, either because its speakers are dying out or "
            "because they are shifting to speaking another language instead. A "
            "language's loss becomes final once it has no remaining native "
            "speakers, at which point it is considered a dead or extinct "
            "language.\n\n"
            "While languages have always gone extinct throughout history, "
            "several modern forces are accelerating the rate of language "
            "death, including globalisation, mass migration, linguistic "
            "imperialism and what some researchers call 'linguicide'. The "
            "usual process is language shift, in which a community gradually "
            "abandons its native tongue in favour of a language that offers "
            "greater social or economic advantage or wider practical use — a "
            "change that ultimately results in a loss of linguistic diversity "
            "and cultural heritage for the communities affected."
        ),
    },
    {
        "id": "memory",
        "topic": "psychology / memory",
        "keywords": ["memory", "remembering", "amnesia", "forgetting"],
        "title": "Memory",
        "source_url": "https://en.wikipedia.org/wiki/Memory",
        "license": "CC BY-SA 4.0, adapted from Wikipedia",
        "text": (
            "Memory is the faculty of the mind by which information is "
            "encoded, stored and retrieved when needed; more broadly, it is "
            "the retention of information over time for the purpose of "
            "guiding future action. Psychologists usually distinguish between "
            "short-term and long-term memory, and between different types of "
            "long-term memory such as episodic memory (personal experiences) "
            "and procedural memory (skills and habits).\n\n"
            "Memory loss typically shows up as ordinary forgetfulness or, in "
            "more severe cases, as a disorder such as amnesia. Memory's "
            "importance is easy to underestimate: if past events could not be "
            "remembered at all, it would be impossible for language, "
            "relationships or even a stable sense of personal identity to "
            "develop."
        ),
    },
    {
        "id": "emotional-intelligence",
        "topic": "psychology / emotional intelligence",
        "keywords": ["emotional intelligence", "eq", "emotions", "goleman"],
        "title": "Emotional Intelligence",
        "source_url": "https://en.wikipedia.org/wiki/Emotional_intelligence",
        "license": "CC BY-SA 4.0, adapted from Wikipedia",
        "text": (
            "Emotional intelligence (EI), sometimes called emotional quotient "
            "(EQ), is the ability to perceive, use, understand and manage "
            "emotions, both one's own and other people's. A person with high "
            "emotional intelligence can recognise their own feelings and those "
            "of others, use emotional information to guide their thinking and "
            "behaviour, tell different feelings apart, and adjust their "
            "emotional responses to suit different situations.\n\n"
            "The concept became widely known after psychologist Daniel Goleman "
            "published his bestselling 1995 book, Emotional Intelligence. "
            "Researchers still disagree about how fixed the trait is: some "
            "believe emotional intelligence can be developed and strengthened "
            "through practice, while others argue it is closer to an innate "
            "characteristic that people are simply born with."
        ),
    },
    {
        "id": "motivation",
        "topic": "psychology / motivation",
        "keywords": ["motivation", "goal-directed behaviour", "drive"],
        "title": "Motivation",
        "source_url": "https://en.wikipedia.org/wiki/Motivation",
        "license": "CC BY-SA 4.0, adapted from Wikipedia",
        "text": (
            "Motivation is the internal state that drives people toward "
            "goal-directed behaviour. It is often described as the force that "
            "explains why a person or animal starts, continues or stops a "
            "particular behaviour at a given moment; its exact definition is "
            "still debated among researchers, and it is studied across "
            "psychology, neuroscience and philosophy.\n\n"
            "Motivational states are usually described in terms of direction, "
            "intensity and persistence: direction refers to the goal being "
            "pursued, intensity is the strength of the drive and how much "
            "effort it produces, and persistence is how long someone keeps "
            "engaging with an activity. Motivation is often broken down into "
            "two phases — first setting a goal, and then making the sustained "
            "effort needed to actually reach it."
        ),
    },
    {
        "id": "mental-health",
        "topic": "health / mental health",
        "keywords": ["mental health", "well-being", "psychological health"],
        "title": "Mental Health",
        "source_url": "https://en.wikipedia.org/wiki/Mental_health",
        "license": "CC BY-SA 4.0, adapted from Wikipedia",
        "text": (
            "Mental health covers a person's emotional, psychological and "
            "social well-being, and influences how they think, perceive the "
            "world and behave. It plays a central role in how people cope with "
            "stress, relate to others and function in daily life. The World "
            "Health Organization defines mental health as a state of "
            "well-being in which a person can realise their own abilities, "
            "cope with the normal stresses of life, work productively, and "
            "contribute to their community.\n\n"
            "The concept covers more than the simple absence of illness: it "
            "includes subjective well-being, a sense of self-efficacy and "
            "autonomy, competence, and the ability to realise one's "
            "intellectual and emotional potential. Mental health also shapes "
            "how people handle everyday stress, maintain relationships and "
            "make decisions."
        ),
    },
    {
        "id": "vaccine",
        "topic": "health / vaccines and immunology",
        "keywords": ["vaccine", "vaccination", "immunity", "immunization"],
        "title": "Vaccine",
        "source_url": "https://en.wikipedia.org/wiki/Vaccine",
        "license": "CC BY-SA 4.0, adapted from Wikipedia",
        "text": (
            "A vaccine is a biological preparation that provides acquired "
            "immunity to a specific infectious or, in some cases, malignant "
            "disease. Most vaccines work by including an agent that resembles "
            "a disease-causing microorganism closely enough to trigger the "
            "immune system to recognise and respond to it, without causing the "
            "disease itself.\n\n"
            "Vaccines can be either preventive, protecting against future "
            "infection, or therapeutic, helping the body fight an existing "
            "disease such as cancer. Some vaccines produce what is called "
            "sterilising immunity, which prevents infection entirely rather "
            "than merely reducing its severity. Vaccination is widely "
            "considered the most effective method of preventing infectious "
            "disease, and large-scale immunisation programmes are credited "
            "with eradicating smallpox worldwide and sharply reducing diseases "
            "such as polio, measles and tetanus."
        ),
    },
    {
        "id": "public-health",
        "topic": "health / public health systems",
        "keywords": ["public health", "healthcare system", "epidemiology"],
        "title": "Public Health",
        "source_url": "https://en.wikipedia.org/wiki/Public_health",
        "license": "CC BY-SA 4.0, adapted from Wikipedia",
        "text": (
            "Public health is the science of preventing disease, prolonging "
            "life and promoting health through the organised efforts of "
            "society, including governments, organisations, communities and "
            "individuals. It rests on analysing the determinants of a "
            "population's health and the threats it faces; the 'public' in "
            "question can be as small as a handful of people or as large as an "
            "entire continent, as a pandemic demonstrates.\n\n"
            "Public health is an interdisciplinary field, drawing on "
            "epidemiology, biostatistics, the social sciences and health "
            "service management, alongside sub-fields such as environmental "
            "health, occupational safety and health economics. Common public "
            "health initiatives include promoting hand-washing, delivering "
            "vaccination programmes, improving air quality, encouraging "
            "smoking cessation, and expanding access to healthcare — all "
            "implemented through the surveillance of health indicators and the "
            "promotion of healthier behaviours across a population."
        ),
    },
    {
        "id": "economic-inequality",
        "topic": "economics / income and wealth inequality",
        "keywords": ["income inequality", "wealth inequality", "economic inequality", "gini coefficient"],
        "title": "Economic Inequality",
        "source_url": "https://en.wikipedia.org/wiki/Economic_inequality",
        "license": "CC BY-SA 4.0, adapted from Wikipedia",
        "text": (
            "Economic inequality is an umbrella term covering three related "
            "concepts: income inequality, or how the total money people earn "
            "is distributed among them; wealth inequality, or how accumulated "
            "assets are distributed among owners; and consumption inequality, "
            "or how spending is distributed among a population. Each can be "
            "measured between countries, within a single country, or between "
            "and within sub-groups such as age, gender or generational "
            "cohorts.\n\n"
            "The Gini coefficient is the most widely used metric for measuring "
            "income inequality, while the Inequality-adjusted Human "
            "Development Index is a composite measure that factors inequality "
            "into a country's overall development score. Discussions of "
            "economic inequality often turn on related concepts such as "
            "equity, equality of outcome and equality of opportunity — which "
            "are not necessarily the same thing."
        ),
    },
    {
        "id": "globalization",
        "topic": "economics / globalization",
        "keywords": ["globalization", "globalisation", "global economy", "international trade"],
        "title": "Globalization",
        "source_url": "https://en.wikipedia.org/wiki/Globalization",
        "license": "CC BY-SA 4.0, adapted from Wikipedia",
        "text": (
            "Globalisation is the process of increasing interdependence and "
            "integration among the economies, markets, societies and cultures "
            "of different countries. It has been driven by a combination of "
            "factors, including reduced trade barriers, freer movement of "
            "capital, improved transport infrastructure and, more recently, "
            "advances in information technology.\n\n"
            "The term itself emerged in the early twentieth century but only "
            "became widely used in the 1990s, when it came to describe the "
            "growing international connectivity that followed the end of the "
            "Cold War. Large-scale globalisation is often traced back to the "
            "1820s, with a further acceleration in the late nineteenth and "
            "early twentieth centuries as transport and communication "
            "technologies advanced rapidly following industrialisation."
        ),
    },
    {
        "id": "tourism",
        "topic": "economics / the tourism industry",
        "keywords": ["tourism", "tourist industry", "travel industry"],
        "title": "Tourism",
        "source_url": "https://en.wikipedia.org/wiki/Tourism",
        "license": "CC BY-SA 4.0, adapted from Wikipedia",
        "text": (
            "Tourism is travel undertaken for pleasure, along with the "
            "commercial activity of providing and supporting that travel. The "
            "UN Tourism agency defines it more broadly still, as people "
            "travelling to and staying in places outside their usual "
            "environment for no more than one consecutive year, for leisure, "
            "business or other purposes, and for at least 24 hours. Tourism "
            "can be domestic, within a traveller's own country, or "
            "international, and international tourism affects a country's "
            "balance of payments in both directions.\n\n"
            "The industry is highly sensitive to global shocks: tourist "
            "numbers fell during the 2008-2009 economic slowdown and the H1N1 "
            "outbreak, recovered over the following decade, and then "
            "collapsed again when the COVID-19 pandemic brought international "
            "travel to a near-total stop. The UN World Tourism Organization "
            "estimated that international arrivals fell by 58 to 78 percent "
            "in 2020, at a potential cost of up to 1.2 trillion US dollars in "
            "lost tourism revenue."
        ),
    },
    {
        "id": "gender-equality",
        "topic": "society / gender equality",
        "keywords": ["gender equality", "gender equity", "women's rights"],
        "title": "Gender Equality",
        "source_url": "https://en.wikipedia.org/wiki/Gender_equality",
        "license": "CC BY-SA 4.0, adapted from Wikipedia",
        "text": (
            "Gender equality, also called sexual equality or equality of the "
            "sexes, is the state of having equal access to resources and "
            "opportunities regardless of gender, including economic "
            "participation and decision-making, and of valuing different "
            "behaviours, aspirations and needs equally regardless of gender. "
            "It does not mean treating everyone identically, but ensuring "
            "everyone has the same underlying rights and opportunities.\n\n"
            "UNICEF describes the goal as ensuring that women and men, girls "
            "and boys, enjoy the same rights, resources, opportunities and "
            "protections — while explicitly noting that this does not require "
            "them to be treated in exactly the same way in every "
            "circumstance. Gender equality is widely treated as both a "
            "fundamental human right and a necessary foundation for a "
            "peaceful, prosperous and sustainable world."
        ),
    },
    {
        "id": "population-ageing",
        "topic": "society / an ageing population",
        "keywords": ["population ageing", "aging population", "elderly", "demographic change"],
        "title": "Population Ageing",
        "source_url": "https://en.wikipedia.org/wiki/Population_ageing",
        "license": "CC BY-SA 4.0, adapted from Wikipedia",
        "text": (
            "Population ageing is an overall shift in the age structure of a "
            "population, usually summarised as a rise in the median age. It is "
            "driven mainly by two long-term trends: declining fertility rates "
            "and declining mortality rates. These trends first appeared in "
            "developed countries in the late 19th century, but by the late "
            "20th century the world's population as a whole had begun to age, "
            "and the pattern is now visible in virtually every developing "
            "country too.\n\n"
            "The number of people aged 60 or older has roughly tripled since "
            "1950, passing 600 million by 2000 and 700 million by 2006; the "
            "United Nations projects that this group will reach 2.1 billion by "
            "2050. Countries vary widely in how fast they are ageing, and "
            "those that started ageing later will generally have less time to "
            "adapt. Policy responses range from measures that grow the "
            "working-age population to reforms that adapt pensions, "
            "healthcare and other systems to an older society."
        ),
    },
    {
        "id": "criminology",
        "topic": "society / crime and criminology",
        "keywords": ["criminology", "crime", "criminal justice", "deviant behaviour"],
        "title": "Criminology",
        "source_url": "https://en.wikipedia.org/wiki/Criminology",
        "license": "CC BY-SA 4.0, adapted from Wikipedia",
        "text": (
            "Criminology is the interdisciplinary study of crime and deviant "
            "behaviour, drawing on sociology, political science, economics, "
            "psychology, philosophy, psychiatry and law. Criminologists study "
            "the nature of crime and criminals, the origins of criminal law, "
            "the causes of criminal behaviour, and how society responds to "
            "it.\n\n"
            "The field generally pursues three lines of inquiry: understanding "
            "criminal law and how it develops, analysing what drives criminal "
            "behaviour and the characteristics of offenders, and studying how "
            "crime can be prevented and how offenders can be rehabilitated. "
            "Because of this broad scope, criminological research touches on "
            "the work of legislatures, police forces, courts, prisons and "
            "social welfare agencies alike."
        ),
    },
    {
        "id": "deforestation",
        "topic": "environment / deforestation",
        "keywords": ["deforestation", "forest clearance", "logging", "tropical forest"],
        "title": "Deforestation",
        "source_url": "https://en.wikipedia.org/wiki/Deforestation",
        "license": "CC BY-SA 4.0, adapted from Wikipedia",
        "text": (
            "Deforestation, or forest clearance, is the removal and "
            "destruction of a forest so that the land can be converted to "
            "another use, such as farming or urban development. Forests "
            "currently cover about 31 percent of the Earth's land surface — "
            "roughly a third less than before large-scale agriculture began, "
            "with much of that loss occurring in just the last few centuries. "
            "Globally, an estimated 2,400 trees are felled every minute, "
            "though tropical deforestation rates vary considerably depending "
            "on the region and the source.\n\n"
            "In 2019 alone, nearly a third of all tree cover loss — some 3.8 "
            "million hectares — occurred in humid tropical primary forest, the "
            "mature rainforest that is especially important for biodiversity "
            "and carbon storage. At that rate, the world is losing an area of "
            "primary forest roughly equivalent to a football pitch every six "
            "seconds."
        ),
    },
    {
        "id": "water-scarcity",
        "topic": "environment / water scarcity",
        "keywords": ["water scarcity", "water stress", "fresh water", "water crisis"],
        "title": "Water Scarcity",
        "source_url": "https://en.wikipedia.org/wiki/Water_scarcity",
        "license": "CC BY-SA 4.0, adapted from Wikipedia",
        "text": (
            "Water scarcity, closely related to water stress, is the lack of "
            "sufficient, locally or economically accessible fresh water to "
            "meet standard demand in a given region. The concept covers two "
            "distinct situations: physical water scarcity, where there simply "
            "is not enough water to meet all demands, including those of "
            "natural ecosystems; and economic water scarcity, where enough "
            "water exists but a lack of investment in infrastructure, "
            "technology or human capacity prevents people from accessing "
            "it.\n\n"
            "Desert regions are the clearest examples of physical scarcity, "
            "while parts of Sub-Saharan Africa illustrate economic scarcity: "
            "natural water resources may be adequate, but poor infrastructure "
            "and underinvestment leave many communities without reliable "
            "access. Distinguishing between the two matters for policy, since "
            "physical scarcity calls for managing demand while economic "
            "scarcity calls for investment in infrastructure."
        ),
    },
    {
        "id": "ocean-acidification",
        "topic": "environment / ocean acidification",
        "keywords": ["ocean acidification", "seawater ph", "marine chemistry"],
        "title": "Ocean Acidification",
        "source_url": "https://en.wikipedia.org/wiki/Ocean_acidification",
        "license": "CC BY-SA 4.0, adapted from Wikipedia",
        "text": (
            "Ocean acidification is the ongoing decrease in the pH of the "
            "Earth's oceans, meaning that average seawater is gradually "
            "becoming less alkaline over time. Between 1950 and 2020, surface "
            "ocean pH fell from around 8.15 to 8.05, a change driven almost "
            "entirely by human carbon dioxide emissions. As atmospheric CO2 — "
            "now above 422 parts per million — dissolves into seawater, it "
            "forms carbonic acid, which breaks down into bicarbonate and "
            "hydrogen ions, lowering the water's pH and increasing its "
            "acidity, even though seawater remains alkaline overall.\n\n"
            "Marine organisms that build shells or skeletons from calcium "
            "carbonate, including corals and mollusks such as oysters and "
            "mussels, are especially vulnerable to this change, since more "
            "acidic water makes it harder for them to form and maintain their "
            "protective structures."
        ),
    },
    {
        "id": "social-media",
        "topic": "technology / social media",
        "keywords": ["social media", "social networking", "online platforms"],
        "title": "Social Media",
        "source_url": "https://en.wikipedia.org/wiki/Social_media",
        "license": "CC BY-SA 4.0, adapted from Wikipedia",
        "text": (
            "Social media are digital technologies that allow users to "
            "create, share and interact with content — such as text, photos, "
            "videos and ideas — within online communities and networks. "
            "Platforms typically combine user-generated content with "
            "organisation- or brand-specific profiles, and let users build "
            "networks by connecting their own profile to others.\n\n"
            "The defining feature of social media is participation: rather "
            "than simply broadcasting information to an audience, platforms "
            "are built around communal activity, letting users share, "
            "co-create, discuss and modify content together through web and "
            "mobile applications. This participatory structure is what "
            "distinguishes social media from earlier, one-directional forms of "
            "mass media such as television or print."
        ),
    },
    {
        "id": "robotics",
        "topic": "technology / robotics",
        "keywords": ["robotics", "robots", "automation technology"],
        "title": "Robotics",
        "source_url": "https://en.wikipedia.org/wiki/Robotics",
        "license": "CC BY-SA 4.0, adapted from Wikipedia",
        "text": (
            "Robotics is the interdisciplinary field concerned with the "
            "design, construction, operation and use of robots; someone who "
            "works in the field is called a roboticist. Most robots combine "
            "four basic components: a power source such as a battery, a "
            "mechanical structure, a control system built from electrical "
            "circuits, and software that governs their behaviour, whether "
            "through remote control or some degree of artificial "
            "intelligence.\n\n"
            "The central aim of most robotics work is to build machines that "
            "assist people across a wide range of fields, including "
            "agriculture, construction, manufacturing, medicine, mining, "
            "space exploration and transportation. Robots are also reshaping "
            "the labour market, displacing some categories of human workers "
            "even as the field itself creates new, often highly skilled, "
            "career opportunities — a tension that has prompted proposals "
            "ranging from retraining programmes to universal basic income."
        ),
    },
    {
        "id": "animal-cognition",
        "topic": "biology / animal cognition and behaviour",
        "keywords": ["animal cognition", "animal behaviour", "animal intelligence"],
        "title": "Animal Cognition",
        "source_url": "https://en.wikipedia.org/wiki/Animal_cognition",
        "license": "CC BY-SA 4.0, adapted from Wikipedia",
        "text": (
            "Animal cognition refers to the mental capacities of non-human "
            "animals, including even insects. The field grew out of "
            "comparative psychology and now draws on ethology, behavioural "
            "ecology and evolutionary psychology to study how different "
            "species perceive, learn, remember and solve problems.\n\n"
            "Researchers have examined cognition across a striking range of "
            "animals, including primates, cetaceans such as dolphins and "
            "whales, elephants, dogs, cats and other mammals; birds such as "
            "parrots and corvids; reptiles including lizards and turtles; and "
            "even fish and invertebrates. This breadth of research has "
            "steadily challenged the older assumption that complex thought is "
            "unique to humans, revealing sophisticated memory, tool use, "
            "social learning and problem-solving abilities across the animal "
            "kingdom."
        ),
    },
]

_PASSAGE_BY_ID: dict[str, dict[str, Any]] = {p["id"]: p for p in PASSAGES}


def find_passage(topic: str) -> dict[str, Any] | None:
    """Fuzzy-match a free-text topic string against the curated passage bank.

    Matches whole words/phrases only (word-boundary regex), not raw substring
    containment: a naive ``"rest" in "deforestation"`` style check would wrongly
    match the "sleep" passage (keyword "rest") against the topic "deforestation"
    (which contains the letters "forest").
    """
    needle = topic.strip().lower()
    if not needle:
        return None
    for passage in PASSAGES:
        haystacks = [passage["topic"], passage["title"], *passage["keywords"]]
        for h in haystacks:
            h_lower = h.lower()
            if re.search(rf"\b{re.escape(h_lower)}\b", needle) or re.search(rf"\b{re.escape(needle)}\b", h_lower):
                return passage
    return None


def passage_public() -> list[dict[str, Any]]:
    """Passage list without full text, for browsing/attribution display."""
    return [
        {"id": p["id"], "topic": p["topic"], "title": p["title"],
         "source_url": p["source_url"], "license": p["license"]}
        for p in PASSAGES
    ]
