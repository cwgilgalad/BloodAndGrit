#!/usr/bin/env python3
# Build "Blood & Grit — The Salt at Coffin Wells", module I, on the shared engine.
# Reads blood-and-grit.html (run build_player.py first), writes module-salt-at-coffin-wells.html.
#
# The adventure is the Keeper's Book Ch. IX, which gives it in two pages. This is the same night
# keyed and run: every scene placed, every person given a want, every fight played on the engine
# before a word was written about how hard it is. The numbers in "What the night costs" came out
# of GK/playtest and nowhere else.
from modules_common import (night_costs, shell, splice, finish, report, runhead, quote, readaloud,
                            keeper, clock, npc, statblock, found, contents)
from module_maps import map_html

VERSION = "1.3"
SLUG = "salt-at-coffin-wells"

H = shell(
    foot="The Salt at Coffin Wells",
    kicker="A First Reckoning, Keyed and Ready to Run",
    tiny_edition="Module I &middot; A one-night adventure for four souls at 1st level",
    tiny_blurb="Coffin Wells is dying of a fever that is not a fever. Four nights remain.",
    colophon="Blood &amp; Grit &middot; Module I &middot; The Salt at Coffin Wells &middot; "
             f"Version {VERSION} &middot; For the Keeper Alone",
    version=VERSION,
    cover_bg="#140d0b",
    cover_key="rgba(150,42,34,.92)",
    cover_foot_ink="#c88a72",
    cover_sub_ink="#cbb79b",
    epigraphs=[
        ('"A banker will tell you a debt is a number. It is not. It is a thing you have promised,\n'
         '    and out here the things you promise come to collect in person."\n'
         '    <span class="src">— Marshal Adelia Cruz, Calvary Crossing</span>'),
        ('"They buried Tom Pell on the Tuesday. He was home by the Friday, and he was hungry,\n'
         '    and I have not slept since."\n'
         '    <span class="src">— Hannah Pell, deposition taken at Coffin Wells</span>'),
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
      ("turn", "What the Town Has Already Decided"),
      ("hook", "The Hook, and Getting Them There"),
      ("ground", "The Ground"),
      ("act1", "Act One &mdash; The Ordinary West"),
      ("act2", "Act Two &mdash; The Wrong Note Answers"),
      ("act3", "Act Three &mdash; The Reckoning"),
      ("cast", "The Cast"),
      ("dead", "What Walks Here"),
      ("cost", "What the Night Costs"),
      ("after", "The Box, and What Comes After"),
      # No Index line here on purpose: build_index appends its own, anchored at #bookindex.
      # Listing one here anchors at #index, which nothing is, and measure_book catches it.
  ]) + '''
</section>
'''

# ============================================================ what this is
WHAT = '''
<section class="page" id="what">
  ''' + runhead("What This Is") + '''
  <h1 class="chapter">What This Is</h1>
  ''' + quote("Run it loose. The map is not the country and the key is not the night.",
              "a note pinned inside the cover of the first printing") + '''
  <p>One night at the table, for four souls at 1st level, in the country the Keeper&rsquo;s Book calls
  Perdition Basin. It wants three to four hours and it wants no preparation beyond reading it once.
  Every creature in it is printed here in full, so the Bestiary can stay on the shelf.</p>

  <p>It is built to do the thing a first session most often fails to do. It opens as an honest
  western (a town, a bar, a man buying a round), and it turns the note slowly enough
  that the players are the ones who notice. By the end of the second act they should be frayed and
  low on Nerve and beginning to understand that this is not the western they thought they rode into.</p>

  <h2 id="what-you-need">What You Need</h2>
  <p>The Player&rsquo;s Book for the souls, and this. The Keeper&rsquo;s Book is useful and not
  required; where this module leans on one of its rules it says which and where. If you are running
  GritKeeper at the table, the posse, the tracker and the clock below all go straight in.</p>

  <h2 id="what-teaches">What It Teaches, and in What Order</h2>
  <p>Three things, one per act, and never two at once.</p>
  <ul>
    <li><strong>Act One teaches the Dread Check.</strong> One check, DC 13, on a graveyard with the
    dirt wrong. Soft on purpose. A table&rsquo;s first Dread Check should be one they mostly pass,
    so they learn the shape of it before it costs them.</li>
    <li><strong>Act Two teaches that some things do not stop.</strong> Three Risen, in a house with
    the supper still on the table. This is the fight where somebody empties a gun into a thing that
    keeps coming, and it is the whole reason the module exists.</li>
    <li><strong>Act Three teaches that shooting is not the answer.</strong> It is not a harder fight.
    It is a different kind of problem, and the module is emphatic about this because the engine is:
    see <a href="#cost">What the Night Costs</a>.</li>
  </ul>

  ''' + keeper(
    "<p>Read the three acts and nothing else. The Cast and the creature entries are reference; "
    "look at them when the table looks at them. A Keeper who has memorised this module runs it worse "
    "than a Keeper who has read it once, because the first one is delivering a night and the second "
    "one is having one.</p>", "Before you run it") + '''
</section>
'''

