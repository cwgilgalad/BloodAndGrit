#!/usr/bin/env python3
# Build "Blood & Grit — What the Water Answers", module III, on the shared engine.
# Reads blood-and-grit.html (run build_player.py first), writes module-what-the-water-answers.html.
#
# Keeper's Book Ch. XIII gives Perdition Basin its spine — the padres' silver nails binding a thing
# under the wells, failing one well at a time — and then stops at the mission door. Both earlier
# modules end within sight of San Clavo and neither goes in. This one goes in, and then goes under.
# Every number under "What the Night Costs" came out of GK/playtest.
from modules_common import (night_costs, shell, splice, finish, report, runhead, quote, readaloud,
                            keeper, clock, npc, statblock, found, contents)
from module_maps import map_html

VERSION = "1.2"
SLUG = "what-the-water-answers"

H = shell(
    foot="What the Water Answers",
    kicker="A Third Reckoning, Keyed and Ready to Run",
    tiny_edition="Module III &middot; A one-night adventure for four souls at 5th level",
    tiny_blurb="The water is going bad from the bottom up, and the mission knows why.",
    colophon="Blood &amp; Grit &middot; Module III &middot; What the Water Answers &middot; "
             f"Version {VERSION} &middot; For the Keeper Alone",
    version=VERSION,
    cover_bg="#0b1416",
    cover_key="rgba(66,110,110,.92)",
    cover_foot_ink="#8fb3ae",
    cover_sub_ink="#bfc7b6",
    epigraphs=[
        ('"They did not build the mission over the well. They built the well first and put the\n'
         '    mission on top of it, the way you put a hand on a lid."\n'
         '    <span class="src">— Fray Ignacio Salcedo, San Clavo, undated</span>'),
        ('"A binding is not a thing you did. It is a thing you are doing. The day you stop is the\n'
         '    day it was never done at all."\n'
         '    <span class="src">— the last full entry in the padres\' ledger</span>'),
    ],
)

# ============================================================ contents
CONTENTS = '''
<section class="page" id="contents">
  ''' + runhead("Contents") + '''
  <h1 class="chapter">Contents</h1>
  ''' + contents([
      ("what", "What This Is"),
      ("truth", "The Truth of It"),
      ("hook", "The Hook, and Getting Them There"),
      ("ground", "The Ground"),
      ("act1", "Act One &mdash; What Comes Up With the Water"),
      ("act2", "Act Two &mdash; The Ledger of the Padres"),
      ("act3", "Act Three &mdash; The Bottom of the Basin"),
      ("cast", "The Cast"),
      ("dead", "What Is Coming Up"),
      ("cost", "What the Night Costs"),
      ("after", "The Water, and What Comes After"),
  ]) + '''
</section>
'''

# ============================================================ what this is
WHAT = '''
<section class="page" id="what">
  ''' + runhead("What This Is") + '''
  <h1 class="chapter">What This Is</h1>
  ''' + quote("Everything in this county drinks from the same hole in the ground. Remember that "
              "when they ask you why it is their business.",
              "a note pinned inside the cover of the first printing") + '''
  <p>One night at the table, for four souls at 5th level, at Mission San Clavo and under it. Four
  hours, and it will want the whole four. Every creature in it is printed here in full, so the
  Bestiary can stay on the shelf.</p>

  <p>This is the third of three and the only one that goes into the mission. Module I ends at its
  east wall. Module II ends forty miles north of it. Perdition Basin has been pointing at San Clavo
  since the Keeper&rsquo;s Book Ch. XIII, and everything the two earlier nights left unexplained is
  in a hole under its floor.</p>

  <p>It does not require either of the others. It is better after both.</p>

  <h2 id="what-you-need">What You Need</h2>
  <p>The Player&rsquo;s Book for the souls, and this. The Keeper&rsquo;s Book Ch. XIII is genuinely
  useful here and still not required; what a Keeper needs from it is on
  <a href="#truth">The Truth of It</a>. If you are running GritKeeper, put the clock on the Tracker
  before Act One begins and let the table watch it fill.</p>

  <h2 id="what-teaches">What It Teaches, and in What Order</h2>
  <p>Three things, one per act, and never two at once.</p>
  <ul>
    <li><strong>Act One teaches that the country is the victim.</strong> A well, a family, and three
    things that drank from it. A fight a 5th-level posse wins.</li>
    <li><strong>Act Two teaches that somebody wrote it down.</strong> The padres kept a ledger of
    what they bound and what keeping it cost, and the last entry stops mid-word. The fight in the
    nave is the one this module lets go badly: the engine cleared it three times in nine.</li>
    <li><strong>Act Three teaches what a binding actually is.</strong> Not a thing done once. A
    thing being done, by somebody, continuously, until they stop. The posse goes down the shaft to
    find out who stopped, and then has to decide whether to start again.</li>
  </ul>

  ''' + keeper(
    "<p>Read the ledger entries in Act Two aloud, slowly, in order. They are the module's whole "
    "argument and they are short on purpose. Everything else here can be improvised; those cannot, "
    "because the last one has to land.</p>", "Before you run it") + '''
</section>
'''

