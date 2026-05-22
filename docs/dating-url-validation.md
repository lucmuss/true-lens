# Dating URL Validation Strategy

## Summary
Official documentation does not provide one universal, permanent, web-share URL schema for all major dating platforms.
Because of this, validation is implemented as:
1. strict `https://` URL parsing,
2. trusted domain allowlist,
3. optional path checks where platform-specific share flows are documented.

## Implemented allowlist (8 platforms)
1. Tinder (`tinder.com`)
2. Bumble (`bumble.com`)
3. Hinge (`hinge.co`, `hinge.com`)
4. OkCupid (`okcupid.com`)
5. Match (`match.com`)
6. PlentyOfFish (`pof.com`, `plentyoffish.com`)
7. Badoo (`badoo.com`)
8. Happn (`happn.com`)

## Why domain-based validation for most platforms?
- Bumble explicitly documents shareable profile links generated in-app.
- Tinder documents unique share links in Matchmaker flow.
- Several other platforms document profile/account usage but do not publish a stable universal profile-share URL format in Help Center docs.

Therefore, parser correctness is guaranteed at domain/trust level and protocol level, while path conventions stay tolerant.

## Sources checked
- Bumble Support: Recommending people to others
  - https://support.bumble.com/hc/en-us/articles/28422987446685-Recommending-people-to-others
- Tinder Help: Tinder Matchmaker
  - https://www.help.tinder.com/hc/en-us/articles/20033039713549-Tinder-Matchmaker
- Hinge Help (profile/help context)
  - https://help.hinge.co/hc/en-us/articles/360011053094-Wie-bearbeite-ich-mein-Profil
- Match Help (profile/help context)
  - https://help.match.com/hc/en-us/articles/6241665737755-Viewing-Your-Own-Profile
- Plenty of Fish Help (profile/help context)
  - https://help.pof.com/hc/en-us/articles/41812694834843-Updating-your-profile
- Badoo Help (account/profile context)
  - https://support.badoo.com/hc/en-us/articles/32091368450205-Signing-up-and-logging-in
- Happn official site (product/profile context)
  - https://www.happn.com/?lng=en
- OkCupid profile help center section
  - https://okcupid-app.zendesk.com/hc/en-us/sections/22707390701211-Profile
