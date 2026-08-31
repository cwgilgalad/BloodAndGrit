#!/usr/bin/env python3
# Build "Blood & Grit — A Face Not His Own", module II, on the shared engine.
# Reads blood-and-grit.html (run build_player.py first), writes module-a-face-not-his-own.html.
#
# The Keeper's Book names this adventure at Saltlick Station and gives it a paragraph. This is that
# paragraph keyed: eight souls under one roof, a tell that a posse in a hurry will shoot past, and
# a Tier III thing the safe-table rule does NOT refuse — which makes it the opposite lesson from
# module I. Every number under "What the Night Costs" came out of GK/playtest.
from modules_common import (basin, night_costs, shell, splice, finish, report, runhead, quote, readaloud,
                            keeper, clock, npc, statblock, found, contents)
from module_maps import map_html

VERSION = "1.6"
SLUG = "a-face-not-his-own"

H = shell(
    foot="A Face Not His Own",
    kicker="A Second Reckoning, Keyed and Ready to Run",
    tiny_edition="Module II &middot; A one-night adventure for four souls at 3rd level",
    tiny_blurb="Eight souls are at Saltlick Station tonight. One of them is wearing somebody.",
    colophon="Blood &amp; Grit &middot; Module II &middot; A Face Not His Own &middot; "
             f"Version {VERSION} &middot; For the Keeper Alone",
    version=VERSION,
    cover_bg="#0f1113",
    cover_key="rgba(122,124,118,.92)",
    cover_foot_ink="#a9b0ac",
    cover_sub_ink="#c4c0b0",
    epigraphs=[
        ('"A man is his face to everybody but his mother, and his mother was forty years dead,\n'
         '    so there was nobody at that station qualified to say."\n'
         '    <span class="src">— Marshal Adelia Cruz, on the Saltlick inquest</span>'),
        ('"Count them. Count them out loud, and count them again in an hour, and if the number\n'
         '    is the same both times you have still learned nothing."\n'
         '    <span class="src">— advice written inside a station-keeper\'s ledger, Saltlick</span>'),
    ],
)

# ============================================================ contents
CONTENTS = '''
<section class="page" id="contents">
  ''' + runhead("Contents") + '''
  <h1 class="chapter">Contents</h1>
  ''' + contents([
      ("what", "What This Is"),
      ("basin", "Perdition Basin"),
      ("truth", "The Truth of It"),
      ("turn", "The Woman Going East"),
      ("hook", "The Hook, and Getting Them There"),
      ("ground", "The Ground"),
      ("act1", "Act One &mdash; The Wrong Note Among Friends"),
      ("act2", "Act Two &mdash; The First Taking"),
      ("act3", "Act Three &mdash; The Tell Made Plain"),
      ("cast", "The Eight"),
      ("dead", "What Wears a Face Here"),
      ("cost", "What the Night Costs"),
      ("after", "The Ride Out, and What Comes After"),
  ]) + '''
</section>
'''

# ============================================================ what this is
WHAT = '''
<section class="page" id="what">
  ''' + runhead("What This Is") + '''
  <h1 class="chapter">What This Is</h1>
  ''' + quote("A locked room is only frightening while the door is the problem.",
              "a note pinned inside the cover of the first printing") + '''
  <p>One night at the table, for four souls at 3rd level, at a relay station on the north road out
  of Perdition Basin. Three to four hours. Every creature in it is printed here in full, so the
  Bestiary can stay on the shelf.</p>

  <p>It is a different animal from <em>The Salt at Coffin Wells</em> and it is meant to be. Module I
  was a night of things coming at the posse out of the dark. This is a night of things already
  inside, sitting at the same table, passing the salt. Nothing charges the door. The horror is that
  the posse has to decide, out loud, in front of everybody, which of eight frightened people is not
  a person, and then be wrong at least once.</p>

  <h2 id="what-you-need">What You Need</h2>
  <p>The Player&rsquo;s Book for the souls, and this. The Keeper&rsquo;s Book is useful and not
  required. If you are running GritKeeper at the table, put all eight of the station&rsquo;s people
  on the Posse tab as NPCs before you start; the act of deleting a row when one of them stops
  being a person does more work at a table than any description will.</p>

  <h2 id="what-teaches">What It Teaches, and in What Order</h2>
  <p>Three things, one per act, and never two at once.</p>
  <ul>
    <li><strong>Act One teaches that the horror can talk.</strong> No fight at all. One Dread Check
    on a man answering to the wrong name, and a long hour of eight people being ordinary at each
    other.</li>
    <li><strong>Act Two teaches the cost of being certain.</strong> Two of the station&rsquo;s
    people are already gone and the posse has to fight them in a room eleven feet across. Somebody
    at your table will kill a person who was still a person. The module is built to let that happen
    and not to punish it.</li>
    <li><strong>Act Three teaches that the answer was written down.</strong> Unlike module I, this
    fight <em>can</em> be won on the field, though the engine says it usually is not, and says why.
    See <a href="#cost">What the Night Costs</a>.</li>
  </ul>

  ''' + keeper(
    "<p>Read the Eight before you read the acts. This module is a cast, a building, and a rule about "
    "what the thing can and cannot do; the three acts are just the order those meet the posse in. A "
    "Keeper who knows the eight can improvise the whole night. A Keeper who has memorised the acts "
    "and not the people will be reading when they should be answering.</p>", "Before you run it") + '''
</section>
'''

