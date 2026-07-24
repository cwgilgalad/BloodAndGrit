#!/usr/bin/env python3
# Assemble the Keeper's Book body and splice it into the Player-shell build.
# Reads blood-and-grit.html (run build_player.py first), writes keeper-handbook.html.
import re

H = open("blood-and-grit.html", encoding="utf-8").read()

# ---- whitespace optimization: make .statblock splittable across pages ----
from pag_patch import patch_paginator as _patch_paginator
H = _patch_paginator(H)

# ---- stat-block + keeper CSS, and cover/meta retext ----
_css = """
  /* ---- Keeper's Book additions ---- */
  .statblock{ background:#efe6cf; border:1px solid var(--gold-d); border-left:4px solid var(--blood); padding:9px 13px 11px; margin:1.1em 0; }
  .statblock .sb-head{ display:flex; justify-content:space-between; align-items:baseline; gap:10px; border-bottom:1.5px solid var(--gold-d); padding-bottom:4px; margin-bottom:6px; }
  .statblock .sb-name{ font-family:var(--display); font-weight:700; color:var(--blood-d); font-size:17px; letter-spacing:.01em; }
  .statblock .sb-tier{ font-style:italic; color:var(--ink-soft); font-size:12.5px; white-space:nowrap; }
  .statblock p{ margin:.3em 0; font-size:14px; line-height:1.34; }
  .statblock .sb-stat strong, .statblock p strong{ color:var(--shade); }
  .statblock hr.sb-rule{ border:none; border-top:1px solid var(--gold-d); opacity:.55; margin:.5em 0; }
  .statblock .sb-tag{ font-variant:small-caps; letter-spacing:.05em; color:var(--blood-d); font-weight:700; font-size:12.5px; }
  .statblock .sb-cont{ font-style:italic; font-weight:400; color:var(--ink-soft); font-size:12px; letter-spacing:0; }
  .keeper-note{ background:#ece2c8; border-left:3px solid var(--gold-d); padding:8px 12px; margin:1em 0; font-size:14.5px; }
  .keeper-note .kn-tag{ font-variant:small-caps; letter-spacing:.06em; color:var(--blood-d); font-weight:700; display:block; font-size:12.5px; margin-bottom:2px; }
  /* Keeper's Book cover — set a shade apart from the Player's Book: colder, darker ground,
     a thin oxblood keyline inside the gilt border, and an oxblood title label. */
  .title-page{ background:#150f09; box-shadow:0 0 0 4px #150f09 inset, 0 0 0 5px rgba(150,32,32,.85) inset, 0 14px 40px rgba(0,0,0,.66); }
  .title-page .t-foot{ color:#c1604a; }
  .title-page .t-sub{ color:#c4b083; }
</style>"""
if ".statblock{" not in H:
    H = H.replace("</style>", _css, 1)
_meta = [
 ("<!-- Blood & Grit — The Player's Book · Version 2.22 -->", "<!-- Blood & Grit — The Keeper's Book · Version 2.9 -->"),
 ("<title>Blood &amp; Grit — The Player's Book (Revised &amp; Expanded · v2.22)</title>", "<title>Blood &amp; Grit — The Keeper's Book (v2.9)</title>"),
 ('<div class="kicker">Being a Field Manual for the Living</div>', '<div class="kicker">For the Eyes of the Keeper Alone</div>'),
 ('<div class="t-foot">The Player\'s Book</div>', '<div class="t-foot">The Keeper\'s Book</div>'),
 ('<div class="t-tiny">Revised &amp; Expanded · Compiled in the Territories · Edition of 1885 · Version 2.22</div>', '<div class="t-tiny">Compiled in the Territories · Edition of 1885 · Version 2.9</div>'),
 ('<div class="t-tiny">Most rules herein are adapted from Pathfinder Second Edition, with some unique rules &amp; systems of its own</div>', '<div class="t-tiny">Companion to the Player\'s Book · the secrets, the monsters, and the running of the dark</div>'),
 ('<p class="note" style="text-align:center; margin:0;">Blood &amp; Grit · The Player\'s Book · Version 2.22 · First Complete Edition</p>', '<p class="note" style="text-align:center; margin:0;">Blood &amp; Grit · The Keeper\'s Book · Version 2.9 · For the Keeper Alone</p>'),
]
for a,b in _meta:
    if a in H: H = H.replace(a,b,1)

# replace the two carried-over Player's epigraph quotes with Keeper-specific ones
import re as _re
def _set_epigraph(s, mt, text, srcline):
    pat = _re.compile(r'<div class="quote" style="margin-top:'+mt+r';">.*?</div>', _re.DOTALL)
    new = ('<div class="quote" style="margin-top:'+mt+';">\n    '+text+
           '\n    <span class="src">\u2014 '+srcline+'</span>\n  </div>')
    s2,n = pat.subn(new, s, count=1); assert n==1, "epi "+mt
    return s2
H = _set_epigraph(H, "120px",
    '"Someone at every fire must keep the watch while the rest dream of grass and gold.\n'
    '    I have kept it so long I have forgotten how to look at a sunset and see only the sun."',
    "attributed to a keeper of the old tales, the name worn from the page")
H = _set_epigraph(H, "90px",
    '"The trick was never the frightening &mdash; any fool with a candle can frighten. The trick is the\n'
    '    fairness: letting them see, the breath before the dark takes them, the one turn they should not have taken."',
    "from the margins of a Keeper's ledger")

def img(key):
    return open(f"/tmp/{key}.uri").read().strip()

def plate(key, alt, cap):
    # Plates removed at the author's request — new illustrations to be added later.
    return ""

def runhead(short):
    return f'<div class="runhead"><span class="l">Blood &amp; Grit</span><span>{short}</span></div>'

def quote(text, src):
    return f'<div class="quote">{text}<span class="src">\u2014 {src}</span></div>'

# ---------------------------------------------------------------- CONTENTS
CONTENTS = f"""<!-- ===================== KEEPER CONTENTS ===================== -->
<section class="page" id="contents">
  {runhead('Contents')}
  <h1 class="chapter">Contents</h1>
  <p class="chapter-sub">The order of the dark, and where to find it.</p>
  <div class="divider"></div>
  <p class="note">This is the Keeper's Book. It holds what the Player's Book withholds &mdash; the
  reckoning behind the rules of fear, the things that wait in the dark, and the craft of setting them
  loose without breaking faith with the souls at your table. If you mean to play and not to run, close it.</p>
  <ul class="toc">
    <li><a href="#chair">I. The Keeper's Chair</a><span class="pg">4</span></li>
    <li><a href="#running">II. Running the Game</a><span class="pg">9</span></li>
    <li><a href="#fear">III. Fear, Nerve &amp; the Mark</a><span class="pg">15</span></li>
    <li><a href="#odds">IV. The Long Odds &mdash; Building the Fight</a><span class="pg">22</span></li>
    <li><a href="#bestiary">V. A Bestiary of the Frontier</a><span class="pg">31</span></li>
    <li><a href="#hazards">VI. Cursed Ground, Hazards &amp; Bad Medicine</a><span class="pg">33</span></li>
    <li><a href="#rewards">VII. Rewards &amp; Reckonings</a><span class="pg">39</span></li>
    <li><a href="#cast">VIII. The Cast</a><span class="pg">44</span></li>
    <li><a href="#firstreckoning">IX. A First Reckoning <span class="sub">(starter adventure)</span></a><span class="pg">48</span></li>
    <li><a href="#secondreckoning">X. A Second Reckoning <span class="sub">(starter adventure)</span></a><span class="pg">52</span></li>
    <li><a href="#keepersyear">XI. The Keeper's Year <span class="sub">(running a campaign)</span></a><span class="pg">57</span></li>
    <li><a href="#pocket">XII. The Country in Your Pocket <span class="sub">(rollable tables)</span></a><span class="pg">62</span></li>
    <li><a href="#basin">XIII. Perdition Basin <span class="sub">(a country ready to ride)</span></a><span class="pg">71</span></li>
    <li><a href="#city">XIV. The Lamplit City <span class="sub">(running the game in town)</span></a><span class="pg">78</span></li>
    <li><a href="#screen">Appendix: The Keeper's Screen</a><span class="pg">78</span></li>
  </ul>
</section>
"""

# ---------------------------------------------------------------- I. THE KEEPER'S CHAIR
CH1 = f"""<!-- I -->
<section class="page" id="chair">
  {runhead('I. The Keeper&rsquo;s Chair')}
  <h1 class="chapter">I. The Keeper's Chair</h1>
  <p class="chapter-sub">What you are for, and the bargain you make with the table.</p>
  <div class="divider"></div>
  <div class="narr">A word before the work, from one host to another. Your players sat down for a western
  &mdash; give them one. Let the first night be cattle prices and bad coffee and a gun that means exactly
  what a gun means. The dark in this game earns nothing by arriving early; it earns everything by
  arriving <em>eventually</em>, through a door the players propped open themselves on some ordinary
  afternoon. You are not the monster's advocate. You are the ordinary evening the monster interrupts
  &mdash; and the longer that evening stays believably ordinary, the further down it can afterward go.</div>
  <p class="dropcap lead">Every other soul at the table plays one person trying to last another day. You play
  everything else &mdash; the town and the trail, the weather and the wolves, the kindly stranger and the thing
  wearing his face. More than that, you play the <strong>country itself</strong>, which in this game is old, and
  patient, and not on anyone's side. The players brought characters. You bring the dark they walked into.</p>

  <h2>What This Book Is</h2>
  <p>The Player's Book makes a character and keeps them breathing &mdash; the dice, the callings, the guns, the rules
  of fear from the inside. This book is the other half: the DCs you set, the monsters you run, the way dread is
  paced so it lands, and the judgment calls the rules leave to you on purpose. Read the Player's Book first; this
  one assumes it. Where the two ever disagree, the Keeper's word settles it at the table and a note in the margin
  settles it after.</p>

  <h2>The Promise</h2>
  <p>Blood &amp; Grit is a western that curdles. It opens in a world the players think they understand &mdash; dust,
  debt, a hard ride, a harder town &mdash; and somewhere in the first night the ground gives a little under their feet.
  Your promise to the table is twofold, and you owe both halves equally:</p>
  <ul>
    <li><strong>Fairness.</strong> The dice fall where they fall. Death is on the table, but it is earned by the
    fiction, never sprung from spite. The players should always be able to point at the moment it went wrong and
    say <em>we should have known</em>.</li>
    <li><strong>Dread.</strong> You promised them horror, not a card game with a skull on the box. If a session
    ends and no one's skin crawled, the machinery worked and the game didn't. Dread is the deliverable.</li>
  </ul>

  <h2>Tone: The Slow Burn</h2>
  <p>The single most common way a Blood &amp; Grit session fails is the Keeper showing the monster in the first ten
  minutes. Resist it. The country curdles in three movements, and you should feel each one before you move to the next:</p>
  <ul>
    <li><strong>The Ordinary West.</strong> Let it be a real place first. A name, a face, a debt, a job. Let the
    players relax into the genre &mdash; gunslingers and ghost towns &mdash; so that the floor has somewhere to drop.</li>
    <li><strong>The Wrong Note.</strong> One detail that doesn't sit right. The dog won't go in the barn. The new
    grave is open and clean. The preacher's shadow falls the wrong way. Don't explain it. Let it itch.</li>
    <li><strong>The Reckoning.</strong> The dark stops hinting. Now the guns come out, the Nerve bleeds, and the
    players learn what the wrong note was always pointing at.</li>
  </ul>
  <div class="keeper-note"><span class="kn-tag">Keeper's eye</span>The horror is strongest in the gap between the
  wrong note and the reckoning. Stretch that gap. A monster seen is a problem to be shot; a monster <em>suspected</em>
  is a dread that follows the players home.</div>

  <h2>Session Zero</h2>
  <div class="box">
    <h4>Before the First Die Is Cast</h4>
    <p>Spend a half-hour, before anyone rolls, settling these:</p>
    <ul>
      <li><strong>The pitch.</strong> "A gritty western where the frontier is haunted by something older than the
      country, and your characters are ordinary people who will not stay ordinary." Make sure everyone wants that.</li>
      <li><strong>Lines &amp; veils.</strong> Name what won't go on the page (a <em>line</em>) and what happens off it
      (a <em>veil</em>). This is a horror game; harm to children, certain real cruelties, and anything a player names
      are off the table, no questions asked. The dark has range enough without them.</li>
      <li><strong>Ties.</strong> Have each player give one reason their character is here and one person, place, or
      debt they'd ride into hell for. That is the rope you will pull on all campaign long.</li>
      <li><strong>The town.</strong> Name the starting town together. Let each player add one thing to it. A place
      they helped build is a place that hurts to lose.</li>
    </ul>
  </div>

  <h2>Pacing the Table</h2>
  <p>Keep scenes moving and the spotlight turning &mdash; everyone should act before anyone acts twice. Cut hard to the
  next thing that matters; "you ride three days and reach the Wells" is a fine sentence. Save your slow, lingering
  description for the wrong note and the reckoning, where dread lives. And learn to sit in silence after something
  awful: do not rush to fill it. The quiet is doing your work for you.</p>

  <h2>Reading Your Table</h2>
  <p>The rules are the same for every group; the table is not. After a few sessions you will be running not one game
  but five or six people who each came for something a little different, and the craft of keeping is partly the craft
  of seeing what each of them is after and feeding it without starving the rest. A few types you will meet, and what
  to do with them:</p>
  <ul>
    <li><strong>The one who came to be scared.</strong> They lean in at the wrong note, they want the dread. Give them
    the secret Notice rolls, the slow reveals, the thing glimpsed and not explained. They are your best instrument;
    play the horror partly to them and the rest of the table catches it.</li>
    <li><strong>The one who came to shoot.</strong> Nothing wrong with it &mdash; this is a western. Give them the
    gunfight, the standoff, the moment their iron is the only answer. But teach them, gently and early, that some
    nights the gun makes it worse, so the lesson lands before it costs the party someone.</li>
    <li><strong>The one who came to solve.</strong> They want the mystery, the clue, the why. Build them a real puzzle
    with a real answer &mdash; the cursed object's origin, the cult's weak link, the tell that names the monster &mdash;
    and never make the solution a die roll they can flub into a dead end.</li>
    <li><strong>The quiet one.</strong> Not every player drives the scene, and that is fine, but make sure the spotlight
    finds them on their terms. Ask them directly what their character does, hand them a private clue, give them the
    NPC who trusts only them. A quiet player is often the most invested; they are just waiting to be invited.</li>
    <li><strong>The one pulling away from the table.</strong> The lone wolf, the murder-hobo, the player whose character
    keeps wandering off alone or turning on the others. Usually this is boredom or a want unmet, not malice. Talk to
    them away from the table, find the want, and write it into the story &mdash; a tie, a grudge, a goal that needs the
    others. A character with a reason to ride with the party rarely rides away from it.</li>
  </ul>
  <div class="keeper-note"><span class="kn-tag">The check-in</span>Once an arc or so, ask the table plainly: are you
  having the kind of fun you came for? Too scary, not scary enough, too much fighting, not enough? It costs five
  minutes and breaks no immersion that a season of quiet resentment wouldn't break worse. The best Keepers adjust;
  only the proud ones guess.</div>
</section>
"""

# ---------------------------------------------------------------- II. RUNNING THE GAME
CH2 = f"""<!-- II -->
<section class="page" id="running">
  {runhead('II. Running the Game')}
  <h1 class="chapter">II. Running the Game</h1>
  <p class="chapter-sub">The loop, the numbers, and when to reach for the dice.</p>
  <div class="divider"></div>
  <p class="dropcap lead">Underneath the dread, the machine is simple and you should keep it that way. You describe a
  situation; a player says what their character does; if the outcome is uncertain and failure is interesting, the
  dice settle it; you narrate what changes; you describe the new situation. Round and round until the story ends or
  they do. Everything else in this chapter is in service of that loop.</p>

  <h2>When to Call for a Roll</h2>
  <p>Do not roll for everything. A roll is for moments that are <strong>both uncertain and consequential</strong>.
  If success is assured, say yes. If failure is dull ("you fail to open the unlocked door"), say yes. Reach for the
  dice only when both a win and a loss would push the story somewhere worth going. Each roll you call should be able
  to answer the question: <em>what new trouble does failure buy?</em></p>

  <h2>Setting the DC</h2>
  <p>When you do call for a roll, you set the number to beat. Hold to one ladder so the table learns its rhythm:</p>
  <table>
    <thead><tr><th>Difficulty</th><th>DC</th><th>What it feels like</th></tr></thead>
    <tbody>
      <tr><td>Trivial</td><td>10</td><td>A trained hand barely thinks about it</td></tr>
      <tr><td>Easy</td><td>13</td><td>Routine, but the green can still flub it</td></tr>
      <tr><td>Average</td><td>15</td><td>A fair test of a capable person</td></tr>
      <tr><td>Hard</td><td>18</td><td>Sweat on the brow; the day's real obstacle</td></tr>
      <tr><td>Very Hard</td><td>20</td><td>Few try it; fewer manage</td></tr>
      <tr><td>Punishing</td><td>25</td><td>The stuff of stories told after</td></tr>
      <tr><td>Beyond</td><td>30</td><td>The country says no, but you may ask</td></tr>
    </tbody>
  </table>
  <p>To beat a living thing &mdash; a shot, a swing, a lie told to its face &mdash; the DC is that creature's
  <strong>Defense</strong> or the relevant save it gets to resist with, not a number off this table. Use the ladder
  for the world; use Defense and saves for the things in it.</p>

  <h2>The Four Degrees</h2>
  <p>Every roll has four outcomes, and you should narrate all four, never just hit-or-miss. Beat the DC by
  <strong>10 or more</strong> (or roll a natural 20 that already succeeds) for a <strong>critical success</strong>;
  miss it by <strong>10 or more</strong> (or roll a natural 1 that already fails) for a <strong>critical failure</strong>.
  A natural 20 bumps the result one step better, a natural 1 one step worse. Spend critical successes on grace &mdash;
  a free truth, a saved bullet, an enemy's nerve broken &mdash; and critical failures on the kind of trouble the players
  will be telling stories about. That is where the texture of the game lives.</p>

  <h2>Rolling in the Dark</h2>
  <p>Some checks the players must not see the result of, or the result tells them what they failed to learn. Roll
  these yourself, behind the screen: <strong>Notice</strong> against a hidden thing, <strong>Lore (Occult)</strong>
  to read a sign, anything where a known failure would itself be a clue. On a failure they simply learn nothing,
  and never know whether there was nothing to learn or they merely missed it. Doubt is a tool. Use it.</p>

  <h2>Success at a Cost</h2>
  <p>When a player just misses on something the story wants to keep moving, offer the deal instead of the dead end:
  <em>you can have it, but&hellip;</em> &mdash; the door opens but the noise carries; the wound is bound but the laudanum's
  gone; you cross the river but the powder's wet. "Failing forward" keeps the night advancing toward its reckoning
  instead of stalling at a locked door.</p>

  <h2>The Trail &amp; the Long Quiet</h2>
  <p>Travel is not dead time; it is your best dread-builder. The long ride between the town and the wrong place is
  where you plant the wrong note &mdash; the cold that comes too early, the birds gone silent, the homesteads
  emptier the further out they go. Provisioning matters here (see the Player's Book, Chapter X): a party that rode
  out short on salt, lamp-oil, and shells is a party you can squeeze. Don't roll for every mile; roll for the mile
  that costs something.</p>

  <h2>The Dark Has a Plan</h2>
  <div class="keeper-note"><span class="kn-tag">The clock</span>Give the dark a goal and a count of how long until it
  gets there &mdash; a clock of four to six steps. The cult needs three more nights to finish the rite; the taint spreads
  one homestead a week; the thing under the mine wakes by the new moon. Tick it forward whenever the players dawdle,
  fail, or look away. A ticking clock turns a haunted set-piece into a living threat the players are racing, and it
  tells you, with no agonizing, what happens when they don't show up.</div>

  <h2>Running a Mystery Without Stalling It</h2>
  <p>Most Blood &amp; Grit nights are mysteries at heart &mdash; what's killing the stock, who's wearing the wrong face,
  why won't the dead lie down &mdash; and the most common way a session dies is a mystery that locks. The players miss
  the roll, find the empty room, run out of leads, and the night grinds to a halt while everyone stares at the table.
  A few habits keep the dark moving toward them:</p>
  <ul>
    <li><strong>Never gate the core clue behind a roll.</strong> The thing the players <em>must</em> know to proceed is
    not a Notice check they can fail &mdash; it is simply there to be found by anyone who looks. Roll for the bonus, the
    edge, the thing that makes it easier; never for the thread the whole night hangs on. The rule of three: put the key
    clue in at least three places, so missing one or two doesn't end the game.</li>
    <li><strong>Clues point forward, not just down.</strong> Every clue should suggest a next place to go or a next
    person to press, and give the party somewhere they haven't yet been. A bloodless steer is a fact; a bloodless steer with the
    tracks leading to the old Vane place is a direction.</li>
    <li><strong>When they stall, have the dark act.</strong> If the players run out of leads, don't wait &mdash; tick
    the clock. Another homestead falls, another body turns up, the thing grows bolder and leaves a fresh trail. The
    investigation that dries up on the players' end gets watered from the monster's. A stalled mystery is just a
    monster you haven't let move yet.</li>
    <li><strong>Let them be wrong productively.</strong> A wrong theory, chased hard, should still cost or reveal
    something &mdash; the innocent man they suspected has his own secret, the dead end has a body in it. Reward the
    digging even when it digs in the wrong place.</li>
  </ul>
  <div class="keeper-note"><span class="kn-tag">The held card</span>Keep one clue in your pocket with no fixed home.
  When the night stalls and nothing you planned has landed, spend it &mdash; the survivor remembers one more thing, the
  letter has a second page, the drifter finally talks. A floating clue you can drop anywhere is the surest cure for a
  table gone quiet, and the players never know it wasn't always there.</div>

  <h2>The Talking Fight</h2>
  <p>Half the dangerous moments in this game never draw a gun &mdash; the standoff talked down, the cultist questioned,
  the bargain weighed, the frightened witness coaxed into the truth. Run these with the same care you give a gunfight.
  A social conflict is not one roll; it is a scene with stakes, position, and degrees:</p>
  <ul>
    <li><strong>Set the stakes and the read first.</strong> What does the NPC want, what would move them, and what
    will they never do? A man bargaining for his life talks differently than a fanatic who's made his peace with
    dying. Know the answer before the players start working on him.</li>
    <li><strong>Roll once it's uncertain, not to open.</strong> Let the players talk &mdash; the actual words, the
    angle, the leverage they bring &mdash; and call for Persuade, Deceive, or Intimidate only when the outcome
    genuinely hangs and they've made their case. A good argument lowers the DC or grants the roll outright; a clumsy
    one raises it or forfeits it. Reward the play, not just the stat.</li>
    <li><strong>Narrate the four degrees here too.</strong> A critical success turns the NPC further than hoped &mdash;
    they volunteer the next clue, become an ally, name a second name. A critical failure shuts the door and may make an
    enemy: the witness clams up for good, the marshal decides the party is the problem.</li>
    <li><strong>Some things cannot be rolled.</strong> No check makes a loyal man betray his daughter or a Hollow
    Prophet abandon his Word. When the want is bedrock, say so &mdash; let the players find a different lever or a
    different door. A social roll is for moving the movable, not for overwriting who a person is.</li>
  </ul>
</section>
"""