# ============================================================ the truth
TRUTH = '''
<section class="page" id="truth">
  ''' + runhead("The Truth of It") + '''
  <h1 class="chapter">The Truth of It</h1>
  <p class="note">For the Keeper alone. Nothing on this page is known to anyone the posse will meet,
  except where it says so.</p>

  <p>Six weeks ago Josiah Vane, who holds the note on most of Coffin Wells and on none of it
  profitably, rode out to the old mission ground east of town with a shovel and a rumour. The rumour
  was silver: that the Spanish padres had put their plate in the ground when they abandoned
  San Clavo, and that the marked grave on the mission&rsquo;s east side was where. The grave was
  marked. It was marked because it was staked and salted, and the padres had written on the stone
  in a language Vane could not read and did not trouble to have read.</p>

  <p>He dug. He found no silver. He found a stake through a chest and he pulled it out, because a
  man who has dug four hours in the dark will pull on anything.</p>

  <p>What sat up made him an offer, and he took it. Blood for the town, fed quietly, a little at a
  time, out at the homesteads where nobody counts. In exchange he lives, and he is made rich, and he
  does not have to watch. He has kept the bargain for six weeks. He is past being able to stop and
  well past being able to confess, and he is drinking a great deal.</p>

  <h2 id="truth-fever">The Fever</h2>
  <p>There is no fever. The outlying homesteads are being fed on, and the ones who die of it do not
  stay dead; they get up two or three days after burial, hungry and slow and wearing the face
  their family knew. Coffin Wells has buried nine people in six weeks and dug up four of them again
  without saying so out loud.</p>

  <h2 id="truth-clock">The Clock</h2>
  <p>This is the pressure and it should be felt rather than announced. The thing at the mission grows
  stronger every night it feeds. Tonight is the fourth night of the fourth week and there are four
  nights left in which a stake will still hold it.</p>

  ''' + clock("The Fourth Night", 4,
              "Fill a segment each time the posse spends a scene on something other than the fever "
              "&mdash; a night in the saloon, a day riding to the county seat, an afternoon on Vane's "
              "books. At four, the thing has fed enough that stake and salt no longer bind it, and "
              "the module's ending changes: see <a href=\"#after\">The Box</a>.") + '''

  ''' + keeper(
    "<p>Do not let a player read this page and do not answer questions about it in the voice you use "
    "for rules. Everything here is discoverable in play, and every route to it is keyed in the acts. "
    "The one thing that is not discoverable is the count of nights; that is yours, and it is "
    "meant to be felt as the town getting worse rather than as a number going up.</p>") + '''
</section>
'''