# ============================================================ the truth
TRUTH = '''
<section class="page" id="truth">
  ''' + runhead("The Truth of It") + '''
  <h1 class="chapter">The Truth of It</h1>
  <p class="note">For the Keeper alone. Nobody at Saltlick knows any of this, including the two who
  are no longer people.</p>

  <p>Eleven days ago the down coach put off a passenger at Saltlick who had boarded at the north
  line as Mr. Amos Dell, commercial traveller in patent remedies. Mr. Dell had been dead since the
  Tuesday previous. What got off the coach had been wearing him for four days and had learned, in
  that time, that a man travelling alone is the easiest thing in the world to be.</p>

  <p>It came south because it had used up the north. It is not hunting the posse and it is not
  hunting the station. It is doing what it has done in five towns already: settling in, taking one
  soul at a time, and leaving before the count gets noticed. Saltlick is a stop, not a destination.
  That is the coldest thing about it and the module should let the players work it out for
  themselves.</p>

  <h2 id="truth-taken">Who It Has Already Taken</h2>
  <p>Two, before the module opens. <strong>Amos Dell</strong> is the skin it arrived in. <strong>Cal
  Mears, the hostler</strong>, it took on the fourth night. It keeps both, and it wears whichever the
  room calls for, but a thing wearing two faces cannot keep both in the same room, and that
  is the whole solution to this module.</p>

  <p>What is left of the men themselves is in the ice house, and the ice house is the only door at
  Saltlick anybody has bothered to lock.</p>

  <h2 id="truth-tell">The Tell</h2>
  <p>It has the face, the voice, the hands and the memories. What it does not have is the habit.
  <strong>Neither Dell nor Mears is ever in the same room as the other.</strong> They are always just
  gone to the barn, just stepped out, just turned in. Six of the station&rsquo;s people will tell the
  posse both men are here tonight and not one of them has seen them together.</p>

  ''' + keeper(
    "<p><strong>Do not withhold this and do not hand it over.</strong> Say, unprompted, that Dell has "
    "just gone out to see to the team, whenever Mears is on stage. Say Mears is in the barn whenever "
    "Dell is. Say it four or five times across Act One in exactly that flat, ordinary way, and put "
    "nothing on it. The table will hear it eventually, and the moment somebody at the table says the "
    "words out loud is the best moment this module has.</p>", "The one thing to run well") + '''

  <h2 id="truth-clock">The Clock</h2>
  ''' + clock("The Count at Saltlick", 4,
              "Fill a segment each time the posse spends a scene on the wrong person, and each time "
              "an hour passes with nobody named. At four, it stops needing the face: Act Three "
              "opens whether the posse is ready or not, and it opens in whatever room they are "
              "standing in.") + '''
</section>
'''