# ---------------------------------------------------------------- III. FEAR, NERVE & THE MARK
CH3 = f"""<!-- III -->
<section class="page" id="fear">
  {runhead('III. Fear, Nerve &amp; the Mark')}
  <h1 class="chapter">III. Fear, Nerve &amp; the Mark</h1>
  <p class="chapter-sub">The engine of dread, and the hand on its throttle.</p>
  <div class="divider"></div>
  <p class="dropcap lead">Nerve and the Mark are the truest hit points in this game, and you control the bleeding of
  both. The Player's Book tells the players what these tracks are. This chapter tells you when to spend them, how
  hard, and how to keep the horror from going slack on one side or lethal on the other. Misjudge this and the game
  becomes a plain western with monsters in it. Get it right and the table will not sleep easy.</p>

  <h2>When to Call a Dread Check</h2>
  <p>A <strong>Dread Check</strong> is a Will save against a Dread DC, made the first time a character truly confronts
  something that should not be. The operative word is <em>truly</em>. Do not call one for every corpse on a frontier
  thick with them. Call it when the ordinary world has visibly failed &mdash; when the corpse <em>moves</em>, when the
  shadow has no man to cast it, when a thing is wrong in a way a gun does not answer. Hold to three habits:</p>
  <ul>
    <li><strong>First sight, not every sight.</strong> One check the first time a horror is met in a scene, not
    every round you describe it. Familiarity is its own slow mercy.</li>
    <li><strong>Once per kind.</strong> The tenth walking corpse is not as terrible as the first. Don't tax Nerve for
    the same revelation twice in a night unless it escalates.</li>
    <li><strong>Earned, not sprung.</strong> The check should follow a thing the players saw coming wrong. Dread you
    set up is dread; dread you ambush them with is just arithmetic.</li>
  </ul>

  {plate('img2_unquiet', 'By moonlight a preacher and a frontier warrior fight risen corpses near an open grave on the prairie.', 'The first sight is the dear one &mdash; call the Dread Check, then let familiarity do its slow work')}

  <h2>The Dread DC Ladder</h2>
  <p>Choose the DC by what is actually witnessed, not by what it is named. A vampire glimpsed as a pale figure at the
  treeline is a lesser sight than the same vampire feeding. Pitch high the first time; let it settle as the night
  wears the players down.</p>
  <table>
    <thead><tr><th>The Sight</th><th>Dread DC</th><th>Nerve lost on a failed save</th></tr></thead>
    <tbody>
      <tr><td>A fresh corpse, plainly murdered</td><td>10</td><td>1</td></tr>
      <tr><td>A mutilation; a thing half-eaten</td><td>13</td><td>1d4</td></tr>
      <tr><td>The walking dead; a true haunting</td><td>16</td><td>1d6</td></tr>
      <tr><td>A thing from outside; the deep dark</td><td>20</td><td>1d10</td></tr>
      <tr><td>A truth that unmakes the world</td><td>25</td><td>1d10 + a lasting Affliction</td></tr>
    </tbody>
  </table>
  <p>A <strong>critical success</strong> costs no Nerve and steadies that character against the same horror for the
  rest of the scene &mdash; reward the hard-bitten. A <strong>critical failure</strong> loses the Nerve and imposes
  <em>Frightened 1</em> at once. Remember the players begin each session at full Nerve (RES score + level); a tough
  hand might bank twelve or fifteen, a green and gentle soul barely six. Know your table's numbers before you start
  spending them.</p>

  <h2>Spending Dread Wisely</h2>
  <div class="keeper-note"><span class="kn-tag">Keeper's eye</span>Nerve is a budget for the whole night, not the first
  fight. If you bleed the party to zero by the second scene you have nowhere left to go and a table of broken
  characters doing chaos for an hour. Drain slow. Let small failures accumulate. Save the 1d10 sights for the
  reckoning, so the players walk into the climax already frayed &mdash; that is when a single failed save lands like a
  gunshot.</div>

  <h2>Running the Break</h2>
  <p>A character at <strong>0 Nerve</strong> breaks: roll on the Player's Book's table for an uncontrolled response,
  and they take a lasting Affliction. The thing to remember at the table is that a broken character is <em>not</em>
  benched &mdash; they are made dangerous, to themselves and to the souls beside them. Lean into it. A man firing wild
  at the threat and whatever's near it, a woman frozen useless while the dark closes &mdash; these are the moments the
  players will remember being scared. But keep it short. Hand control back the moment the immediate response plays
  out; a player narrating their own slow ruin is good horror, a player benched for an hour is a bored friend.</p>

  <h2>Afflictions &mdash; the Scars That Stay</h2>
  <p>When a soul breaks, or endures a sight that unmakes the world, it does not always come back whole. An
  <strong>Affliction</strong> is a lasting wound to the spirit &mdash; not a penalty the player chose, but a scar the
  dark left, and a thread for you to pull on. Roll one, or choose the one that bites deepest, whenever the rules call
  for it: a true Break, a horror beheld at DC 25, or a Mark step that should cost more than the rest.</p>
  <table>
    <thead><tr><th>d10</th><th>The Affliction</th><th>What it costs</th></tr></thead>
    <tbody>
      <tr><td>1</td><td>The Shakes</td><td>&minus;2 to anything fine or steady-handed while under any strain</td></tr>
      <tr><td>2</td><td>Night Terrors</td><td>No Nerve returns from sleep alone &mdash; only by a fire, in company, or in drink</td></tr>
      <tr><td>3</td><td>The Long Stare</td><td>&minus;2 to be trusted or read by folk; they see the haunt on you</td></tr>
      <tr><td>4</td><td>A Compulsion</td><td>A small rite &mdash; counting, salt, a rhyme &mdash; must be done, or be Shaken until it is</td></tr>
      <tr><td>5</td><td>The Cold</td><td>Never quite warm again; &minus;2 against cold and against fear</td></tr>
      <tr><td>6</td><td>Faithless</td><td>The old comforts &mdash; prayer, ward, hymn &mdash; no longer steady you as they did</td></tr>
      <tr><td>7</td><td>The Whisper</td><td>You hear it now; once a session it tells you something true, to earn a lie later</td></tr>
      <tr><td>8</td><td>Brittle Nerve</td><td>Begin each session at &minus;2 maximum Nerve until it heals</td></tr>
      <tr><td>9</td><td>Marked in Dreams</td><td>The dark knows where you sleep; count your Taint exposure one step worse</td></tr>
      <tr><td>10</td><td>The Hollow</td><td>A piece did not come back; &minus;1 to one ability score until you are made whole</td></tr>
    </tbody>
  </table>
  <p>Afflictions heal slowly and seldom on their own. A full season of safety, a true sanctification, the care of an
  Alienist (a Sawbones art &mdash; Player's Book, Ch. V), or the facing-down of the very thing that caused it may lift one. Some will not
  fade until the larger wrong of the campaign is righted &mdash; and that is the point of them.</p>
  <div class="keeper-note"><span class="kn-tag">A kindness</span>An Affliction is a story hook, not a punishment. Name
  it, let the table watch it work on their friend, and offer &mdash; somewhere down the trail &mdash; a hard road to
  its healing. A character who earned the Whisper and then silenced it has a tale worth more than the scare that gave
  it to them.</div>

  <h2>Giving Back Nerve</h2>
  <p>Nerve does not come back in the field. It returns at full only with the new session &mdash; a night survived,
  a fire, the company of the living. You may grant a small recovery (1d4) in play for a true respite: a safe night
  in a real bed, a hymn sung all the way through, whiskey shared with people who saw the same thing and lived. Never
  in sight of the dark, and never for merely waiting. The point is to make safety precious.</p>

  <h2>A Night's Worth of Dread &mdash; Worked</h2>
  <p>The hardest thing to feel for, starting out, is how much Nerve a night should cost. Too little and the horror
  never bites; too much and the party breaks in the second scene and spends the climax useless. Here is one full night
  budgeted for a hard-bitten 2nd-level character starting with <strong>11 Nerve</strong> (RES&nbsp;9 + level&nbsp;2),
  to show the shape of it:</p>
  <div class="box">
    <h4>The Bleeding of One Eli, Across One Session</h4>
    <ul>
      <li><strong>Act One, the wrong note.</strong> A mutilated steer, drained and wrong (DC&nbsp;13). He saves &mdash;
      no loss. The dread is in the suspicion, not the tax. <em>Nerve: 11.</em></li>
      <li><strong>Act Two, the first true sight.</strong> The dead get up in the Pell barn (DC&nbsp;16). He fails;
      loses 4. This is the night's hinge, and it should sting. <em>Nerve: 7.</em></li>
      <li><strong>Act Two, the cellar.</strong> The half-turned wife, pleading (DC&nbsp;16 again, but once-per-kind
      &mdash; so no check for more Risen; this is a <em>new</em> horror, the living victim). He saves this time, hardened
      a little. <em>Nerve: 7.</em></li>
      <li><strong>The ride to the mission.</strong> No check &mdash; travel is for building dread, not taxing it. Let
      him stew. <em>Nerve: 7.</em></li>
      <li><strong>Act Three, the reckoning.</strong> The Nightwalker's regard in the dark of the church
      (DC&nbsp;16). He walks in already frayed at 7, and a failed save here &mdash; lose 1d6 &mdash; could drop him
      toward the break right as the climax peaks. <em>That</em> is the design: the night's worst sight lands on the
      thinnest Nerve.</li>
    </ul>
  </div>
  <p>Notice the rhythm: one save passed early to build confidence, one hard failure at the hinge, a quiet stretch to
  let it settle, and the deepest danger saved for the climax when the cushion is gone. A character who walks into the
  reckoning at full Nerve has had too easy a night; one who broke before it had too cruel a one. Aim to bring them to
  the climax frayed but standing, with just enough left that one bad roll matters.</p>
  <div class="keeper-note"><span class="kn-tag">Reading the room</span>Watch the actual numbers as you go. If the party
  is bleeding faster than this &mdash; bad saves, a low-RES table &mdash; ease off: skip a check, let familiarity cover
  the next sight. If they're sailing through untouched, pitch the reckoning's DC higher or stack a second sight on it.
  The budget is a feel, not a formula, and the table tells you which way to lean.</div>

  <h2>The Mark</h2>
  <p>Nerve frays; the Mark <em>stains</em>. It is a track of six steps that does not heal on its own &mdash; it only
  ever waits. Grant it rarely and never cheaply, in exactly three cases:</p>
  <ul>
    <li><strong>Breaking utterly</strong> &mdash; only on the rare roll (a 6 on the breaking table, a moment of terrible
    clarity) where the dark gets a hook in.</li>
    <li><strong>Reaching for the Old Dark</strong> &mdash; when a character draws on power the world was not meant to
    hold: a hex worked, a bargain struck, a sign cut into living ground.</li>
    <li><strong>Touching the deep dark and surviving changed</strong> &mdash; a Patron met and walked away from, a
    truth at DC 25 endured.</li>
  </ul>
  <p>Each step costs the character something the table can feel &mdash; dogs that will not meet their eye, a chill,
  a hunger, a voice that gives good advice. At the sixth, the dark owns them, and they pass from a player's hands into
  yours. That is a campaign-ending fate and should take a campaign to reach. Make the Marked feel the road they're on
  long before its end. Redemption exists &mdash; a true sacrifice, a sanctified ground held, a debt paid in full &mdash;
  but it is the rarest medicine in the country, and it should cost more than the bargain ever did.</p>

  <p>The trouble, in play, is that "the table can feel it" is easy to write and hard to improvise at midnight. So here
  is the road, step by step &mdash; signs you can drop in without slowing the scene, each one a touch worse than the last:</p>
  <table>
    <thead><tr><th>Step</th><th>What the world does around them</th></tr></thead>
    <tbody>
      <tr><td><strong>1</strong></td><td>Animals go uneasy &mdash; a dog growls low, a horse sidesteps, the cat leaves the room. Nothing a person would notice yet, but the beasts know.</td></tr>
      <tr><td><strong>2</strong></td><td>A cold that travels with them; the fire seems to lean away. Folk feel it without naming it and sit a little farther off.</td></tr>
      <tr><td><strong>3</strong></td><td>They know things they shouldn't &mdash; a stranger's grief, the bad card coming, the lie under a kind word. The good advice no one asked for, and the unease when it proves right.</td></tr>
      <tr><td><strong>4</strong></td><td>A hunger, a habit, a thing they do now &mdash; salt they must throw, a count they must finish, a taste for the raw or the dark. The other players start to watch them.</td></tr>
      <tr><td><strong>5</strong></td><td>The dark speaks to them plainly and offers, and the offers are good, and turning them down gets harder each time. They are useful now in ways that frighten the people who love them.</td></tr>
      <tr><td><strong>6</strong></td><td>The road's end. What stands up wearing their face answers to you now, not the player &mdash; and it knows everything the character knew, including the party's soft places.</td></tr>
    </tbody>
  </table>

  <div class="keeper-note"><span class="kn-tag">A word of warning</span>Never hand a player the Mark as punishment for
  a bad roll. The Mark is for <em>choices</em>. A character cursed by a die is a victim; a character Marked by a
  decision they'd make again is a tragedy, and tragedy is the game.</div>
</section>
"""