# ============================================================ the turn
# The module's second truth, and the one it is actually about. Vane's bargain is the plot; the
# Wednesday reading is the horror, and it survives the plot being solved. Keyed here rather than
# folded into "The Truth of It" because a Keeper who reads only that page should still be able to
# run the module — this page changes what the ending means, and nothing about how the night runs.
TURN = '''
<section class="page" id="turn">
  ''' + runhead("The Reading") + '''
  <h1 class="chapter">What the Town Has Already Decided</h1>
  ''' + quote("We have always read the arrears. My father read them. It is how a small place keeps "
              "honest with itself.",
              "Deacon Loomis Pratt, Coffin Wells Methodist, asked why") + '''

  <p>Vane chose the first two. He rode out to the homesteads that owed him and were furthest from
  anyone, and he did it in a sweat, and he was sick after. He has not chosen anybody since. He has
  not had to.</p>

  <p>On the first Wednesday of the month the town eats together in the Methodist hall, and at the
  end of it, before the plates go round a second time, the ledger of accounts in arrears is read
  aloud. Eleven years they have done this. It began as an ordinary cruelty and a useful one: a
  man behind on his note hears his name in front of his neighbours and finds the money. Nobody
  has ever proposed it, voted it, or written it down as a rule. It is simply what happens on the
  first Wednesday.</p>

  <p>The names read in arrears in March are the names buried in April. The names read in April
  are the names buried in May. Nine people in six weeks, and every one of them a name the room
  had heard said out loud.</p>

  ''' + keeper(
      " Nobody in Coffin Wells has made this connection and several of them are one quiet hour "
      "from making it. That is the pressure on this page. The town is not keeping a secret — it "
      "has assembled a machine out of a hundred ordinary preferences and cannot see the shape of "
      "it, because no single part of it was ever a decision. Who the doctor rides to first. Whose "
      "water gets shared in a dry month. Which child gets the seat at the school. Vane feeds "
      "where the town has already stopped looking, and the town has been showing him where that "
      "is, once a month, in a clear voice, over supper.",
      "What this page is for") + '''

  <h2 id="turn-routes">Three Ways In</h2>
  <p>Every route is a document, because the discovery has to be something the players do rather
  than something a Keeper tells them.</p>

  <p><strong>The ledger and the register.</strong> Vane&rsquo;s arrears column and the church
  burial register are two lists in two buildings, and either one alone is a page of names. Laid
  side by side on a table they are the same list, in order, four to six weeks apart. This is the
  moment the module is built around and it wants no roll at all. Let whoever thought to fetch the
  second book be the one who sees it.</p>

  <p><strong>Hannah Pell.</strong> She buried Tom on the Tuesday and she has been to every supper
  since. She knows. She has known for two weeks and she has not been able to make the sentence
  come out, and if the posse gets her alone and does not push, it comes out sideways: she will
  ask them whether they were at the supper, and what they thought of it, and whether they noticed
  anything about the reading. <em>Lore (Occult)</em> is no use here. Sitting still is. There are
  two places she can be got alone and both are late: <a href="#a2-cellar">the cellar</a>, where
  she is still herself for now, and the midnight walk into town if the posse would not ride out
  to Pell&rsquo;s. If the module runs long enough to reach a first Wednesday she is at the
  supper, and she watches the posse listen to it.</p>

  <p><strong>Going to the supper.</strong> If the module runs across a first Wednesday, put the
  posse in the hall. Serve them. Let three people be kind to them. Then read the names, in the
  flat voice a deacon reads anything in, and move on to the announcements about the roof fund.
  Do not linger, do not cut to anyone&rsquo;s face, and do not let the scene mean anything. It
  will mean something later, which is worse.</p>

  ''' + readaloud(
      "Deacon Pratt sets down his coffee, stands, and opens the book without ceremony, the way a "
      "man opens a book he opens every month. He reads six names and the sums beside them. "
      "Nobody looks up. At the fourth name a woman two benches down stops chewing, and starts "
      "again. When he is done he says there is pie, and there is.") + '''

  <h2 id="turn-ending">What It Does to the Ending</h2>
  <p>Staking the thing at the mission ends the feeding. It does not end the arrangement, because
  the arrangement was never the thing&rsquo;s and was never Vane&rsquo;s either. Hang Vane and
  the reading happens in November. Burn the ledger and Pratt writes another, because the arrears
  still have to be read, because they have always been read.</p>

  <p>A posse that works this out has one real move, and it is not a fight: get up in that hall
  and say what the reading is. They will be heard politely. Roll nothing. Tell the player what
  the room does, which is that it goes quiet, and that a man at the back says they are strangers
  and do not know how it has always been done here, and that four people nod, and that two do
  not.</p>

  ''' + keeper(
      " Those two are the whole reward. Name them at the table — pick two of the people the posse "
      "has been kind to — and let the table see that something moved. A town does not turn in a "
      "night. Two people out of forty is what a hard truth buys, and in this game that is a "
      "victory worth the ride.") + '''
</section>
'''