# ============================================================ the turn
# The second truth. "The Truth of It" explains what is at Saltlick; this explains why it stayed.
# The module works without this page and is a different module with it, so it is kept separate
# and a Keeper is told plainly which one they are running before they start.
TURN = '''
<section class="page" id="turn">
  ''' + runhead("Mrs. Follett") + '''
  <h1 class="chapter">The Woman Going East</h1>
  ''' + quote("He was nine weeks a better man than he was forty years. I have thought about that "
              "every day since and I have not got to the bottom of it.",
              "Mrs. Ada Follett, if anyone ever asks her twice") + '''

  <p>Saltlick is a stop and not a destination, and the thing has run out of nothing here. It has
  a full station, a locked ice house and eleven quiet days. By its own arithmetic it should have
  been three towns south a week ago. It is still here, and the reason is sitting in the common
  room with her bag packed, watching the door to the barn.</p>

  <h2 id="turn-kearney">What Happened at Kearney</h2>
  <p>Ada Follett is going east to bury a brother. Her brother died at Kearney in the spring, three
  towns back along the same line, and he was buried there in April by people who knew him. She is
  not going east to bury him. She is going east because that is the direction the coach goes.</p>

  <p>Nine weeks before he died, something began wearing Peter Follett. She knew inside a
  fortnight. She has never been able to say exactly how — the way a sister knows, and no more
  than that. What she can say, and will not, is that those nine weeks were the best nine weeks of
  her brother&rsquo;s life and of hers. He did not drink. He came in at a decent hour. He asked
  her about her day and then he listened to the answer, which the man himself had never once
  done in forty years.</p>

  <p>She said nothing for seven weeks. She has had four months on coaches to work out what that
  makes her, and she has not arrived anywhere.</p>

  ''' + keeper(
      " Ada has told it nothing. She has never spoken to it, warned it, or handed it a name. What "
      "she has done is watch — for four hours in that common room, longer than anyone, sharper "
      "than anyone — and keep her mouth shut. Cal Mears is dead in part because a woman who saw "
      "it happening had reasons of her own for letting the night run on. Play her as the "
      "module already plays her: the best witness in the building, unasked. Everything she says "
      "is true. She simply never says it first.",
      "The exact shape of it") + '''

  <h2 id="turn-tell">The Tell Behind the Tell</h2>
  <p>Six of the station&rsquo;s people will say both men are here tonight. Ada says it earliest
  and says it flattest, and if a player thinks to ask the others where they got it, four of them
  got it from her. She has been keeping the thing&rsquo;s alibi without ever being asked to,
  because she would like to see how it ends.</p>

  <p>If the posse asks her a direct question she answers it completely and without hedging, and
  she looks relieved. Nobody has asked her anything in eleven days.</p>

  <h2 id="turn-offer">The Offer</h2>
  <p>When it is cornered in Act Three, it does not fight first. It makes an offer, and the offer
  is the best scene in this module.</p>

  ''' + readaloud(
      "It stops with its back to the ice-house door and lets its shoulders down, and when it "
      "speaks the voice is not Dell&rsquo;s and not Mears&rsquo;s. It is a voice from your own "
      "life, one you have not heard in some years, saying your name the way only that person "
      "said it. &ldquo;I could be him again,&rdquo; it says, kindly, without hurry. &ldquo;Better "
      "than he was at the end. He would be at your table Sunday and he would be sober and he "
      "would remember your birthday, and you would have him back, and it would cost you "
      "nothing.&rdquo; It waits. &ldquo;The man I am wearing tonight was going to die of the "
      "drink inside two years and nobody was going to write it down. This way somebody misses "
      "him.&rdquo;") + '''

  ''' + keeper(
      " Every word of that is true and the Keeper must know it going in. It can do the thing it "
      "is offering. It will keep the bargain for as long as it is fed and it has kept longer ones. "
      "Do not play it as a trick, do not have it sneer, and do not put a tell in the voice. The "
      "horror in this scene is that the offer is good, and that a table full of grown people has "
      "to turn it down out loud, one at a time, in front of each other.",
      "Do not make this easy") + '''

  <p><strong>If a player takes it.</strong> Let them. They give it a name — someone who will not
  be missed, which means the player has to think of one, which is the price and is meant to be
  felt. They gain the person back, in the shape it wore, for as long as they keep feeding it.
  Mark them one step and give them a standing thread. Do not roll for this and do not offer a
  save. A soul who says yes to that has said yes.</p>

  <p><strong>Ada will take it.</strong> She has been waiting four months to be asked. If the
  posse has been decent to her she may hesitate, and if one of them has actually spoken to her
  about her brother she may not take it at all, and that is the largest thing a kindness has ever
  bought in this module. Play the hesitation honestly and let the dice stay in the cup.</p>
</section>
'''

# ============================================================ the hook
HOOK = '''
<section class="page" id="hook">
  ''' + runhead("The Hook") + '''
  <h1 class="chapter">The Hook, and Getting Them There</h1>

  ''' + readaloud(
    "The norther came down off the mesa about three and by four you could not see the trail. "
    "Saltlick Station has a light in it and a barn with a roof, and the man on the step is waving "
    "you in with both arms like he has been waiting all day for somebody to be glad to see.") + '''

  <p>They do not need a reason to be here. They need a reason not to leave, and the weather is it.
  The norther runs until first light and the module ends at first light, which is not a coincidence.</p>

  <h2 id="hook-why">Three Ways In</h2>
  <ul>
    <li><strong>The weather.</strong> Simplest and best. They are on the north road, it turns, and
    Saltlick is the only roof in eleven miles.</li>
    <li><strong>The coach.</strong> They are riding it, or escorting it, or waiting on it. It is due
    at dawn and it will arrive on time, which matters; see
    <a href="#after-coach">the ride out</a>.</li>
    <li><strong>Following module I.</strong> The scrap of worked silver off Tom Pell&rsquo;s body has
    a mate. Marshal Cruz has heard of a traveller in patent remedies buying old church silver up and
    down the north line and paying too much for it. That is a true rumour and a false lead: the thing
    buys silver to know where it is.</li>
  </ul>

  ''' + npc("Ollie Gant, station keeper",
            "the coach to come on time and nothing else to happen ever again",
            "he is proud of his station and will not have it called unclean",
            "Eleven days without a word of trouble. You will want to not be the trouble.") + '''
</section>
'''

