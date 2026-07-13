# Bestiary additions: 25 ordinary (natural) beasts as a new section, plus a
# build-time pass that sorts every creature section by (tier asc, name asc) and
# regenerates the appendix index from the actual stat blocks (so it never drifts).
import re
from collections import defaultdict

ROMAN = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5}


def primary_tier(tier_str):
    head = tier_str.split("&middot;")[0]
    romans = re.findall(r'\b(I|II|III|IV|V)\b', head)
    return ROMAN[romans[0]] if romans else 9


def name_key(name_html):
    t = re.sub(r'<[^>]+>', '', name_html)
    t = (t.replace('&amp;', '&').replace('&mdash;', '-')
           .replace('&ndash;', '-').replace('&rsquo;', "'").replace('&middot;', ' '))
    t = re.sub(r"^(the|a|an)\s+", "", t.strip(), flags=re.I)
    return t.lower()


def _spans_for_marker(s, marker):
    """Return (start,end) spans of top-level divs opened by `marker` (depth-matched)."""
    spans = []
    i = 0
    while True:
        st = s.find(marker, i)
        if st == -1:
            break
        depth = 0
        j = st
        while j < len(s):
            if s.startswith('<div', j):
                depth += 1
                j += 4
            elif s.startswith('</div>', j):
                depth -= 1
                j += 6
                if depth == 0:
                    break
            else:
                j += 1
        spans.append((st, j))
        i = j
    return spans


def extract_statblocks(s):
    """Return (start,end) spans of each creature unit, depth-matched.

    A creature unit is a top-level <div class="creature"> wrapper when present
    (it carries the lore + stat block + keeper note as one sortable unit); the
    function falls back to bare <div class="statblock"> for any creature that
    has not yet been wrapped. The two never overlap because a wrapped stat block
    lives *inside* its wrapper, so we exclude bare blocks that fall within a
    wrapper's span.
    """
    wrappers = _spans_for_marker(s, '<div class="creature">')
    bare = _spans_for_marker(s, '<div class="statblock">')

    def inside_wrapper(st):
        return any(w0 <= st < w1 for (w0, w1) in wrappers)

    spans = list(wrappers) + [(st, en) for (st, en) in bare if not inside_wrapper(st)]
    spans.sort()
    return spans


def sort_sections(body, ids):
    for sid in ids:
        m = re.search(r'(<section class="page" id="' + sid + r'">)(.*?)(</section>)', body, re.S)
        if not m:
            continue
        inner = m.group(2)
        spans = extract_statblocks(inner)
        if not spans:
            continue
        first, last = spans[0][0], spans[-1][1]
        prefix, middle, suffix = inner[:first], inner[first:last], inner[last:]
        items, leftover = [], middle
        for (st, en) in spans:
            blk = inner[st:en]
            leftover = leftover.replace(blk, "", 1)
            tier = re.search(r'<span class="sb-tier">(.*?)</span>', blk, re.S).group(1)
            name = re.search(r'<span class="sb-name">(.*?)</span>', blk, re.S).group(1)
            items.append((primary_tier(tier), name_key(name), blk))
        assert leftover.strip() == "", f"section {sid}: non-statblock content between creatures: {leftover.strip()[:80]!r}"
        items.sort(key=lambda x: (x[0], x[1]))
        new_inner = prefix + "\n  ".join(b for *_, b in items) + suffix
        body = body[:m.start()] + m.group(1) + new_inner + m.group(3) + body[m.end():]
    return body


