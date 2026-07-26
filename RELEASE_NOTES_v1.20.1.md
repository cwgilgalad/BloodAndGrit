## GritKeeper v1.20.1

Two things were noted as loose ends at the end of v1.20.0. Both are fixed at the source rather than in the text, because both are the kind that come back otherwise.

### The reference screen said eleven leaves. It holds thirteen.

Miracles of the Faithful and Running in Town were added to the Keeper's screen back in v1.17.0, and the prose describing the deck was not. So the five-minute lesson, the README, and the handoff doc all told Keepers there were eleven leaves while the app paged through thirteen.

Correcting the sentence would have lasted until the next leaf. Instead the count is now **derived** from `RefLeafTitles` — the single list the deck is built from — and every mention interpolates it. Add a leaf and the prose is right by construction.

`--selftest` also builds the deck on purpose now (tabs are realized lazily, so it was never touched by the old check) and confirms every title has a renderer beside it. **16 checks, all passing, up from 13.**

### `package.ps1` no longer dies on a running app

If a copy of GritKeeper is running out of the delivered `GritKeeper\app\` folder, it holds its own exe and the packaging step cannot overwrite it. That failed twice during this session's releases — two thirds of the way through, as a raw `Copy-Item` access error that named no cause.

Now the script looks for the process before it starts:

```
GritKeeper.exe  version 1.20.1.0  signature Valid
  GritKeeper is running from GritKeeper\app (pid 20368, started 13:58).
  It holds GritKeeper\app\GritKeeper.exe, so that folder is left as it is.
  Building the zip from a staging tree instead — the zip is unaffected.
  Close that instance and re-run to bring GritKeeper\app up to date too.
```

The running instance is never touched. The zip is built from a staging tree and is byte-for-byte what it would have been. Two more improvements while in there: the script **verifies the zip carries the exe, the README, and the full source** before declaring itself ready, and it prints the exact `gh release create` line for the version it just packaged instead of a hard-coded old one.

Smoke suite green; self-test 16/16; the button audit reports 118 buttons, every one with a handler and a tooltip.

**Install:** download `GritKeeper.zip`, unzip, run `GritKeeper.exe`. Self-contained and Authenticode-signed — no .NET install, nothing to configure.