# ============================================================ the ground / map
GROUND = '''
<section class="page" id="ground">
  ''' + runhead("The Ground") + '''
  <h1 class="chapter">The Ground</h1>
  <p class="note">Every numbered place below is a keyed scene, and the number on the map is the
  number in the margin of the act it belongs to.</p>

  ''' + map_html(SLUG,
                 "the whole of the night, four buildings and a yard, with the twelve keyed scenes "
                 "pinned where they happen") + '''

  <h2 id="ground-shape">What the Shape of It Does</h2>
  <p>Saltlick is four buildings around a yard forty paces across, on a flat with no cover for a mile
  in any direction. That geometry is doing three jobs and it is worth knowing which.</p>
  <ul>
    <li><strong>Nobody can leave.</strong> The doors are not locked. It is dark, and blowing, and
    there is nowhere to go. The players will test this. Let them, once, briefly, and
    let the country turn them around.</li>
    <li><strong>Everybody keeps crossing the yard.</strong> Which is how the posse can be told six
    times that both men are here and never see them together.</li>
    <li><strong>The last act has an open field.</strong> Act Three is fought in the yard on purpose:
    forty paces of nothing, at first light, with a line of ash across it.</li>
  </ul>

  ''' + keeper(
    "<p>Hand the map to the table. There is nothing on it the posse cannot see from the step, and a "
    "table that can point at the ice house will use the ice house. The download beside it prints on "
    "one sheet.</p>") + '''
</section>
'''

# ============================================================ act one
ACT1 = '''
<section class="page" id="act1">
  ''' + runhead("Act One") + '''
  <h1 class="chapter">Act One &mdash; The Wrong Note Among Friends</h1>
  <p class="note">Aim for an hour. No fight. One Dread Check, and eight people being ordinary.</p>

  <h2 id="a1-house">1. The Station House</h2>
  <p>Low, long, warm, and smelling of coffee and wet wool. Gant takes their coats and tells them the
  rules of his house, which are: pay for what you eat, do not go in the ice house, and do not wake
  the passengers before five.</p>

  <p>The ice house rule is the only one he means. He means it because there is a side of beef in
  there he has been over-charging for, and he is embarrassed. He does not know what else is in there.</p>

  <h2 id="a1-common">2. The Common Room, and Eight Names</h2>
  <p>Introduce all eight here, quickly, in one pass, the way a room actually introduces itself. Full
  entries under <a href="#cast">The Eight</a>. Do not slow down for them and do not let a player
  interview them one at a time yet; the room should feel crowded and cheerful and slightly
  too loud.</p>

  ''' + readaloud(
    "Somebody is losing at cards, badly and happily. The Chinese cook is arguing about the price of "
    "coal with a woman who is not paying for the coal. And a big man by the fire says, without "
    "looking up: &ldquo;Cal&rsquo;s got the team. Dell&rsquo;s gone out to help him. They&rsquo;ll "
    "want feeding when they&rsquo;re in.&rdquo;") + '''

  ''' + keeper(
    "<p>That is the first plant and it is deliberately worthless. Nobody should notice it. Say four "
    "more like it across this act, always about the same two men, always in somebody else's mouth, "
    "always while one of them is in the room.</p>") + '''

  <h2 id="a1-barn">3. The Barn</h2>
  <p>Warm, dark, full of the noise of animals not settling. The stalls are along the north wall and
  the horses in the two nearest the door will not stand: they have been moved twice tonight
  and they will be moved again.</p>

  <p>A Mountain Man or anyone with a hand for stock reads this in a moment: the horses are not
  spooked at the weather. They are spooked at a thing that keeps walking past them.</p>

  <h2 id="a1-corral">4. The Corral, and the Horses That Will Not</h2>
  <p>Six head, outside, in a norther, because they would not come in. Gant is angry about it and has
  given up. Anyone who works them can get them as far as the barn door and no further.</p>

  ''' + found("The Skin-Walker") + '''

  <h2 id="a1-dread">The Dread Check of Act One</h2>
  <p><strong>Dread Check, DC 15, Will save.</strong> Tier II loss. It fires the first time somebody
  calls the hostler by name and he answers to the wrong one. He says &ldquo;Amos&rdquo; is
  fine, or he answers to Cal a half-second late, and then laughs it off so smoothly that the moment
  closes before anyone can put a hand on it.</p>

  ''' + keeper(
    "<p>One check, and it is on the wrongness rather than on anything seen. Nobody at this table has "
    "seen a monster yet and the module is in no hurry for them to. Sleep is a Toll rather than a "
    "scene: a night in the cold with the doors barred costs each soul 2 Blood and nothing else.</p>") + '''
</section>
'''