# ============================================================ the truth
TRUTH = '''
<section class="page" id="truth">
  ''' + runhead("The Truth of It") + '''
  <h1 class="chapter">The Truth of It</h1>
  <p class="note">For the Keeper alone. Two people in the module know a piece of this. Nobody alive
  knows all of it.</p>

  <p>In 1809 the padres of San Clavo found something at the bottom of the first well they dug, which
  is the only reason there is a mission here at all. They did not destroy it. Fray Ignacio Salcedo,
  who wrote most of the ledger, is explicit that they could not, and unusually clear-eyed about
  what they did instead: they pinned it. Seven wells across the Basin, each with a nail of worked
  silver driven at the waterline, each blessed, each renewed by hand on a schedule.</p>

  <p>The mission burned in 1811 and the order went home. One man stayed, and then one man after him,
  and then one after that: seventy years of a single person walking a circuit of seven wells
  with a hammer and a prayer, telling almost nobody, because the ledger says plainly that a thing
  widely known is a thing eventually dug up.</p>

  <h2 id="truth-keeper">The Last Keeper of It</h2>
  <p><strong>Esperanza Ríos died in her sleep in April, eighty-one years old, four miles from here,
  and told nobody.</strong> She had been walking the circuit alone for thirty-one years. She meant to
  hand it on and she kept meaning to, the way a person does. There is no villain in this module and
  the module should not go looking for one.</p>

  <h2 id="truth-wells">What Is Failing, and in What Order</h2>
  <p>Four months without renewal. The nails are giving in the order they were driven, which is the
  order of the wells outward from the mission, which means the failures have been walking toward
  the towns and away from the thing all summer. Three have gone. The Cardoza well went eleven days
  ago and is where Act One opens.</p>

  <p>What comes up first is not the thing. It is the water: bad, and then wrong, and then busy. The
  ones who drink it drown standing up, in air, months later, and get up afterward.</p>

  <h2 id="truth-clock">The Clock</h2>
  ''' + clock("The Wells, Failing Outward", 6,
              "Three segments are already filled when the module opens: three nails gone. "
              "Fill one each time the posse spends a night elsewhere, and one when they open the "
              "shaft. At six the first well fails, which is the one directly over it, which is the "
              "one they are standing on in Act Three.") + '''

  ''' + keeper(
    "<p>Show the clock. Put it on the table with three pips already inked and do not explain it "
    "until Act Two. A clock the players can see and cannot read is the best pressure this system "
    "has, and this module is the one that earns it.</p>") + '''
</section>
'''