# ============================================================ hook
HOOK = '''
<section class="page" id="hook">
  ''' + runhead("The Hook") + '''
  <h1 class="chapter">The Hook, and Getting Them There</h1>

  <p>Any reason that puts the posse in Coffin Wells at dusk will serve, and the module does not care
  which. Four that work:</p>
  <ul>
    <li><strong>Cattle.</strong> They are driving forty head to the railhead at Calvary Crossing and
    Coffin Wells is the last water before the dry stretch.</li>
    <li><strong>Paper.</strong> One of them is carrying a dodger with a name on it, and the name was
    last seen here.</li>
    <li><strong>Kin.</strong> A letter from somebody&rsquo;s sister stopped coming in April. She
    homesteaded eleven miles out, at a place called Pell&rsquo;s.</li>
    <li><strong>Thirst.</strong> They have been eleven days in the saddle and there is a town.</li>
  </ul>

  ''' + readaloud(
    "The sun is most of the way down when the road bends and gives you the town. Coffin Wells is "
    "one street, forty buildings, and a water tower with the paint gone off the north face. Every "
    "shutter you can see is closed. It is not late enough for that.") + '''

  <p>The gate is that the shutters are shut too early. Let them notice it, and let nobody explain it.
  A man crossing the street looks at them and keeps walking. The livery boy takes the horses and does
  not ask where they have come from, which is the only question anybody in a town this size ever asks.</p>

  <h2 id="hook-marshal">The Marshal Wants Them Gone</h2>
  <p>Marshal Adelia Cruz will find them inside the hour, and she is not hostile. She is tired and
  frightened and she has buried nine people, and she has worked out that strangers in a town with a
  fever either catch it or start a panic. She asks them to be gone by morning. She will not make them.</p>

  <p>She is the module&rsquo;s way in and she will become their ally in Act Two, so do not play her as
  an obstacle. Play her as a woman doing arithmetic she does not like the answer to.</p>

  ''' + npc("Marshal Adelia Cruz",
            "the burying to stop, and to not be the one who has to name why it is happening",
            "she will trade anything she knows for anyone who will ride out to the Pell place, "
            "because she has been three times and cannot make herself go a fourth",
            "Nine in six weeks. In a town of four hundred. You do that sum and then tell me it is a fever.") + '''
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
                 "the town, the Pell road and the mission ground, with the keyed scenes pinned "
                 "where they happen") + '''

  <h2 id="ground-shape">What the Shape of It Does</h2>
  <p>Four miles of the mission road, and everything in this module hangs off that distance. It is
  an hour on a tired horse in the dark. It is short enough that the posse can go out and come back
  in one night, and long enough that going out is a decision.</p>
  <ul>
    <li><strong>The town is west and the answer is east.</strong> Every scene in Act One faces the
    wrong way on purpose. The boot-hill is the first thing on the map that points the other
    direction.</li>
    <li><strong>The Pell place is off the road.</strong> South, down a track, out of sight of
    anywhere. That is why nobody has counted what has been happening to the homesteads.</li>
    <li><strong>The mission is on open ground and the graveyard is on its east side</strong>,
    which is the side the sun comes up on. Act Three ends at dawn, in the open, and the map is
    quietly telling the Keeper where to stand everyone.</li>
  </ul>

  ''' + keeper(
    "<p>Hand the map to the table in Act One. Nothing on it is a secret. A stranger riding "
    "into Coffin Wells can see the mission road and be told where it goes. The download beside it "
    "prints on one sheet.</p>") + '''
</section>
'''

# ============================================================ act one
ACT1 = '''
<section class="page" id="act1">
  ''' + runhead("Act One") + '''
  <h1 class="chapter">Act One &mdash; The Ordinary West</h1>
  <p class="note">Aim for forty minutes. One Dread Check, DC 13, and no monster.</p>

  <p>This act has one job: be a real town, so that the second act has something to ruin. Play the
  scenes below in whatever order the posse walks into them, and cut the act the moment they decide
  to ride out to Pell&rsquo;s.</p>

  <h2 id="a1-saloon">1. The Ipswich House</h2>
  <p>The saloon, and the only lit building on the street. Eleven people in it, all of them local, all
  of them talking about the fever and none of them using the word. The barkeep, Ozzie Vane, is
  Josiah&rsquo;s cousin and knows nothing.</p>
  <p>Somebody will mention the Pell place inside five minutes. Somebody else will change the subject.</p>

  <h2 id="a1-vane">2. Josiah Vane Buys a Round</h2>
  <p>He arrives twenty minutes in, and he is charming, and he is drunk in the careful way of a man
  who has been drunk every night for six weeks. He buys. He asks where they are headed and he is very
  pleased to hear it is anywhere else.</p>
  <p>If the posse mentions the fever he will agree that it is dreadful and steer hard. If they mention
  the mission ground he will go quiet for exactly one beat too long, and then be charming about it.
  <strong>That beat is the whole clue.</strong> Do not underline it. A player who catches it has
  earned the third act.</p>

  ''' + npc("Josiah Vane",
            "to not be found out, and under that, to be forgiven, which he has stopped believing is available",
            "he cannot stand to be alone after dark and will invent reasons to keep company",
            "The country takes people. That is all it has ever done. You would think we would have "
            "learned to stop being surprised.") + '''

  <h2 id="a1-boothill">3. The Boot-Hill</h2>
  <p>Up the rise north of town, and worth walking to if anyone thinks of it. Nine fresh graves. Four
  of them have been dug up <em>from the inside</em>: the dirt is heaped outward, the boards
  are pushed out rather than in, and one coffin lid is lying eleven feet from its hole.</p>

  ''' + readaloud(
    "The dirt on four of these is wrong. It is not sunk the way settled ground sinks. It is heaped "
    "out and away, in a ring, the way dirt lies when something has come up through it.") + '''

  <p><strong>Dread Check, DC 13, Will save.</strong> Tier I loss on a failure. This is the table&rsquo;s
  first, and it is soft deliberately. Call it out loud, name the save, and let a failure sting a
  little without costing anybody the night.</p>

  <h2 id="a1-dogs">4. Small Wrongnesses</h2>
  <p>Scatter two or three of these and no more. They are seasoning.</p>
  <ul>
    <li>No dog in town will go east of the water tower. They will not be led, and one will bite.</li>
    <li>Hannah Pell&rsquo;s sister-in-law says, once, quietly, that Tom Pell came home on the Friday
    after they buried him on the Tuesday. She will not say it twice and denies it if pressed.</li>
    <li>The general store has sold out of salt. All of it. Six weeks running.</li>
  </ul>

  ''' + keeper(
    "<p>End the act when they ride for Pell's, whether the Marshal asked them to or their own "
    "curiosity did. If they will not go, have the Marshal come and get them at midnight: Hannah Pell "
    "walked into town on foot, eleven miles, barefoot, and will not say what from.</p>") + '''