# ============================================================ act two
ACT2 = '''
<section class="page" id="act2">
  ''' + runhead("Act Two") + '''
  <h1 class="chapter">Act Two &mdash; The First Taking</h1>
  <p class="note">Aim for ninety minutes. One Dread Check, one fight in a very small room.</p>

  <h2 id="a2-well">5. The Well</h2>
  <p>The bucket comes up with a coat button in it, and the coat is hanging by the door, and its owner
  has been asleep in the bunk row for four hours and can prove it.</p>

  <p>It is a real clue and it points at nothing. The thing dropped it crossing the yard four nights
  ago. Let the posse spend a scene on it if they want, and fill a segment of
  <a href="#truth-clock">the clock</a> when they do, because that is exactly what the clock is for.</p>

  <h2 id="a2-bunks">6. The Bunk Row</h2>
  <p>Six bunks, a curtain, and no privacy at all. This is where the posse can get people alone, and
  it is where the module wants them: one soul, one lamp, one frightened person, and a question.</p>

  <p>Everybody here will answer honestly. Six of them will say both Dell and Mears are at the station
  tonight. Asked directly &mdash; <em>when did you last see the two of them together?</em> &mdash;
  every one of them will stop, and think, and not be able to say.</p>

  ''' + keeper(
    "<p><strong>This is the scene the module exists for. Do not rush it and do not help.</strong> If "
    "nobody asks the question, they do not get the answer, and Act Three simply costs more. If "
    "somebody does ask it, give them the pause and the honest, frightened, useless answer, and then "
    "let the table do the rest.</p>", "The hinge") + '''

  <h2 id="a2-ice">7. The Ice House</h2>
  <p>Locked, and Gant has the key on him and will not give it up for asking. Behind the beef, under
  sacking, are Amos Dell and Cal Mears: both of them, both intact, both wearing the clothes
  they were taken in, and neither of them marked anywhere a coat would not cover.</p>

  <p><strong>Dread Check, DC 17, Will save.</strong> Tier II loss. Not for the bodies. For the arithmetic
  the posse does standing over them, which is that both of these men were at supper.</p>

  <h2 id="a2-tack">8. The Tack Room</h2>
  <p>Eleven feet by nine, one door, hooks and harness on every wall, a lamp on a nail. Whatever the
  posse has worked out, this is where it stops being talk: the two it has already been inside come
  off the wall at them, in the dark, in a room too small to back out of.</p>

  ''' + found("The Possessed") + '''

  <p>Full entry under <a href="#dead">What Wears a Face Here</a>. Two of them. It has finished with
  both bodies and left behind whatever it put in them, and both still wear the faces the posse has
  been sharing a room with all night.</p>

  ''' + keeper(
    "<p><strong>The engine says the posse wins this one</strong>: ten clears in twelve, in "
    "about two rounds. That is by design. Act Two is the fight this module lets them have, so that "
    "Act Three can be the one it does not. Let it be brutal and fast and let them win it.</p>"
    "<p>If a player refuses to fire on a face they know, that is not a problem to solve. Let them "
    "hold, let it cost them, and let another soul do it. Then remember which of them hesitated, "
    "because Act Three will ask again.</p>") + '''
</section>
'''