# ============================================================ the hook
HOOK = '''
<section class="page" id="hook">
  ''' + runhead("The Hook") + '''
  <h1 class="chapter">The Hook, and Getting Them There</h1>

  ''' + readaloud(
    "Calvary Crossing has been drinking hauled water for nine days and paying for it. The man who "
    "hauls it will not go back to the Cardoza place, and he will not say why in front of his wife, "
    "and he will say it for two dollars out back by the wagon.") + '''

  <p>The posse is being hired to look at a well. That is all. It should sound like the least
  dangerous work anybody has offered them all year, and a table coming off module II will be
  suspicious of exactly how boring it sounds, which is fine and even useful.</p>

  <h2 id="hook-why">Three Ways In</h2>
  <ul>
    <li><strong>Paid.</strong> Calvary Crossing wants its water back and will pay forty dollars for
    somebody to tell them why they cannot have it.</li>
    <li><strong>Following module I.</strong> The scrap of worked silver off Tom Pell&rsquo;s body is
    a piece of a nail. Anyone who kept it will find it warm to the hand within a mile of the mission,
    and cold at the wells that have already failed.</li>
    <li><strong>Following module II.</strong> The Skin-Walker was buying old church silver up and
    down the north line and paying too much for it. It had a list. The list is a list of wells.</li>
  </ul>

  ''' + npc("Elías Cardoza, who owns the well",
            "his family to stop being sick and his water to stop being wrong",
            "he buried two of his own eleven days ago and did not dig deep, because the ground was "
            "wet and he was tired",
            "It is a well. It has been a well for forty years. Tell me what a well can be.") + '''
</section>
'''

# ============================================================ the ground / map
GROUND = '''
<section class="page" id="ground">
  ''' + runhead("The Ground") + '''
  <h1 class="chapter">The Ground</h1>
  <p class="note">Every numbered place below is a keyed scene, and the number on the map is the
  number in the margin of the act it belongs to. The map is drawn in two panels because the last
  act happens under the first one.</p>

  ''' + map_html(SLUG,
                 "the mission and the road to it above, and a section through the first well below, "
                 "with the eleven keyed scenes pinned where they happen") + '''

  <h2 id="ground-shape">What the Shape of It Does</h2>
  <p>Two panels, two scales, and the second one is the point. The upper panel is six miles of open
  country and a ruin on a rise, the country the posse has spent two modules riding across.
  The lower panel is a hundred and forty feet straight down, drawn to its own scale, and it will not
  fit on the same drawing as the first because it is not that kind of distance.</p>
  <ul>
    <li><strong>The mission is uphill from everything.</strong> Which is why its well was dug first,
    and why every other well in the Basin is downstream of whatever is in it.</li>
    <li><strong>The shaft is wet the whole way.</strong> There is no dry descent and no clever
    route. Whatever the posse brings down, it brings down soaked.</li>
    <li><strong>The bottom is wider than the shaft.</strong> That is not a drawing error. The padres
    did not dig the bottom.</li>
  </ul>

  ''' + keeper(
    "<p>Show the table the upper panel in Act One and cover the lower one with your hand. Uncover it "
    "when somebody looks down the wellhead in Act Three. The download beside the map prints both "
    "panels on one sheet, so you can cut it if you would rather.</p>") + '''
</section>
'''