def gen_appendix(body, ids):
    tiers = defaultdict(list)
    for sid in ids:
        m = re.search(r'<section class="page" id="' + sid + r'">(.*?)</section>', body, re.S)
        if not m:
            continue
        inner = m.group(1)
        for (st, en) in extract_statblocks(inner):
            blk = inner[st:en]
            tier_str = re.search(r'<span class="sb-tier">(.*?)</span>', blk, re.S).group(1)
            name = re.search(r'<span class="sb-name">(.*?)</span>', blk, re.S).group(1)
            head = tier_str.split("&middot;")[0]
            romans = re.findall(r'\b(I|II|III|IV|V)\b', head)
            if not romans:
                continue
            if '/' in head:  # dual stat block (e.g. flock / prophet): list in each tier
                for r in dict.fromkeys(romans):
                    tiers[ROMAN[r]].append(name)
            else:            # single or range: place at its lowest (first) tier
                tiers[ROMAN[romans[0]]].append(name)
    sub = {1: "(1st&ndash;2nd lvl)", 2: "(~4th lvl)", 3: "(~6th lvl)",
           4: "(~8th lvl)", 5: "(~10th lvl &amp; beyond)"}
    lbl = {1: "I", 2: "II", 3: "III", 4: "IV", 5: "V"}
    rows = []
    for t in (1, 2, 3, 4, 5):
        names = sorted(dict.fromkeys(tiers[t]), key=name_key)
        rows.append(f'      <tr><td><strong>{lbl[t]}</strong> <span class="sub">{sub[t]}</span></td>'
                    f'<td>{", ".join(names)}</td></tr>')
    new_tbody = "<tbody>\n" + "\n".join(rows) + "\n    </tbody>"
    m = re.search(r'(<section class="page" id="index">.*?)<tbody>.*?</tbody>(.*?</section>)', body, re.S)
    return body[:m.start()] + m.group(1) + new_tbody + m.group(2) + body[m.end():]