# ---------------------------------------------------------------- IV. THE LONG ODDS
CH4 = f"""<!-- IV -->
<section class="page" id="odds">
  {runhead('IV. The Long Odds')}
  <h1 class="chapter">IV. The Long Odds &mdash; Building the Fight</h1>
  <p class="chapter-sub">Balancing a gunfight that can kill, against monsters that should.</p>
  <div class="divider"></div>
  <p class="dropcap lead">Combat in Blood &amp; Grit is fast and thin. Blood totals are low, guns hit hard, and a
  first-level character can die in a single exchange they walked into wrong. That is a feature; this is a horror
  western, not a fantasy of heroes who soak ten wounds. Your job is to build fights that threaten without
  slaughtering by accident, and to know which dial to turn when the dice run cruel.</p>

  {plate('img3_gunfight', 'Two gunmen face off on a frontier main street outside a saloon, pistols drawn.', 'Most fights are short, loud, and decided by who shot first &mdash; build them so the players can see the cost coming')}

  <h2>Threat by Tier</h2>
  <p>Every adversary in this book carries a <strong>Tier</strong>, a rough measure of its danger. Use this benchmark
  table to build a foe from nothing, reskin one, or judge whether the thing you're about to set loose is fair. The
  numbers are what a creature of that tier should hit and take; bend them a point or two for flavor.</p>
  <table class="lvl">
    <thead><tr><th>Tier</th><th>Defense</th><th>Attack</th><th>Blood</th><th>Strong / Weak save</th><th>Damage / hit</th><th>Dread DC</th></tr></thead>
    <tbody>
      <tr><td>I &mdash; a mean dog of a thing</td><td>13</td><td>+4</td><td>12</td><td>+6 / +2</td><td>1d6+2</td><td>&mdash; / 10&ndash;13</td></tr>
      <tr><td>II &mdash; a real threat</td><td>15</td><td>+6</td><td>22</td><td>+8 / +3</td><td>1d8+3</td><td>13</td></tr>
      <tr><td>III &mdash; the night's monster</td><td>17</td><td>+9</td><td>40</td><td>+11 / +5</td><td>2d6+4</td><td>16</td></tr>
      <tr><td>IV &mdash; an apex horror</td><td>20</td><td>+13</td><td>70</td><td>+15 / +8</td><td>2d8+6</td><td>20</td></tr>
      <tr><td>V &mdash; a thing from outside</td><td>23</td><td>+17</td><td>110</td><td>+19 / +11</td><td>3d8+8</td><td>25</td></tr>
    </tbody>
  </table>
  <p>As a rough rule, a creature's Tier is a fair, dangerous fight for a party whose <strong>level equals twice the
  Tier</strong>: Tier I tests 1st&ndash;2nd level, Tier II around 4th, Tier III around 6th, and so on. A monster two
  Tiers above the party's reckoning is a thing to be fled, not fought &mdash; and good horror has plenty of those.</p>

  <h2>Budgeting a Fight</h2>
  <p>For a quick measure, give the party a budget of <strong>4 points per character</strong>. Spend it on foes:</p>
  <ul>
    <li><strong>A mook</strong> (Tier at or below party-level&minus;2): <strong>1 point</strong>.</li>
    <li><strong>An even foe</strong> (Tier matching the rule above): <strong>4 points</strong>.</li>
    <li><strong>A standout</strong> (one Tier above): <strong>8 points</strong>.</li>
  </ul>
  <p>Spend the budget for a <strong>standard</strong> fight the party should win bloodied. Spend half for an
  <strong>easy</strong> one; spend half again over for a <strong>hard</strong> one; double it for a
  <strong>deadly</strong> one someone may not walk away from &mdash; and tell the fiction so, with a sight, an omen,
  a dead man already on the ground, before the players commit.</p>

  <h2>Building a Threat from Scratch</h2>
  <p>The Bestiary holds a hundred and fifty things to fight, and the country always has one more. To make your own,
  work down this list &mdash; it takes about a minute.</p>
  <div class="box">
    <h4>Six Steps to a Monster</h4>
    <ul>
      <li><strong>1. Pick the Tier.</strong> Half the party's level, rounded toward danger. That is a fair, hard fight.</li>
      <li><strong>2. Copy the row.</strong> Read Defense, attack, Blood, saves, damage, and Dread DC straight off the
      Threat-by-Tier table above. You now have a working monster.</li>
      <li><strong>3. Set its nature.</strong> Choose the strong save: the dead and the cursed hold Will and Fortitude
      and fail Reflex; beasts hold Reflex and Fortitude and fail Will; the Old Dark holds Will above all.</li>
      <li><strong>4. Give it one Special.</strong> The single thing the numbers don't say &mdash; it heals, it drains,
      it cannot be seen whole, it calls more of its kind. One is plenty; two makes a boss.</li>
      <li><strong>5. Give it one weakness.</strong> The <em>Putting It Down</em> &mdash; the salt, the fire, the stake,
      the named truth. Every monster has its one thing, and learning it is the players' work.</li>
      <li><strong>6. Name the sight.</strong> Decide what first seeing it costs in Nerve, and whether touching its
      power costs Mark. Then describe it so the table feels the Tier before they roll.</li>
    </ul>
  </div>
  <p>Worked in a breath &mdash; <em>a haunt-hound</em>, Tier II for a 4th-level party. Off the table: Defense 15,
  attack +6, Blood 22, saves +8&nbsp;/&nbsp;+8&nbsp;/&nbsp;+3, damage 1d8+3, Dread 13. Nature: a beast, so strong
  Reflex and Fortitude, weak Will. Special: it runs down whatever flees and never tires. Weakness: it cannot cross a
  threshold freely given. Sight: DC 13, the green fire where its eyes should be. Two minutes, and the dark has a new
  hound.</p>

  <h2>The Gunfight</h2>
  <p>A few rulings will carry every shoot-out you run:</p>
  <ul>
    <li><strong>Range &amp; cover.</strong> A target behind cover adds +2 (partial) or +4 (good) to its Defense;
    a target with no cover in the open is a target the smart foe takes first. Sidearms past their range, and long
    guns up close, take the penalty in the Player's Book.</li>
    <li><strong>The draw.</strong> When a fight breaks from a standoff, the side that meant to draw acts first;
    if both meant to, it's a Reflex contest. Reward the player who said "I keep my hand near my iron" in the talking.</li>
    <li><strong>Aim vs. volume.</strong> A character may take the aim (a Beat to steady, then a surer shot) or
    pour it on (multiple shots at the rising Multiple Attack Penalty). Let the desperate spray and the patient
    aim; both are westerns.</li>
    <li><strong>The ambush.</strong> A foe who strikes from true surprise gets a free round and, often, a Dread
    Check for the horror of it. This is how a Tier-III monster fairly threatens a higher party: it picks the ground.</li>
  </ul>

  <h2>Morale &amp; the Flight of Men</h2>
  <p>Men are not monsters; they break and run. When a human foe is bloodied, leaderless, or has watched the dark
  take the fight out of their hands, call a morale check (a Will save against the situation). Bandits flee, surrender,
  or scatter. Monsters, as a rule, do not &mdash; and that difference is itself a horror the players will come to feel.</p>

  <h2>Pursuit</h2>
  <p>When something chases or is chased, run it as a short series of opposed checks &mdash; Ride, Athletics, Survival,
  whatever fits the ground &mdash; best of three deciding it, with each exchange a chance to describe the gap closing.
  Do not let a chase become a math problem; let it be a string of hard choices made at a gallop.</p>

  <h2>The Ground Is Half the Fight</h2>
  <p>Where a fight happens decides it more often than who's in it. A flat empty street is the dullest battlefield in
  the country; give every reckoning a <em>map in the mind</em> &mdash; cover to break line of sight, high ground worth
  taking, a hazard to be used or feared, a chokepoint that funnels the dead. The players should always have a terrain
  decision to make, and the monster should always have one the players can turn against it.</p>
  <ul>
    <li><strong>Cover and concealment.</strong> Cover stops bullets (+2 or +4 Defense, Ch. above); concealment only
    hides (a miss chance, a broken line of sight). Smoke, dark, and dust grant concealment &mdash; which the players
    can use as readily as the dark can, and a clever party will.</li>
    <li><strong>High ground and chokepoints.</strong> The lip of the canyon, the top of the stairs, the doorway a swarm
    must come through one at a time. A party that seizes the choke turns a losing numbers-fight into a fair one; let
    them, and let the smart monster try to flank it.</li>
    <li><strong>The hazard in the room.</strong> The lamp-oil, the dynamite, the rotten floor, the deep water, the
    edge. Seed one usable danger in every fight and the players will find ways to weaponize it you never imagined.
    The Drowned dragged onto dry land, the Hidebehind forced into the open, the swarm funneled past the open flame
    &mdash; these are the fights players remember.</li>
  </ul>
  <div class="keeper-note"><span class="kn-tag">Keeper's eye</span>Before you run a fight, name three features of the
  ground out loud as you set the scene. Doing it before initiative means the players treat them as tools, not as
  things you invented to save them. A battlefield described is a battlefield played on; a blank room is just two rows
  of dice trading hits.</div>

  <h2>Running the Mob</h2>
  <p>A graveyard of Risen, a sounder of hogs, a pack run as one &mdash; many small foes can bog a table to a crawl if
  you roll each one in turn. Don't. A few tricks keep the swarm fast and frightening:</p>
  <ul>
    <li><strong>Run them in clumps.</strong> Treat a group attacking the same target as one roll with a bonus, or
    one pool of damage, rather than six separate dice. Five Risen on one character is one attack at advantage that
    hits hard, not five turns of arithmetic.</li>
    <li><strong>One initiative for the lot.</strong> The mob acts together on a single count. It moves together, strikes
    together, and you describe it as a tide, not as individuals &mdash; which is also how it should <em>feel</em>.</li>
    <li><strong>Give the swarm a heart.</strong> The Gravecaller, the lead wolf, the relic at the center. A swarm with
    a source can be ended by reaching the source, which turns a grinding attrition fight into a tactical objective and
    gives the players a way to win that isn't "kill all forty." Most of the Bestiary's swarms are built this way on
    purpose &mdash; lean on it.</li>
    <li><strong>Let the mook die easy.</strong> A foe at Tier party-level&minus;2 should drop to one solid hit. Don't
    give the small things Blood totals that make the players saw through them; the threat of a mob is its numbers and
    its tirelessness, not the toughness of any one body.</li>
  </ul>

  <h2>When the Dice Turn Cruel</h2>
  <p>Combat in this game can kill, and sometimes it kills more than you meant. A run of bad saves, a monster crit, a
  plan gone wrong, and suddenly the whole party is bleeding out on the church floor. You have tools, and using them is
  not cheating &mdash; it is keeping the promise of fairness when the dice broke it:</p>
  <ul>
    <li><strong>Capture, don't kill.</strong> Most monsters and all men have reasons to take rather than slay &mdash;
    a cult needs sacrifices, a Nightwalker needs cattle, an outlaw needs hostages. A downed party can wake bound in
    the cellar with everything to play for, which is far better horror than a sheet of dead characters anyway.</li>
    <li><strong>Bring the dawn.</strong> Sunlight, a relief column, the storm breaking, the ally arriving &mdash; seed
    a clock that can rescue as easily as it can doom. A party pinned and dying saved by the gray of dawn, at the cost
    of the thing escaping, is a defeat that still moves the story.</li>
    <li><strong>Let the cost be the cost.</strong> Sometimes someone dies, and that is the game keeping faith. When it
    comes, give it weight: the last word, the Grit spent to buy a friend's escape, the body that must be carried out or
    left behind. A death the table saw coming and could not stop is not a failure of the game &mdash; it is the dread
    made real, and it is why the rest will be remembered.</li>
  </ul>
  <div class="keeper-note"><span class="kn-tag">The honest TPK</span>If the whole party falls fair &mdash; warned,
  bloodied, beaten by a thing they walked into eyes open &mdash; honor it. Don't fudge a total-party kill that the
  fiction earned; it cheapens every death that came before. But a TPK from a single freak run of dice, with no warning
  and no out, is the one you quietly soften, because it breaks the promise. Know the difference: a TPK the players can
  point at and say <em>we should have run</em> is a story; one they can only call bad luck is a betrayal.</div>

  <h2>A Hand at the Table</h2>
  <p>Rules read cold on the page. Here is the engine warm &mdash; a few beats of real play to show how the pieces move
  together. The Keeper's words are plain; the dice and rulings are in brackets.</p>
  <div class="box">
    <h4>Worked Example: The Pell Barn</h4>
    <p><strong>Keeper:</strong> The barn door hangs open on a dark you can't see the back of, and something in there
    is breathing wet and slow. What do you do?</p>
    <p><strong>Eli:</strong> I ease up to the door and listen &mdash; can I tell what it is?</p>
    <p><strong>Keeper:</strong> Give me a Notice. [<em>Uncertain and consequential, so a roll; the dark hides a
    Risen, DC 15.</em>] &hellip; A 19. [<em>Success.</em>] It's a man's shape, swaying, and the breathing isn't
    breathing at all &mdash; it's wind in a chest that doesn't work anymore. Then it turns, and its eyes catch your
    lantern, and they are the wrong color clean through. [<em>First true sight of the walking dead &mdash; a Dread
    Check, Will DC 16.</em>] Give me a Will save against the dread of it.</p>
    <p><strong>Eli:</strong> &hellip;That's a 7. [<em>Failure: lose 1d6 Nerve, 4 rolled; Eli drops from 9 to 5.</em>]</p>
    <p><strong>Keeper:</strong> Your nerve goes out of you like water. You've seen dead men &mdash; never one that
    looked back. It comes off the wall toward you, arms rising. You have the time it takes to cross the barn.</p>
    <p><strong>Eli:</strong> I draw and put two in its chest. [<em>Two Beats: a shot, then a second at the Multiple
    Attack Penalty.</em>]</p>
    <p><strong>Keeper:</strong> First shot [<em>+5 vs Defense 12 &mdash; hits</em>] punches clean through, and the
    thing doesn't so much as flinch; it does not stop for pain. The second [<em>at &minus;5 MAP</em>] goes wide as it
    closes. It's on you now.</p>
    <p><strong>Eli:</strong> I spend a Grit to make that second shot count &mdash; reroll. [<em>Grit spent; the reroll
    hits.</em>]</p>
    <p><strong>Keeper:</strong> The second takes its jaw off and it staggers &mdash; but the Risen don't stop for
    ruin short of true ruin. It's still coming. Now you know what the salt and the lamp-oil in your saddlebag are
    <em>for</em>.</p>
  </div>
  <p>Notice what the engine did in those few lines: a check rolled only because failure was interesting; the degrees
  narrated, not just hit-or-miss; the first true horror taxed in Nerve; the action economy and the Multiple Attack
  Penalty shaping the gunfight; a Grit point spent to seize a moment; and a weakness seeded for the player to
  discover. Run every scene like this and the rules vanish into the story, which is where they belong.</p>

</section>
"""

# ---------------------------------------------------------------- V. BESTIARY
def statblock(name, tier, lines):
    body = "".join(f"<p>{l}</p>" for l in lines)
    return (f'<div class="statblock"><div class="sb-head"><span class="sb-name">{name}</span>'
            f'<span class="sb-tier">{tier}</span></div>{body}</div>')

CH5 = f"""<!-- V -->
<section class="page" id="bestiary">
  {runhead('V. The Bestiary &amp; How to Use It')}
  <h1 class="chapter">V. The Bestiary &amp; How to Use It</h1>
  <p class="chapter-sub">Where the monsters went, and how to set them loose.</p>
  <div class="divider"></div>
  {quote("Know the thing before you set it loose. A monster the Keeper does not understand is a monster that kills the wrong player.", "from a Keeper's ledger")}
  <p class="dropcap lead">The creatures once kept in this chapter have a book of their own now &mdash; <em>The Bestiary</em>,
  the third of these volumes, where a hundred and fifty of the things that walk the country are set down with the numbers
  to run them and the one hard truth that puts each one down. This chapter is the bridge: how to choose a horror, read
  its block, and wield it well. Keep the Bestiary at your elbow; this book tells you how to use it.</p>

  <div class="box">
    <h4>Reading a Stat Block</h4>
    <ul>
      <li><strong>Tier</strong> (I&ndash;V) is the measure of danger &mdash; a fair, hard fight for a party of twice
      that in levels (Ch. IV). <strong>Defense</strong> is the number to hit it; <strong>Blood</strong> is what it takes.</li>
      <li><strong>Saves</strong> are Fortitude / Reflex / Will. <strong>Attacks</strong> give the bonus to hit and the
      damage on a hit; apply the Multiple Attack Penalty to extra strikes as a player would.</li>
      <li><strong>Dread</strong> is the Will-save DC on first sight and the Nerve a failure costs (Ch. III).
      <strong>Mark</strong>, where it appears, is the soul-cost of touching the thing's power.</li>
      <li><strong>Putting It Down</strong> is the secret &mdash; the weakness the players must learn, usually the hard way.</li>
    </ul>
  </div>

  <h2>Choosing the Night's Monster</h2>
  <p>Pick by Tier first &mdash; the budget in Chapter IV tells you what is fair &mdash; then by the kind of fear you want.
  The Bestiary is sorted to help: the restless dead for sieges and grief; cursed beasts for the hunt; men and the shapes
  of men for paranoia and the gun; spirits and hauntings for the slow, helpless dread of a place; the wild and the
  weather for survival; and the Old Dark for the nights the players are meant only to survive.</p>
  <p>Its last two chapters are sorted differently, and they are the ones a new Keeper reaches for last and should reach
  for first. The beasts of the living world and the hard men and hard country are sixty-five things that will maim a
  posse with nothing supernatural about them at all &mdash; a rustler with a running iron, a river in flood, a sow with
  cubs, a norther coming down at four in the afternoon. None of them costs a point of Nerve. That is the whole use of
  them: spend the first month of a campaign there, and the table learns that this country is dangerous on its own
  terms, that their guns work, and that you are dealing straight with them. Everything in the seven chapters above
  lands harder on a table that has been taught to expect an ordinary explanation.</p>

  <h2>Reskin Without Mercy</h2>
  <div class="keeper-note"><span class="kn-tag">Keeper's eye</span>A name is a costume. When the players have learned a
  thing's secret &mdash; the stake, the tell, the salted door &mdash; change its face <em>and</em> its secret, and let them
  learn again from nothing. The numbers in the Bestiary serve a dozen monsters each: the Pale Wolf's line runs any cursed
  pack, the Nightwalker's any blood-drinking dead. Familiarity is the death of dread, and reskinning is its cure.</div>

  <h2>One Monster, Used Well</h2>
  <p>A single horror, glimpsed wrong three times before it is seen whole, frightens a table more than a parade of stat
  blocks ever will. Show the work it does before you show the thing: the drained steer, the wrong tracks, the survivor
  who will not speak. Let the players build the monster in their own heads, where it is always worse than anything on the
  page. The Bestiary gives you the body; your patience gives it the dread.</p>
</section>
"""

# ---------------------------------------------------------------- VI. HAZARDS
CH6 = f"""<!-- VI -->
<section class="page" id="hazards">
  {runhead('VI. Cursed Ground &amp; Hazards')}
  <h1 class="chapter">VI. Cursed Ground, Hazards &amp; Bad Medicine</h1>
  <p class="chapter-sub">The dangers that have no eyes to shoot for.</p>
  <div class="divider"></div>
  <div class="narr">Mark this chapter as the place your campaign quietly changes its nature. Up to here the
  players have fought things &mdash; and a thing that can be fought, however terrible, is still a western.
  From here on, some of what is wrong has no eyes to shoot for and no Blood to spend, and the game the
  players thought they were playing begins, by honest degrees, to be the other one. Do not announce it.
  Let them discover that the revolver has stopped being the answer, one unanswered shot at a time.</div>
  <p class="dropcap lead">Not every threat in the country has a Blood total. Some of it is the ground itself, the
  weather, the long thirst, and the slow poison of places where the dark has soaked in. These hazards are how you
  threaten a party between monsters &mdash; and how you make a haunted place feel haunted before anything with teeth
  shows up.</p>

  {plate('img5_hexing', 'An old woman kneels on a cabin floor chalking strange hex-signs by lantern-light amid herbs and bottles.', 'Where the signs are cut, the ground remembers &mdash; cursed places ask a toll of everyone who lingers')}

  <h2>Tainted Ground</h2>
  <p>Where blood was spilled in the dark's name, where a mine broke into the deep, where the veil has worn thin, the
  land itself takes a stain &mdash; and asks a toll of every living soul who lingers, monster or no. Run it as the
  <em>Taint</em> clock from the Player's Book (Chapter XII): for every three days on cursed ground, a Fortitude save
  (the body first) or Will (once it reaches the mind) against the ground's DC &mdash; <strong>13</strong> for soured
  earth, <strong>16</strong> for a blighted seat, <strong>20</strong> for a Patron's own ground. Fail and the Taint
  deepens a step; the four steps run from a souring sickness to a whisper that turns the soul onto the dark's errands.
  This is your tool for a haunted house that hurts to stay in even before the haunting starts. Wards, salt, and the
  right Provisions ease the DC; only true sanctification sheds it for good.</p>

  <h2>The Wrong House</h2>
  <p>A haunted place should fight the players quietly: doors that won't stay shut, a cold that lamps don't touch, a
  room that is wider inside than out. Spend Notice and Lore (Occult) checks (rolled in secret, Ch. II) to dole out
  the wrongness piece by piece. Keep a small clock for the haunting's escalation &mdash; cold, then movement, then a
  sight, then a reckoning &mdash; and tick it as the players pry where they shouldn't.</p>

  <h2>Cursed Objects</h2>
  <p>A thing carried out of a wrong place may carry the wrong with it. Use these sparingly; one good cursed object is
  a whole campaign thread.</p>
  <table>
    <thead><tr><th>The Object</th><th>The Gift</th><th>The Toll</th></tr></thead>
    <tbody>
      <tr><td>A dead man's revolver</td><td>Never misfires; +1 to hit</td><td>It wants to be fired; Will save to holster it with a target in sight</td></tr>
      <tr><td>A locket of hair</td><td>The wearer dreams true</td><td>The dreams are someone else's, and they are coming closer</td></tr>
      <tr><td>A vein of cold silver</td><td>Coin that always spends</td><td>+1 Taint a week to whoever holds the purse</td></tr>
      <tr><td>A prophet's bible</td><td>Reads the dark's signs at a glance</td><td>It reads you back; +1 Mark the day you trust it</td></tr>
    </tbody>
  </table>

  <h2>When Players Dabble</h2>
  <div class="keeper-note"><span class="kn-tag">Bad medicine</span>Sooner or later a player works a sign, reads a rite,
  or takes a bargain. Let them &mdash; the Old Dark is in the Player's Book for a reason &mdash; but the dark always
  delivers exactly what was asked and never what was wanted, and the bill comes in Mark. A rite worked wrong (a failed
  check) does something, just not the something intended: it calls the wrong thing, or the right thing to the wrong
  place, or works on the caster. The fun is real and the cost is real. Hold to both.</div>

  <h2>The Plain Hazards of a Hard Country</h2>
  <p>Don't forget the mundane killers; on the frontier they do half your work. A killing thirst or cold (Fortitude,
  rising DC, Fatigued then Blood loss), a river crossing (Athletics DC 15, more in flood), a fall, a prairie fire,
  a fever in camp, a rattler in the bedroll. Set the DC off the ladder in Chapter II, let a critical failure cost
  real Blood, and remember that a party worn down by the road is a party already half-beaten when the dark finds them.</p>

  <p>For when you need a number on the spot, here is the hard country priced out:</p>
  <table>
    <thead><tr><th>The Hazard</th><th>Save</th><th>On a failure</th></tr></thead>
    <tbody>
      <tr><td>Killing thirst (per day, desert)</td><td>Fort, DC 13 rising +2/day</td><td>Fatigued, then 1d6 Blood and worsening</td></tr>
      <tr><td>Killing cold (per night, exposed)</td><td>Fort, DC 13 rising +2/night</td><td>Fatigued, then 1d6 Blood; sleep risks worse</td></tr>
      <tr><td>A bad fall (per 10 ft)</td><td>Ref, DC 15 to catch</td><td>1d6 Blood per 10 ft fallen</td></tr>
      <tr><td>River in flood</td><td>Athletics, DC 18</td><td>Swept downstream; gear lost; drowning clock</td></tr>
      <tr><td>Camp fever / bad water</td><td>Fort, DC 15</td><td>Sickened, &minus;2 to all rolls until it breaks</td></tr>
      <tr><td>Prairie fire / smoke</td><td>Ref to flee, Fort vs. smoke, DC 16</td><td>1d8 fire; choking and blind</td></tr>
      <tr><td>Snakebite / spider</td><td>Fort, DC 15</td><td>1d6 and Enfeebled; worsens untreated</td></tr>
      <tr><td>Quicksand / bog</td><td>Athletics, DC 15</td><td>Sinks a step each round; rope and aid needed</td></tr>
      <tr><td>Bad laudanum / rotgut</td><td>Fort, DC 13</td><td>Stupefied; a poor choice in a crisis</td></tr>
    </tbody>
  </table>
  <p>A critical failure on any of these costs roughly double, or skips a step toward the worst the hazard can do. And
  the country stacks: a party that fails the thirst, then the fever, then meets the dark is a party you will barely
  need a monster to threaten.</p>

  <h2>Rites, Signs &amp; the Working of the Craft</h2>
  <p>Sooner or later the players will want to <em>do</em> the dark's work themselves &mdash; cleanse a ground, ward a
  door, read a sign, work a rite out of a dead hexer's book. Here is how to run it without inventing it fresh each
  time. A working has four parts: a <strong>cost</strong> (time, materials, sometimes Blood or Mark), a
  <strong>check</strong> (usually Lore (Occult), at a DC set by how far the working reaches), an <strong>effect</strong>
  on a success, and a <strong>price</strong> on a failure &mdash; because a botched rite never simply fizzles.</p>
  <table>
    <thead><tr><th>The Working</th><th>DC</th><th>Done right / Done wrong</th></tr></thead>
    <tbody>
      <tr><td>Ward a threshold (salt, sign, prayer)</td><td>13</td><td>The dark cannot cross till dawn / it crosses, and knows you tried</td></tr>
      <tr><td>Read a sign or omen aloud</td><td>15</td><td>A true answer / a true answer twisted, or a thing notices the reading</td></tr>
      <tr><td>Cleanse a tainted spot</td><td>18</td><td>The ground eases a step / the taint flares and spreads to the cleanser</td></tr>
      <tr><td>Lay a restless dead to rest</td><td>16</td><td>It rests / it wakes angry, or wakes its neighbors</td></tr>
      <tr><td>Work a hex or bargain (the Old Dark)</td><td>20+</td><td>The dark delivers &mdash; and collects in Mark / it delivers to the wrong door, or onto the caster</td></tr>
    </tbody>
  </table>
  <div class="keeper-note"><span class="kn-tag">The botched rite</span>The most important word above is <em>never
  fizzles</em>. A failed working does something &mdash; just not the something intended. It calls the wrong thing, or
  the right thing to the wrong place, or turns its effect on the one who worked it. This keeps the Craft genuinely
  frightening to use, which is exactly right: power over the dark should never feel safe, and a player who works a rite
  with a steady hand and a held breath is a player playing the game as built.</div>

  <h2>The Shape of a Bargain</h2>
  <p>The deepest working is the deal, and it deserves its own care because it is the engine of the Mark and half the
  tragedy of the game. When a player &mdash; or a desperate NPC &mdash; bargains with the Old Dark, hold to three
  rules and the deals will run themselves:</p>
  <ul>
    <li><strong>The dark gives exactly what was asked, and never what was wanted.</strong> Wish the rival dead and he
    dies &mdash; and rises. Ask to save the child and she lives &mdash; changed. Read the letter of the request back to
    yourself and grant <em>that</em>, not the intent behind it. The gap between the two is where the horror lives.</li>
    <li><strong>The price is always Mark, and always more than it looks.</strong> A small deal is one step; a large one,
    two or more; a deal to undo death or unmake a loss, the deepest stain the game allows. Name the cost honestly when
    asked &mdash; the dark does not hide its terms, because it doesn't need to.</li>
    <li><strong>Every bargain solves one problem and plants the next.</strong> The deal that saves tonight should be
    the seed of a worse night later. A bargain with no future cost is just a magic item; a bargain that comes back
    wearing a debt is a story. And when the bill comes due, it often comes wearing the Tallyman's coat (see the
    Bestiary) &mdash; the collector who cannot be refused.</li>
  </ul>

</section>
"""