# ============================================================ act one
ACT1 = '''
<section class="page" id="act1">
  ''' + runhead("Act One") + '''
  <h1 class="chapter">Act One &mdash; What Comes Up With the Water</h1>
  <p class="note">Aim for an hour. One Dread Check, one fight the posse should win.</p>

  <h2 id="a1-house">1. The Cardoza Place</h2>
  <p>Adobe, forty years old, four miles east of Calvary Crossing on the mission road. Eleven people
  lived here in the spring. Six do now. Two are buried out back in ground that will not stay dry and
  three have gone to relatives and are not coming home.</p>

  <p>Elías Cardoza will let them look at anything and answer anything. He is not hiding a thing and
  he has not got a thing to hide, and a posse two modules deep in this country will spend twenty
  minutes establishing that, which is time well spent.</p>

  <h2 id="a1-well">2. The Cardoza Well</h2>
  <p><strong>Dread Check, DC 16, Will save.</strong> Tier II loss. Not for anything that moves. For
  what the bucket brings up.</p>

  ''' + readaloud(
    "The water is clear. That is the first wrong thing: it has been clear for eleven days in "
    "a well nobody can drink from. The second wrong thing is in the bottom of the bucket, under the "
    "water, lying flat: a hand&rsquo;s worth of long dark hair, and it is clean, and it is combed.") + '''

  <p>Anyone who goes down on the rope finds the waterline, and at the waterline finds a socket cut
  square into the stone, four inches deep, empty, and greened at the edges where something silver
  sat in it for seventy years.</p>

  ''' + keeper(
    "<p><strong>Plant the socket and move on.</strong> Do not explain it. The posse will see six "
    "more of them before the night is out and the seventh is the one that matters. If somebody in "
    "the party is carrying the silver scrap from module I, let it go cold in their hand at the "
    "wellhead, once, and say nothing about it.</p>") + '''

  <h2 id="a1-fight">3. The Ones Who Drank First</h2>
  <p>The two Cardoza graves are not what is coming. What is coming is the three who went to
  relatives, who are back, and who arrive up the road at dusk on foot, together, walking well.</p>

  ''' + found("The Drowned") + '''

  <p>Full entry under <a href="#dead">What Is Coming Up</a>. Three of them. They are wet to the
  waist in a dry country and they have been walking two days.</p>

  ''' + keeper(
    "<p><strong>The engine says the posse wins this</strong>: nine clears in twelve, about "
    "three rounds. It is meant to be won. What it is not meant to be is free: the fight is in "
    "the dooryard of a family that is watching, and two of the three are recognised on sight by "
    "somebody standing behind the posse.</p>") + '''

  <h2 id="a1-road">The Walk to the Mission</h2>
  <p>Six miles, uphill, on bad water, and the module charges for it: <strong>3 Blood from each soul,
  no save</strong>, unless they thought to haul clean water from the Crossing. Nobody will have.
  Charge it once, say what it feels like, and do not make it a scene.</p>
</section>
'''

# ============================================================ act two
ACT2 = '''
<section class="page" id="act2">
  ''' + runhead("Act Two") + '''
  <h1 class="chapter">Act Two &mdash; The Ledger of the Padres</h1>
  <p class="note">Aim for ninety minutes. One Dread Check, one fight that can go wrong, and the
  whole answer written down in somebody else&rsquo;s hand.</p>

  <h2 id="a2-court">4. The Courtyard</h2>
  <p>Roofless since 1811. Grass in the flags, a fig tree that should not be alive, and the well the
  posse is going to end the night in, capped with a cut stone somebody has been keeping clear of
  brush. Recently. Within the year.</p>

  <p>That detail is the module&rsquo;s first honest clue and the best one: somebody has been
  <em>maintaining</em> this ruin, and stopped four months ago.</p>

  <h2 id="a2-nave">5. The Nave</h2>
  <p>Three walls, no roof, and the carved panels module I sends its posse to read are on the east
  wall of this room. If your table played that night, let them recognise the carvings from across
  the floor, and let that be the first time this campaign has handed them something for free.</p>

  <h2 id="a2-fight">6. What Has Been Living in the Nave</h2>
  <p>Under the fallen roof timbers at the west end, where the rain collects. They have been here
  since the spring and they are what happens when the water gets into people who were already dead.</p>

  ''' + found("The Plague-Dead") + '''

  <p>Full entry under <a href="#dead">What Is Coming Up</a>. Three of them, and this is the fight
  this module lets go badly: three clears in nine on the engine. See
  <a href="#cost">What the Night Costs</a> before you run it, because the reason is not the
  creature.</p>

  ''' + keeper(
    "<p>Fight it in the rubble. Broken ground, standing water, and a roof timber that will come down "
    "on somebody if it is shot through. A posse that treats this like the dooryard fight in Act One "
    "will find out why the numbers are worse.</p>") + '''

  <h2 id="a2-ledger">7. The Sacristy, and the Ledger</h2>
  <p>The one room in the mission with a roof on it, because somebody has kept a roof on it. Dry,
  swept, and holding a chest, a hammer, a whetstone, four blanks of unworked silver, and the ledger.</p>

  <p>Read these aloud, in order, as they are found. They are the module.</p>

  ''' + readaloud(
    "<strong>1809, in Salcedo&rsquo;s hand.</strong> &ldquo;We have not killed it and I will not "
    "write that we have. We have put a nail in it and we will keep putting nails in it. Whoever "
    "reads this after me: the work is not the nail. The work is the returning.&rdquo;") + '''

  ''' + readaloud(
    "<strong>1834, a different hand.</strong> &ldquo;Seven wells walked this month as every month. "
    "I am fifty-one. I have told no one, per the instruction, and I begin to think the instruction "
    "was written by a young man.&rdquo;") + '''

  ''' + readaloud(
    "<strong>March, this year, a small careful hand, the last full entry.</strong> &ldquo;Seven "
    "wells walked. I am eighty-one years old. I will speak to the Cardoza girl at Easter and she "
    "will say yes, and then I will sleep. Thirty-one years and I have never once been late.&rdquo;") + '''

  ''' + readaloud(
    "<strong>And then the last line, which is not an entry.</strong> Four words in the same hand, "
    "at the top of the next page, begun and not finished: &ldquo;If I am not&rdquo;") + '''

  ''' + keeper(
    "<p><strong>Stop there. Do not add to it.</strong> Esperanza Ríos died in April. Nobody was "
    "late, nobody betrayed anything, and nothing in seventy years failed except that a very old "
    "woman meant to do a thing at Easter and did not live to Easter. Every player at the table will "
    "understand that, and it will do more work than any villain this module could have had.</p>",
    "The whole module") + '''

  <p>The chest also holds the circuit: seven wells, named and mapped, in the order they were driven.
  The seventh on the list is the one in the courtyard, and beside it, in Salcedo&rsquo;s hand, the
  only underlined word in the ledger, <em>primero</em>. First.</p>
</section>
'''

