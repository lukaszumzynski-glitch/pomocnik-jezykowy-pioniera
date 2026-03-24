import bcrypt
password = input("Podaj hasło: ")
hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
print(f"Zahashowane hasło: {hashed}")