# ---------------------------------------------------------------- VII. REWARDS
CH7 = f"""<!-- VII -->
<section class="page" id="rewards">
  {runhead('VII. Rewards &amp; Reckonings')}
  <h1 class="chapter">VII. Rewards &amp; Reckonings</h1>
  <p class="chapter-sub">What to give, what to withhold, and the slow price of the dark.</p>
  <div class="divider"></div>
  <p class="dropcap lead">The country gives nothing away, but you must give the players <em>something</em> &mdash; growth,
  coin, the occasional grace &mdash; or the table goes hollow. The trick is to make every reward feel wrested from a
  hard place, and to let the dark's rewards always carry a hook.</p>

  <h2>Advancement</h2>
  <p>Run levels by <strong>milestone</strong>: advance the party when they close a chapter of the story &mdash; a
  monster put down, a place cleansed, a truth survived &mdash; not by a tally of kills. A new level every two or three
  sessions keeps the numbers climbing without outrunning the dread; a party that levels too fast soon shrugs off the
  horrors that should still chill them. When in doubt, slow down. A 3rd-level character in this game is a hardened,
  capable soul; a 7th is a legend the territory will remember; there is no need to climb past ten.</p>

  <h2>Grit</h2>
  <p>Grit is the players' small mercy &mdash; their hero points &mdash; and you are its other source. Hand a point,
  there at the table, for a deed of true courage, a moment of perfect character, or a line that makes the whole table
  go quiet. Be generous with it before a hard reckoning and the players will spend it bravely; hoard it and they will
  too, and someone will die clutching an unspent token. The point of Grit is to be spent.</p>

  <h2>Coin &amp; Goods</h2>
  <p>Money is scarce and worth being scarce. Reward the players in things with stories &mdash; a dead outlaw's good
  rifle, a stake in a claim, a debt called in, a town's grudging gratitude that opens a door later &mdash; more than in
  loose dollars. A single box of silver shells, hard-won, is worth more dread-mileage than a saddlebag of gold, because
  the players will agonize over when to spend it.</p>

  <h2>The Dark's Wages</h2>
  <p>The Old Dark pays well and collects worse. When a Patron offers, let the offer be real and the price be Mark
  (Ch. III) &mdash; never a flat "no," which only makes the dark boring, but never a free "yes" either. The best
  bargains solve the immediate problem and plant the next one. A player who took the deal to save a friend, and would
  take it again, is exactly where the game wants them: one step further down a road they chose.</p>

  <h2 id="patrons-table">The Patrons at the Table</h2>
  <p>The Player's Book names six Patrons (Ch. VII) and wisely tells no more than a drifter's rumor of each. Here is
  the rest &mdash; how each one actually comes at a table of players, and when. Thirty years behind a screen teaches
  one thing above all others about devils: an offer made on schedule is a mechanic, and an offer made at the exact
  wrong moment is a memory the table keeps for years. A Patron never simply appears. Each waits at a different door,
  and the players open every one of those doors themselves.</p>

  <h3>The Devourer &mdash; the door of want</h3>
  <p>It comes when the body is failing: the snowed-in pass, the tainted well, the wound going bad three days' ride
  from help. It has no voice and needs none &mdash; its offer arrives as meat. Game where no game should be, strength
  flooding into a starving frame, and only afterward the understanding of what was traded. Make the offer only after
  the players have said out loud what they might be willing to do to survive, and never a moment sooner &mdash;
  otherwise it is you tempting them, and not the country. Its progress shows at every camp thereafter: the served one
  eats first, eats most, and stops asking what the meat is. Let the other players notice before the one who took it does.</p>

  <h3>The Whisperer &mdash; the door of the question</h3>
  <p>It waits on curiosity, and its moment is the fact the players cannot reach: the name three sessions hunted, the
  hour the train passes, what is really under the church. It answers questions no one has asked aloud &mdash; a
  certainty arriving at the edge of sleep, sourceless and correct. The craft here is discipline: everything it says
  must be true, every time, or it dies as a horror at your table. Its price rides inside the gift &mdash; each answer
  carries one more truth the asker did not want and cannot now unknow. It is the Patron for the party's thinker, and
  it will find the one soul at your table who cannot leave a locked box alone.</p>

  <h3>The Cold Deep &mdash; the door of hurt</h3>
  <p>It comes to the grieving and the broken, and never during the horror &mdash; after. The shaking hour past
  midnight when it is over; the day after the funeral; the first camp after a soul has Broken at 0 Nerve. It does not
  offer power. It offers relief &mdash; an end to the shaking &mdash; and relief is the hardest offer a player ever
  refuses on behalf of a hurting character. Its price is paid in subtraction, and you should run it that way: the
  character stops flinching, then stops weeping, then stops laughing. Roll no dice for any of it. Just let the table
  watch a friend go quiet.</p>

  <h3>The Long Trail &mdash; the door of the grave</h3>
  <p>It bargains exactly once, and its circumstance is a death &mdash; there at the table, with the body still warm
  and the players still silent. That is the hour the rider is on the ridge. One offer, in plain terms, no haggling;
  refused, it touches its hat brim and is gone, and it does not come back for that soul. Never offer twice &mdash;
  scarcity is the whole of its power, and the table must learn the refusal was real. If the deal is taken, remember
  that those it carries back come back a little wrong, and that the door it opened stays ajar: the returned soul sees
  the dusk rider now on every far ridge, and knows who it is waiting for.</p>

  <h3>The Thing Beneath the Mountain &mdash; the door of the strike</h3>
  <p>The one Patron that pays first and bargains after. Its circumstance is prosperity: the vein too rich for the
  ground it sits in, the claim sold suspiciously cheap, the town growing faster than any honest town grows. It seldom
  addresses the players at all &mdash; it works through the diggings and the money, and every dollar out of that
  ground is a signature on its paper. Run it as economics before you run it as horror: the players profit, the town
  booms, and only slowly does the arithmetic of what is waking underneath come due. It corrupts towns, not souls,
  and lets the town do the rest to the players.</p>

  <h3>The Red Sermon &mdash; the door of the flock</h3>
  <p>It rarely wants the players. It wants the crowd around them, and so it comes at the table sideways &mdash;
  through the revival tent, the new church, the charity that is feeding the hungry and filling the pews. Its moment
  is the moment your players begin to love a congregation, a town, a good man in a pulpit. What it offers a soul is
  legitimate success &mdash; full pews, a town's love, a gospel that visibly works &mdash; which is why it is the
  Patron that catches Preachers and Prophets who set out meaning well. Fight it as a rival for people, not a monster
  in the dark: every session the players spend elsewhere, it gains a family, a deacon, a street. The horror is
  arithmetic, and the players can read it in the faces at the church socials.</p>

  <div class="keeper-note"><span class="kn-tag">The veteran's rules</span>Four rules carry all six. A Patron makes
  its offer at the moment of weakness it owns and not before &mdash; hold the offer you have planned until the door
  is truly open, even if that takes a season. It almost never speaks in its own voice; it prefers heralds, dreams,
  signs, meat, money, and paperwork, and it is the more frightening for the indirection. One waking Patron is a
  campaign; two is a muddle &mdash; keep the others as rumors at the edge of the map. And the answer must always
  genuinely be allowed to be no. The Mark means something only because the player chose it &mdash; and a table that
  turns a Patron down flat has just told you, precisely, what they hold dearest. The dark was listening, and so
  were you.</div>

  <h2>Carrying the Marked</h2>
  <div class="keeper-note"><span class="kn-tag">The long fall</span>A Marked character is a slow tragedy you are
  telling together. Show the steps &mdash; the dogs, the chill, the good advice no one asked for &mdash; and let the
  other players see them too, so the table feels the road. Offer redemption, but make it cost: a sacrifice, a ground
  held, a debt paid in full. And if a character reaches the sixth step, honor it &mdash; the dark owns them, they pass
  into your hands, and their fall becomes the next character's reason to ride. A Mark fully earned is one of the most
  memorable ends this game offers. Do not cheapen it, and do not flinch from it.</div>
  <h2>The Long Game</h2>
  <p>A single night you now know how to run. A campaign is a different animal &mdash; a slow tightening, where the
  country's wrongness spreads from one homestead to a county, and the same dark hand shows behind a season of separate
  horrors. A few principles carry you from a one-night scare to a saga.</p>
  <ul>
    <li><strong>The dark has a shape.</strong> Behind the monsters, set one patient cause &mdash; a Patron waking, a
    cult building toward its rite, a curse spreading like blight, a Marked man climbing. Each adventure is a symptom;
    the campaign is the disease, and the players are slowly learning its name.</li>
    <li><strong>Mark and Taint are the campaign's clock.</strong> They only ever climb. A campaign is partly the story
    of who falls and who is pulled back &mdash; let the players feel the track filling over months, and let a hard-won
    step <em>backward</em> be one of the great victories the game can offer.</li>
    <li><strong>Run in seasons.</strong> Three to five sessions make an arc: a wrong note, a deepening, a reckoning
    that closes one door and cracks open a worse one. End each arc with something the players changed and something the
    dark gained.</li>
    <li><strong>Let it end.</strong> Every Blood &amp; Grit campaign should be <em>able</em> to end &mdash; a last door
    closed for good, the cause undone, the country quieter than they found it &mdash; and the ending should cost. A west
    that can never be saved is a treadmill with skulls; a west the players bleed to save is a story.</li>
  </ul>
  <div class="keeper-note"><span class="kn-tag">The recurring hand</span>Give the campaign a face the players come to
  hate or pity &mdash; a Hollow Prophet who keeps rising, a Marshal going slowly Marked, a Patron's herald always one
  town ahead. Met across a season, a single antagonist does more for dread than a parade of monsters seen once and shot.</div>

  <h2>Between the Reckonings</h2>
  <p>The quiet stretches matter as much as the nights of blood. Downtime &mdash; the days or weeks between one
  reckoning and the next &mdash; is where characters heal, where Afflictions are worked on, where the players invest in
  the country that the dark will later threaten. Give them real things to do with it:</p>
  <ul>
    <li><strong>Mending body and nerve.</strong> A true season of safety heals Blood fully and gives a chance at lifting
    one Affliction (a hard road, Ch. III). This is also when the doctor sets the bone right, the preacher hears the
    confession, the drink wears off. Make rest a place, not just a montage.</li>
    <li><strong>Putting down roots.</strong> Let them buy the claim, court the widow, take the deputy's star, build the
    ranch. Every root they put down is a thing the dark can later threaten &mdash; and a reason they can't just ride
    away when it does. A character with nothing to lose is a character hard to frighten.</li>
    <li><strong>Working the leads.</strong> Downtime is when the players chase the campaign's slow questions &mdash;
    research the old mission, write to the city for records, lean on a contact. Reward the digging with real threads.
    Let them <em>prepare</em>, sometimes, so the night they're ready feels earned.</li>
    <li><strong>The dark doesn't rest.</strong> While they heal and build, tick the campaign clock. The cult gains a
    town, the Marked man falls another step, the herald rides closer. Downtime that costs the players nothing on the
    far side makes the world feel safe; let the price of resting be a little ground given.</li>
  </ul>
  <div class="box">
    <h4>Before You Run a Night &mdash; the Half-Hour Prep</h4>
    <p>A whole session needs less preparation than you'd fear, if you prepare the right things. Settle these and walk in
    ready:</p>
    <ul>
      <li><strong>The truth.</strong> One paragraph: what's really happening, who's behind it, and what they want. If
      you can't say it in a breath, the players won't be able to either.</li>
      <li><strong>The clock.</strong> What the dark is doing and how many steps until it gets there. Write the steps;
      tick them in play.</li>
      <li><strong>Three wrong notes.</strong> The omens you'll drop in Act One &mdash; the cold, the silence, the
      grave. Have more than you'll need.</li>
      <li><strong>The core clue, placed thrice.</strong> The one thing the players must learn, and the three places
      they can learn it (Ch. II). Never gate it behind a roll.</li>
      <li><strong>The night's monster, read once.</strong> Know its tier, its one Special, and its <em>Putting It
      Down</em> cold &mdash; so you run it right and the weakness is there to be found.</li>
      <li><strong>One held card.</strong> A floating clue or complication in your pocket, for when the night stalls
      (Ch. II).</li>
    </ul>
    <p>Six lines of preparation. Everything else &mdash; the faces, the talk, the ground &mdash; you can improvise off
    the tools in this book the moment the table needs it.</p>
  </div>

</section>
"""

# ---------------------------------------------------------------- VIII. THE CAST
CH8 = f"""<!-- VIII -->
<section class="page" id="cast">
  {runhead('VIII. The Cast')}
  <h1 class="chapter">VIII. The Cast</h1>
  <p class="chapter-sub">The living souls of the country, made fast and run faster.</p>
  <div class="divider"></div>
  <p class="dropcap lead">Most of what the players meet is people &mdash; frightened, greedy, kindly, complicit. You
  need to make them on the fly and run them without a stat block most of the time. Here is the quick way, and a
  roster of the common folk for when iron comes out.</p>

  <h2>An NPC in Three Lines</h2>
  <p>To improvise anyone the players turn to talk to, name three things and no more: <strong>a want</strong> (what
  they're after right now), <strong>a tell</strong> (a voice, a habit, a thing they always do), and <strong>a
  secret</strong> (what they're not saying). That is a whole person at the table. Reach for numbers only when the
  conversation turns to violence.</p>

  <h2>Reaction &amp; Morale</h2>
  <p>When it matters how a stranger takes the players, roll a quick reaction: a Will or Presence contest, or a flat
  d20 read against the situation. And when a human foe is bloodied, leaderless, or staring at something no bullet
  fixes, call the morale save from Chapter IV. People in this country mostly want to live; let them act like it.</p>

  <h2>Who Is Actually Out Here</h2>
  <p>A Keeper who peoples the frontier out of the picture-shows will run a thinner country than the real one, and a
  duller game. The West of 1885 is the most mixed ground on the continent, and the mixing is not a footnote &mdash;
  it is the trade, the vocabulary, and the town.</p>
  <p>Start with the work itself. The cattle business is Mexican before it is anything else, and every player at your
  table already speaks its language: the <em>lariat</em> is <em>la reata</em>, the <em>chaps</em> are
  <em>chaparreras</em>, the <em>remuda</em> (the herd of spare mounts), the <em>corral</em>, the <em>rodeo</em>, the <em>mustang</em> out of
  <em>mesteño</em>, and the <em>stampede</em> out of <em>estampida</em>. The vaquero taught the trade to everyone
  who came after him, and on any outfit worth riding for, the segundo &mdash; the man the trail boss actually
  listens to &mdash; is as likely to be a vaquero as not. Roughly one working hand in four on the great drives is
  Black or Mexican, and the outfit that says otherwise is lying to the census.</p>
  <p>Then the rest of the county. Men and women freed by the war came west by the tens of thousands in the exodus of
  '79 and built whole towns of their own on the Kansas and Indian Territory grass, and their sons ride in the Ninth
  and Tenth Cavalry &mdash; the finest horse soldiers in the Territory, and the ones the Army sends first. The
  Chinese laid the Central Pacific through the Sierra, nine men in ten on that grade, and when the rails met they
  went into the mines, the laundries, the market gardens, the fishing boats, and the kitchen of every outfit that
  was lucky enough to hire one; three years back Congress shut the door behind them, and they are still here, and
  they are still building. New Mexican families have held their grant land since long before there was a United
  States to argue with, and are now watching a court in Santa Fe decide whether the paper their great-grandfathers
  signed still means anything. And the peoples who were here first are not one people: the Comanche and the Kiowa
  and the Chiricahua and the Diné and the Lakota and the Nez Perce and the Tohono O'odham want different things,
  speak unrelated languages, and have as little in common with one another as a Georgian has with a Swede.</p>
  <div class="keeper-note"><span class="kn-tag">Keeper's eye</span>None of this needs a speech at your table; a speech would spoil it. It needs <em>names and jobs</em>. The doctor who sets a bone in Act One is Doc Wong, who
  trained in Guangzhou and again in San Francisco and is better than the man the Army sent. The segundo who reads
  the river and says <em>not here, further up</em> is Esperanza Ochoa, and she is right. The blacksmith the party
  will beg for a favor in Act Three is Jubal Deets, late of the Tenth, who has forgotten more about horses than
  anyone in the county ever knew. Give these people competence, a want, and a stake, and the country fills in
  behind them without a word of explanation. The one thing to avoid is the reverse: a face that is only there to be
  a face, or to be a victim, or to deliver a warning and leave. Everybody in the county has business of their own.</div>

  <div class="keeper-note"><span class="kn-tag">On the dark, and whose it is</span>Two entries in the Bestiary
  &mdash; the Wendigo and the Skin-Walker &mdash; come out of Algonquian and Diné belief, and one comes out of
  Mexican and New Mexican belief, the Bruja. These are not folklore anybody made up for a game; they are things
  people hold, and in some cases hold sacred and do not discuss. Run them the way you would run something out of a
  neighbor's church: as terrible and real, never as costume, and never with an Indian or a Mexican character
  attached to explain it to the party. Where a horror comes out of a living tradition, the person who knows most
  about it should be the one the party is lucky to have on their side &mdash; and should be under no obligation to
  tell them everything.</div>

  <h2>Folk of the Frontier</h2>
  {statblock("Townsfolk &amp; Homesteaders", "the people the dark comes for",
    ["<span class='sb-tag'>Defense</span> 11 &nbsp; <span class='sb-tag'>Blood</span> 8 &nbsp; <span class='sb-tag'>Saves</span> +2 / +1 / +2",
     "<span class='sb-tag'>Attacks</span> whatever's to hand +2 (1d6); a shotgun by the door +3 (2d6, close).",
     "<span class='sb-tag'>Note</span> Not fighters. Their role is to be saved, lost, lied to, or revealed as worse than they seemed. One named, liked homesteader in danger is worth more than any monster."]) }

  {statblock("Frontier Lawman", "the star, for what it's worth",
    ["<span class='sb-tag'>Defense</span> 15 &nbsp; <span class='sb-tag'>Blood</span> 24 &nbsp; <span class='sb-tag'>Saves</span> +5 / +5 / +5",
     "<span class='sb-tag'>Attacks</span> revolver +6 (1d8+2); scattergun +6 (2d6+1, close); fists +5 (1d4+2).",
     "<span class='sb-tag'>Note</span> Allies or obstacles. A good marshal is a fragile friend; a bad one is a Tier-II human threat with the town behind him. Either way the law was built for men, and breaks against the dark."]) }

  {statblock("Hired Gun", "a problem with a price",
    ["<span class='sb-tag'>Defense</span> 16 &nbsp; <span class='sb-tag'>Blood</span> 30 &nbsp; <span class='sb-tag'>Saves</span> +6 / +8 / +4",
     "<span class='sb-tag'>Attacks</span> two shots a round +8 (1d8+3, range 80 ft); knife +7 (1d6+3). <strong>The drop:</strong> +2 and a die of damage from surprise or a won standoff.",
     "<span class='sb-tag'>Note</span> A Tier-II/III duelist. Run him with cover and patience; he is what the players' gunslingers fear to meet on a clear street."]) }

  {statblock("Doctor, Preacher &amp; Drifter", "the useful strangers",
    ["<span class='sb-tag'>Defense</span> 12 &nbsp; <span class='sb-tag'>Blood</span> 14 &nbsp; <span class='sb-tag'>Saves</span> +3 / +3 / +4",
     "<span class='sb-tag'>The Doctor</span> mends Blood and may know what the cursed man is dying of.",
     "<span class='sb-tag'>The Preacher</span> may truly hold a line against the dark &mdash; or may be hollow (Ch. V).",
     "<span class='sb-tag'>The Drifter</span> knows the country, has seen the thing before, and will not say all of it.",
     "<span class='sb-tag'>Note</span> These three are how you feed the players what they need to survive &mdash; and how you lie to them. Trust each at your peril."]) }

  <h2>The Town as a Character</h2>
  <p>Once a campaign settles into a place, the town stops being a backdrop and becomes a character in its own right
  &mdash; one the players will fight to save, and one the dark will use against them. Build it the way you build a
  person: with a want, a tell, and a secret. A town that wants the railroad will look the other way at a great deal;
  a town with a secret in its boot-hill will close ranks against questions. Give it a few standing fixtures and it
  runs itself:</p>
  <ul>
    <li><strong>A heart &mdash; the place they gather.</strong> The saloon, the church, the store. This is where the
    players take the town's temperature and where you stage the public scene: the accusation, the town meeting, the
    funeral. When the heart goes wrong &mdash; the saloon gone silent, the church locked &mdash; the players feel it.</li>
    <li><strong>A handful of faces.</strong> Four or five named locals with wants and tells (three lines each, above)
    are a whole town. Reuse them; let the players learn them. A named barkeep who dies in Act Three is worth more than
    a massacre of strangers.</li>
    <li><strong>A pressure already on it.</strong> Debt, drought, a closing mine, a land-grab, an old feud. The dark
    rarely arrives to a happy town &mdash; it moves into the cracks already there, and the mundane pressure is what
    makes the supernatural one bite. The bank foreclosing is half the horror before a single corpse walks.</li>
    <li><strong>A way it can be lost.</strong> Know what it looks like when the players fail this town &mdash; emptied,
    burned, hollowed, gone over to the dark. A town that can fall is a town worth saving, and the threat of its
    falling is most of why the players stay.</li>
  </ul>

  <h2>Factions &amp; the Pull of the Country</h2>
  <p>A place with more than one power in it runs itself, because the powers push against each other and the players
  are caught in the middle. You don't need many &mdash; two or three standing interests turn a static town into a
  board in motion. Give each a <strong>want</strong>, a <strong>lever</strong> (what it can do to get its way), and a
  <strong>line</strong> (what it won't do &mdash; until it does):</p>
  <ul>
    <li>The <strong>cattle baron</strong> who owns the land and the law and wants the squatters gone &mdash; lever:
    hired guns and held notes; line: he won't burn folk out, until the dark gives him a reason.</li>
    <li>The <strong>church</strong> that knows what's in the old mission ground and wants it left buried &mdash; lever:
    the trust of the town; line: it won't lie outright, but it will let you believe wrong.</li>
    <li>The <strong>railroad</strong> that wants the route cleared and doesn't care what's in the way &mdash; lever:
    money and outside men; line: none worth the name, which is its own kind of horror.</li>
  </ul>
  <p>Set the players among these and every choice has a cost on some other ledger. Help the baron and the church turns
  cold; trust the church and the railroad moves against you. The dark's genius is to be the secret behind one of them,
  so that the faction the players sided with was the wrong one all along.</p>
  <div class="keeper-note"><span class="kn-tag">Keeper's eye</span>Don't script how the factions resolve &mdash; let
  the players' choices tip the board, and play each power honestly toward its want. A faction that reacts to what the
  players actually do, rather than waiting in a box for its scene, is the difference between a living country and a
  diorama. Move them between sessions, off-screen, and let the players walk back into a town that changed while they
  were gone.</div>
</section>
"""