# ============================================================ act three
ACT3 = '''
<section class="page" id="act3">
  ''' + runhead("Act Three") + '''
  <h1 class="chapter">Act Three &mdash; The Bottom of the Basin</h1>
  <p class="note">Aim for an hour and be willing to give it more. One Dread Check, one descent, and
  a decision that outlives the module.</p>

  <h2 id="a3-shaft">8. The First Well</h2>
  <p>Capped, in the courtyard, and the cap comes off with two people and a bar. Under it is dressed
  stone going down further than a lamp will show, and cold air coming up out of it that smells of
  wet rock and, faintly, of church.</p>

  <p>Opening it fills a segment of <a href="#truth-clock">the clock</a>. Say so, out loud, and ink
  the pip in front of them.</p>

  <h2 id="a3-descent">9. Down the Shaft</h2>
  <p><strong>Dread Check, DC 19, Will save.</strong> Tier III loss. A hundred and forty feet of wet
  rope in the dark, and the cut sockets going past at every waterline the well has ever had:
  six of them, one above another, each one greened, each one empty, a record of how far the water
  has fallen in seventy years and how many times somebody climbed down here to reset a nail into
  new stone.</p>

  ''' + readaloud(
    "The rope is wet and the walls are wet and about eighty feet down the lamp shows you the last "
    "socket, and it is not empty. There is a nail in it. It is bright. Somebody polished it, and "
    "not very long ago, and they polished it from a rope with no one at the top to hold it.") + '''

  <h2 id="a3-nail">10. The Sixth Nail</h2>
  <p>The one Esperanza Ríos reset last, in March, at eighty-one, alone. It is holding. It is the
  only thing in the Basin that still is, and it will hold for perhaps another year.</p>

  <p>There are four blanks of unworked silver in the sacristy chest, a hammer, and a whetstone. That
  is not a puzzle and the module does not want it treated as one. It is an offer, and the players
  will understand it the moment they see the four blanks, and what they do about it is the ending.</p>

  <h2 id="a3-bottom">11. The Bottom of the Basin</h2>
  <p>The shaft opens out. The padres dug a hundred and twenty feet of it and did not dig the last
  twenty, and the chamber at the bottom is wider than any well and older than any digging.</p>

  ''' + found("The Hunger That Walks") + '''

  <p>Full entry under <a href="#dead">What Is Coming Up</a>. One, and two of the Drowned with it,
  standing in water to the knee.</p>

  ''' + keeper(
    "<p><strong>Read its Putting It Down line before you run this and then read the second half of "
    "it again.</strong> Fire and iron will do it, slowly, and the engine says slowly is longer than "
    "the posse has: zero clears, one round of trading, see <a href='#cost'>What the Night "
    "Costs</a>. The other half of the line is the module's real ending: a true name, and a held "
    "warmth, may call the man back from it once.</p>"
    "<p>The name is in the ledger. Every keeper of the circuit wrote their own name at the head of "
    "their first year, and the name at the head of 1809 is not Salcedo's. It is the name of the man "
    "they found down here and could not save, and could only pin. A posse that read the sacristy "
    "carefully has it. A posse that grabbed the map and ran does not.</p>", "The ending") + '''

  <h2 id="a3-out">The Way Back Up</h2>
  <p>The escape valve, and it is always available. The rope is right there and nothing at the bottom
  of this well climbs. A posse that goes back up alive has not failed. They have left a thing
  pinned by one nail with a year on it, and they know exactly what that means now, which is more
  than anybody in the Basin knew this morning.</p>
</section>
'''

