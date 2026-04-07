# Bezpieczna komunikacja TCP (TLS)

Projekt pokazuje prostą komunikację **klient-serwer TCP** zabezpieczoną przez **TLS** z użyciem certyfikatu self-signed.

## Co robi projekt

- `TCP/server.py` uruchamia serwer TCP i owija połączenie warstwą TLS.
- `TCP/client.py` łączy się z serwerem, wykonuje handshake TLS i wysyła wiadomości.
- Dane aplikacyjne są przesyłane w zaszyfrowanym kanale TLS.

## Struktura katalogów

```text
Bezpieczna komunikacja/
├── README.md
└── TCP/
    ├── server.py
    ├── client.py
    ├── cert.pem
    └── key.pem
```

## Wymagania

- Python 3.10+ (zalecane)
- OpenSSL (do ewentualnego wygenerowania certyfikatów)
- System Linux/macOS/Windows

## Szybki start

Przejdź do katalogu projektu:

```bash
cd "/home/pawel/Dokumenty/Studia/Semestr 6/Programowanie usług sieciowych/Projekty/Bezpieczna komunikacja"
```

Uruchom serwer (terminal 1):

```bash
cd TCP
python3 server.py
```

Uruchom klienta (terminal 2):

```bash
cd TCP
python3 client.py
```

## Generowanie certyfikatu self-signed (opcjonalnie)

Jeśli chcesz odtworzyć pliki `cert.pem` i `key.pem`:

```bash
cd TCP
openssl req -x509 -newkey rsa:2048 -keyout key.pem -out cert.pem -days 365 -nodes -subj "/CN=localhost"
```

## Uwagi bezpieczeństwa

- To projekt dydaktyczny; certyfikat self-signed nie daje zaufania jak CA publiczne.
- W kliencie ustawiono `check_hostname = False`, co upraszcza testy lokalne, ale nie jest zalecane produkcyjnie.
- W środowisku produkcyjnym użyj certyfikatów od zaufanego CA i pełnej weryfikacji hosta.

## Najczęstsze problemy

- **Brak połączenia**: upewnij się, że najpierw działa `server.py`.
- **Błąd TLS/SSL**: sprawdź, czy `cert.pem` i `key.pem` są w katalogu `TCP/`.
- **Zły adres/port**: w obu plikach ustawiono `HOST='127.0.0.2'`, `PORT=8888`.