# ---------------------------------------------------------------- IX. FIRST RECKONING (adventure)
CH9 = f"""<!-- IX -->
<section class="page" id="firstreckoning">
  {runhead('IX. A First Reckoning')}
  <h1 class="chapter">IX. A First Reckoning</h1>
  <p class="chapter-sub">A complete first night, built to teach the game while it scares the table.</p>
  <div class="divider"></div>
  <p class="dropcap lead"><em>The Salt at Coffin Wells</em> is a one-session adventure for a fresh party of 1st-level
  characters. It is built to do the thing a first session most often fails to do: open as an honest western, turn the
  wrong note slowly, and teach Nerve, the Mark, and the gun all in one night &mdash; with every monster you need drawn
  from the Bestiary so you never have to leave this book. Read it once; run it loose.</p>

  <div class="box">
    <h4>The Truth (for the Keeper alone)</h4>
    <p>Coffin Wells is a dying cattle town. Six weeks ago its banker, <strong>Josiah Vane</strong>, ruined and
    desperate, dug up the wrong grave on the old mission ground east of town &mdash; the grave of something the
    Spanish padres had staked and salted a century back. He meant to rob it of rumored silver. He woke a
    <strong>Nightwalker</strong> instead, and struck a bargain to save his own neck: blood for the town, fed to it
    quietly, in trade for being spared and made rich.</p>
    <p>The "fever" taking the outlying homesteads is the Nightwalker
    feeding, and the freshly dead are beginning to rise as <strong>Risen</strong>. Vane is in too deep to stop and
    too afraid to confess. <strong>The clock:</strong> the Nightwalker grows stronger each night it feeds; in four
    nights it will be past any stake, and Coffin Wells will be a town of the dead.</p>
  </div>

  <h2>The Hook</h2>
  <p>Any reason that gets the party to Coffin Wells serves &mdash; a job driving cattle, a name on a wanted dodger, a
  letter from kin gone quiet, simple thirst at the end of a long ride. They arrive at dusk to a town with its
  shutters already closed against the dark, and a marshal who wants them gone by morning.</p>

  <h2>Act One &mdash; The Ordinary West</h2>
  <p>Let it be a real town for a scene. The saloon, the wary barkeep, the talk of "fever" out at the homesteads, the
  banker Vane buying a round and steering the talk away. Plant the wrong notes gently: the new graves at the
  boot-hill are <em>disturbed</em>; the dogs won't go east; a homesteader's wife says her husband came home three
  days after they buried him, and won't say more. <strong>No monster yet.</strong> End the act when the party rides
  out to the Pell homestead to look into the fever &mdash; the marshal's reluctant errand, or their own curiosity.</p>

  <h2>Act Two &mdash; The Wrong Note Answers</h2>
  <p>The Pell place is dark, the door open, the supper cold on the table. Here the players meet the dead getting up:
  <strong>2&ndash;3 Risen</strong> (Tier I), one of them the buried husband. <strong>This is the first Dread Check</strong>
  &mdash; DC 16, 1d6 Nerve &mdash; and their first lesson that some foes do not stop. Pitch it as a fair, frightening
  fight they can win with fire and a cool head; let someone learn what salt and a shotgun do. In the cellar they find
  the wife, bled and half-turned, and a choice that teaches the Cursed Man's lesson in miniature: a mercy, or a hope
  that costs them. A scrap of mission silver in the husband's pocket points east, to the old church.</p>

  <div class="keeper-note"><span class="kn-tag">Teaching the engine</span>This is the act where Nerve becomes real to
  the players. Call the Dread Check out loud, name the save, let a failure sting. If someone breaks, lean in briefly,
  then hand control back. By the end of Act Two the party should be frayed, low on Nerve, and starting to understand
  that this is not the western they thought they rode into.</div>

  <h2>Act Three &mdash; The Reckoning</h2>
  <p>The trail leads to the ruined mission and the opened grave. Vane is here at the climax &mdash; come to feed it,
  or to beg it, or dragged by the players' questioning &mdash; and the <strong>Nightwalker</strong> (Tier III) is the
  night's monster. Run the confrontation in the dark of the church: the Dread regard, the cold, the thing climbing
  the walls. The players cannot simply out-shoot it; they must <em>learn its weakness in the moment</em> &mdash; the
  stake, the salt, the coming dawn &mdash; from the padres' carvings on the wall, a clue in Vane's stolen papers, or
  the drifter's half-told warning if you planted one. Give them the tools and let them put the pieces together under
  fire. That solved puzzle, won at the edge of breaking, is the night's triumph.</p>

  <h2>The Box</h2>
  <p>However it ends, give it weight. If they stake and burn the thing and salt the grave, Coffin Wells lives, and
  the players have their first legend &mdash; and a banker to hang or pity. If Vane gets away, or the dawn comes too
  late, leave a thread: a town half-saved, a survivor who saw too much, a debt the dark considers unpaid. And whatever
  happened to the Pell wife in that cellar should follow at least one character into the next night's dreams. That is
  how you end a first reckoning: with the floor dropped, and the players already wondering what else the country has
  been waiting in the quiet to show them.</p>

  <div class="box">
    <h4>Scaling the Night</h4>
    <ul>
      <li><strong>A bigger or bolder party:</strong> add Risen in Act Two, give Vane a pair of desperate Road Agents
      as hired guards in Act Three, and let the Nightwalker open with an ambush.</li>
      <li><strong>A smaller or greener party:</strong> fewer Risen, and let the church carvings spell out the
      weakness plainly. The Nightwalker can be <em>fed and slow</em> the first night &mdash; Defense 16, no regard &mdash;
      if the party reaches it early.</li>
      <li><strong>If the dice turn cruel:</strong> the dawn is always one scene away, and sunlight is the great
      equalizer. A party pinned and dying can be saved by the sky going gray &mdash; at the cost of the thing escaping
      to be hunted another night.</li>
    </ul>
  </div>
</section>
"""

# ---------------------------------------------------------------- APPENDIX: THE SCREEN
APX = f"""<!-- APPENDIX -->
<section class="page" id="screen">
  {runhead('Appendix: The Keeper&rsquo;s Screen')}
  <h1 class="chapter">Appendix: The Keeper's Screen</h1>
  <p class="chapter-sub">Every number you reach for, on one spread.</p>
  <div class="divider"></div>

  <div class="twocol">
    <h3>The DC Ladder</h3>
    <p>Trivial 10 &middot; Easy 13 &middot; Average 15 &middot; Hard 18 &middot; Very Hard 20 &middot; Punishing 25
    &middot; Beyond 30. Against a living thing, use its Defense or save instead.</p>

    <h3>The Four Degrees</h3>
    <p>Beat the DC by 10 (or nat 20) = critical success. Miss by 10 (or nat 1) = critical failure. Nat 20 / nat 1
    shift one step. Narrate all four.</p>

    <h3>Dread Checks (Will save)</h3>
    <p>Corpse, murdered &mdash; DC 10, lose 1.<br>
    Mutilation &mdash; DC 13, lose 1d4.<br>
    Walking dead, true haunting &mdash; DC 16, lose 1d6.<br>
    The deep dark &mdash; DC 20, lose 1d10.<br>
    A world-unmaking truth &mdash; DC 25, 1d10 + Affliction.<br>
    Crit success: no loss, steeled. Crit fail: lose + Frightened 1.</p>
  </div>

  <div class="twocol">
    <h3>Nerve &amp; Breaking</h3>
    <p>Max Nerve = RES score + level; full each session. At 0: roll the Break, take an Affliction, stay dangerous in
    play. Recover only in true safety (1d4), never near the dark.</p>

    <h3>The Mark (6 steps)</h3>
    <p>Grant for: breaking utterly (the rare roll), reaching for the Old Dark, surviving the deep dark changed. Never
    for a bad roll. At 6, the dark owns them.</p>

    <h3>Tainted Ground</h3>
    <p>Save every 3 days (Fort, then Will). Soured DC 13 &middot; Blighted DC 16 &middot; Unhallowed DC 20. Fail =
    +1 step (crit = +2). Wards &amp; salt ease by 2.</p>

    <h3>Grit</h3>
    <p>3 per character per session; award more for courage, character, or a line that stops the table. Spent to
    add 1d6, reroll, steady a fright, stay on your feet at 0 Blood, or soften a critical failure.</p>
  </div>

  <div class="twocol">
    <h3>Threat by Tier</h3>
    <p>I: Def 13 / Atk +4 / Blood 12.<br>
    II: 15 / +6 / 22.<br>
    III: 17 / +9 / 40.<br>
    IV: 20 / +13 / 70.<br>
    V: 23 / +17 / 110.<br>
    Fair fight &asymp; party level = twice the Tier. Budget 4 points/PC; even foe 4, mook 1, standout 8.</p>

    <h3>d12 &mdash; An Omen of the Dark</h3>
    <p>1 birds gone silent &middot; 2 a cold that lamps won't touch &middot; 3 milk soured, water iron &middot; 4 a
    dog that won't stop watching one door &middot; 5 a shadow a beat behind its man &middot; 6 a child's rhyme no one
    taught &middot; 7 cattle dead untouched &middot; 8 a grave clean and open &middot; 9 the wrong number at the
    supper table &middot; 10 a reflection that lags &middot; 11 salt that won't pour &middot; 12 your own name,
    called from the dark.</p>

    <h3>d10 &mdash; A Frontier Complication</h3>
    <p>1 the powder's wet &middot; 2 a horse goes lame &middot; 3 a stranger's already here &middot; 4 the law wants
    a word &middot; 5 a storm rolls in &middot; 6 someone's been followed &middot; 7 the bridge is out &middot; 8 a
    debt comes due &middot; 9 the wrong man overheard &middot; 10 it's already too late for one of them.</p>
  </div>

  <div class="twocol">
    <h3>d20 &mdash; A Name for Anyone</h3>
    <p>1 Amos &middot; 2 Cassius &middot; 3 Eb &middot; 4 Halloran &middot; 5 Jensen &middot; 6 Coyle &middot; 7 Ashby
    &middot; 8 Vane &middot; 9 Tuttle &middot; 10 Pell &middot; 11 Devereaux &middot; 12 Calla &middot; 13 Stroud
    &middot; 14 Mercy &middot; 15 Obadiah &middot; 16 Sull &middot; 17 Wren &middot; 18 Hettie &middot; 19 Lafe
    &middot; 20 the one they will not name</p>

    <h3>d20 &mdash; A Name for the Rest of the County</h3>
    <p>Roll here as often as above &mdash; oftener, in the border counties and the rail towns (Ch. VIII).<br>
    1 Esperanza Ochoa &middot; 2 Jubal Deets &middot; 3 Wong Kai-lun &middot; 4 Refugio Baca &middot; 5 Delphia
    Kearse &middot; 6 Ah Sing &middot; 7 Trinidad Mestas &middot; 8 Isham Boyd &middot; 9 Soledad Herrera
    &middot; 10 Lum Fong &middot; 11 Prospero Vigil &middot; 12 Naomi Pettiford &middot; 13 Chee Yee &middot;
    14 Casimiro Luján &middot; 15 Hosea Tolliver &middot; 16 Altagracia Sandoval &middot; 17 Willa Redd
    &middot; 18 Yuen Sook-ping &middot; 19 Eleuterio Padilla &middot; 20 the one who has not given it yet</p>

    <h3>d12 &mdash; A Name Out of the Nations</h3>
    <p>Ask whose country you are in before you roll &mdash; these are seven unrelated peoples, not one.<br>
    1 Quanah Parker's cousin, Comanche &middot; 2 Ha-o-zinne, Chiricahua &middot; 3 Little Elk, Kiowa &middot;
    4 Hastiin Tso, Diné &middot; 5 Mary Sits-Alone, Crow &middot; 6 Standing Bear's nephew, Ponca &middot;
    7 Yellow Robe, Lakota &middot; 8 Josefa Antone, Tohono O'odham &middot; 9 Two Kettles, Cheyenne &middot;
    10 Isidro Naranjo, of Taos &middot; 11 Wetatonmi's daughter, Nez Perce &middot; 12 a scout, and he has an
    Army name and a real one</p>

    <h3>d12 &mdash; A Town's Wrong Note</h3>
    <p>1 no children seen &middot; 2 the church is locked &middot; 3 too many fresh graves &middot; 4 all owe the same
    man &middot; 5 a bell rung nightly &middot; 6 the well's gone bad &middot; 7 a stranger they all defer to &middot;
    8 no dogs anywhere &middot; 9 a name no one will say &middot; 10 the doctor left sudden &middot; 11 salt over every
    door &middot; 12 they were expecting you</p>

    <h3>d10 &mdash; Why They're Out Here</h3>
    <p>1 a job gone quiet &middot; 2 a name on a dodger &middot; 3 kin stopped writing &middot; 4 driving stock through
    &middot; 5 running from the last town &middot; 6 a map off a dying man &middot; 7 the railroad sent them &middot;
    8 a debt to collect &middot; 9 a grave to find &middot; 10 nowhere left to be</p>

    <h3>d8 &mdash; What the Locals Whisper</h3>
    <p>1 it only takes the wicked <em>(false)</em> &middot; 2 the old church ground is salted for a reason &middot;
    3 don't drink from the east well &middot; 4 the banker knows more than he says <em>(true)</em> &middot; 5 a child
    saw it and won't speak &middot; 6 it can't cross running water &middot; 7 the last lawman rode out and never came
    back &middot; 8 there's a way to end it, but it costs</p>
  </div>

  <div class="divider"></div>
  <p class="note" style="text-align:center;">Blood &amp; Grit &middot; The Keeper's Book &middot; Run it slow. Bleed
  the Nerve slower. Salt the grave.</p>
</section>
"""

# ---------------------------------------------------------------- X. SECOND RECKONING (adventure)
CH10 = f"""<!-- X -->
<section class="page" id="secondreckoning">
  {runhead('X. A Second Reckoning')}
  <h1 class="chapter">X. A Second Reckoning</h1>
  <p class="chapter-sub">A second first night &mdash; quieter, crueler, and won with the eyes, not the gun.</p>
  <div class="divider"></div>
  <p class="dropcap lead"><em>A Face Not His Own</em> is a one-session adventure for 1st&ndash;2nd level characters, and a
  deliberate change of key from <em>The Salt at Coffin Wells</em>. Where the first reckoning is a siege you shoot your
  way out of, this is a locked-room of paranoia where the players cannot win by drawing first &mdash; the monster is
  already inside, already wearing a friend's face, and the only way out is to <strong>see</strong> the wrong thing
  before it sees its chance. Run it to teach a hard lesson: in this country, the gun is not always the answer, and
  sometimes the most dangerous figure at the table is the one smiling back.</p>

  <div class="box">
    <h4>The Truth (for the Keeper alone)</h4>
    <p>Saltlick Station is a lonely stage relay a hard day from anywhere. Two weeks ago a <strong>Skin-Walker</strong>
    (Tier III, Ch. V) killed the hostler, <strong>Eli Stroud</strong>, and put on his skin. It has been thinning the
    travelers who stop here ever since, learning to pass for a man &mdash; and it is getting good at it.</p>
    <p>Tonight a
    blue norther closes the trail and strands the party at the station overnight, alongside a handful of other
    souls. The thing means to take them one at a time through the long dark, and to ride out at dawn wearing whichever
    new face is freshest. <strong>The clock:</strong> it acts once a night-watch &mdash; isolating, mimicking, killing
    &mdash; and by the gray of dawn the storm lifts and it intends to be gone. It will not stand and fight unless
    cornered and exposed; a stand-up brawl with it is how a low party dies, and you should let the fiction warn them.</p>
  </div>

  <h2>The Hook</h2>
  <p>The party is on the trail &mdash; carrying mail, chasing a name, or just riding through &mdash; when the sky goes
  the color of a bruise and the wind picks up teeth. Saltlick Station is the only roof for twenty miles. They make it
  in as the storm closes the world down to white and wind. The doors are barred behind them. No one is leaving till
  it breaks.</p>

  <h2>The Souls Under the Roof</h2>
  <p>Besides the party, give the station a handful of NPCs (Ch. VIII numbers) &mdash; one of whom is the thing. Name
  them, give each a want and a tell, and let the players get comfortable before anything goes wrong:</p>
  <ul>
    <li><strong>"Eli," the hostler</strong> &mdash; easy, helpful, knows the horses by name. <em>This is the
    Skin-Walker.</em> Play him warm and useful; let the players come to like him.</li>
    <li><strong>Mrs. Pruitt</strong>, who cooks and runs the place &mdash; sharp, tired, has noticed Eli's "been
    off" since his fever but can't say how.</li>
    <li><strong>Foss</strong>, a drummer with a wagon of patent tonics &mdash; nervous, talkative, the first to
    panic and the first to accuse.</li>
    <li><strong>Calla</strong>, a quiet traveler with a good gun and a hard eye &mdash; suspicious of everyone,
    the party included; a useful red herring.</li>
  </ul>

  <h2>Act One &mdash; The Wrong Note Among Friends</h2>
  <p>Let the first hour be ordinary and even warm: a fire, a meal, the storm shut outside. Then plant the tells, one
  at a time, on <strong>secret</strong> Notice and Lore (Occult) checks (Ch. II) so the players are never sure what's
  real:</p>
  <ul>
    <li>The station dog will not come inside while Eli is in the room, and watches him without blinking.</li>
    <li>The horses go wall-eyed and scream when Eli enters the barn, though he's gentled them for years.</li>
    <li>By firelight, for half a breath, Eli's eyes catch the light the way an animal's do.</li>
    <li>Eli misremembers a thing the real Eli would know cold &mdash; or knows a thing he shouldn't.</li>
    <li>The cracked mirror by the door shows his reflection a beat behind him, once, if someone's watching.</li>
  </ul>
  <div class="keeper-note"><span class="kn-tag">Teaching the engine</span>This is the act of <em>doubt</em>. Roll
  the tells in secret so a failed check leaves the player unsure whether they saw nothing or merely missed it. No
  Dread Check yet &mdash; save it. The horror here is social, not supernatural: the slow certainty that one of these
  faces is wrong, and the cost of guessing.</div>

  <h2>Act Two &mdash; The First Taking</h2>
  <p>On the deepest watch of the night, the thing makes its move: someone goes out to the barn for wood or a horse and
  does not come back &mdash; or is found at the edge of the lamplight, wrong. <strong>This is the first Dread Check</strong>
  (DC 16, 1d6 &mdash; the walking dead's tier of wrongness, for a body left as the Skin-Walker leaves them). Now the
  paranoia turns to fear. The thing's game is to sow doubt: it mimics a voice from the dark, apes another's manner,
  points the finger first. The players must put the tells together and name the monster &mdash; and the awful turn of
  the screw is that they might name the wrong soul, and do murder, and learn the truth only after. Let accusations
  have weight. Let Calla nearly get shot. The night should cost them trust before it costs them blood.</p>

  <h2>Act Three &mdash; The Tell Made Plain</h2>
  <p>The climax is not a slugging match &mdash; a Tier-III Skin-Walker will kill a green party in a fair fight, and the
  fiction should make that plain (let it shrug off a solid hit early, move wrong, be <em>fast</em>). The win is to
  <strong>force the tell into the open</strong> and then <strong>ward or break</strong> the thing: hold it before the
  mirror so all can see what wears Eli's face; drag it into the firelight; lay the line of <strong>ash and bone</strong>
  across the threshold it cannot cross; and finish it with a bullet that has been <strong>prayed over or cast of
  silver</strong> (the Player's Book, Ch. X, and the Bestiary entry). Give the players the pieces &mdash; Mrs. Pruitt's
  grandmother's warding rhyme, a silver crucifix, a box of blessed shot in the strongbox &mdash; and let them assemble
  the answer under pressure. A monster <em>exposed and cornered</em> is killable; a monster fought blind is not. That
  difference is the whole adventure.</p>

  <h2>The Box</h2>
  <p>If they expose it and end it, the storm breaks toward dawn and the survivors ride out into a clean cold morning
  &mdash; never quite sure, after this, of a stranger's face in poor light. If it slips away into the white, then it
  is out there still, wearing someone the players trusted, and it knows their faces now. Either way, leave one small
  wrong note at the end &mdash; a reflection that lags, a dog that growls at a friend &mdash; and let the table wonder.</p>

  <div class="box">
    <h4>Scaling the Night</h4>
    <ul>
      <li><strong>A bolder party:</strong> let the Skin-Walker take a second NPC, and have it wear a <em>player's</em>
      absent character or a beloved face in the finale, so the killing blow costs something.</li>
      <li><strong>A greener party:</strong> stack the tells thick and obvious, hand them the warding rhyme early, and
      let the cornered thing be already wounded from its last kill (start it bloodied). The mirror alone can drive it
      out if they think to use it.</li>
      <li><strong>If the dice turn cruel:</strong> the storm is the clock and the mercy both &mdash; a party that
      barricades well and survives till the norther breaks can drive the thing out into the dawn rather than kill it,
      and live to hunt it another night.</li>
    </ul>
  </div>
</section>
"""