# ============================================================ cast
CAST = '''
<section class="page" id="cast">
  ''' + runhead("The Cast") + '''
  <h1 class="chapter">The Cast</h1>
  <p class="note">A want, a lever, and a line, per the Keeper&rsquo;s Book Ch. VIII.</p>

  ''' + npc("Elías Cardoza",
            "his water back and his family to stop dying of it",
            "he buried two of his own in wet ground and did not dig deep, and he knows he did not",
            "I put them in myself. I want you to know I put them in myself.") + '''

  ''' + npc("Rosalía Cardoza, sixteen",
            "to be asked, by somebody, what the old woman wanted to talk to her about at Easter",
            "Esperanza Ríos meant to hand her the circuit and died before she could, and Rosalía "
            "has spent four months assuming it was about a marriage",
            "She said she had something to give me and she would tell me at Easter. She was very old. I did not press her.") + '''

  ''' + npc("Hollis Deakin, who hauls the water",
            "to be paid and not to go back out there",
            "he has seen one of the Drowned on the road at dusk and told nobody, and it is eating him",
            "I hauled water past a man walking with his boots full. Two dollars, and I have not said that out loud before.") + '''

  ''' + npc("Fray Ignacio Salcedo, dead sixty years, in his own hand",
            "whoever comes next to understand that the work is the returning",
            "his ledger is the only honest account of the Basin anybody ever wrote",
            "The work is not the nail. The work is the returning.") + '''

  ''' + npc("Esperanza R&iacute;os, dead since April, aged eighty-one",
            "to hand it on at Easter",
            "she never told a living soul, exactly as instructed, and the instruction is what killed the Basin",
            "&mdash;") + '''

  ''' + keeper(
    "<p>Both of the people who matter most in this module are dead before it begins and neither of "
    "them did anything wrong. If your table goes looking for somebody to blame, let them look, and "
    "let them come up empty, and let one of the living ones say so.</p>") + '''
</section>
'''

