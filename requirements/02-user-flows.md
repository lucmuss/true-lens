# User Flows

## 1) Entry Gate
1. User opens landing page.
2. Only logo + benefits + captcha is visible.
3. Search UI remains hidden until captcha solved.
4. JS challenge token is issued and required for all API calls.

## 2) Search Step 1 (required)
Required input order:
1. Country
2. Province/region
3. First name
4. Gender

On submit:
- Backend returns candidate count only.
- If count is 0, offer "create new profile" flow.
- If count > 0, show next-step strategy buttons (Cases 1-6).

## 3) Search Cases
Case 1: First name + birthdate + city + hair color.
Case 2: First name + email + city.
Case 3: First name + phone + city.
Case 4: First name + age + city.
Case 5: First name + dating profile URL + city + age.
Case 6: First name + last name + city.

## 4) Matching Rules
- First name and last name use fuzzy matching and accent normalization.
- Step timeout is enforced in frontend and backend.
- On timeout, flow invalidates and can trigger temporary IP ban after threshold.

## 5) Profile View
Show:
- Full first name.
- Last name masked (first and last letter visible).
- Age, hair color, gender.
- Email and phone masked (first/last character visible).
- Profile views count.
- Distinct recruiter votes count.
- Attribute tiles sorted descending by vote count.

## 6) Voting
- Only authenticated recruiters.
- Max 3 categories per vote action.
- Recruiter cannot vote same profile twice.
- Recruiter can vote only once per 3 days globally.
- Optional anonymous vote toggle.
- Vote carries date (YYYY-MM-DD).
- Threshold highlighting:
  - >2 votes: highlighted.
  - >=5 votes: stronger highlight.

## 7) Contact Relay
When recruiter B votes a candidate already voted by recruiter A:
1. A receives notification mail.
2. A can click contact button.
3. B approves by replying through secure flow.
4. System then exchanges emails for both recruiters with candidate reference.

## 8) Credits
- 1 EUR = 1 credit (configurable).
- 1 daily lookup is free.
- Additional lookup consumes 1 credit.
- Reward rules:
  - New profile created: +2 credits.
  - Existing profile voted: +1 credit.
  - Missing datapoint enrichment (2 new fields): +1 credit.

## 9) Data Enrichment and Moderation
- Certain immutable fields: first name, last name, birthdate, age.
- Mutable fields: hair color, location hierarchy, secondary contact fields.
- Changes enter moderation queue and require admin approval.
