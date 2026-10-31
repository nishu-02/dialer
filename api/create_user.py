import sys

from app.auth import create_user

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("usage: python create_user.py <email> <password> [role]")
        sys.exit(1)
    email, password = sys.argv[1], sys.argv[2]
    role = sys.argv[3] if len(sys.argv) > 3 else "rep"
    create_user(email, password, role)
    print(f"created {email}")