# ============================================================ bestiary
DEAD = '''
<section class="page" id="dead">
  ''' + runhead("What Is Coming Up") + '''
  <h1 class="chapter">What Is Coming Up</h1>
  <p class="note">Printed in full so the Bestiary can stay on the shelf. These entries are generated
  from the same file the app reads, so they cannot drift from the book they came out of.</p>

  <h2 id="dead-drowned">The Drowned</h2>
  ''' + statblock("The Drowned",
                  "Three in Act One, on the road at dusk; two more at the bottom of the shaft. "
                  "They are wet in a dry country and they are recognised on sight.") + '''

  <h2 id="dead-plague">The Plague-Dead</h2>
  ''' + statblock("The Plague-Dead",
                  "Three, in the fallen west end of the nave. Fight them in the rubble; the "
                  "ground is why this fight is harder than its Tier.") + '''

  <h2 id="dead-hunger">The Hunger That Walks</h2>
  ''' + statblock("The Hunger That Walks",
                  "One, at the bottom, in the water. Read the second half of its Putting It Down "
                  "line twice: the module's ending is in it, and the name it needs is in the "
                  "sacristy ledger.") + '''

  ''' + keeper(
    "<p><strong>On the safe-table rule, and why it is silent here.</strong> A 5th-level posse is "
    "Tier 3 and everything in this module is Tier II or III, and nothing is over them at all. "
    "GritKeeper will seat every one of these fights without a murmur, which is the third of three "
    "answers the modules give: in module I the app refuses the boss outright, in module II it "
    "allows it grudgingly at one rung over, and here it has nothing to say. The posse has caught "
    "up with the country. The country is still winning, and now that is about tactics rather than "
    "about tiers.</p>", "Why the app has nothing to say") + '''
</section>
'''

# ============================================================ playtest numbers
COST = '''
<section class="page" id="cost">
  ''' + runhead("What the Night Costs") + '''
  <h1 class="chapter">What the Night Costs</h1>

  <p>Every number on this page came out of the game&rsquo;s own engine. Twelve posses (a Gunhand, a
  Preacher, a Mountain Man and a Sawbones, built by the generator, at 5th level)
  were run through all three acts on the same rules library the app runs on, with the Bestiary&rsquo;s
  numbers for every foe and the book&rsquo;s dice for every roll. The runs are seeded and reproduce.</p>

''' + night_costs("What the Water Answers",
      ["The ones who drank first (Act One)", "What lives in the nave (Act Two)", "The thing at the bottom (Act Three)"]) + '''

  <p>Read the first two rows together, because they are the interesting pair. Both fights are Tier
  II. In the second one the posse shoots half again as well &mdash; 61 per cent against 41 &mdash;
  and clears it one time in eight where it cleared the first two times in three. Same tier, same
  party, better dice, far worse outcome.</p>

  <p>What changed is that the posse arrived at the nave already spent. The round counts say it:
  Act One runs three rounds, and the nave is finished inside a round and a half, which at this
  level is what losing looks like rather than what winning looks like. Eight of twelve reached the
  nave; one of eight got past it.</p>

  ''' + keeper(
    "<p><strong>This is the module's own lesson about itself.</strong> Attrition is the enemy here, "
    "not any one creature. Module I could not be out-shot and module II could be out-prepared. This "
    "one is arithmetic across four hours: every Blood spent in the dooryard is Blood that is not "
    "in the nave, and every point not in the nave is not at the bottom of the shaft.</p>"
    "<p>So let the Sawbones work. Let them camp at the mission. Let them go back up the rope and "
    "come down again tomorrow; it costs a segment of the clock and the module is built to "
    "charge exactly that and no more.</p>") + '''

  <h2 id="cost-night">The Night, End to End</h2>
  <p>Zero of twelve finished the night on their feet. Nine broke off and rode out; three were put down
  to the last soul. Souls down at the end averaged 2.9 of 4. Nerve, though, finished at 70.1 of a
  possible 75, and <strong>not one soul broke in twelve runs</strong>: the lowest Nerve cost
  of the three modules, at the highest level, against the worst things.</p>

  <p>That is not an accident of the dice. A 5th-level posse has the Nerve to look at this, and the
  module knows it. What it does not have is the Blood to walk through it, and the Sawbones running
  between acts moved the count by one run in twelve. This is a night to be survived carefully, not
  charged.</p>

  <h2 id="cost-scaling">Scaling the Night</h2>
  <ul>
    <li><strong>A bigger or bolder posse.</strong> Four Plague-Dead in the nave and drop the timber
    on somebody. Have the sixth nail be already failing when they reach it: hours, not a
    year. Do not add Blood to the thing at the bottom; take the ledger name away instead.</li>
    <li><strong>A smaller or greener posse.</strong> Two Drowned in Act One. Let the sacristy be
    found before the nave. Have Rosalía Cardoza ride up to the mission on her own and say what the
    old woman told her, which shortcuts the ledger entirely.</li>
    <li><strong>If the dice turn cruel.</strong> The rope is always right there. Use it.</li>
  </ul>
</section>
'''