# ---- 25 ordinary beasts, 5 per tier. sb signature:
# (name, tier, defense, blood, speed, fort, ref, will, attacks, special, dread, down)
N = "&mdash;"
LIVING_CREATURES = [
    # ---- Tier I ----
    ("The Coyote", "Tier I &middot; the trickster of the waking world", 14, 10, "very fast", "+5", "+8", "+2",
     "bite +5 (1d6+1)",
     "<strong>Wary and clever.</strong> Hunts the lone and the weak; a few will harry but rarely commit, and all break for the dark the moment a gun speaks true.",
     N, "It is a coyote. A shot, a shout, or a fire turns it; only hunger or madness makes one truly press a man."),
    ("The Rattlesnake", "Tier I &middot; the coil in the dust", 13, 8, "slow; strikes a blur", "+5", "+7", "+0",
     "bite +6 (1d4 plus venom: Fort save or 1d6 and sickened a day)",
     "<strong>Venom.</strong> It would as soon be left alone and rattles to say so; step wrong and it answers from arm's length before the eye can follow.",
     N, "Watch the ground and the warm rocks. A hoe, a heel, or a load of shot &mdash; and carry a remedy for the bitten."),
    ("The Badger", "Tier I &middot; a low temper in a hole", 14, 12, "slow; burrows", "+7", "+4", "+1",
     "claws &amp; bite +5 (1d6+2)",
     "<strong>Will not quit.</strong> Cornered or dug at, it fights with a fury far past its size and does not flee, yield, or learn fear.",
     N, "Leave it be and it leaves you. If it must die it will make you spend for it &mdash; many guns, or none."),
    ("The Bobcat", "Tier I &middot; the small cat that waits above", 15, 9, "fast; leaps; climbs", "+5", "+8", "+2",
     "claws +5 (1d6+1, rake)",
     "<strong>Ambush.</strong> Drops from a ledge or a limb onto the straggler; the first strike from hiding lands with a vengeance, and then it is simply gone.",
     N, "It rarely presses a fight it cannot win; one hard answer and it quits the field."),
    ("The Stray Pack", "Tier I &middot; dogs gone back to the wild", 13, 12, "fast", "+6", "+6", "+2",
     "bite +4 (1d6+1, drag down)",
     "<strong>Pack.</strong> Surrounds a lone traveler and pulls him down by weight and number; bolder than wolves, for they have lost their fear of men.",
     N, "Drop the boldest and the rest remember they are only dogs; fire and a raised voice scatter them."),
    # ---- Tier II ----
    ("The Gray Wolf", "Tier II &middot; the hunter of the long winter", 15, 20, "very fast", "+8", "+8", "+3",
     "bite +6 (1d8+3, trip)",
     "<strong>Pack hunter.</strong> Harries, hamstrings, and waits; a lone wolf weighs the odds and slips away, but a pack in a hard winter does not.",
     N, "Fire and a steady gun earn its respect; break the pack's nerve and the rest follow the leader off into the trees."),
    ("The Mountain Lion", "Tier II &middot; the cat you never see", 17, 18, "very fast; leaps far", "+7", "+9", "+3",
     "pounce +6 (1d8+3, knocks prone, then rake)",
     "<strong>Silent ambush.</strong> Takes the last man in line from above or behind, drops him, and is at his throat before the others can turn.",
     N, "Stay together and watch the high rocks. It hunts the straggler; deny it one and it goes hungry."),
    ("The Wild Boar", "Tier II &middot; the razorback out of the bottoms", 16, 26, "fast", "+9", "+5", "+2",
     "tusks +6 (1d8+3, gore)",
     "<strong>Charge.</strong> Comes head-down and does not feel the first wound; a hide like a plank turns light shot, and a temper that turns toward the gun, not from it.",
     N, "A tree, a high seat, or a heavy ball square in the shoulder. Do not let it close, and do not wound it by halves."),
    ("The Black Bear", "Tier II &middot; the raider of the camp", 15, 24, "fast; climbs", "+8", "+5", "+3",
     "claws +6 (1d8+3)",
     "<strong>Mostly wants your supper.</strong> Bluster and noise usually turn it &mdash; unless it is cornered, starving, or a sow with you between her and the cubs, and then it is all teeth.",
     N, "Make yourself big and loud and it likely quits. Never step between sow and cub; that bear has no quit in it."),
    ("The Range Bull", "Tier II &middot; a ton of bad temper", 14, 28, "fast in a charge", "+9", "+4", "+2",
     "horns +6 (1d8+4, toss)",
     "<strong>Charge and trample.</strong> A longhorn that has decided he hates you; gores, tosses, and comes around for another pass while you are still in the dirt.",
     N, "The fence, the gate, a fast horse, or a red rag thrown wide &mdash; or drop him where he stands, which is a great deal of dropping."),
    # ---- Tier III ----
    ("The Grizzly Bear", "Tier III &middot; the lord of the high country", 17, 44, "fast (briefly, faster than a horse)", "+11", "+5", "+4",
     "claws +9 (2d6+4; a hit rakes with both)",
     "<strong>Takes the lead and keeps coming.</strong> Shrugs off the first solid wound, runs down a fleeing man over short ground, and does not stop for pain.",
     N, "It takes more lead than seems possible &mdash; aim true behind the shoulder. A tree is no help; a grizzly will simply wait you out."),
    ("The Bison Bull", "Tier III &middot; a hill of muscle and horn", 16, 48, "very fast in a straight line", "+13", "+4", "+4",
     "horns &amp; trample +9 (2d6+5)",
     "<strong>Unstoppable in a line.</strong> A ton and a half at a dead run; it neither swerves nor tires before you do.",
     N, "A big-bore rifle behind the shoulder &mdash; or simply not be where it is going. Turning it is easier than killing it."),
    ("The Bull Gator", "Tier III &middot; the log that was not a log", 18, 42, "slow on land; fast in water", "+11", "+6", "+4",
     "bite +9 (2d6+4, grab and roll under)",
     "<strong>Death roll.</strong> Explodes from the shallows, clamps on, and rolls to drown and dismember; on its own water, nothing the frontier owns can hold it.",
     N, "Stay back from the cut bank and the still water. The eye and the soft of the throat &mdash; and never wade where one might wait."),
    ("The Wolf Pack", "Tier III &middot; the winter pack, of one mind", 16, 40, "very fast", "+10", "+9", "+4",
     "bite +9 (2d6+4, all who stand close)",
     "<strong>Run as one (a swarm).</strong> A single pool of Blood and a single will; it surrounds, drags down, and thins as it bleeds rather than dropping man by man.",
     N, "You cannot kill a pack a wolf at a time. Fire, high ground, and breaking their nerve &mdash; take the leader and the rest may scatter."),
    ("The Bull Moose", "Tier III &middot; a thousand pounds in a foul mood", 16, 46, "fast", "+12", "+5", "+3",
     "antlers &amp; hooves +9 (2d6+4, trample)",
     "<strong>Fears nothing in the rut.</strong> Charges horse, man, or locomotive without a second thought; enormous, untroubled by a wound, and quick for its size.",
     N, "Give it the road and the right of way. It tires of you sooner than you tire of it &mdash; if you live the first charge."),
    # ---- Tier IV ----
    ("The Great Bear", "Tier IV &middot; the man-killer of legend", 20, 72, "fast", "+15", "+8", "+8",
     "claws &amp; bite +13 (2d8+6; the hit rakes twice)",
     "<strong>Has learned men.</strong> Wears the scars of every gun that failed to stop it; a wound only makes it worse, and it has killed enough hunters to be careful, and cruel.",
     N, "It has survived a dozen hunts. It takes a small army or one perfect shot; men have spent their whole lives, and their lives, on less."),
    ("The Stampede", "Tier IV &middot; the herd, run as a wall", 18, 70, "very fast", "+15", "+6", "+6",
     "trample +13 (2d8+6, everything in the lane)",
     "<strong>Not a fight &mdash; a flood.</strong> A moving wall of the herd that cannot be reasoned with or fought, only outrun, turned, or survived; it fills the draw and takes all within it.",
     N, "You do not kill a stampede. Ride out of the lane, gain high ground, or turn the lead with fire &mdash; and pray the ground is not a box canyon."),
    ("The Man-Eater", "Tier IV &middot; the cat that learned to hunt men", 20, 64, "very fast; leaps", "+13", "+13", "+7",
     "pounce +13 (2d8+6, drops and pins)",
     "<strong>Hunts you in turn.</strong> Takes the sentry and the straggler by night, patient and learned; never seen until it strikes, and it never strikes a fair fight.",
     N, "It must be hunted as it hunts &mdash; with bait, patience, and an iron nerve. Stand watch in pairs, and never sleep where it can come from above."),
    ("The Old Tusker", "Tier IV &middot; the boar that breaks the dogs", 19, 74, "fast", "+15", "+7", "+6",
     "tusks +13 (2d8+6, gore and throw)",
     "<strong>A hide like a plank, a temper like the devil.</strong> Has broken dogs, horses, and the men on them; charges clean through what would stop anything smaller and comes back for the rest.",
     N, "Men hunt it for years and bury friends doing it. A tree, a wall, and a heavy enough ball &mdash; and never on foot in the open."),
    ("The Pale Stallion", "Tier IV &middot; the wild horse no man rides", 20, 66, "very fast", "+13", "+13", "+8",
     "hooves &amp; teeth +13 (2d8+6, strike and trample)",
     "<strong>Suffers no rider.</strong> Leads its band and kills to keep it; strikes with hooves and teeth, runs men down, and is as cunning as any outlaw and twice as proud.",
     N, "It cannot be broken, only outlasted or shot, and many a wrangler has died learning which. Cut it from the band first, if you can."),
    # ---- Tier V ----
    ("The Mountain That Walks", "Tier V &middot; the primeval bear of the old tales", 23, 112, "fast", "+19", "+11", "+11",
     "claws &amp; bite +17 (3d8+8; rakes twice and seizes)",
     "<strong>Bigger than a bear has the right to be.</strong> The high-country legend made flesh; it takes wounds the way a hillside takes rain, and has outlived every hunter ever sent for it.",
     N, "A thing out of the grandfather-tales. It will take everything you brought and everything you are &mdash; and may yet walk away."),
    ("The White Bison", "Tier V &middot; the great pale buffalo, omen and terror", 22, 108, "very fast", "+19", "+11", "+12",
     "horns &amp; trample +17 (3d8+8)",
     "<strong>Sacred and cursed both.</strong> Huge beyond reason; the people count it holy and the hunters count it doom, and the herd follows where it leads &mdash; a thousand head at its back.",
     N, "Many will tell you it must not be killed at all. If you must, it is a mountain of muscle and wrath, and the herd behind it is the rest of your trouble."),
    ("The Great Serpent", "Tier V &middot; the snake grown long as a wagon-train", 21, 100, "fast; burrows", "+18", "+13", "+9",
     "bite +17 (3d8+8 plus venom: Fort save or 2d6 and weakened)",
     "<strong>Long as a fence-line, thick as a barrel.</strong> Strikes from the dust with the reach of a tall man and more; its venom answers to no remedy the frontier carries.",
     N, "Keep to high rock and open ground where you can see it come. The head must be taken &mdash; and getting close enough is the whole of the danger."),
    ("The Carcajou", "Tier V &middot; the devil-bear of the north woods", 22, 104, "fast; climbs; tireless", "+18", "+12", "+10",
     "claws &amp; bite +17 (3d8+8; never lets go)",
     "<strong>The wolverine of legend, grown vast.</strong> Drives bears off their kills, fears nothing that lives, and pursues a grudge for days without rest or quit.",
     N, "It does not stop and it does not tire. You cannot outlast it; you must end it all at once, or keep moving until one of you is dead."),
    ("The Old Man of the Swamp", "Tier V &middot; the gator that owns the bayou", 23, 110, "slow on land; fast in black water", "+19", "+10", "+10",
     "bite +17 (3d8+8, takes a horse under whole)",
     "<strong>Older than the parish.</strong> Longer than a flatboat and patient as the tide; it takes a man or a mount under without a ripple, and the water is all its own.",
     N, "The black water is its kingdom and your grave. Draw it onto dry land or never face it at all; in the water you will simply be gone."),
]