# ============================================================ act three
ACT3 = '''
<section class="page" id="act3">
  ''' + runhead("Act Three") + '''
  <h1 class="chapter">Act Three &mdash; The Tell Made Plain</h1>
  <p class="note">Aim for an hour. One Dread Check, one open field, and a sunrise.</p>

  <h2 id="a3-tell">9. It Stops Pretending</h2>
  <p><strong>Dread Check, DC 18, Will save.</strong> Tier III loss. It happens when the last face
  comes off, and the module is specific about how: it does not tear, and it does not melt. The man
  standing in front of them simply stops doing the thousand small things a man does, all at once,
  and goes still in a way nothing alive goes still, and then it is not wearing anybody at all.</p>

  ''' + readaloud(
    "It has been holding its shoulders like a man who is cold. It stops. It does not put them down "
    "&mdash; it stops holding them, and they are not where a man&rsquo;s shoulders are. "
    "&ldquo;You counted,&rdquo; it says, in Cal Mears&rsquo;s voice, and it sounds pleased. "
    "&ldquo;Five towns and nobody counted.&rdquo;") + '''

  <h2 id="a3-count">10. The Count</h2>
  <p>Whoever is still alive gets one scene (sixty seconds at the table) to do
  something with what they know before it comes across the yard. This is where the ash line gets
  laid, or the mirror gets fetched off the wall of the bunk row, or somebody works a Sign, or the
  Preacher prays over a handful of shot.</p>

  ''' + keeper(
    "<p><strong>Everything a posse can do here is printed in the creature's own entry</strong> and "
    "the entry is on the next page. It cannot abide its true reflection. It cannot cross a line of "
    "ash and bone. A prayed-over or silver bullet wounds it past the borrowed skin. There is a "
    "mirror in the bunk row, there is a stove full of ash and a yard full of bone-meal for the "
    "stock, and there is a Preacher. The module has been putting all three in front of them since "
    "Act One.</p>", "Say the three out loud if you have to") + '''

  <h2 id="a3-yard">11. The Yard at First Light</h2>
  <p>Forty paces of open ground, going gray at the east end. It comes across it without hurrying,
  because it has done this in five towns and it has not yet met the one that counted in time.</p>

  ''' + found("The Skin-Walker") + '''

  <p>Full entry under <a href="#dead">What Wears a Face Here</a>. Unlike module I, the safe-table
  rule does <em>not</em> refuse this fight: a 3rd-level posse is Tier 2 and a Skin-Walker is
  Tier III, one rung over, which the book calls a hard fight rather than an impossible one. The app
  will seat it on the field without arguing.</p>

  ''' + keeper(
    "<p><strong>And the engine still says they will not win it by shooting.</strong> Twelve runs, "
    "zero clears, every one of them broken off &mdash; see <a href='#cost'>What the Night "
    "Costs</a>. The difference from module I is the reason. Module I's boss had no answer on the "
    "field at all. This one is a fight the posse loses on the numbers by a little, and one "
    "prepared thing flips it. The "
    "mirror does not kill it. The mirror makes it hesitate, and hesitation is the whole margin.</p>") + '''

  <h2 id="a3-privy">12. The Ash Line</h2>
  <p>Behind the privy is a barrel of stove ash and, in the barn, forty pounds of bone-meal bought for
  the stock. A line of the two mixed, laid across the yard, is the second half of the
  creature&rsquo;s own answer &mdash; and it does not have to be a big line. It has to be between the
  thing and the door it wants.</p>

  <p>Laying it is one action and anyone can take it. Crossing it is the one thing the Skin-Walker
  cannot do, and the module is emphatic that a Keeper should honour that absolutely: no save, no
  roll, no exception. A rule the country obeys without a die is worth more to a table than any ten
  it negotiates.</p>

  <h2 id="a3-dawn">The Coach at Dawn</h2>
  <p>The escape valve, and it is always available. The down coach makes Saltlick at first light,
  every day, and it makes it tonight. Six armed strangers and a shotgun messenger arriving in the
  middle of an open-field fight will end it, one way or the other. It costs the posse the ending. It
  does not cost them the night.</p>
</section>
'''

# ============================================================ cast
CAST = '''
<section class="page" id="cast">
  ''' + runhead("The Eight") + '''
  <h1 class="chapter">The Eight</h1>
  <p class="note">A want, a lever, and a line, per the Keeper&rsquo;s Book Ch. VIII. Two of these
  people are already gone; the entries do not say which, because the Keeper already knows and the
  page is easier to read at the table if it treats them all alike.</p>

  ''' + npc("Ollie Gant, station keeper",
            "his station to be a clean-run house that the company never has to think about",
            "the ice house key is on his belt and his pride is the lock on it",
            "There has been no trouble here in eleven days and I intend to keep the run going.") + '''

  ''' + npc("Amos Dell, traveller in patent remedies",
            "to be found agreeable and then forgotten",
            "he is generous with his stock and nobody can name a thing he has sold",
            "Take two of these for the cold. No, no charge. I have had a good month.") + '''

  ''' + npc("Cal Mears, hostler",
            "the horses settled and the night over",
            "he is the only man here the animals will not go near, and he has noticed",
            "They have been like this since the weather turned. Stock know weather.") + '''

  ''' + npc("Mrs. Ada Follett, going east to bury a brother",
            "to get where she is going and not be spoken to kindly",
            "she is the sharpest observer in the building and nobody has asked her anything &mdash; "
            "and she is the reason the thing is still here on the eleventh day "
            "(<a href=\"#turn\">The Woman Going East</a>, which the Keeper should read before "
            "running her)",
            "I have been watching that room for four hours, and I would not care to say what I have seen.") + '''

  ''' + npc("Wu Cheng-hsi, who cooks and keeps the accounts",
            "the coal money settled and the coach on time",
            "he keeps the station's ledger, and the ledger records who was fed and when",
            "Eight at supper. Eight plates. I do not make a mistake with plates.") + '''

  ''' + npc("Deputy Sam Orr, moving a prisoner east",
            "his prisoner delivered and no complications on the paper",
            "he will not unchain the man for anything, which is either the safest thing in the "
            "building or the cruellest",
            "Whatever this is, it is not my business and he is not going anywhere.") + '''

  ''' + npc("Bill Teague, in irons, being moved for a hanging",
            "not to be in this building when whatever it is finishes",
            "he has been awake and chained in the common room for four nights and has seen more of "
            "the station than anyone alive",
            "I ain't seen those two men in a room together. Four nights. Ask me again slow.") + '''

  ''' + npc("Tobe, the boy who does the boots, fourteen",
            "to be treated as one of the men",
            "he goes everywhere, he is invisible, and he has been in the ice house twice",
            "There's a smell in there ain't beef. I said. Nobody wanted it said.") + '''

  ''' + keeper(
    "<p>Teague and Tobe are the two who hand the posse the answer, and both are people the West "
    "trains a table to discount: a man in irons and a boy. That is the point and it is not "
    "subtle. Play it straight and let the table find it.</p>") + '''
</section>
'''