# ---------------------------------------------------------------- XI. THE KEEPER'S YEAR
CH11 = f"""<!-- XI -->
<section class="page" id="keepersyear">
  {runhead('XI. The Keeper&rsquo;s Year')}
  <h1 class="chapter">XI. The Keeper's Year</h1>
  <p class="chapter-sub">Carrying the dark from a single night to a saga, and three to set you riding.</p>
  <div class="divider"></div>
  <p class="dropcap lead">A one-night scare you now know how to run. The two reckonings before this chapter taught the
  siege and the locked room; the rest of this book taught the engine under them. This chapter is the long view &mdash;
  how to take all of it and run not a night but a <em>year</em>, where the country's wrongness has a shape, the
  players have a stake, and the dark they close the door on in the spring is the same dark that comes back in the fall
  wearing a worse face. Here is the frame, the rhythm, and three campaigns ready to ride.</p>

  <h2>The Three Frames</h2>
  <p>Most Blood &amp; Grit campaigns sit in one of three shapes. Pick the one that fits your table and the dark almost
  organizes itself.</p>
  <ul>
    <li><strong>The Haunted County.</strong> The players root in one place &mdash; a town, a valley, a stretch of
    trail &mdash; and defend it across a year as the dark closes in from every side. Strength: the town becomes a
    character they bleed to save (Ch. VIII), and every loss lands. Run it when your table wants attachment, stakes,
    and a place to call theirs.</li>
    <li><strong>The Long Trail.</strong> The players ride, drifting town to town, each a self-contained reckoning, with
    a single thread pulling them onward &mdash; a name, a debt, a thing they're chasing or that's chasing them. Strength:
    variety and momentum; you can run nearly any one-shot as a stop on the road. Run it when your table likes the new
    and the open, and a campaign that's a journey, not a siege.</li>
    <li><strong>The Closing Circle.</strong> The players know, from early, what the great dark is &mdash; the Patron
    waking, the cult's rite, the Wound widening &mdash; and the whole campaign is the race to close it before it
    finishes. Strength: a clear, mounting dread with a real ending in sight. Run it when your table wants a story with
    a spine and a climax they can see coming for them.</li>
  </ul>

  <h2>The Rhythm of a Year</h2>
  <p>Whatever the frame, the year breathes in arcs &mdash; three to five sessions each, a wrong note to a reckoning &mdash;
  and the arcs stack into seasons. Hold to a shape and the campaign paces itself:</p>
  <ul>
    <li><strong>The Opening (1&ndash;2 arcs).</strong> Establish the ordinary west, the place and people, the first
    taste of the dark. The players learn the engine and put down roots. End it with a reckoning that reveals there's
    something <em>behind</em> the first monster.</li>
    <li><strong>The Deepening (2&ndash;3 arcs).</strong> The pattern emerges; the same dark hand shows behind separate
    horrors. Mark and Taint climb. The players invest, lose someone or something, and start to grasp the shape of the
    larger wrong. Raise the stakes each arc.</li>
    <li><strong>The Reckoning (1&ndash;2 arcs).</strong> The great dark moves openly. Old threads pay off, the recurring
    hand is met at last, and the players spend everything they've built to close the door for good &mdash; at a price.
    End it. A campaign that can end, and does, is a story; one that can't is a treadmill (Ch. VII).</li>
  </ul>
  <div class="keeper-note"><span class="kn-tag">The throughline</span>Whatever frame you choose, run one thread the
  whole way &mdash; a Patron, a cult, a curse, a Marked soul climbing. Each session is a symptom; the campaign is the
  disease, slowly named. Drop a clue toward the throughline in nearly every night, even the standalone ones, and by the
  end the players will feel the whole year was one story tightening &mdash; because it was.</div>

  <h2>Three Campaigns, Ready to Ride</h2>
  <p>Each of these is a year in a paragraph &mdash; a frame, a throughline, a clock, and the door that closes it. Take
  one whole, or strip it for parts.</p>

  <div class="box">
    <h4>The Salt Valley &mdash; a Haunted County</h4>
    <p><strong>The frame:</strong> the players settle in Saltlick Valley, a hard ranching country ringed by old mission
    ground. <strong>The throughline:</strong> a century ago the padres staked and salted a Patron's reaching hand into
    the valley floor; the railroad's blasting has cracked the seal, and the dark is leaking back, one homestead at a
    time. <strong>The clock:</strong> each season the unhallowed ground spreads a ranch further, the dead get bolder,
    and the valley's folk turn on each other (the Drought-Bringer's despair, made political). <strong>The door:</strong>
    the players must find what the padres did, pay the price to seal the hand again &mdash; and decide what the railroad,
    and the future, is worth. <strong>Bestiary:</strong> Risen and the Gravecaller early; the Veinwork in the railroad
    cut; the Servant of the Deep Dark at the seal; the Tallyman for whoever bargained.</p>
  </div>

  <div class="box">
    <h4>The Name in the Dust &mdash; a Long Trail</h4>
    <p><strong>The frame:</strong> the players ride a circuit of frontier towns, hunting (or hunted by) a man who can't
    be killed wrong. <strong>The throughline:</strong> the Deathless Gun is collecting something across the territory
    &mdash; a name, a debt, a string of fair duels &mdash; and every town he's passed through has a fresh grave and a
    piece of the truth. <strong>The clock:</strong> he's always one town ahead, and what he's gathering nears completion
    with each duel he wins. <strong>The door:</strong> the players learn his bargain and its terms, and someone among
    them must meet him fair, alone, in the open &mdash; the one way he can fall. <strong>Bestiary:</strong> a different
    reckoning each town (the Hexed Beast, the Hanging Judge, the Mesmerist), with the Deathless Gun's shadow over all,
    and the Crossroads Man behind the bargain he made.</p>
  </div>

  <div class="box">
    <h4>The Widening Dark &mdash; a Closing Circle</h4>
    <p><strong>The frame:</strong> from the first night, the players know a Wound is opening in the deep country and
    the sky is starting to look back. <strong>The throughline:</strong> a cult of the Open Eye is working, season by
    season, to tear the veil wide &mdash; and the players have until it's done. <strong>The clock:</strong> a six-step
    rite across the campaign; each arc the players can disrupt a step, or arrive too late and watch it turn. <strong>The
    door:</strong> reach the Wound before it widens past closing, and pay what closing it costs &mdash; a rite undone, a
    sacrifice given right, a name struck out. <strong>Bestiary:</strong> the Flock and the Hollow Prophet as the cult's
    body; the Pallid Herald and the Faceless Rider as its heralds; the Wound in the World and the Eye Between Stars at
    the end of everything.</p>
  </div>

  <div class="keeper-note"><span class="kn-tag">A last word</span>You will run more of this game than you plan and less
  than you hope, and that is the way of every table. Don't hoard your best ideas for a someday campaign &mdash; spend
  them. Let the players surprise you, and surprise them back. Keep the watch, bleed the Nerve slow, and salt the grave.
  The country was here before them and will be here after, and for a year you get to be its voice in the dark. Make it
  worth the night.</div>
</section>
"""

# ---------------------------------------------------------------- XII. THE COUNTRY IN YOUR POCKET
CH12 = f"""<!-- XII -->
<section class="page" id="pocket">
  {runhead('XII. The Country in Your Pocket')}
  <h1 class="chapter">XII. The Country in Your Pocket</h1>
  <p class="chapter-sub">Rollable tables for the moment the players ride somewhere you haven't built yet.</p>
  <div class="divider"></div>
  <p class="dropcap lead">Every Keeper meets the moment: the players turn their horses off the road you prepared and
  ask what's over the next rise. This chapter is for that moment. Roll, read, and ride on &mdash; a town in three
  rolls, a face in four, a rumor, a night on the trail, a find, an omen. Nothing here needs preparation, and everything
  here is a seed you can grow later if the players take root in it.</p>

  <h2>A Town in Three Rolls</h2>
  <p>Roll a d20 twice for the name (front, then back), then a d12 each for what ails it and what it hides.</p>
  <table>
    <thead><tr><th>d20</th><th>Front</th><th>Back</th></tr></thead>
    <tbody>
      <tr><td>1</td><td>Dry</td><td>Creek</td></tr>
      <tr><td>2</td><td>Salt</td><td>Wells</td></tr>
      <tr><td>3</td><td>Coffin</td><td>Gulch</td></tr>
      <tr><td>4</td><td>Providence</td><td>Flats</td></tr>
      <tr><td>5</td><td>Bitter</td><td>Springs</td></tr>
      <tr><td>6</td><td>Lament</td><td>Crossing</td></tr>
      <tr><td>7</td><td>Redemption</td><td>Ridge</td></tr>
      <tr><td>8</td><td>Widow's</td><td>Hollow</td></tr>
      <tr><td>9</td><td>Gallows</td><td>Bend</td></tr>
      <tr><td>10</td><td>Mercy</td><td>Station</td></tr>
      <tr><td>11</td><td>Rattle</td><td>Rock</td></tr>
      <tr><td>12</td><td>Perdition</td><td>Fork</td></tr>
      <tr><td>13</td><td>Cinder</td><td>Camp</td></tr>
      <tr><td>14</td><td>Hope</td><td>Landing</td></tr>
      <tr><td>15</td><td>Blackwater</td><td>Draw</td></tr>
      <tr><td>16</td><td>Furnace</td><td>Mesa</td></tr>
      <tr><td>17</td><td>Lonesome</td><td>Butte</td></tr>
      <tr><td>18</td><td>Grave</td><td>City (pop. 61)</td></tr>
      <tr><td>19</td><td>Judgment</td><td>Junction</td></tr>
      <tr><td>20</td><td>Last</td><td>Chance</td></tr>
    </tbody>
  </table>
  <table>
    <thead><tr><th>d12</th><th>What ails it (plain to see)</th><th>What it hides (dig for it)</th></tr></thead>
    <tbody>
      <tr><td>1</td><td>The mine is played out and the men aren't leaving</td><td>The last shift never came up, and no one went looking</td></tr>
      <tr><td>2</td><td>Drought; the wells are down to mud</td><td>The one sweet well belongs to a man who prays to something for it</td></tr>
      <tr><td>3</td><td>The railroad is coming through &mdash; or past</td><td>The survey line runs through ground the town swore never to open</td></tr>
      <tr><td>4</td><td>Stock dying; wolves blamed</td><td>The stock is drained, not eaten, and the wolves left weeks ago</td></tr>
      <tr><td>5</td><td>A feud between the two big families</td><td>Both patriarchs answer to the same buried bargain</td></tr>
      <tr><td>6</td><td>The church burned last spring</td><td>The congregation set the fire themselves, and won't say why</td></tr>
      <tr><td>7</td><td>Too many fresh graves for a town this size</td><td>Fewer bodies in them than headstones over them</td></tr>
      <tr><td>8</td><td>The marshal is a drunk or a coward</td><td>He saw what runs this town and was left alive to keep order anyway</td></tr>
      <tr><td>9</td><td>Nobody will ride the north road after dark</td><td>Someone feeds the north road, on a schedule, to keep it satisfied</td></tr>
      <tr><td>10</td><td>A revival tent has half the town in it every night</td><td>The preacher's sermons are true, word for word, and getting truer</td></tr>
      <tr><td>11</td><td>Children have gone missing &mdash; two this season</td><td>They come back, eventually. Changed. The town pretends not to see.</td></tr>
      <tr><td>12</td><td>The town is emptying; wagons leave weekly</td><td>The ones who leave are never heard from again, and the road east shows no tracks</td></tr>
    </tbody>
  </table>

  <h2>A Face in Four Rolls</h2>
  <p>A d20 for the given name, a d20 for the surname, a d12 for what they want, a d12 for their tell.</p>
  <table>
    <thead><tr><th>d20</th><th>Given</th><th>Surname</th><th>d20</th><th>Given</th><th>Surname</th></tr></thead>
    <tbody>
      <tr><td>1</td><td>Amos</td><td>Ashford</td><td>11</td><td>Lucinda</td><td>McCready</td></tr>
      <tr><td>2</td><td>Beulah</td><td>Blackwood</td><td>12</td><td>Merritt</td><td>Nye</td></tr>
      <tr><td>3</td><td>Cassius</td><td>Cole</td><td>13</td><td>Nora</td><td>Oakes</td></tr>
      <tr><td>4</td><td>Dorothea</td><td>Danvers</td><td>14</td><td>Obadiah</td><td>Pruitt</td></tr>
      <tr><td>5</td><td>Ezekiel</td><td>Eastman</td><td>15</td><td>Prudence</td><td>Quirk</td></tr>
      <tr><td>6</td><td>Flora</td><td>Fenn</td><td>16</td><td>Roscoe</td><td>Reyes</td></tr>
      <tr><td>7</td><td>Gideon</td><td>Grady</td><td>17</td><td>Salome</td><td>Slade</td></tr>
      <tr><td>8</td><td>Hattie</td><td>Holloway</td><td>18</td><td>Thaddeus</td><td>Tanner</td></tr>
      <tr><td>9</td><td>Isaiah</td><td>Ives</td><td>19</td><td>Una</td><td>Vane</td></tr>
      <tr><td>10</td><td>Josephine</td><td>Krieg</td><td>20</td><td>Wilbur</td><td>Whitlock</td></tr>
    </tbody>
  </table>
  <table>
    <thead><tr><th>d12</th><th>What they want</th><th>Their tell</th></tr></thead>
    <tbody>
      <tr><td>1</td><td>Money, plainly and now</td><td>Counts things &mdash; coins, exits, your party</td></tr>
      <tr><td>2</td><td>To leave this town and can't</td><td>Always faces the door</td></tr>
      <tr><td>3</td><td>Their child back &mdash; from debt, drink, or the dark</td><td>Wears something of the child's, worried smooth</td></tr>
      <tr><td>4</td><td>Revenge dressed up as justice</td><td>Smiles only when someone else is hurting</td></tr>
      <tr><td>5</td><td>To confess something to anyone safe</td><td>Starts sentences and buries them</td></tr>
      <tr><td>6</td><td>Protection, and won't say from what</td><td>Salt in every pocket; checks windows at dusk</td></tr>
      <tr><td>7</td><td>To be believed, at last</td><td>Talks too fast, brings written proof no one reads</td></tr>
      <tr><td>8</td><td>The party gone by morning</td><td>Overly helpful with directions out of town</td></tr>
      <tr><td>9</td><td>To sell you something you shouldn't buy</td><td>Handles the merchandise with gloves</td></tr>
      <tr><td>10</td><td>Company; they are desperately lonely</td><td>Keeps refilling your glass unasked</td></tr>
      <tr><td>11</td><td>To keep a promise made to the dead</td><td>Visits the boneyard daily, same hour</td></tr>
      <tr><td>12</td><td>What the dark promised them &mdash; almost paid off now</td><td>The animals won't come near; they've stopped noticing</td></tr>
    </tbody>
  </table>

  <h2>Bar Talk &mdash; a d20 of Rumors</h2>
  <p>Half of these are true in any given town. You decide which half after the players choose one to chase.</p>
  <table>
    <thead><tr><th>d20</th><th>What they're saying</th><th>d20</th><th>What they're saying</th></tr></thead>
    <tbody>
      <tr><td>1</td><td>The stage hasn't come in two weeks; the road's fine</td><td>11</td><td>The new preacher don't cast a shadow at evening service</td></tr>
      <tr><td>2</td><td>Old Krieg pays double for night work at his place; nobody goes twice</td><td>12</td><td>They hanged the wrong man in '81 and the right one still buys drinks here</td></tr>
      <tr><td>3</td><td>A white bison was seen on the flats; the tribes have gone quiet about it</td><td>13</td><td>The mine took on a new vein; the ore hums if you hold it</td></tr>
      <tr><td>4</td><td>A whole wagon train wintered at the pass and never came down</td><td>14</td><td>The Vane girl came back from the river three days after she drowned</td></tr>
      <tr><td>5</td><td>There's a gunfighter in the territory can't be killed; ask at the faro table</td><td>15</td><td>Cattle on the north range born wrong this spring &mdash; every one</td></tr>
      <tr><td>6</td><td>The Army's buying salt by the wagonload and won't say why</td><td>16</td><td>A woman weeps along the creek at night; don't answer her</td></tr>
      <tr><td>7</td><td>Doc's been ordering twice the laudanum for half the patients</td><td>17</td><td>The bounty on the Sorrel Gang doubled; the last posse's horses came home alone</td></tr>
      <tr><td>8</td><td>Something's been opening graves &mdash; from underneath</td><td>18</td><td>There's a door in the mesa the old people painted shut</td></tr>
      <tr><td>9</td><td>The railroad man buys land nobody'd want at prices nobody'd refuse</td><td>19</td><td>The marshal burned a bundle of letters the night the judge died</td></tr>
      <tr><td>10</td><td>A traveling show is a day behind you on the road; folk vanish where it plays</td><td>20</td><td>It's quiet lately. Too quiet. Even the coyotes have moved on.</td></tr>
    </tbody>
  </table>

  <h2>The Trail &mdash; d12 by Day, d12 by Night</h2>
  <table>
    <thead><tr><th>d12</th><th>By day</th><th>By night</th></tr></thead>
    <tbody>
      <tr><td>1</td><td>Weather turning &mdash; a wall of it, hours off</td><td>The fire won't take, and the wood is dry</td></tr>
      <tr><td>2</td><td>Tracks crossing yours: shod horses, moving fast, one bleeding</td><td>A light on the ridge that answers when you cover yours</td></tr>
      <tr><td>3</td><td>Buzzards, a mile off, patient</td><td>The horses wake you, staring at the same nothing</td></tr>
      <tr><td>4</td><td>A homestead: door open, table set, nobody</td><td>Singing, far off, in a language nobody owns to knowing</td></tr>
      <tr><td>5</td><td>Fence line cut &mdash; from the outside</td><td>One of the party talks in their sleep, answering questions</td></tr>
      <tr><td>6</td><td>A stranger afoot, no water, won't say from where</td><td>Something big circles the camp once, upwind, and leaves</td></tr>
      <tr><td>7</td><td>Fresh grave by the trail, marker turned face-down</td><td>The stars are wrong over one quarter of the sky</td></tr>
      <tr><td>8</td><td>Good water, good grass &mdash; and old bones in the reeds</td><td>A child's voice asks to share the fire. There is no child.</td></tr>
      <tr><td>9</td><td>A drummer's wagon, wares half-price, seller in a hurry</td><td>Dawn is an hour late. Nobody's watch agrees.</td></tr>
      <tr><td>10</td><td>Smoke ahead &mdash; too much for a campfire, too little for a town</td><td>Every snare and picket is undone, gently, from within</td></tr>
      <tr><td>11</td><td>The shortcut everyone knows about; nobody's used it in a year</td><td>Frost, in August, in the shape of footprints</td></tr>
      <tr><td>12</td><td>A rider pacing you on the far ridge all afternoon</td><td>You wake where you camped. The ashes are a week cold.</td></tr>
    </tbody>
  </table>

  <h2>Plunder &amp; Finds &mdash; a d12</h2>
  <table>
    <thead><tr><th>d12</th><th>The find</th></tr></thead>
    <tbody>
      <tr><td>1</td><td>$2d20 in mixed coin, some of it minted nowhere you know</td></tr>
      <tr><td>2</td><td>A good horse, saddled, patient, waiting &mdash; branded to a dead man's outfit</td></tr>
      <tr><td>3</td><td>A fine revolver with eleven notches and a name scratched out</td></tr>
      <tr><td>4</td><td>Letters home, unsent, that explain everything if read in order</td></tr>
      <tr><td>5</td><td>A doctor's bag, complete, monogrammed, one instrument missing</td></tr>
      <tr><td>6</td><td>A claim deed, legal and current, to ground the locals won't name</td></tr>
      <tr><td>7</td><td>A silver crucifix, heavy, bent nearly double by hand</td></tr>
      <tr><td>8</td><td>Tintypes of strangers &mdash; and on a second look, one of a party member</td></tr>
      <tr><td>9</td><td>A journal, sane for forty pages, then diagrams</td></tr>
      <tr><td>10</td><td>Trade goods: powder, salt, coffee &mdash; worth $30 to the right town, questions to the wrong one</td></tr>
      <tr><td>11</td><td>A child's doll, new, dry, forty miles from anywhere</td></tr>
      <tr><td>12</td><td>A key of black iron, cold in any weather; you'll know the lock when you see it</td></tr>
    </tbody>
  </table>

  <h2>Wrong Notes &mdash; a d20 of Omens</h2>
  <p>For seasoning any scene that needs a chill without a check. One at a time; let them accumulate.</p>
  <table>
    <thead><tr><th>d20</th><th>The wrong note</th><th>d20</th><th>The wrong note</th></tr></thead>
    <tbody>
      <tr><td>1</td><td>The birds stop, all at once, mid-phrase</td><td>11</td><td>A rocking chair, rocking, wind or no</td></tr>
      <tr><td>2</td><td>Milk gone sour in the pail, morning-fresh</td><td>12</td><td>The dog won't cross a particular floorboard</td></tr>
      <tr><td>3</td><td>Every clock in the house stopped at the same minute</td><td>13</td><td>Fresh flowers on a grave nobody tends</td></tr>
      <tr><td>4</td><td>A cold spot the width of a doorway, in open ground</td><td>14</td><td>The well rope is wet. The bucket is dry.</td></tr>
      <tr><td>5</td><td>Handprints on the window. Outside. Second floor.</td><td>15</td><td>A hymn hummed from the barn; the barn is empty</td></tr>
      <tr><td>6</td><td>The horses are watching something walk the fence line</td><td>16</td><td>Salt spilled across every sill, from inside</td></tr>
      <tr><td>7</td><td>Seven crows on the wire, facing the house</td><td>17</td><td>The family Bible open to a page that's been cut out</td></tr>
      <tr><td>8</td><td>A smell of lightning on a clear day</td><td>18</td><td>Your reflection is a half-second behind in the shaving glass</td></tr>
      <tr><td>9</td><td>Wet bootprints from the creek to the door, none returning</td><td>19</td><td>The baby laughs at the empty corner, every evening, same time</td></tr>
      <tr><td>10</td><td>The candle flames all lean the same direction; there is no draft</td><td>20</td><td>Somewhere out on the flats, a church bell. There is no church.</td></tr>
    </tbody>
  </table>

  <div class="keeper-note"><span class="kn-tag">The seed rule</span>Anything you roll here that makes the table lean
  forward is no longer a random result &mdash; it is now part of the campaign. Write it down, give it a cause, and hang
  a thread from it (Ch. II). The tables are not filler; they are an oracle, and the players will treat whatever comes
  out of them as deliberate. Let them be right.</div>
</section>
"""