</section>
'''

# ============================================================ act two
ACT2 = '''
<section class="page" id="act2">
  ''' + runhead("Act Two") + '''
  <h1 class="chapter">Act Two &mdash; The Wrong Note Answers</h1>
  <p class="note">Aim for an hour. Two Dread Checks and the fight the module is built around.</p>

  <h2 id="a2-arrive">5. The Pell Place</h2>
  ''' + readaloud(
    "Eleven miles of nothing, and then a house with its door standing open and no light in it. The "
    "supper is on the table and has been there long enough to have stopped smelling of supper. Four "
    "chairs. Three of them pushed back.") + '''

  <p><strong>Dread Check, DC 16, Will save.</strong> Tier I loss. Nobody has met anything yet, which
  is the point: the house does this on its own.</p>

  <p>The house gives up three things to anyone who looks:</p>
  <ul>
    <li>The third chair was not pushed back. It was knocked over and set upright again, badly.</li>
    <li>There is a Bible on the sideboard with a page torn out of Leviticus. The torn page is under
    the door, folded, wedged as a shim. Somebody was trying to keep the door shut.</li>
    <li>The salt cellar is empty and the ring of salt on the floor around the youngest child&rsquo;s
    bed is unbroken. That child is alive, upstairs, and has not spoken in four days.</li>
  </ul>

  <h2 id="a2-fight">6. The Dead Getting Up</h2>
  <p>They come out of the barn, and one of them is Tom Pell, who was buried on the Tuesday and is
  wearing what he was buried in.</p>

  ''' + found("The Risen") + '''

  <p><strong>Three Risen.</strong> Full entry under <a href="#dead">What Walks Here</a>. Play them
  slow and play them relentless. They do not flinch, they do not take cover, and a shot that would
  put a man down puts one of them on the ground for a round and then it gets back up.</p>

  ''' + keeper(
    "<p><strong>This is the lesson fight and it must be won.</strong> The engine says a fresh posse "
    "clears it two times in twelve if they only shoot, and ten times in twelve if somebody "
    "thinks of fire, the barn door as a bottleneck, or the lamp oil on the shelf. Put the lamp oil "
    "where they can see it. If the fight turns badly, Marshal Cruz arrives on the third round: she "
    "followed them, and she has a shotgun and a bad conscience.</p>", "Running it") + '''

  <h2 id="a2-cellar">7. The Cellar</h2>
  <p>Hannah Pell is down there, bled thin and half-turned, and she is still herself for now. She knows
  what is happening to her. She asks them to see to it before she stops being able to ask.</p>

  <p><strong>Dread Check, DC 16, Will save.</strong> Tier II loss. This one is meant to cost.</p>

  ''' + readaloud(
    "She has been down here two days and she has thought it all the way through. &ldquo;There is a "
    "shotgun on the pegs by the stair,&rdquo; she says. &ldquo;I would do it myself but my hands "
    "have gone wrong and I do not trust them to be quick.&rdquo;") + '''

  ''' + keeper(
    "<p>There is no correct answer here and the module refuses to supply one. A mercy costs a Dread "
    "Check and nothing else. A hope (taking her to town, tying her, riding for a doctor) "
    "costs a segment off the clock and puts her in Act Three, where she will turn, and where what she "
    "does then is on them. Both are playable. Neither is punished. Whatever they choose should follow "
    "at least one of them into the next module.</p>") + '''

  <p>On Tom Pell&rsquo;s body: a scrap of worked silver, old, stamped with a cross and a word in
  Latin. It came off a reliquary. It points east, to the mission.</p>
