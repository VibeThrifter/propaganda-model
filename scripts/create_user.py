#!/usr/bin/env python3
"""
Gebruikersbeheer-CLI (verbeterplan M0.6): accounts voor mensen en agents.

Voorbeelden:
    # Eigenaarsaccount (mens, maintainer) met een API-token voor Claude Code:
    python3 scripts/create_user.py maxime --rol maintainer --new-token --save

    # Wachtwoord (interactief) zetten voor de inlogportal:
    python3 scripts/create_user.py maxime --set-password

    # Agent-account (provenance verplicht) met token:
    python3 scripts/create_user.py monitor-agent --kind agent --provenance "claude-fable-5" \
        --new-token --save

    # Overzicht:
    python3 scripts/create_user.py --list

Bestaat de gebruiker al, dan werken --rol/--new-token/--set-password als update.
Het token wordt één keer getoond (en met --save naar data/tokens/<naam>.token
geschreven, chmod 600); in de database staat alleen de sha256-hash.
"""
import argparse
import getpass
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
import auth  # noqa: E402  (repo-root module, gedeeld met server.py)

DB_PATH = ROOT / "data" / "propaganda_model.db"
TOKENS_DIR = ROOT / "data" / "tokens"


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("username", nargs="?", help="gebruikersnaam (kebab-case)")
    parser.add_argument("--kind", choices=["mens", "agent"], default="mens")
    parser.add_argument("--rol", choices=["bijdrager", "reviewer", "maintainer"],
                        default=None, help="rol (default bij aanmaak: bijdrager)")
    parser.add_argument("--provenance", help="agents: model + versie (verplicht)")
    parser.add_argument("--new-token", action="store_true",
                        help="genereer/roteer het API-token (één keer getoond)")
    parser.add_argument("--save", action="store_true",
                        help="schrijf het token naar data/tokens/<naam>.token (chmod 600)")
    parser.add_argument("--set-password", action="store_true",
                        help="zet interactief een wachtwoord (alleen mensen)")
    parser.add_argument("--deactivate", action="store_true", help="zet het account op inactief")
    parser.add_argument("--list", action="store_true", help="toon alle accounts")
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    if args.list:
        for u in conn.execute("SELECT username, kind, role, active, provenance,"
                              " password_hash IS NOT NULL AS pw, token_hash IS NOT NULL AS tok,"
                              " created_at, last_login_at FROM users ORDER BY id"):
            vlag = "" if u["active"] else " [INACTIEF]"
            extra = f" provenance={u['provenance']}" if u["provenance"] else ""
            print(f"{u['username']:<20} {u['kind']:<6} {u['role']:<11}"
                  f" wachtwoord={'ja' if u['pw'] else 'nee'} token={'ja' if u['tok'] else 'nee'}"
                  f"{extra}{vlag}")
        conn.close()
        return

    if not args.username:
        parser.error("username is verplicht (of gebruik --list)")
    naam = args.username.strip()

    bestaand = conn.execute("SELECT * FROM users WHERE username = ?", (naam,)).fetchone()
    if bestaand is None:
        if args.kind == "agent" and not args.provenance:
            parser.error("een agent-account vereist --provenance (model + versie)")
        conn.execute(
            "INSERT INTO users (username, kind, role, provenance) VALUES (?, ?, ?, ?)",
            (naam, args.kind, args.rol or "bijdrager", args.provenance))
        conn.commit()
        print(f"Account aangemaakt: {naam} ({args.kind}, {args.rol or 'bijdrager'})")
    else:
        if args.rol and args.rol != bestaand["role"]:
            conn.execute("UPDATE users SET role = ? WHERE username = ?", (args.rol, naam))
            conn.commit()
            print(f"Rol bijgewerkt: {bestaand['role']} → {args.rol}")
        if args.provenance:
            conn.execute("UPDATE users SET provenance = ? WHERE username = ?",
                         (args.provenance, naam))
            conn.commit()

    if args.deactivate:
        conn.execute("UPDATE users SET active = FALSE WHERE username = ?", (naam,))
        conn.commit()
        print(f"Account gedeactiveerd: {naam}")

    if args.set_password:
        kind = conn.execute("SELECT kind FROM users WHERE username = ?", (naam,)).fetchone()[0]
        if kind != "mens":
            sys.exit("Wachtwoorden zijn alleen voor mensen; agents gebruiken een token.")
        pw = getpass.getpass(f"Nieuw wachtwoord voor {naam}: ")
        if len(pw) < 8:
            sys.exit("Minimaal 8 tekens.")
        if getpass.getpass("Nogmaals: ") != pw:
            sys.exit("Wachtwoorden verschillen.")
        conn.execute("UPDATE users SET password_hash = ? WHERE username = ?",
                     (auth.hash_password(pw), naam))
        conn.commit()
        print("Wachtwoord gezet.")

    if args.new_token:
        token = auth.new_token()
        conn.execute("UPDATE users SET token_hash = ? WHERE username = ?",
                     (auth.hash_token(token), naam))
        conn.commit()
        print(f"Nieuw token (wordt NIET opgeslagen, alleen de hash):\n  {token}")
        if args.save:
            TOKENS_DIR.mkdir(parents=True, exist_ok=True)
            pad = TOKENS_DIR / f"{naam}.token"
            pad.write_text(token + "\n")
            pad.chmod(0o600)
            print(f"Token geschreven naar {pad} (chmod 600; map staat in .gitignore)")
        print('Gebruik:  Authorization: Bearer <token>')

    conn.close()


if __name__ == "__main__":
    main()