# ============================================================ after
AFTER = '''
<section class="page" id="after">
  ''' + runhead("The Water") + '''
  <h1 class="chapter">The Water, and What Comes After</h1>

  <p>However it ends, give it weight before anybody rolls anything else.</p>

  <h2 id="after-nails">If they take up the circuit</h2>
  <p>Four blanks, a hammer, seven wells, and a schedule. This is the ending the module is built for
  and it is a job. Forever, and nobody can be told about it. Ask the player
  who takes the hammer how often they intend to walk it, write the answer down, and hold them to it
  in every session after this one. A campaign obligation the players wrote themselves is worth ten a
  Keeper hands out.</p>

  <h2 id="after-name">If they called it by name</h2>
  <p>Then there is a man at the bottom of a well who has been down there since 1809 and is now
  awake, and old, and himself, and dying. He will last about a day. What he has to say in it is
  entirely the Keeper&rsquo;s, and it should be short, and it should not be grateful.</p>

  <h2 id="after-lost">If they went back up the rope</h2>
  <p>Do not run this as a failure. They know what nobody else in the Basin knows: seven wells, one
  nail left, and about a year. That is a campaign, and it is a better one than a clean kill would
  have been. The Basin has been living on borrowed water since 1809 and now somebody alive knows the
  terms of the loan.</p>

  ''' + quote("The work is not the nail. The work is the returning.",
              "Fray Ignacio Salcedo, San Clavo, 1809") + '''

  <h2 id="after-three">The three nights together</h2>
  <p>A posse that has run all three has been told the same thing three ways: at Coffin Wells that
  some things cannot be shot, at Saltlick that some things must be prepared for, and here that some
  things have to be kept. Coffin Wells and Saltlick both end within sight of this mission. That was
  always on purpose.</p>
</section>
'''

BODY = (CONTENTS + WHAT + TRUTH + HOOK + GROUND + ACT1 + ACT2 + ACT3
        + CAST + DEAD + COST + AFTER)

html = splice(H, BODY)
html = finish(
    html,
    curated=[
        ("Mission San Clavo", "ground"),
        ("Cardoza, El&iacute;as", "a1-house"),
        ("Cardoza, Rosal&iacute;a", "cast"),
        ("Deakin, Hollis", "cast"),
        ("R&iacute;os, Esperanza", "truth-keeper"),
        ("Salcedo, Fray Ignacio", "a2-ledger"),
        ("The Cardoza well", "a1-well"),
        ("The courtyard", "a2-court"),
        ("The nave", "a2-nave"),
        ("The sacristy", "a2-ledger"),
        ("The ledger", "a2-ledger"),
        ("The shaft", "a3-descent"),
        ("The sixth nail", "a3-nail"),
        ("The silver nails", "truth-wells"),
        ("The circuit of seven wells", "after-nails"),
        ("The true name", "a3-bottom"),
        ("The Drowned", "dead-drowned"),
        ("The Plague-Dead", "dead-plague"),
        ("The Hunger That Walks", "dead-hunger"),
        ("Safe-table rule (why the app is silent)", "dead"),
        ("The Wells, Failing Outward (clock)", "truth-clock"),
        ("Attrition, as the real enemy", "cost"),
        ("Scaling the night", "cost-scaling"),
        ("What the engine says", "cost"),
        ("The map", "ground"),
    ],
    subtitle="Every person, place and thing in this night, and the page it waits on.",
    intro="Scene numbers run 1&ndash;11 across the three acts and are keyed in the margin of each, "
          "and on the map in <a href=\"#ground\">The Ground</a>.",
    out=f"module-{SLUG}.html",
)
report(f"module-{SLUG}.html", html)