</section>
'''

# ============================================================ act three
ACT3 = '''
<section class="page" id="act3">
  ''' + runhead("Act Three") + '''
  <h1 class="chapter">Act Three &mdash; The Reckoning</h1>
  <p class="note">Aim for an hour. One Dread Check, one problem, and a sunrise.</p>

  <h2 id="a3-mission">8. Mission San Clavo, the East Ground</h2>
  <p>Roofless, burned in 1811, and the graveyard on the east side is the only part anybody has kept
  the brush off. One grave is open. The stake is lying beside the hole with six weeks of weather on
  it, and there is a shovel with a banker&rsquo;s initials burned into the handle.</p>

  <p>The carvings on the standing wall of the nave are the answer, and they are in three panels,
  and they are the padres telling whoever comes next what they did and how.</p>
  <ul>
    <li><strong>First panel.</strong> A figure pinned to the ground with a spear through the chest.</li>
    <li><strong>Second panel.</strong> The same figure with its head off, and the head in a fire.</li>
    <li><strong>Third panel.</strong> Men pouring something from sacks in a ring around the grave.
    The sacks are the only thing in three panels the carver bothered to render in detail, and what
    is coming out of them is grains.</li>
  </ul>

  ''' + keeper(
    "<p><strong>Give them the panels early and let them work.</strong> Pin, take the head, burn it, "
    "salt the ground. That is the Bestiary's answer, printed under the entry, and it is the only "
    "thing that ends this. A posse that reads the wall in Act Three and solves it under fire has "
    "earned the best moment this module has. A posse that walks past the wall gets a very bad night.</p>",
    "The whole climax") + '''

  <h2 id="a3-vane">9. Vane, at the Grave</h2>
  <p>He is here. He came to feed it, or to beg it, or the posse dragged him, and it makes very little
  difference which. He is done pretending and he will tell them everything in about ninety seconds if
  anyone asks him a direct question, because he has been waiting six weeks for somebody to make him.</p>

  <p>He does not know the answer. He never read the wall. That is his whole character in one sentence
  and it is worth saying out loud at the table if it lands.</p>

  <h2 id="a3-thing">10. The Thing Out of the Grave</h2>
  <p><strong>Dread Check, DC 18, Will save.</strong> Tier III loss, and it is its regard that does it
  rather than its appearance; it looks at each of them in turn, the way a man looks at stock.</p>

  ''' + found("The Nightwalker") + '''

  <p>Full entry under <a href="#dead">What Walks Here</a>. Run the confrontation in the dark of the
  nave: the cold coming off it, the way it goes up a wall, the way it does not hurry.</p>

  ''' + keeper(
    "<p><strong>This cannot be shot down and the module means that literally.</strong> Twelve posses "
    "were run at this fight on the engine and not one of them won it with guns; see "
    "<a href=\"#cost\">What the Night Costs</a> for the count. Do not soften the fight to make it "
    "winnable. Make the wall readable instead, and let the answer be a thing they do rather than a "
    "roll they pass. Pin it: the stake is right there in the dirt. Take the head. Burn it. "
    "Salt the grave. Every one of those is an action anyone can take, and none of them is an attack "
    "roll against Defense 18.</p>", "Read this before you run it") + '''

  <h2 id="a3-dawn">11. The Sky Goes Gray</h2>
  <p>The escape valve, and it is always available. If the posse is pinned and dying, the east goes
  gray and the thing leaves, because it must. It costs them the ending and it does not cost them the
  night. A Keeper who uses this has not failed; the module is built with it in.</p>
</section>
'''

# ============================================================ cast
CAST = '''
<section class="page" id="cast">
  ''' + runhead("The Cast") + '''
  <h1 class="chapter">The Cast</h1>
  <p class="note">A want, a lever, and a line, per the Keeper&rsquo;s Book Ch. VIII.</p>

  ''' + npc("Ozzie Vane, barkeep",
            "his cousin to stop coming in and drinking like that where people can see",
            "he is loyal and he is not stupid, and those two are pulling opposite ways",
            "Josiah has had a bad year. That is all it is. A man is allowed a bad year.") + '''

  ''' + npc("Hannah Pell",
            "to be seen to before she stops being herself",
            "she is the only person in the module who will tell the posse the whole truth about the "
            "fever unprompted &mdash; and the one thing she cannot get out is what she noticed at "
            "the supper, which comes sideways if they sit with her and do not push "
            "(<a href=\"#turn-routes\">Three Ways In</a>)",
            "It was not a fever and you know it was not. Say it, so I know somebody said it.") + '''

  ''' + npc("Elder Bram Tuttle, who keeps the store",
            "to be paid what he is owed and to be left out of it",
            "he has sold six weeks of salt to somebody and he knows exactly who, and he will say for money",
            "Salt is salt. A man buys what he buys. I keep a store, not a diary.") + '''

  ''' + npc("Deacon Loomis Pratt, Coffin Wells Methodist",
            "the roof fund closed out and the suppers to go on the way they always have",
            "he has read the arrears aloud on the first Wednesday for eleven years and nobody has "
            "ever asked him why, and the question lands on him harder than an accusation would",
            "Six names this month. It was eleven when I started. That is a town getting better, "
            "if you look at it right.") + '''

  ''' + npc("The Pell child, nine, unnamed on purpose",
            "nothing that can be put into words yet",
            "she has not spoken in four days and she drew the thing on the wall of the barn in charcoal, "
            "twice, from memory, and it is a good likeness",
            "&mdash;") + '''

  ''' + keeper(
    "<p>Name the child at the table, in play, and let a player do it if one offers. A person the "
    "posse names is a person the posse comes back for, and this module is the first of three.</p>") + '''