def build_living(sb, runhead, quote, creature):
    blocks_list = []
    for c in LIVING_CREATURES:
        stat = sb(*c)
        lore, found = LIVING_LORE.get(c[0], ("", ""))
        if lore:
            blocks_list.append(creature(stat, lore=lore, found=found, keeper="", kn_tag=""))
        else:
            blocks_list.append(stat)
    blocks = "\n  ".join(blocks_list)
    return f'''<!-- VIII -->
<section class="page" id="living">
  {runhead('VIII. Beasts of the Living World')}
  <h1 class="chapter">VIII. Beasts of the Living World</h1>
  <p class="chapter-sub">The honest dangers &mdash; flesh, blood, tooth, and no curse at all.</p>
  <div class="divider"></div>
  {quote("Folk ask me which of the territory's animals are the dangerous ones. I tell them: the hungry ones, and the ones you have cornered. That is the whole of the list.", "from the field-books of N. Ashby")}
  <p class="dropcap lead">Not everything that kills a man on the frontier came back from a grave or down from the stars. The country is full of plain animals that will end you for plain reasons &mdash; hunger, fear, a calf to guard, a trail you had no business riding &mdash; and between them they bury more men than all the horrors in this book combined.</p>
  <p class="note"> <strong>Signs of the kind:</strong> tracks in the mud and scat on the trail, a kill cached under brush, the birds gone quiet at the treeline, stock that will not settle &mdash; the plain sign any frontiersman learns to read, or dies not reading.</p>
  <div class="keeper-note"><span class="kn-tag">No Nerve, no Mark</span>These beasts cost the party <em>no Nerve</em> &mdash; there is no Dread Check against an honest animal, and their <strong>Dread</strong> line is marked &ldquo;&mdash;&rdquo; to say so. Nor do they ever move the Mark. Run them straight off the numbers. Their place in this book is to make the country real, to bloody a party grown careless &mdash; and to set the moment a thing that looks like an ordinary wolf turns its head, and its eyes are wrong.</div>
  {blocks}
</section>
'''


