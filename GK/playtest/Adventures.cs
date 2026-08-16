// The three adventures, declared as data so one runner plays all of them.
//
// Every creature here is named, never described — the runner looks each one up in
// Data/creatures.json and plays it on the Bestiary's own Defense, Blood, attacks and Dread DC.
// If a name does not resolve, the run FAILS rather than quietly substituting something plausible:
// an adventure that cites a creature the Bestiary does not have is an adventure a Keeper cannot
// run. That check has already earned its keep — the first draft of this file asked for "Risen",
// "Skinwalker" and "Ghoul", and the Bestiary has "The Risen", "The Skin-Walker" and no ghoul at
// all. Two near-misses and an invention, in four names.

using BloodAndGritKeeper;

/// <summary>One thing that happens to a posse. A scene either frightens them, costs them, or puts
/// something in front of them that has to be fought.</summary>
public enum BeatKind { Dread, Fight, Toll }

public record Beat(
    BeatKind Kind,
    string Name,
    string[] Foes = null,        // Bestiary names, one entry per body on the field
    int DreadDc = 0,
    int DreadTier = 0,           // which rung of the Nerve-loss ladder a failure pays
    int Toll = 0,                // Blood taken by the country itself — a fall, a fever, bad water
    string Note = null);

public record Act(string Title, string Purpose, Beat[] Beats);

public record Adventure(
    string Slug,
    string Title,
    string Subtitle,
    int PartyLevel,
    string Site,
    string Truth,
    Act[] Acts);

public static class Adventures
{
    // ---------------------------------------------------------------- I
    // Keeper's Book Ch. IX, pinned at Coffin Wells on the Perdition Basin map. The book gives it in
    // two pages and names both foes outright: Risen in Act Two, a Nightwalker in Act Three. What
    // the book does NOT say is whether three acts run end to end leave a 1st-level posse standing.
    // That is what the runner is for, and the answer is going in the module.
    public static readonly Adventure Salt = new(
        "salt-at-coffin-wells",
        "The Salt at Coffin Wells",
        "A first reckoning for a fresh posse — one night, three acts, and a banker who dug where he was told not to",
        PartyLevel: 1,
        Site: "Coffin Wells",
        Truth: "Josiah Vane dug up a staked and salted grave on the old mission ground hunting silver, "
             + "woke what the padres put there, and bought his own life with the town's blood. The fever "
             + "on the homesteads is the thing feeding. The freshly dead are getting up. In four nights "
             + "it is past any stake.",
        Acts: new[]
        {
            new Act("Act One — The Ordinary West",
                "Be a real town for one scene, then turn the note.",
                new[]
                {
                    new Beat(BeatKind.Dread, "the boot-hill graves are disturbed", DreadDc: 13, DreadTier: 1,
                        Note: "Soft on purpose. The first Dread Check of a campaign should be survivable."),
                }),
            new Act("Act Two — The Wrong Note Answers",
                "The dead get up. Nerve becomes real.",
                new[]
                {
                    new Beat(BeatKind.Dread, "the supper cold on the table, the door standing open", DreadDc: 16, DreadTier: 1),
                    new Beat(BeatKind.Fight, "the Pell place — the dead getting up",
                        Foes: new[] { "The Risen", "The Risen", "The Risen" }),
                    new Beat(BeatKind.Dread, "the wife in the cellar, bled and half-turned", DreadDc: 16, DreadTier: 2),
                }),
            new Act("Act Three — The Reckoning",
                "The ruined mission, the opened grave, and the thing that came out of it.",
                new[]
                {
                    new Beat(BeatKind.Dread, "its regard, in the dark of the church", DreadDc: 18, DreadTier: 3),
                    new Beat(BeatKind.Fight, "the Nightwalker at the opened grave",
                        Foes: new[] { "The Nightwalker" },
                        Note: "The book says outright that the players cannot simply out-shoot this. "
                            + "The runner plays it as though they tried, which is the only way to find "
                            + "out what that costs."),
                }),
        });

