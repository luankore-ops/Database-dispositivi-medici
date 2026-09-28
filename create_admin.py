from sqlalchemy import select

from auth import hash_password
from database import SessionLocal
from models import Utente, RuoloUtente


def main():
    print("=" * 60)
    print(" CREAZIONE UTENTE AMMINISTRATORE")
    print("=" * 60)

    username = input("Username amministratore: ").strip()

    if not username:
        print("Errore: lo username non può essere vuoto.")
        return

    # La password viene mostrata mentre viene digitata
    password = input("Password: ")

    if len(password) < 12:
        print("Errore: la password deve contenere almeno 12 caratteri.")
        return

    confirm_password = input("Conferma password: ")

    if password != confirm_password:
        print("Errore: le password non coincidono.")
        return

    db = SessionLocal()

    try:
        existing_user = db.scalar(
            select(Utente).where(
                Utente.username == username
            )
        )

        if existing_user:
            print(
                f"Errore: l'utente '{username}' esiste già."
            )
            return

        admin = Utente(
            username=username,
            password_hash=hash_password(password),
            ruolo=RuoloUtente.ADMIN,
            attivo=True,
        )

        db.add(admin)
        db.commit()
        db.refresh(admin)

        print()
        print("=" * 60)
        print(" UTENTE AMMINISTRATORE CREATO")
        print("=" * 60)
        print(f"Username: {admin.username}")
        print(f"Ruolo:    {admin.ruolo.value}")
        print(f"ID:       {admin.id}")
        print("=" * 60)

    except Exception as exc:
        db.rollback()

        print()
        print("Errore durante la creazione dell'utente:")
        print(exc)

    finally:
        db.close()


if __name__ == "__main__":
    main()