</section>
'''

# ============================================================ bestiary
DEAD = '''
<section class="page" id="dead">
  ''' + runhead("What Walks Here") + '''
  <h1 class="chapter">What Walks Here</h1>
  <p class="note">Printed in full so the Bestiary can stay on the shelf. These entries are generated
  from the same file the app reads, so they cannot drift from the book they came out of.</p>

  <h2 id="dead-risen">The Risen</h2>
  ''' + statblock("The Risen",
                  "Three of them at the Pell place, and one is Tom Pell. Play them slow. The horror "
                  "of a Risen is not that it is fast.") + '''

  <h2 id="dead-night">The Nightwalker</h2>
  ''' + statblock("The Nightwalker",
                  "One, at the opened grave. Read its Putting It Down line twice before you run "
                  "Act Three; it is the act's solution and it is printed right there.") + '''

  ''' + keeper(
    "<p><strong>On the safe-table rule.</strong> A Nightwalker is Tier III and a 1st-level posse is "
    "Tier 1, which is two Tiers over, so by the Keeper's Book Ch. IV this horror is sign and "
    "spoor rather than a fight, and GritKeeper will offer to put it on the trail instead of the field "
    "if you build it there. That is correct and this module does not override it. Act Three is not a "
    "fight the posse wins by fighting. It is a thing in the room with them while they do the four "
    "things the wall told them to do.</p>", "Why the app will argue with you") + '''
</section>
'''

# ============================================================ playtest numbers
COST = '''
<section class="page" id="cost">
  ''' + runhead("What the Night Costs") + '''
  <h1 class="chapter">What the Night Costs</h1>

  <p>Every number on this page came out of the game&rsquo;s own engine. Twelve posses (a Gunhand, a
  Preacher, a Mountain Man and a Sawbones, built by the generator, at 1st level)
  were run through all three acts on the same rules library the app runs on, with the Bestiary&rsquo;s
  numbers for every foe and the book&rsquo;s dice for every roll. The runs are seeded and reproduce.</p>

  <p>They were run twice over: once <em>cold</em>, with no recovery between acts and no Grit spent
  and no Sign or Miracle worked, and once <em>tended</em>, with the posse back to half Blood between
  acts. The point of the second was to find out whether the night is an attrition problem.</p>

''' + night_costs("The Salt at Coffin Wells",
      ["The dead getting up (Act Two)", "The Nightwalker (Act Three)"]) + '''

  <p>Read the second row and then read it again. Twelve posses, cold and tended both, and the
  Nightwalker was never once put down by shooting it. Giving the posse back half its Blood between
  every act changed that count by nothing, which is how you know it is not an attrition problem.
  Twelve Strikes a round at rising MAP land about one time in eight against Defense 18, and the thing
  hits back three times in four.</p>

  ''' + keeper(
    "<p><strong>So the module says it plainly: Act Three is not a fight.</strong> It is a room with "
    "a monster in it and four things written on the wall. Pin it, take the head, burn it, salt the "
    "grave. A posse doing those four things under fire is a posse having the best twenty minutes "
    "this module has to offer. A posse trading Strikes with it is a posse the numbers above are "
    "about.</p>") + '''

  <h2 id="cost-act2">On the Act Two fight</h2>
  <p>Two clears in twelve looks alarming and is not. That row is a posse that only shoots, standing
  in the open, in a yard, against three things that do not stop. The same fight with the barn door
  as a bottleneck, or with the lamp oil used, or with the Marshal arriving on round three, is a fight
  a fresh posse wins comfortably, and every one of those is keyed into <a href="#a2-fight">scene 6</a>
  for exactly this reason.</p>

  <p>What the number is really telling you is the shape of the lesson: <strong>this game does not
  reward standing still and firing.</strong> Act Two is where a table learns that, cheaply, against
  Tier I. Act Three is where it matters.</p>

  <h2 id="cost-scaling">Scaling the Night</h2>
  <ul>
    <li><strong>A bigger or bolder posse.</strong> Add a fourth Risen in Act Two. Give Vane two
    hired guns at the mission. Let the Nightwalker open Act Three from above rather than from the
    grave.</li>
    <li><strong>A smaller or greener posse.</strong> Two Risen. Have the wall panels be plainer:
    a carved word, in English, put there by a later hand. Run the Nightwalker fed and slow: Defense
    16 and no regard, if the posse reaches the mission on the first night.</li>
    <li><strong>If the dice turn cruel.</strong> The dawn is always one scene away. Use it.</li>
  </ul>