from perdition_map import keeper_map_html

CH13 = f"""<!-- XIII -->
<section class="page" id="basin">
  {runhead('XIII. Perdition Basin')}
  <h1 class="chapter">XIII. Perdition Basin</h1>
  <p class="chapter-sub">One county, drawn whole and keyed &mdash; the worked example of a Haunted Year.</p>
  <div class="divider"></div>
  <div class="narr">Submitted for your consideration, then: one county, surveyed and staked, whole enough
  to hold a year. It begins as every good lie in this country begins &mdash; with the truth. A river, a
  bank, a stage road, a marshal, cattle at fair prices. Nothing in Perdition Basin will read as anything
  but a western until the third or fourth night, and that is its design and its lesson in one: the
  slow burn is not a trick you play <em>on</em> the county. It is what the county is.</div>
  <p class="dropcap lead">Everything before this chapter handed you parts: the engine, the monsters, the craft, two finished
  nights, and the frame for stringing nights into a year. This chapter spends all of it in one place. <strong>Perdition
  Basin</strong> is a whole county &mdash; mapped, keyed, and built so you can open this book and run. It is the home
  ground of both reckonings you already have: <em>The Salt at Coffin Wells</em> (Ch. IX) and <em>A Face Not His Own</em>
  (Ch. X). Run them here and they stop being two one-shots and become the first two nights of one story &mdash; the
  <em>Haunted County</em> of Ch. XI, drawn out and given a map. Take it whole, or strip it for parts and hang them on a
  country of your own.</p>

  {keeper_map_html()}

  <h2 id="basin-truth">The Truth of the Basin</h2>
  <p>Perdition Basin is a low, dry bowl of a country, its life strung along the failing <strong>Calvary River</strong>
  and the scattered wells and springs that are the only sure water for a hard day's ride in any direction. That is the
  honest map, and it is the one your players will draw. Here is the one they will not: <strong>the water rises from
  something beneath, and the something is awake.</strong></p>
  <p>A century ago the Franciscan padres of <strong>Mission San Clavo</strong> learned it &mdash; from the ground, from
  the dead that would not stay down, and last and least willingly from the <strong>Painted Mesa people</strong>, who had
  said as much for longer than the mission had stood and had not been heeded. What lay under the water was no devil the
  padres had a rite to burn. It was a <strong>Patron</strong> (Player's Book Ch. VII) &mdash; one of the old reaching
  hands of the Dark &mdash; and it was coming up through the wells the way damp comes up through a wall.</p>
  <p>They could not kill it. They did the next thing, and the harder one: they <strong>bound</strong> it. Blessed silver
  driven as nails &mdash; <em>clavos</em> &mdash; into the mouth of every spring and well in the basin; salt packed around
  each; a rite said over each; and the whole ring closed like a fence around the thing's reaching fingers. It held for a
  hundred years. The basin got its quiet century: cattle, three towns, a stage road, a county seat.</p>
  <p>Now the seal is coming apart, and for three plain reasons &mdash; all of them the players' kind of trouble:</p>
  <ul class="dash">
    <li><strong>Drought.</strong> The water table is dropping. Wells that were deep run shallow; nails driven into wet
    ground now sit in dust, and dry silver holds nothing.</li>
    <li><strong>Blasting.</strong> The railroad is surveying the basin, and its powder has already split ground the padres
    sealed. (This is the crack in the <em>Salt Valley</em> seed of Ch. XI; Perdition Basin is that seed made a place.)</li>
    <li><strong>Greed.</strong> The nails are silver, and silver is money to a ruined man. They are being pulled, one well
    at a time, by people who do not know or do not care what the nail was set to hold. The banker who dug up the wrong
    grave at Coffin Wells (Ch. IX) is only the first the players will meet.</li>
  </ul>
  <p>Every nail that fails, a well goes bad, and something comes up through it. The basin does not fall all at once. It
  fails <strong>well by well</strong> &mdash; and that, drawn on a map, is your clock, your travelogue, and your whole
  campaign at once.</p>
  <div class="keeper-note"><span class="kn-tag">The one thing to hold</span>The players need to know none of this to
  begin. They ride into a town with a fever problem. The Truth is what <em>you</em> hold and they <em>earn</em>, in the
  order the map gives you: a bad well, then another, then the pattern, then the nails, then the mission, and only at the
  last the thing under the water. Name the whole shape late, or let them name it &mdash; and feel the floor go.</div>

  <h2 id="basin-wells">A Reckoning of the Wells</h2>
  <p>The binding is a ring of wells and springs, and the Keeper's map shows the state of each: a plain ring, the nail
  holds; a broken ring, the binding is failing; a struck-through ring, the well is gone and something is already loose.
  Restore the ring, or learn what it holds, before the last nail falls &mdash; that is the spine. Here is what each one
  is, and what it lets up when it goes.</p>
  <table>
    <thead><tr><th>The well</th><th>On the map</th><th>The truth beneath</th></tr></thead>
    <tbody>
      <tr><td><strong>Coffin Wells</strong></td><td>broken</td><td>The first to fall. A <strong>Nightwalker</strong>
      (staked here by the padres) was dug up for its rumored silver; the dead now rise as <strong>Risen</strong>. This is
      <em>The Salt at Coffin Wells</em> &mdash; site &#9312;, Ch. IX.</td></tr>
      <tr><td><strong>Saltlick well</strong></td><td>failing</td><td>The seal thins, and the thinning drew a
      <strong>Skin-Walker</strong> to easy prey at the lonely relay. This is <em>A Face Not His Own</em> &mdash; site
      &#9313;, Ch. X.</td></tr>
      <tr><td><strong>the Mission spring</strong></td><td>failing</td><td>The heart of the ring, at San Clavo itself. When
      this nail goes, the Patron's hand is free. The whole campaign is the race to keep it, or re-drive it.</td></tr>
      <tr><td><strong>the South well</strong></td><td>broken</td><td>Gone quietly, out in the Badlands, and nobody living
      near to notice yet. What came up is yours to choose (roll the Old Dark, Bestiary Ch. VII) &mdash; a whole reckoning
      waiting to be found.</td></tr>
      <tr><td><strong>Crossing well</strong></td><td>bound</td><td>Still holds &mdash; it waters the county seat, so its
      nail is watched. If it ever fails, the disaster is <em>public</em>, and that is a reckoning of a different kind.</td></tr>
      <tr><td><strong>the North seep</strong> &middot; <strong>Roadman's well</strong> &middot; <strong>Painted
      spring</strong></td><td>bound</td><td>The ring's still-sound quarter. The Painted spring the Mesa people tend
      themselves, and have far longer than the padres &mdash; ask why, and who taught whom.</td></tr>
    </tbody>
  </table>

  <h2 id="basin-places">The Places</h2>
  <p>Six places carry the county. Each is a scene waiting; each has a hook that pulls toward the ring. For a town you
  need on the fly, roll one up (Ch. XII) and hang it on the nearest well.</p>

  <h3 id="basin-crossing">Calvary Crossing &mdash; the county seat</h3>
  <p>The one place in the basin with a marshal, a bank, a doctor, and a second street. It sits where the Stage Road fords
  the Calvary, and it is the closest thing to safe: its well still holds. Calvary Crossing is where the players resupply,
  hear the county's talk, and meet the men who are quietly pulling the nails and calling it progress. The bank is here,
  and so is the railroad's survey office. Play it as the ordinary west at its most convincing &mdash; so the floor has
  somewhere to drop.</p>
  <p><span class="hook">Hook &mdash;</span> the marshal, <strong>T. Coyle</strong> (Ch. II's voice), knows three wells
  have "gone sour" and is one honest man short of admitting it is more than water. He will not deputize strangers &mdash;
  until he has to.</p>

  <h3 id="basin-coffin">Coffin Wells &mdash; the dying cattle town</h3>
  <p>A day south and west, a shrinking cattle town named for the boot-hill and the wells both. Its nail is <em>pulled</em>
  and its well is <em>broken</em>: this is where the campaign's dread first shows its face, and it is a finished night
  ready to run (Ch. IX). Run it first. Whatever the players do to the Nightwalker under the mission ground, the well
  stays broken unless a nail is re-driven &mdash; and re-driving a nail is a rite nobody left in Coffin Wells knows.</p>
  <p><span class="hook">Hook &mdash;</span> the banker <strong>Josiah Vane</strong>, if he lives through Ch. IX, is the
  thread straight to the faction pulling nails county-wide. If he dies, his ledger survives, and the ledger names names.</p>

  <h3 id="basin-saltlick">Saltlick Station &mdash; the lonely relay</h3>
  <p>A hard day north and east of the Crossing, the last roof for twenty miles on the Stage Road, out where the country
  gets thin. Its well is <em>failing</em>, and the failing drew the thing that now wears the hostler's face (Ch. X). Run
  it as the campaign's second night, or as the players' introduction to the idea that a bad well pulls predators the way
  a wound pulls flies.</p>
  <p><span class="hook">Hook &mdash;</span> whatever rides out of Saltlick at dawn wearing a new face (Ch. X) can ride
  straight into the next town on your map &mdash; a recurring hand for the whole year, if you let it live.</p>

  <h3 id="basin-mission">Mission San Clavo &mdash; the ruined heart</h3>
  <p>The oldest thing the settlers built, and a ruin for fifty years: a broken adobe church on the ground the padres
  chose because it sat over the Patron's reaching hand. The <strong>Mission spring</strong> rises in its cracked
  baptistry, and the master nail &mdash; the one that closes the whole ring &mdash; is driven into the altar stone. Come
  here and the campaign's true shape is on the walls: the padres' carvings, the record of the binding, and the warning
  they left for whoever came after. It is also where the last keeper of the ring can be found.</p>

  <h3 id="basin-homesteads">The Homesteads &mdash; where it shows first</h3>
  <p>Scattered between the towns, the outlying homesteads are the county's nerve endings. A well goes bad out here weeks
  before a town notices: the stock sicken, a buried kinsman comes home wrong, a family stops answering. The homesteads
  are your early-warning system and your bank of small, sharp tragedies &mdash; the Pell place (Ch. IX) is one; you have
  a dozen more in a single roll (Ch. XII).</p>

  <h3 id="basin-mesa">The Painted Mesa &mdash; the ones who knew</h3>
  <p>Rising red in the south-east, the Painted Mesa is the ground of the people who were in this country long before the
  mission, and who told the padres what lay under the water &mdash; and were displaced for their trouble. They tend the
  Painted spring by rites older than the nails, and they know things about the thing beneath that no carving at San Clavo
  records. They are not an oracle the players may squeeze. They are people with their own stake (the Patron threatens
  their ground too), their own grievance (the settlers owe them, not the other way around), and every right to weigh
  whether these particular strangers deserve help.</p>
  <div class="keeper-note"><span class="kn-tag">Play them as people</span>Give the Painted Mesa folk names, faces,
  disagreements, and interests of their own &mdash; an elder who counsels caution, a young rider who is done being patient
  with settlers, a keeper of the spring who will talk only once respect is earned in the fiction, not bought with a good
  roll. Their knowledge is a relationship, not a treasure. Handle the history plainly and without romance; the horror of
  Blood &amp; Grit is the country's, and this is the part of it the settlers made themselves.</div>

  <h2 id="basin-hands">The Three Hands</h2>
  <p>Three interests pull on the basin. Each wants something the players can help or hinder; each is on the map as a wash
  of colour (see the Keeper's map). Run them as factions (Ch. VIII): know the want, and you can play the county.</p>
  <ul>
    <li><strong>The Vane Interest &mdash; the cattle-and-rail money.</strong> Ruined ranchers, a hungry bank, and the
    railroad's agents, bound together by the one thing all of them want: the basin cheap and under their thumb. They are
    the hand pulling the nails &mdash; some for the silver, some to clear title to "sour" land, most too willful to hear
    what a nail was for. The human engine of the whole disaster, and the faction the players can actually punch.</li>
    <li><strong>The Last Bell of San Clavo &mdash; the ring's lone keeper.</strong> One old soul who knows the truth of
    the nails and has been re-driving them alone for years, and is losing: <strong>Padre Ildefonso</strong>, or the
    layfamily that kept the mission after the church forgot it. Undermanned, half-broken, and the players' one source for
    the rite that closes a well. A quest-giver who is also a warning of where this ends.</li>
    <li><strong>The Painted Mesa people &mdash; the ones who knew.</strong> Not a monolith and not a resource: a people
    with the oldest true knowledge of the thing under the water, their own reasons to want it kept down, and no debt to
    the settlers that would oblige them to fix the settlers' mess. Earn them, and they are the deepest well of truth in
    the basin. Fail them, and they will let the county reap what it planted &mdash; and who could blame them.</li>
  </ul>

  <h2 id="basin-running">Running the Basin</h2>
  <p>You can run Perdition Basin three ways, and the map serves all three:</p>
  <ul>
    <li><strong>As a one-shot.</strong> Run either reckoning (Ch. IX or X) exactly as written. The county is the world it
    happens in; the players need never see the ring.</li>
    <li><strong>As a short arc.</strong> Run both reckonings back to back, then reveal the pattern &mdash; two bad wells,
    the same silver missing from each &mdash; and let the players decide to chase it. Three to five nights.</li>
    <li><strong>As the Haunted Year</strong> (Ch. XI). The ring is the season clock. Each season a nail falls (you choose
    or roll which well); the players race the map, re-driving what they can and reckoning with what they can't, toward
    the Mission spring and the master nail. <strong>The door that closes it:</strong> re-drive the master nail at San
    Clavo &mdash; which costs a life freely given, the padres' price and now the players' &mdash; or find the older
    working the Mesa people hold, and pay <em>its</em> price instead. Either way, someone does not ride out of the basin.</li>
  </ul>
  <p>For everything the map does not name &mdash; a town's third street, a homesteader's face, the rumor in the Crossing
  saloon &mdash; roll it live (Ch. XII) and hang it on the nearest well. The basin is built to be filled in at the table,
  not memorized before it.</p>
  <div class="keeper-note"><span class="kn-tag">The map is the campaign</span>Put the Keeper's map where you can see it
  and the players cannot. Every session, ask one question of it: <em>which nail is going next, and who is pulling it?</em>
  Answer that, and the country writes your next night for you &mdash; because a failing well is a place, a victim, a
  culprit, and a monster, all in one mark on a map. That is the whole trick of a Haunted County, and Perdition Basin is
  it, drawn out so you can see how.</div>
</section>
"""