# ============================================================ bestiary
DEAD = '''
<section class="page" id="dead">
  ''' + runhead("What Wears a Face") + '''
  <h1 class="chapter">What Wears a Face Here</h1>
  <p class="note">Printed in full so the Bestiary can stay on the shelf. These entries are generated
  from the same file the app reads, so they cannot drift from the book they came out of.</p>

  <h2 id="dead-possessed">The Possessed</h2>
  ''' + statblock("The Possessed",
                  "Two, in the tack room, and both of them are faces the posse has eaten supper "
                  "with. Play them as people who are still trying to say something.") + '''

  <h2 id="dead-skin">The Skin-Walker</h2>
  ''' + statblock("The Skin-Walker",
                  "One, in the yard, at first light. Read its Putting It Down line to yourself "
                  "twice before Act Three: all three of its answers are keyed into the station, "
                  "and none of them is an attack roll.") + '''

  ''' + keeper(
    "<p><strong>On the safe-table rule, and why it is quiet this time.</strong> A Skin-Walker is "
    "Tier III and a 3rd-level posse is Tier 2 (one rung over, not two), so GritKeeper "
    "will seat this fight on the field without a word. Module I's Nightwalker was two rungs over and "
    "the app argues about it. The rule has not changed; the posse has. That is worth pointing at, "
    "because a table that only ever meets the rule when it refuses something never learns what it is "
    "actually measuring.</p>", "Why the app is quiet this time") + '''
</section>
'''

# ============================================================ playtest numbers
COST = '''
<section class="page" id="cost">
  ''' + runhead("What the Night Costs") + '''
  <h1 class="chapter">What the Night Costs</h1>

  <p>Every number on this page came out of the game&rsquo;s own engine. Twelve posses (a Gunhand, a
  Preacher, a Mountain Man and a Sawbones, built by the generator, at 3rd level)
  were run through all three acts on the same rules library the app runs on, with the Bestiary&rsquo;s
  numbers for every foe and the book&rsquo;s dice for every roll. The runs are seeded and reproduce.</p>

  <p>They were run twice over: once <em>cold</em>, with no recovery between acts and no Grit spent
  and no Sign or Miracle worked, and once <em>tended</em>, with the posse back to half Blood between
  acts.</p>

''' + night_costs("A Face Not His Own",
      ["The tack room (Act Two)", "The yard at first light (Act Three)"]) + '''

  <p>Nobody died. Across twelve cold runs the posse was never put down to the last soul, not
  once, and they never finished the night on their feet either. Twelve out of twelve broke
  off and rode out. Souls down at the end averaged 2.2 of 4, and Nerve finished at 49.6 of a
  possible 71, with one run in twelve seeing a soul break outright.</p>

  <p>That is a very particular shape and it is the shape this module was built for. The Act Two
  fight is a fight the posse wins. The Act Three fight is a fight the posse survives. Giving them
  back half their Blood between acts changed neither count, which is how you know the difference
  between the two rows is not attrition.</p>

  ''' + keeper(
    "<p><strong>Twenty per cent, against seventy-two.</strong> That is the Act Three row, whole. "
    "Four souls trading Strikes at rising MAP against Defense 17 land one blow in five, and it "
    "hits back nearly three times in four. A round and a half of that is the entire fight. Bring "
    "nothing to the yard, and the yard is a countdown.</p>"
    "<p>Now put one prepared thing in their hands. A mirror off the bunk-room wall costs it its "
    "first round. A line of ash and bone takes the yard away from it. Silver or prayed-over shot "
    "moves that twenty per cent to something that matters. None of those is a house rule: "
    "all three are printed in the creature's own entry, three pages back.</p>") + '''

  <h2 id="cost-compare">Against Module I</h2>
  <p>The same harness ran <em>The Salt at Coffin Wells</em> at 1st level and this at 3rd, and the two
  Tier III fights failed differently. The Nightwalker was never beaten and never could be: it is two
  Tiers over the posse and the safe-table rule says so out loud. The Skin-Walker is one Tier over,
  the app seats it without complaint, and the engine never once cleared it;
  but every posse that reached the yard was a posse that only shot at it.</p>

  <p><strong>Module I's lesson is that some things are not fights. This one's is narrower and
  harder: some things are fights you lose unless you did something first.</strong></p>

  <h2 id="cost-scaling">Scaling the Night</h2>
  <ul>
    <li><strong>A bigger or bolder posse.</strong> Three Possessed in the tack room instead of two.
    Have it take Tobe in Act Two, so the posse is fighting a boy in Act Three. Do not add Blood to
    the Skin-Walker; take the mirror away instead.</li>
    <li><strong>A smaller or greener posse.</strong> One Possessed. Let Mrs. Follett say what she
    has seen without being asked. Have the ash barrel already standing open in the yard, where
    somebody will trip over it.</li>
    <li><strong>If the dice turn cruel.</strong> The coach is always one scene away. Use it.</li>
  </ul>
</section>
'''