    // ---------------------------------------------------------------- II
    // Keeper's Book Ch. X, pinned at Saltlick Station. Level 3 rather than 1: the Skin-Walker is
    // Tier III, and against a 1st-level posse the safe-table rule makes it sign and spoor rather
    // than a fight. A module that puts a foe on the field the app would refuse to seat is a module
    // that disagrees with the game it ships with.
    public static readonly Adventure Face = new(
        "a-face-not-his-own",
        "A Face Not His Own",
        "A second reckoning — a lonely relay, eight souls under one roof, and one of them is wearing somebody",
        PartyLevel: 3,
        Site: "Saltlick Station",
        Truth: "Something at Saltlick takes a face and keeps it. It came in with the last coach and has "
             + "been working through the station one soul at a time. The tell is small enough that a "
             + "posse in a hurry shoots the wrong person before they find it.",
        Acts: new[]
        {
            new Act("Act One — The Wrong Note Among Friends",
                "Eight names, one roof, and something already inside it.",
                new[]
                {
                    new Beat(BeatKind.Dread, "the hostler answers to a name that is not his", DreadDc: 15, DreadTier: 2),
                    new Beat(BeatKind.Toll, "a night in the cold with the doors barred", Toll: 2),
                }),
            new Act("Act Two — The First Taking",
                "It takes somebody the posse has spoken to, and leaves what it does not need.",
                new[]
                {
                    new Beat(BeatKind.Dread, "what is left of the one it finished with", DreadDc: 17, DreadTier: 2),
                    new Beat(BeatKind.Fight, "the tack room, and the two it has already been inside",
                        Foes: new[] { "The Possessed", "The Possessed" }),
                }),
            new Act("Act Three — The Tell Made Plain",
                "The tell named out loud, and the thing that no longer needs the face.",
                new[]
                {
                    new Beat(BeatKind.Dread, "it stops pretending", DreadDc: 18, DreadTier: 3),
                    new Beat(BeatKind.Fight, "the yard at first light",
                        Foes: new[] { "The Skin-Walker" }),
                }),
        });

    // ---------------------------------------------------------------- III
    // The third Hand, at Mission San Clavo — the ruined heart of the Basin from Ch. XIII. The two
    // book adventures both END at the mission and neither goes into it. This one does, and goes
    // under it. Level 5 puts the posse at Tier 3, which is what a Tier III boss wants.
    // The title was retired in modules-v1.1 — "The Reckoning of the Wells" collided with "The Salt
    // at Coffin Wells" on the word AND on the grammar, which is the whole reason audit_names.py
    // exists. The harness kept the dead name for six days after the module was renamed, and carried
    // it into PLAYTEST.md, which SHIPS inside BloodAndGrit-Modules.zip. Nothing looked: audit_names
    // reads the built modules and names.json, and no auditor reads this file.
    public static readonly Adventure Wells = new(
        "what-the-water-answers",
        "What the Water Answers",
        "A third reckoning — the water is going bad from the bottom up, and the mission knows why",
        PartyLevel: 5,
        Site: "Mission San Clavo",
        Truth: "The wells of the Basin were bound one by one by the padres of San Clavo, and a binding "
             + "is a thing that has to be kept rather than a thing that was done. The last keeper of it "
             + "died without telling anybody. What the wells were bound against has been coming up "
             + "through them ever since, one well at a time, from the bottom of the Basin.",
        Acts: new[]
        {
            new Act("Act One — What Comes Up With the Water",
                "A well gone wrong, and the homesteads that drink from it.",
                new[]
                {
                    new Beat(BeatKind.Dread, "what the bucket brings up", DreadDc: 16, DreadTier: 2),
                    new Beat(BeatKind.Fight, "the ones who drank first",
                        Foes: new[] { "The Drowned", "The Drowned", "The Drowned" }),
                    new Beat(BeatKind.Toll, "the walk to the mission on bad water", Toll: 3),
                }),
            new Act("Act Two — The Ledger of the Padres",
                "The mission's own record of what it bound, and what keeping it cost.",
                new[]
                {
                    new Beat(BeatKind.Dread, "the last entry, in a hand that stops mid-word", DreadDc: 17, DreadTier: 2),
                    new Beat(BeatKind.Fight, "what has been living in the nave",
                        Foes: new[] { "The Plague-Dead", "The Plague-Dead", "The Plague-Dead" }),
                }),
            new Act("Act Three — The Bottom of the Basin",
                "Down the well the padres bound first.",
                new[]
                {
                    new Beat(BeatKind.Dread, "the dark at the bottom of the shaft", DreadDc: 19, DreadTier: 3),
                    new Beat(BeatKind.Fight, "the thing the first binding was for",
                        Foes: new[] { "The Hunger That Walks", "The Drowned", "The Drowned" }),
                }),
        });

    public static readonly Adventure[] All = { Salt, Face, Wells };
}
