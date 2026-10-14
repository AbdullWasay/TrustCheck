# TrustCheck PK — Prompt Document (Assignment 3)

GitHub URL: https://github.com/AbdullWasay/TrustCheck

## Main prompts

1. **Integrate Assignment 3 stack into the existing MVP**
   - Intent: Turn the Assignment 2 React MVP into a full app with React frontend, Python backend, and Supabase persistence while keeping all screens working.

2. **Keep Supabase credentials on the backend only**
   - Intent: Meet the security requirement that API keys/connection secrets are environment variables and not exposed in frontend code.

3. **Persist the full seller-check workflow**
   - Intent: Save login/register users and each seller check step to Supabase, then retrieve history and assessment results for Trust Snapshot, Evidence, and Decision screens.

## Follow-up prompts

4. **Add dynamic trust scoring in Python**
   - Intent: Replace hardcoded medium-risk copy with backend logic based on payment method, return policy, HTTPS, and contact details.

5. **Show saved checks from Supabase on the seller check screen**
   - Intent: Prove data retrieval from the database for the demo video / Table Editor walkthrough.

6. **Prepare local run scripts and env examples**
   - Intent: Make the project easy to start for development and deployment demos.