</section>
'''

# ============================================================ after
AFTER = '''
<section class="page" id="after">
  ''' + runhead("The Box") + '''
  <h1 class="chapter">The Box, and What Comes After</h1>

  <p>However it ends, give it weight before anybody rolls anything else.</p>

  <h2 id="after-won">If they put it down</h2>
  <p>Coffin Wells lives. Nine people are still dead and four of them had to be put down twice, and
  the posse has a legend and a banker to hang or to pity. Let the town be grateful in the awkward way
  a town is grateful to strangers who saw it at its worst.</p>

  <h2 id="after-lost">If it gets away</h2>
  <p>Or if the fourth segment filled and the stake no longer held. Do not run this as a failure. Run
  it as a thread: a town half-saved, a survivor who saw too much, and a debt the dark considers
  unpaid. It has a name for each of them now, which is worse than being hunted.</p>

  <h2 id="after-wednesday">The first Wednesday of the month</h2>
  <p>It comes whatever they did. The hall is warm, the coffee is bad, and there are eleven years
  of Wednesdays behind this one. Deacon Pratt stands up with the book because that is what he does
  with it, the room settles because the room always settles, and he reads the arrears.</p>

  <p>Read two names at your table. Make one of them somebody the posse liked. Then say that there
  is pie, and there is, and go round and ask each player what their soul does with their hands.</p>

  ''' + keeper(
      " End the session there. Attach no roll to it and let nobody tell them whether it worked. "
      "Half a year on, if the campaign rides back through Coffin Wells, count the graves: if the "
      "posse stood up in that hall there are two fewer than there would have been, no one in town "
      "connects that with them, and no one ever will.") + '''

  <h2 id="after-hannah">Whatever happened in the cellar</h2>
  <p>It follows one of them. Pick the soul who was closest to the decision and let it turn up in a
  dream, once, three sessions from now, with no mechanical effect at all. This module is the first of
  three and that is the thread the other two pull on.</p>

  ''' + quote("A first night is a promise. Keep it honest and keep it frightening, and they will "
              "follow you into a hundred more.",
              "from a Keeper's ledger, quoted in the Keeper's Book") + '''

  <h2 id="after-next">What comes next</h2>
  <p><strong>Module II, <em>A Face Not His Own</em></strong>, is a relay station forty miles north
  and about a year later, for a posse at 3rd level. It is the same country and it does not require
  this one.</p>
</section>
'''

BODY = (CONTENTS + WHAT + TRUTH + TURN + HOOK + GROUND + ACT1 + ACT2 + ACT3
        + CAST + DEAD + COST + AFTER)

html = splice(H, BODY)
html = finish(
    html,
    curated=[
        ("Coffin Wells", "hook"),
        ("Vane, Josiah", "a1-vane"),
        ("Cruz, Marshal Adelia", "hook-marshal"),
        ("Pratt, Deacon Loomis", "cast"),
        ("Pell, Hannah", "a2-cellar"),
        ("Pell, Tom", "a2-fight"),
        ("Mission San Clavo", "a3-mission"),
        ("The boot-hill", "a1-boothill"),
        ("The cellar", "a2-cellar"),
        ("The carved panels", "a3-mission"),
        ("The Risen", "dead-risen"),
        ("The Nightwalker", "dead-night"),
        ("Dread Checks in this module", "cost"),
        ("Safe-table rule (why the app argues)", "dead"),
        ("Scaling the night", "cost-scaling"),
        ("The Fourth Night (clock)", "truth-clock"),
        ("The first Wednesday supper", "turn"),
        ("The reading of the arrears", "turn"),
        ("The ledger and the burial register", "turn-routes"),
        ("Standing up in the hall", "turn-ending"),
        ("Dawn, as an escape valve", "a3-dawn"),
        ("What the engine says", "cost"),
        ("The map", "ground"),
    ],
    subtitle="Every person, place and thing in this night, and the page it waits on.",
    intro="Scene numbers run 1&ndash;11 across the three acts and are keyed in the margin of each, "
          "and on the map in <a href=\"#ground\">The Ground</a>.",
    out=f"module-{SLUG}.html",
)
report("module-salt-at-coffin-wells.html", html)