CH14 = f"""<!-- XIV -->
<section class="page" id="city">
  {runhead('XIV. The Lamplit City')}
  <h1 class="chapter">XIV. The Lamplit City</h1>
  <p class="chapter-sub">Dodge, Kansas City, Frisco, Butte &mdash; and what the dark does with a crowd.</p>
  <div class="divider"></div>
  {quote("Out on the Cimarron a man screams and nobody hears him. In Kansas City a man screams and forty people hear him, and they go on in to supper. I have come to think the second is the worse country.", "Pinkerton operative, reporting to the Chicago office")}
  <div class="narr">There is a fear, when a Keeper first moves the game off the open range, that the dark
  will not survive the gaslight &mdash; that a country horror needs a lonely country, and that a city with
  police in it, and a hospital, and four newspapers, and sixty thousand souls, is simply too well lit to be
  frightened in. Put the fear down. The dark does not need the dark. It needs to be able to work unremarked,
  and there has never been a better place for that than a city where nobody knows their neighbor's name.</div>

  <p class="dropcap lead">By 1885 the West has cities, and they are not a compromise with the western &mdash; they are the
  western's other half. Dodge is the cattle capital of the continent. Kansas City runs the beef trade of a nation out of the
  West Bottoms. San Francisco is the great city of the West and about the ninth in the nation. Butte sits on the richest
  hill on earth and is hollow underneath. Every trail your players ride ends in one of these places, because that is where the money is, and the
  money is why anybody came. This chapter is how to run a night there without losing a thing.</p>

  <h2>Why the Dark Prefers a City</h2>
  <p>The country horror runs on isolation: nobody is coming, and the nearest help is a day's ride. A city takes that away
  and hands you something better in exchange.</p>
  <ul>
    <li><strong>Anonymity beats isolation.</strong> A thing that takes one soul a week from a town of two hundred empties
    it in a season and is noticed by Tuesday. The same thing in Kansas City takes one a week forever. The population turns
    over constantly &mdash; drovers, rail hands, immigrants, whores, drifters, men whose families think they are in Oregon
    &mdash; and a missing stranger is not a mystery. It is a filing, if that.</li>
    <li><strong>The crowd is cover.</strong> Out on the flat, a stranger on the ridge is an event. On Front Street a
    stranger is Tuesday. Things that could never cross open ground in daylight walk the city at noon in a good coat, and
    the only person who notices is the one who has learned what to look for &mdash; which is your party, and nobody else.</li>
    <li><strong>Indifference does the work fear used to.</strong> The country horror's line is <em>nobody can hear you</em>.
    The city horror's line is <em>everybody heard you and went in to supper</em>. That is a colder note, and it plays.</li>
    <li><strong>Scale.</strong> A haunting in the country takes a house. In a city it takes a block, a trade, a ward.
    A thing under Perdition Basin wants a valley. A thing under the Kansas City stockyards has its hand on the beef of a
    continent, and every steer the players ever drove came here to die.</li>
  </ul>

  <h2>What Changes at the Table</h2>
  <p>Six things, and only six. Everything else in this book runs unaltered.</p>
  <div class="box">
    <h4>1. The gun goes in a rack</h4>
    <p>Dodge City has a <strong>deadline</strong> &mdash; the railroad tracks &mdash; and north of it firearms are checked
    at the first place of business you enter, by ordinary municipal ordinance and a marshal with a shotgun. Most cattle
    towns have the same rule, and every real city has some version. This is the single best gift the setting ever gave a
    horror Keeper: it disarms the party <em>lawfully</em>, in a way they agreed to, in a place they chose to be. Make the
    check-in a scene. Then put the thing they need to shoot on the wrong side of the deadline at eleven at night.</p>
    <h4>2. Firing costs something</h4>
    <p>On the trail, a gunfight is a scene. In a city it is an arrest, a coroner's inquest, two newspapers, a bail bond,
    and a lawyer. Do not forbid it &mdash; charge for it. A justified killing still costs the party three days and a
    hundred dollars, and the thing they were chasing does not wait three days.</p>
    <h4>3. Witnesses and the press</h4>
    <p>Everything the players do in public happens in front of forty people and is in a newspaper by morning, usually
    wrong. This cuts both ways and both ways are good: they cannot quietly bury a problem, and they can, if they are
    clever, put a thing in the paper that its owner very badly needed kept out.</p>
    <h4>4. Help exists, and is worse</h4>
    <p>There are police, hospitals, and a coroner. Use them &mdash; and let the party learn that a city's institutions are
    not built to believe them. A man raving about the dead walking is not ignored in Kansas City; he is <em>committed</em> &mdash; a far more frightening end than being disbelieved on the trail. The asylum is the city's version of dying
    alone in the snow.</p>
    <h4>5. Paper is the new tracking</h4>
    <p>The country skills do not work here, so give the city its own: the newspaper morgue, the city directory, the county
    recorder, the coroner's inquest book, the hospital register, the ship manifest, the telegraph clerk who can be bought
    for two dollars. A party that learns to hunt through paper in a city is doing exactly what a party that learns to cut sign is doing on the trail, and finds it just as satisfying. Run these as Lore, Notice, and Persuade against the usual
    ladder.</p>
    <h4>6. Dread has new rooms</h4>
    <p>The city has no wide dark sky, so take the fear indoors and underground: the packing-house floor at three in the
    morning, the tenement stair, the fog off the bay, the ore drift eighteen hundred feet down where the rock is a hundred
    and thirty degrees, the sewer, the crib alley, the charity ward. Dread DCs and Nerve loss are unchanged &mdash;
    what changes is that the party cannot ride away from it, because they have nowhere to ride to.</p>
  </div>

  <h2>The Bestiary, Downtown</h2>
  <p>Each kind bends differently to a city, and the bend is usually an improvement.</p>
  <ul>
    <li><strong>The Restless Dead (Ch. II).</strong> The country's dead haunt a grave; a city's dead haunt a
    <em>system</em>. A potter's field with eleven thousand in it. A cholera trench built over by a good address. The
    dissection room at the medical college, and the resurrection men who supply it &mdash; the Resurrectionist stops being
    a lone ghoul with a spade and becomes a going concern with a price list and a standing order from a professor. Run a
    siege on a tenement block instead of a farmhouse and the numbers get worse in every direction.</li>
    <li><strong>Cursed Beasts (Ch. III).</strong> Harder to hide and therefore better: a thing that must feed nightly in a
    city is on borrowed time, and knows it, and gets desperate on a clock. Put it in the stockyards, where a hundred
    thousand head a day are killed anyway and nobody counts a carcass twice. Or in the rail yards. Or the sewers, where the city puts everything it would rather not look at.</li>
    <li><strong>Men, and the Shapes of Men (Ch. IV).</strong> The city is their native ground. A Skin-Walker in a town of
    two hundred is caught in a week because everyone knows everyone; in San Francisco it can wear a new face every month
    for a decade. The Mesmerist gets a lecture hall and a subscription list. The Deathless Gun gets a reputation, a saloon
    named after him, and an entire ward that would rather not testify.</li>
    <li><strong>Spirits &amp; Hauntings (Ch. V).</strong> Cities are built on their own dead ground, and the good ones are
    built on it twice. San Francisco's financial district stands on the hulls of the gold-rush fleet, scuttled and buried
    where they lay, and there are ships under those foundations with cargo and crew still in them. That is not an invention; it is the ground, and there is no finer haunting site in the West.</li>
    <li><strong>The Wild &amp; the Weather (Ch. VI).</strong> The one kind that weakens &mdash; so change its target. The
    Thirst in a city is the water main and the typhoid ward. The Red Wind is the smelter smoke that turns Butte's noon into
    night for three days at a stretch. A blizzard that kills one drover on the flat kills four hundred in a tenement
    district with no coal.</li>
    <li><strong>The Old Dark (Ch. VII).</strong> Unchanged, and worse. What the Old Dark wants is scale, and a city is
    scale: a mine that goes down two thousand feet under a hundred thousand people, a subterranean waterworks, a ward it
    can hollow out one household at a time. Where the country gave it a valley, the city gives it an <em>industry</em>.</li>
    <li><strong>Hard Men &amp; Hard Country (Bestiary Ch. IX).</strong> Every entry survives the move and several improve.
    The Lynch Mob becomes a race riot with a fire company in it. The Hired Gun becomes a detective agency with a contract
    and an office. The Cattle Baron's Men become a corporation. Run these for the first month here exactly as you would
    on the range.</li>
  </ul>

  <h2>The Dark Cultist, Incorporated</h2>
  <p>This is the chapter's most useful idea, so take it whole. In the country a cult is a barn, a pit, and eleven people
  who have to meet in secret. In a city it does not have to hide at all &mdash; it <strong>charters</strong>.</p>
  <p>It becomes the Benevolent Association, the Subscription Library, the Improvement Society, the Widows' and Orphans'
  Fund, the private lodge with a fine building on a good street and a brass plate by the door. It has a president, a
  treasurer, minute-books, and a lawyer. It gives generously and publicly. Its members are the alderman, the coroner, the
  editor of the second-largest paper, two police captains, and the man who holds the note on the boarding house where the
  party is staying. It does not need to silence a witness; it can simply outspend one, or sue one, or have one committed.</p>
  <div class="keeper-note"><span class="kn-tag">Keeper's eye</span>The horror of this is not the robes. It is the moment
  the party realizes that every institution they were going to appeal to is already on the membership roll &mdash; and that
  the thing has been perfectly, boringly legal the entire time. Give the party one honest official, well down the ladder,
  with no power and a family. Everything the campaign is about will run through that person.</div>
  <p>Practically: build the cult as a <em>faction</em> out of Chapter VIII, with a want, a lever, and a line. Its lever is
  money and standing. Its line is publicity &mdash; it will do a great deal, but not in front of the papers. Everything the party has to work with lives in that gap. The final scene of a city campaign is more often an exposure than a gunfight, and it
  should be: make the players choose between killing the thing and proving it, and let proving it be harder, slower, and
  better.</p>

  <h2>Ten Cities, Keyed</h2>
  <p>A hook apiece. Each is a real place in 1885, and the wrongness listed is yours to keep or trade.</p>
  <table>
    <tbody>
      <tr><td><strong>Dodge City, Kansas</strong> <span class="sub">cattle capital, ~1,200</span></td><td>The deadline at
      the tracks, Front Street, Boot Hill, and the Kansas quarantine law that is killing the trade this very year. A town
      with one boom left in it, and something under Boot Hill that has noticed the drives are ending.</td></tr>
      <tr><td><strong>Kansas City, Missouri</strong> <span class="sub">~100,000 and doubling</span></td><td>The West Bottoms: stockyards
      and packing houses where the whole beef of the continent comes to die, working day and night. Blood in the river.
      Something in the killing floors that has been very well fed for eleven years and has grown accordingly.</td></tr>
      <tr><td><strong>San Francisco, California</strong> <span class="sub">~250,000</span></td><td>Fog, the Barbary Coast,
      Chinatown, and a financial district built on the buried hulls of the abandoned gold fleet. Ships under the streets,
      with their holds shut. The city's foundations are a graveyard nobody consecrated.</td></tr>
      <tr><td><strong>Butte, Montana</strong> <span class="sub">~8,000 and climbing fast</span></td><td>The richest hill on
      earth, and entirely hollow &mdash; three thousand feet of workings under the houses, and men dying of the heat at
      depth. The smelter smoke blots out noon. Everything in this book that lives underground lives here.</td></tr>
      <tr><td><strong>Tombstone, Arizona</strong> <span class="sub">~5,000, falling</span></td><td>The silver is playing
      out and the lower workings are filling with water. A town on the way down is a town that will agree to anything, and
      what came up with the water table has opinions about who stays.</td></tr>
      <tr><td><strong>Omaha, Nebraska</strong> <span class="sub">~40,000, about to treble</span></td><td>Union Pacific headquarters, the
      shops, and the brand-new stockyards at South Omaha. Every soul heading west passes through, which means every soul
      heading west can be counted, followed, and selected from.</td></tr>
      <tr><td><strong>Denver, Colorado</strong> <span class="sub">~50,000</span></td><td>Larimer Street, the smelters, and
      new money building mansions on Capitol Hill fast enough to bury what the digging turned up. The respectable half of
      town is six years old and already has a secret.</td></tr>
      <tr><td><strong>Virginia City, Nevada</strong> <span class="sub">the Comstock, past its peak</span></td><td>The
      deepest hard-rock workings on the continent, hot enough at the bottom to kill a man in an hour, and the Sutro Tunnel
      draining it. The mine is played out. Something is still down there, and the pumps are what is holding it.</td></tr>
      <tr><td><strong>Cheyenne, Wyoming</strong> <span class="sub">~6,000, and the richest club in the West</span></td><td>The
      Cheyenne Club, where the cattle barons take their brandy and decide who gets invaded. This is where the Regulators
      (Bestiary Ch. IX) are hired, over dinner, by men in evening dress.</td></tr>
      <tr><td><strong>Leadville, Colorado</strong> <span class="sub">~14,000 at 10,200 feet</span></td><td>A silver camp
      grown into a city where the air is thin, the winter is nine months, and the graveyard fills faster than the
      churches. Altitude, cold, and a boom that is one bad assay from over.</td></tr>
    </tbody>
  </table>

  <h2>Building Your Own City</h2>
  <p>Chapter VIII builds a town with a want, a tell, and a secret. A city needs four more things, and they are the four
  that generate every plot you will ever need there.</p>
  <ul>
    <li><strong>An industry.</strong> Cattle, silver, copper, rail, shipping, packing. It decides who lives there, what
    the air smells like, who has money, and what the city will forgive.</li>
    <li><strong>A machine.</strong> Whoever really runs it &mdash; the ward boss, the association, the company, the
    committee of vigilance that never quite disbanded. The mayor is rarely the answer.</li>
    <li><strong>A quarter the city pretends not to have.</strong> The tenderloin, the crib alley, the Chinese quarter, the
    shanties by the yards. This is where the dark works, because it is where the city has already agreed not to look.</li>
    <li><strong>A below.</strong> Sewers, mine workings, cellars, a buried creek, a filled-in ravine, the old fort's
    magazine, the ships under the fill. Every city has one. The third act happens there.</li>
  </ul>

  <div class="twocol">
    <h3>d12 &mdash; A City's Wrong Note</h3>
    <p>1 the potter's field is full again &middot; 2 the same charity buries them all &middot; 3 a ward with no children in
    it &middot; 4 the paper killed the story &middot; 5 four inquests, one verdict &middot; 6 the night shift will not go
    below &middot; 7 a fine new building on bad ground &middot; 8 the asylum is taking in strangers &middot; 9 the police
    do not patrol one street &middot; 10 the tunnels were bricked last spring &middot; 11 a society nobody can join
    &middot; 12 the mortality figures were amended</p>

    <h3>d10 &mdash; Who Runs This Town, Really</h3>
    <p>1 the packing company &middot; 2 the ward boss and his saloon &middot; 3 the mine's parent corporation &middot;
    4 the vigilance committee that never disbanded &middot; 5 the railroad's land office &middot; 6 the bishop &middot;
    7 the newspaper &middot; 8 the madam who holds everyone's secrets &middot; 9 a benevolent association with a fine
    brass plate &middot; 10 nobody, and that is the emergency</p>

    <h3>d10 &mdash; A City Job for a Country Posse</h3>
    <p>1 escort a witness to the courthouse &middot; 2 find a drover's brother, last seen in the yards &middot; 3 recover
    a body before the college does &middot; 4 sit up with a coffin &middot; 5 collect on a note nobody will collect on
    &middot; 6 guard a payroll through the tenderloin &middot; 7 find who is buying the fresh graves &middot; 8 walk a
    reporter into the quarter and back &middot; 9 identify the thing in the charity ward &middot; 10 attend a lodge dinner
    and listen</p>
  </div>

  <div class="keeper-note"><span class="kn-tag">Keeper's eye &mdash; keeping the tone</span>The failure mode is letting the
  city become a different game: a mystery in overcoats, all parlors and no dust. Guard against it three ways. Keep the
  party's country competence <em>valuable</em> &mdash; they read sign, sit a horse, and stay calm with a gun, and the city
  has almost nobody who can do all three. Keep the money problems mundane: a hotel bill, a stabling fee, a fine. And get
  them out of town regularly &mdash; the best city campaigns run a ride out to a ranch, a mine, or a rail camp every third
  night, so the city is a place they come back to rather than a box they are stuck in. The West is the trail
  <em>and</em> the terminus. Run both, and the dark has twice as many doors.</div>
</section>
"""

BODY = CONTENTS + CH1 + CH2 + CH3 + CH4 + CH5 + CH6 + CH7 + CH8 + CH9 + CH10 + CH11 + CH12 + CH13 + CH14 + APX


def _inject_quote(body, cid, text, srcline):
    sec = f'<section class="page" id="{cid}">'
    i = body.find(sec)
    if i == -1: return body
    d = body.find('<div class="divider"></div>', i)
    if d == -1: return body
    e = d + len('<div class="divider"></div>')
    return body[:e] + '\n  ' + quote(text, srcline) + body[e:]
_chq = {
 "chair": ("The players brought the heroes. You brought the country &mdash; and it was here first, and it will be here when the last of them is a name cut in a boot-hill board.", "N. Ashby"),
 "running": ("Roll the bones only when the answer matters and you do not already know it. The rest is talk &mdash; and talk is where the game lives.", "Marshal T. Coyle"),
 "fear": ("Fear is a coin, and you are a poor man. Spend it slow, and never the whole purse at once.", "from a Keeper's ledger"),
 "odds": ("A fair fight is one the players can see the shape of before they walk into it. The rest is arithmetic and funerals.", "Eb Tuttle, trapper"),
 "hazards": ("The ground remembers what was done on it. Tell your players so early, and mean it, and they will come to fear the dirt itself.", "Rev. A. Jensen"),
 "rewards": ("Give them little, and let it cost. A thing that came easy is a thing they will spend without a prayer.", "Eulalie &lsquo;Lucky&rsquo; Devereaux"),
 "cast": ("Every soul they meet wants something. Know the want and you can play the man &mdash; even one you made up a breath ago.", "Marshal T. Coyle"),
 "firstreckoning": ("The first night is a promise. Keep it honest and keep it frightening, and they will follow you into a hundred more.", "from a Keeper's ledger"),
 "secondreckoning": ("The gun is not always the answer &mdash; the craft is teaching them that before the answer they reach for gets someone killed.", "Marshal T. Coyle"),
 "pocket": ("Preparation is a fine horse, but the players will shoot it in the first act. Learn to walk.", "from a Keeper's ledger"),
 "keepersyear": ("A single night is a campfire tale. A year of them, told right, is the country itself &mdash; and the players will swear they lived there.", "from a Keeper's ledger"),
 "basin": ("I have mapped every well in this country and named every town. It is the wells I no longer sleep for. A town is only people. A well is a door, and someone has been leaving them open.", "from the field-books of N. Ashby, naturalist"),
 "screen": ("Everything a Keeper needs mid-night fits on one card. Everything a Keeper fears fits in the pause before the players roll.", "from a Keeper's ledger"),
}
for _cid,(_t,_s) in _chq.items():
    BODY = _inject_quote(BODY, _cid, _t, _s)


# ---- splice: replace from the contents marker to the closing </div> before <script> ----
start_marker = "<!-- ===================== CONTENTS ===================== -->"
si = H.find(start_marker)
assert si != -1, "contents marker not found"
# find the closing of the book div right before <script>
sci = H.find("<script>")
assert sci != -1
div_close = H.rfind("</div>", si, sci)
assert div_close != -1, "book closing div not found"

new_html = H[:si] + BODY + "\n</div>\n" + H[sci:]

from nav_tools import add_detailed_toc, build_index
KEEP_INDEX = [
    # --- the craft, by chapter ---
    ("The Keeper's Chair", "chair"), ("Session Zero", "chair"),
    ("Tone: the slow burn", "chair"), ("Pacing the table", "chair"),
    ("Reading your table", "chair"),
    ("Running the Game", "running"), ("Setting the DC", "running"),
    ("The four degrees (Keeper's side)", "running"), ("Success at a cost", "running"),
    ("Running a mystery", "running"), ("The talking fight", "running"),
    ("Rolling in the dark", "running"),
    ("Fear, Nerve &amp; the Mark", "fear"), ("Dread Checks, when to call", "fear"),
    ("The Dread DC ladder", "fear"), ("Spending Dread", "fear"),
    ("Afflictions", "fear"), ("Giving back Nerve", "fear"), ("The Mark (running)", "fear"),
    ("The Long Odds (building the fight)", "odds"), ("Threat by Tier", "odds"),
    ("Budgeting a fight", "odds"), ("Building a threat from scratch", "odds"),
    ("The gunfight", "odds"), ("Morale &amp; the flight of men", "odds"),
    ("Pursuit", "odds"), ("The ground in a fight", "odds"),
    ("When the dice turn cruel", "odds"),
    ("Choosing the night's monster", "bestiary"), ("Reskinning monsters", "bestiary"),
    ("Cursed Ground, Hazards &amp; Bad Medicine", "hazards"), ("Tainted ground", "hazards"),
    ("The wrong house", "hazards"), ("Cursed objects", "hazards"),
    ("When players dabble", "hazards"), ("Plain hazards of a hard country", "hazards"),
    ("Rewards &amp; Reckonings", "rewards"), ("Advancement (Keeper's side)", "rewards"),
    ("Grit (running)", "rewards"), ("Carrying the Marked", "rewards"),
    ("The Patrons at the table", "patrons-table"), ("The Dark's Wages", "rewards"),
    ("The Cast", "cast"), ("An NPC in three lines", "cast"),
    ("Reaction &amp; morale", "cast"), ("Folk of the frontier", "cast"),
    ("The town as a character", "cast"), ("Factions", "cast"),
    # --- the adventures & the campaign ---
    ("A First Reckoning", "firstreckoning"),
    ("The Salt at Coffin Wells <span class=\"note\">(adventure)</span>", "firstreckoning"),
    ("A Second Reckoning", "secondreckoning"),
    ("A Face Not His Own <span class=\"note\">(adventure)</span>", "secondreckoning"),
    ("The Keeper's Year", "keepersyear"), ("The three campaign frames", "keepersyear"),
    ("The Haunted County", "keepersyear"), ("The Long Trail", "keepersyear"),
    ("The Closing Circle", "keepersyear"), ("The rhythm of a year", "keepersyear"),
    ("The Salt Valley <span class=\"note\">(campaign seed)</span>", "keepersyear"),
    ("The Country in Your Pocket <span class=\"note\">(tables)</span>", "pocket"),
    ("Town generator", "pocket"), ("NPC generator", "pocket"), ("Rumors (a d20)", "pocket"),
    ("Trail events", "pocket"), ("Plunder &amp; finds", "pocket"), ("Omens (a d20)", "pocket"),
    ("The Keeper's Screen", "screen"),
    # --- the city ---
    ("The Lamplit City", "city"), ("Cities (running the game in)", "city"),
    ("The deadline (checking guns)", "city"), ("Anonymity (the city's isolation)", "city"),
    ("The Dark Cultist, Incorporated", "city"), ("Paper (hunting through records)", "city"),
    ("Ten Cities, Keyed", "city"), ("Building your own city", "city"),
    ("Dodge City", "city"), ("Kansas City", "city"), ("San Francisco", "city"),
    ("Butte, Montana", "city"), ("Tombstone", "city"), ("Omaha", "city"),
    ("Denver", "city"), ("Virginia City", "city"), ("Cheyenne", "city"), ("Leadville", "city"),
    # --- Perdition Basin ---
    ("Perdition Basin", "basin"), ("The truth of the basin", "basin-truth"),
    ("The wells (the binding ring)", "basin-wells"), ("The ring of nails", "basin-wells"),
    ("The clavos (the padres' nails)", "basin-truth"), ("The Patron beneath the basin", "basin-truth"),
    ("Calvary Crossing", "basin-crossing"), ("Coffin Wells (the town)", "basin-coffin"),
    ("Saltlick Station", "basin-saltlick"), ("Mission San Clavo", "basin-mission"),
    ("The Painted Mesa", "basin-mesa"), ("The Homesteads (Perdition Basin)", "basin-homesteads"),
    ("The Badlands (Perdition Basin)", "basin-places"),
    ("The Three Hands (factions)", "basin-hands"),
    ("The Vane Interest (faction)", "basin-hands"), ("Josiah Vane (banker)", "basin-coffin"),
    ("The Last Bell of San Clavo (faction)", "basin-hands"), ("Padre Ildefonso", "basin-hands"),
    ("The Painted Mesa people (faction)", "basin-hands"), ("Marshal T. Coyle", "basin-crossing"),
    ("Running Perdition Basin", "basin-running"),
]
new_html = build_index(
    new_html, curated=KEEP_INDEX, creatures=False,
    subtitle="The craft, the country, and where each waits.",
    intro="A leading &ldquo;the&rdquo; is ignored in the ordering. Where a concept fills a "
          "whole chapter, the page given is where that chapter opens.")
new_html = add_detailed_toc(new_html)
open("keeper-handbook.html", "w", encoding="utf-8").write(new_html)
print("spliced. imgs:", new_html.count("<img"), "| size:", len(new_html))