# ---- Field-guide lore for the ordinary beasts. Honest animals get a concise
# treatment (one descriptive paragraph + a 'Found' line); their how-to-fight
# already lives in the stat block's Special and Putting-It-Down lines, and the
# section keeper-note covers the no-Nerve/no-Mark rule, so no per-beast keeper
# note is added. Keyed by the creature's name (LIVING_CREATURES[n][0]).
LIVING_LORE = {
  "The Coyote": (
    "The trickster of the waking world, and mostly a coward with a clever face. A coyote wants the easy meal &mdash; the lame calf, the unguarded chickens, the carcass already cooling &mdash; and it weighs every risk with a gambler's care. A few may shadow a lone traveler, yipping in the dark to unsettle him, but they rarely commit, and the speech of a gun sends them flowing back into the brush like water. Only hunger past reason, or the froth of madness, makes one truly press a man.",
    "Open range, brush country, and the edges of every settlement; wherever there's carrion, stock, or scraps. Heard far more than seen, especially at dusk and the small hours."),
  "The Rattlesnake": (
    "The coil in the dust, and the most honest killer on this list &mdash; it tells you plainly to leave it be, and only answers when you don't. It would far rather not waste its venom on a thing too big to eat, and the dry buzz of its rattle is a courtesy, a warning given before the strike. But step wrong in the warm rocks, reach a hand where you can't see, and it answers from arm's length faster than the eye can follow, and the venom it spends will cost you a bad day or a worse week.",
    "Sun-warmed rocks, woodpiles, brush, and the shade under any ledge in dry country. Most dangerous in the cool of morning and evening when it lies out, and at any time a careless hand or boot finds it first."),
  "The Badger": (
    "A low temper in a hole, and pound for pound about the meanest thing the honest country has to offer. The badger asks only to be left alone in its diggings, and grants the same courtesy in return &mdash; but corner it, dig at it, press it where it cannot flee, and it fights with a berserk fury far past its size, all claw and muscle and a refusal to quit that no wound seems to teach. It does not flee, does not yield, and does not learn fear.",
    "The open grasslands and dry country where it digs, riddling a hillside or a pasture with burrows. Encountered when something disturbs its den &mdash; a horse's leg in a hole, a dog gone to ground after it, a careless boot."),
  "The Bobcat": (
    "The small cat that waits above, patient and silent and gone before you've finished flinching. A bobcat hunts the straggler and the small &mdash; it drops from a ledge or a low limb onto whatever passes beneath, and its first strike from hiding lands with a startling vengeance for so modest a creature. But it has a cat's clear sense of a losing fight, and one hard answer usually convinces it the meal isn't worth the trouble.",
    "Rocky country, broken timber, and brushy draws where it can climb and lie up unseen. It favors the high ground and the ambush; watch the ledges and the low branches along a narrow trail."),
  "The Stray Pack": (
    "Dogs gone back to the wild, and the sadder and more dangerous for once having known the hearth. A stray pack has lost a dog's fear of men but kept a dog's boldness and a dog's understanding of them, which is a poor combination to meet on a lonely road. They surround a lone traveler and pull him down by weight and number, snapping and dragging, bolder than wolves because they remember that men are not gods after all.",
    "The margins of failed homesteads, ghost camps, and any place men have come and gone and left their dogs behind. They work the lonely roads and the edges of struggling settlements, especially in hard seasons."),
  "The Gray Wolf": (
    "The hunter of the long winter, and a creature of pure, patient calculation. A lone wolf weighs the odds coldly and slips away from a fair fight nearly every time; it is the pack in a hard winter, hungry and coordinated, that buries men. They harry, they hamstring, they wait, testing a quarry's strength and nerve before they ever commit, and they commit only when the arithmetic favors them.",
    "The deep timber, the high country, and the open winter range. A pack hunts a wide territory and follows game and weakness; the danger climbs with the snow and the lean months."),
  "The Mountain Lion": (
    "The cat you never see, until the last man in the line is simply gone. A cougar is the perfect ambush &mdash; it takes its prey from above or behind, drops it, and is at the throat before the rest of the party can turn at the sound. It hunts the straggler, the lone rider, the one who wandered from the fire, and it almost never strikes a fight it hasn't already won by surprise.",
    "Rocky, broken country and timbered slopes with high ground to stalk from. It haunts the game trails and the narrow passes; watch the rocks and the ledges above, and never let the line straggle out."),
  "The Wild Boar": (
    "The razorback out of the bottoms, all bad temper and worse hide. A wild boar comes head-down and does not feel the first wound, or the second; a hide like a plank turns light shot, and a temper that turns toward the gun rather than away from it makes it the rare animal that will charge a man who's already firing. Get it angry by halves and you've made a bad problem worse.",
    "The brushy bottoms, swamps, and thickets where it roots and wallows. Most dangerous in close cover where it can charge before you've a clear shot, and worst when wounded, cornered, or guarding young."),
  "The Black Bear": (
    "The raider of the camp, and mostly a thief rather than a killer &mdash; which is no comfort if you're between it and what it wants. A black bear usually wants your supper, not your life, and bluster and noise will turn most of them. But corner one, starve one, or step between a sow and her cubs, and the genial robber becomes all teeth and terrible speed, and there is no quit in a frightened or furious bear.",
    "Timber and brush country near food &mdash; berry patches, salmon runs, and especially the careless camp or the unsecured larder. Bold around settlements that have taught it men mean easy meals."),
  "The Range Bull": (
    "A ton of bad temper on four legs, and a reminder that not every deadly animal is a predator. A longhorn that has decided he hates you will gore, toss, and come around for another pass while you're still picking yourself out of the dirt, and there is a great deal of him to stop. He is slow to anger and unstoppable once roused, and a fence is worth more than a gun.",
    "The open range and the holding pens, anywhere cattle run half-wild. Most dangerous in the press of a herd, guarding cows, or simply in a foul mood with a rider who got too close."),
  "The Grizzly Bear": (
    "The lord of the high country, and the animal that has ended more confident hunters than any other on this list. A grizzly takes the lead and keeps coming &mdash; it shrugs off the first solid wound, runs down a fleeing man over short ground faster than a horse, and does not stop for pain. It takes more lead than seems possible, and a tree is no help, for a grizzly will simply wait you out.",
    "The high mountains, the open slopes, and the river bottoms in salmon season. It ranges widely and fears nothing; encountered on its own terms, which are always bad ones for a man on foot."),
  "The Bison Bull": (
    "A hill of muscle and horn, and unstoppable in a straight line. A ton and a half at a dead run neither swerves nor tires before you do; a bison bull in a temper or a stampede is less an animal to fight than a force to be elsewhere from. Turning one is easier than killing it, and not being in its path is easier than either.",
    "The open plains and grasslands where the great herds run. Most dangerous in the bull's rutting temper or the blind momentum of a moving herd; the lone old bull cut from the herd is a cussed and dangerous thing."),
  "The Bull Gator": (
    "The log that was not a log, and the undisputed master of its own black water. A bull gator explodes from the shallows, clamps on, and rolls to drown and dismember &mdash; on its own water, nothing the frontier owns can hold it. On land it is slow and beatable; in the water it is simply death with teeth, and the cut bank and the still pool are its kingdom.",
    "The swamps, bayous, slow rivers, and still backwaters of the hot country. Lies up along cut banks and in the murk; never wade or water stock where one might wait."),
  "The Wolf Pack": (
    "The winter pack run as one mind &mdash; not several wolves but a single will with many mouths, a swarm of fang and patience. It surrounds, drags down, and thins as it bleeds rather than dropping man by man; you cannot kill a pack a wolf at a time. Fire, high ground, and breaking their nerve are the only answers, and taking the leader may scatter the rest &mdash; or may not, in a hard enough winter.",
    "The deep winter range and the high lonesome country, far from help. The pack follows game and weakness across a wide territory; the threat is greatest in the lean cold months when hunger overrides caution."),
  "The Bull Moose": (
    "A thousand pounds in a foul mood, and afraid of nothing in the rut. A bull moose will charge a horse, a man, or a locomotive without a second thought, enormous and untroubled by a wound and far quicker than its bulk suggests. Give it the road and the right of way; it tires of you sooner than you tire of it, if you live the first charge.",
    "The northern timber, the willow bottoms, and the marshy lakeshores. Most dangerous in the autumn rut and when a cow defends her calf; a moose on the trail is a thing to wait out, not push past."),
  "The Great Bear": (
    "The man-killer of legend, a grizzly grown old and cunning and cruel on the failures of every hunter sent against it. It wears the scars of a dozen guns that did not stop it, and a wound only makes it worse; it has killed enough men to have learned them, to be careful and patient and savage all at once. Men have spent their whole lives, and their lives, hunting one.",
    "The deep wild high country, far from any help, where a legendary bear has reigned long enough to earn a name and a body count. It knows men and their tricks, and it does not make the mistakes a younger bear would."),
  "The Stampede": (
    "Not a fight but a flood &mdash; the herd run as a moving wall, a thing that cannot be reasoned with or fought, only outrun, turned, or survived. A stampede fills the draw and takes everything in the lane, a thousand head of blind panic and pounding hooves, and the only counsel is to ride out of its path, gain high ground, or turn the lead with fire and pray the ground ahead is not a box canyon.",
    "The open range and the trail-drive country, anywhere a great herd can be spooked by lightning, a gunshot, a cut bank in the dark. The terrain decides whether a stampede is a danger or a death sentence."),
  "The Man-Eater": (
    "The cat that learned to hunt men, and now hunts you in turn. A cougar or other great cat that has acquired the taste takes the sentry and the straggler by night, patient and learned, never seen until it strikes and never striking a fair fight. It must be hunted as it hunts &mdash; with bait, patience, and an iron nerve &mdash; for it has all three and the dark besides.",
    "The country around a settlement, camp, or trail where a great cat has turned to taking men. It works by night and from above; stand watch in pairs, and never sleep where something can come from the rocks overhead."),
  "The Old Tusker": (
    "The boar that breaks the dogs, a wild hog grown old and vast and malicious, with a hide like a plank and a temper like the devil. It has broken dogs, horses, and the men on them, and charges clean through what would stop anything smaller before coming back for the rest. Men hunt it for years and bury friends doing it.",
    "The deep brush and bad bottoms where an old boar has ranged long enough to grow huge and hateful. Most dangerous in close cover and never to be faced on foot in the open; a tree and a heavy ball, or nothing."),
  "The Pale Stallion": (
    "The wild horse no man rides, and kills to keep it so. A great wild stallion leads its band and suffers no rider and no rival &mdash; it strikes with hooves and teeth, runs men down, and is as cunning as any outlaw and twice as proud. It cannot be broken, only outlasted or shot, and many a wrangler has died learning which.",
    "The open range and the high desert where the wild bands run. Encountered guarding its mares or running off a rival; cut it from the band first, if you can, for in the band's midst it is the least of your troubles and the worst."),
  "The Mountain That Walks": (
    "The primeval bear of the old tales, the high-country legend made flesh &mdash; bigger than a bear has any right to be, and older. It takes wounds the way a hillside takes rain and has outlived every hunter ever sent for it; a thing out of the grandfather-stories that will take everything you brought and everything you are, and may yet walk away unbothered.",
    "The deepest, highest, least-traveled country, where a thing can grow vast and ancient with no man left alive who's seen it twice. A legend with a territory; you do not find it so much as trespass on it."),
  "The White Bison": (
    "The great pale buffalo, omen and terror both, sacred to some and doom to others. Huge beyond reason, it leads a herd a thousand head strong wherever it goes; the people count it holy and the hunters count it cursed, and many will tell you it must not be killed at all. If you must, it is a mountain of muscle and wrath, and the herd at its back is the rest of your trouble.",
    "The great plains where the herds run, moving at the head of its following. As much a sign as a creature; where the white bison walks, men's beliefs and fears walk with it, and that is half its danger."),
  "The Great Serpent": (
    "The snake grown long as a wagon-train and thick as a barrel, a thing that strikes from the dust with the reach of a tall man and more. Its venom answers to no remedy the frontier carries, and getting close enough to take its head &mdash; which is the only way to end it &mdash; is the whole of the danger. Keep to high rock and open ground where you can see it come.",
    "The badlands, the rocky desert, and the broken sun-baked country where a serpent can grow monstrous and burrow deep. It lies up in the rocks and the dust; the warm hours bring it out to hunt."),
  "The Carcajou": (
    "The devil-bear of the north woods, the wolverine of legend grown vast and tireless and full of grudge. It drives bears off their kills, fears nothing that lives, and pursues a wrong for days without rest or quit. It does not stop and it does not tire; you cannot outlast it, and must end it all at once or keep moving until one of you is dead.",
    "The deep northern timber and the high cold country, ranging a vast territory with relentless appetite. It follows a trail or a grudge tirelessly; once it has fixed on a party or a trapline, it does not simply wander off."),
  "The Old Man of the Swamp": (
    "The gator that owns the bayou, older than the parish and longer than a flatboat, patient as the tide. It takes a man or a mount under without a ripple, and the black water is all its own; draw it onto dry land or never face it at all, for in the water you will simply be gone. The swamp is its kingdom and your grave.",
    "The deepest, oldest black water of the great swamps and bayous, where a gator has reigned long enough to grow legendary. It knows every channel and cut bank of its domain; on its own water, it is undefeated and undefeatable."),
}

