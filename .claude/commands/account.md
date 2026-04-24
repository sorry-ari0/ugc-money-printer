Manage TikTok accounts.

Usage:
  /account add @handle    — Register a new account
  /account use @handle    — Switch active account
  /account list           — Show all accounts and active one

Steps:
1. Parse the subcommand (add/use/list)
2. Use AccountManager from ugc.accounts
3. For 'add': create account directory structure, start initial download
4. For 'use': switch active account in accounts.json
5. For 'list': display all accounts with active indicator