# ============================================================ after
AFTER = '''
<section class="page" id="after">
  ''' + runhead("The Ride Out") + '''
  <h1 class="chapter">The Ride Out, and What Comes After</h1>

  <p>However it ends, give it weight before anybody rolls anything else.</p>

  <h2 id="after-won">If they put it down</h2>
  <p>Six people live who would not have. Two of them will not thank the posse, because two of them
  watched a stranger shoot somebody they knew by name. Let Saltlick be grateful and unfriendly at the
  same time, which is how a place is when it has been saved from something it still does not believe
  in.</p>

  <h2 id="after-lost">If it walks away</h2>
  <p>Or if the fourth segment filled and it did not need the face any more. Do not run this as a
  failure. It leaves wearing somebody, and the somebody is a person the posse spent a night with.
  Six towns now. It has learned that a posse can count, which makes it careful, which makes it
  slower and worse and further away.</p>

  <h2 id="after-coach">The Coach</h2>
  <p>It arrives at first light either way and it goes east on time, and whoever gets on it is a
  decision the table makes in front of each other. If nobody thought to look at who boarded, say so
  plainly, once, three sessions from now.</p>

  ''' + quote("A thing that can sit at your table can be beaten at your table. That is the only "
              "comfort in it and it is a real one.",
              "from a Keeper's ledger, quoted in the Keeper's Book") + '''

  <h2 id="after-ada">Who has a ticket</h2>
  <p>Ada Follett boards the eastbound at first light with her bag and her hat box, and she is
  calm, and she thanks whoever hands her up. Whether anything sits down beside her is the
  Keeper&rsquo;s to decide and the table&rsquo;s to notice.</p>

  <p>If they turned it down and put it down, she goes east alone and she is not grateful, and the
  last thing she says to the posse is that they have no idea what they took off the table. If one
  of them sat with her and let her talk about Peter, she says something else, and it should be
  short, and it should be the warmest line anybody says in this module.</p>

  ''' + keeper(
      " Ada is the module&rsquo;s argument and she should never be punished for it. A woman who "
      "watched her brother be happy for nine weeks and then had to bury him is not a monster and "
      "is not a fool. Play her all the way to the coach with her dignity intact, and let the "
      "table sit with the fact that the most reasonable person in the building would have said "
      "yes.") + '''

  <h2 id="after-next">What comes next</h2>
  <p><strong>Module III, <em>What the Water Answers</em></strong>, goes south and down, to Mission
  San Clavo and the shaft beneath it, for a posse at 5th level. Both earlier modules end within sight
  of that mission and neither one goes inside. That one does.</p>
</section>
'''

BASIN = basin("Saltlick Station", this_module="II")

BODY = (CONTENTS + WHAT + BASIN + TRUTH + TURN + HOOK + GROUND + ACT1 + ACT2 + ACT3
        + CAST + DEAD + COST + AFTER)

html = splice(H, BODY)
html = finish(
    html,
    curated=[
        ("Saltlick Station", "ground"),
        ("Dell, Amos", "truth-taken"),
        ("Mears, Cal", "truth-taken"),
        ("Gant, Ollie", "a1-house"),
        ("Follett, Mrs. Ada", "turn"),
        ("Follett, Peter, at Kearney", "turn-kearney"),
        ("The offer, in Act Three", "turn-offer"),
        ("Who told the others (the alibi)", "turn-tell"),
        ("Wu Cheng-hsi", "cast"),
        ("Orr, Deputy Sam", "cast"),
        ("Teague, Bill", "cast"),
        ("Tobe", "cast"),
        ("The tell (never in one room)", "truth-tell"),
        ("The ice house", "a2-ice"),
        ("The tack room", "a2-tack"),
        ("The bunk row", "a2-bunks"),
        ("The yard", "a3-yard"),
        ("The ash line", "a3-privy"),
        ("The mirror", "a3-count"),
        ("The Possessed", "dead-possessed"),
        ("The Skin-Walker", "dead-skin"),
        ("Safe-table rule (why the app is quiet)", "dead"),
        ("The Count at Saltlick (clock)", "truth-clock"),
        ("Scaling the night", "cost-scaling"),
        ("What the engine says", "cost"),
        ("The map", "ground"),
    ],
    subtitle="Every person, place and thing in this night, and the page it waits on.",
    intro="Scene numbers run 1&ndash;12 across the three acts and are keyed in the margin of each, "
          "and on the map in <a href=\"#ground\">The Ground</a>.",
    out=f"module-{SLUG}.html",
)
report(f"module-{SLUG}.html", html)
