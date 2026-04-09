# Bezpieczna komunikacja TCP i QUIC z TLS i własnym CA

Ten projekt pokazuje komunikację **TCP klient-serwer** oraz **QUIC klient-serwer** zabezpieczoną warstwą **TLS**.
Serwer korzysta z certyfikatu podpisanego przez lokalne **CA** (Certification Authority), a klient ufa temu CA.

## Co robi projekt

- `TCP/server.py` uruchamia serwer TCP i otwiera połączenie TLS.
- `TCP/client.py` łączy się z serwerem, wykonuje handshake TLS i wysyła wiadomości.
- `QUIC/server.py` uruchamia serwer QUIC (UDP + TLS 1.3) i wymusza certyfikat klienta.
- `QUIC/client.py` łączy się z serwerem QUIC i wysyła wiadomości strumieniami.
- Cała komunikacja aplikacyjna jest szyfrowana.
- Wariant TCP i QUIC działa spójnie w trybie mTLS (obie strony prezentują certyfikat).

## Struktura katalogów

```text
Bezpieczna komunikacja/
├── README.md
├── Certs/
│   ├── CA/
│   │   ├── ca.crt
│   │   ├── ca.key
│   │   ├── ca.srl
│   │   ├── client.crt
│   │   ├── client.csr
│   │   ├── client.key
│   │   ├── san.cnf
│   │   ├── server.crt
│   │   ├── server.csr
│   │   └── server.key
│   └── Self signed/
│       ├── cert.pem
│       └── key.pem
├── QUIC/
│   ├── client.py
│   └── server.py
└── TCP/
    ├── client.py
    └── server.py
```

## Wymagania

- Python 3.10+ (lub nowszy)
- OpenSSL
- System Linux, macOS lub Windows

## Jawna polityka TLS/QUIC

- **TCP**: TLS 1.2+ (`ssl.PROTOCOL_TLS_SERVER` / `ssl.PROTOCOL_TLS_CLIENT`, `minimum_version=TLSv1_2`).
- **QUIC**: TLS 1.3 (wynika z protokołu QUIC i `aioquic`).
- **mTLS**: serwer wymaga certyfikatu klienta, klient wymaga poprawnego certyfikatu serwera.
- **Zaufanie**: certyfikaty obu stron muszą być podpisane przez lokalne CA (`Certs/CA/ca.crt`).
- **Host verification**: klient TCP ma `check_hostname=True`, więc `CN/SAN` certyfikatu serwera musi pasować do hosta.
- **ALPN**: oba transporty używają jednego identyfikatora aplikacyjnego `secure-chat/1`.

## Model zagrożeń (skrót)

Założenia:
- Atakujący może podsłuchiwać i modyfikować ruch sieciowy (MITM).
- Atakujący może próbować podszyć się pod klienta lub serwer.
- Atakujący nie ma dostępu do poprawnie chronionych kluczy prywatnych.

Chronimy się przed:
- podsłuchem treści wiadomości (szyfrowanie TLS),
- podszyciem pod serwer (walidacja certyfikatu serwera przez klienta),
- podszyciem pod klienta (wymaganie certyfikatu klienta przez serwer),
- prostą modyfikacją danych w locie (integralność rekordów TLS).

Poza zakresem tego projektu:
- HSM, OCSP/CRL online, automatyczna rotacja certyfikatów,
- twarde limity anty-DoS i pełny monitoring produkcyjny.

## Kryteria ocen 3.0 / 4.0 / 5.0

- **3.0**: działa szyfrowana komunikacja TLS na TCP (np. certyfikaty self-signed).
- **4.0**: działa obustronne uwierzytelnianie certyfikatami (mTLS) dla klienta i serwera.
- **5.0**: działa klient i serwer QUIC oraz zachowana jest spójna polityka bezpieczeństwa (mTLS + weryfikacja certyfikatów) między TCP i QUIC.

Dla czytelności oceny:
- `TCP/server.py` + `TCP/client.py` realizują TLS + mTLS na TCP,
- `QUIC/server.py` + `QUIC/client.py` realizują TLS 1.3 + mTLS na QUIC.

## Jak działa wariant z CA

Najpierw tworzysz własne CA, potem generujesz klucz i żądanie certyfikatu dla serwera, a następnie podpisujesz to żądanie certyfikatem CA.

> Uwaga: klucze prywatne i wygenerowane certyfikaty to artefakty runtime/deweloperskie.
> W repo przechowujemy tylko szablony/konfiguracje (np. `.cnf`) i dokumentację, a nie sekrety.

Ten wariant zapewnia **uwierzytelnianie serwera**: klient sprawdza, czy certyfikat serwera został podpisany przez zaufane CA.

Jeśli chcesz zrobić **obustronne uwierzytelnianie** (**mTLS**), dopisz jeszcze certyfikat klienta podpisany przez to samo CA i ustaw serwer tak, żeby wymagał certyfikatu klienta.
### Co daje mTLS

- serwer potwierdza tożsamość klienta,
- klient potwierdza tożsamość serwera,
- połączenie działa tylko dla certyfikatów wystawionych przez zaufane CA.

### 1. Wejdź do katalogu projektu

```bash
cd "/sciezka/do/projektu/Bezpieczna komunikacja"
```

### 2. Utwórz katalog na pliki CA

```bash
mkdir -p Certs/CA
cd Certs/CA
```

### 3. Wygeneruj klucz prywatny CA

```bash
openssl genrsa -out ca.key 2048
```

Ten plik jest tajny. Służy do podpisywania certyfikatów.

### 4. Wygeneruj certyfikat CA

```bash
openssl req -x509 -new -nodes -key ca.key -sha256 -days 3650 -out ca.crt
```

To publiczny certyfikat CA. Ten plik dodajesz do zaufanych po stronie klienta.

### 5. Wygeneruj klucz prywatny serwera

```bash
openssl genrsa -out server.key 2048
```

To tajny klucz serwera. Musi pozostać na komputerze, na którym działa serwer.

### 6. Wygeneruj żądanie podpisania certyfikatu dla serwera

```bash
openssl req -new -key server.key -out server.csr
```

Gdy konsola spyta o CN to trzeba podać `localhost`. Plik `server.csr` zawiera dane potrzebne do wystawienia certyfikatu serwera.

### 7. Podpisz żądanie certyfikatem CA

```bash
openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out server.crt -days 365 -sha256
```

Wynikiem jest `server.crt`, czyli certyfikat serwera podpisany przez lokalne CA.

Jeśli chcesz jawnie dodać SAN z pliku konfiguracyjnego, możesz użyć wariantu:

```bash
openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out server.crt -days 365 -sha256 -extfile san.cnf -extensions v3_req
```

### 8. Wygeneruj certyfikat klienta

W katalogu `Certs/CA/` analogicznie do serwera wykonaj:

```bash
openssl genrsa -out client.key 2048
openssl req -new -key client.key -out client.csr
openssl x509 -req -in client.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out client.crt -days 365 -sha256
```

## Co oznaczają wygenerowane pliki

### `Certs/CA/ca.key`

- prywatny klucz CA,
- używany do podpisywania certyfikatów,
- nie powinien być udostępniany.

### `Certs/CA/ca.crt`

- publiczny certyfikat CA,
- klient używa go do sprawdzenia, czy certyfikat serwera został podpisany przez zaufane CA.

### `Certs/CA/ca.srl`

- plik z numerem seryjnym,
- OpenSSL używa go przy wystawianiu kolejnych certyfikatów,
- pozwala utrzymać unikalne numery seryjne certyfikatów.

### `Certs/CA/san.cnf`

- plik konfiguracyjny OpenSSL z ustawieniami rozszerzeń certyfikatu,
- najczęściej definiuje `subjectAltName` (SAN), np. `DNS:localhost`, `IP:127.0.0.1`,
- dzięki temu weryfikacja hosta po stronie klienta działa poprawnie przy `check_hostname = True`.

### `Certs/CA/server.key`

- prywatny klucz serwera,
- służy serwerowi do potwierdzenia własnej tożsamości podczas handshake TLS.

### `Certs/CA/server.csr`

- CSR, czyli Certificate Signing Request,
- zawiera publiczną część klucza serwera i dane identyfikacyjne,
- trafia do CA w celu podpisania.

### `Certs/CA/server.crt`

- certyfikat serwera podpisany przez CA,
- to właśnie ten plik serwer ładuje podczas startu TLS.

Analogicznie działają pliki klienta: `Certs/CA/client.key`, `Certs/CA/client.csr`, `Certs/CA/client.crt`.
## Wariant self-signed

Katalog `Certs/Self signed/` zawiera prostszy wariant testowy, w którym serwer używa certyfikatu self-signed.

### `Certs/Self signed/key.pem`

- prywatny klucz serwera dla testowego wariantu.

### `Certs/Self signed/cert.pem`

- certyfikat self-signed wygenerowany bez osobnego CA,
- przydatny do szybkich testów lokalnych.

Jeśli chcesz odtworzyć ten wariant, możesz użyć:

```bash
cd Certs/Self\ signed
openssl req -x509 -newkey rsa:2048 -keyout key.pem -out cert.pem -days 365 -nodes -subj "/CN=localhost"
```

## Uruchomienie programu

### 1. Uruchom serwer

W osobnym terminalu:

```bash
cd "/home/pawel/Dokumenty/Studia/Semestr 6/Programowanie usług sieciowych/Projekty/Bezpieczna komunikacja/TCP"
python3 server.py
```

### 2. Uruchom klienta

W drugim terminalu:

```bash
cd "/home/pawel/Dokumenty/Studia/Semestr 6/Programowanie usług sieciowych/Projekty/Bezpieczna komunikacja/TCP"
python3 client.py
```

### 3. (Opcjonalnie) wariant QUIC

W dwóch osobnych terminalach:

```bash
cd "/home/pawel/Dokumenty/Studia/Semestr 6/Programowanie usług sieciowych/Projekty/Bezpieczna komunikacja/QUIC"
python3 server.py
```

```bash
cd "/home/pawel/Dokumenty/Studia/Semestr 6/Programowanie usług sieciowych/Projekty/Bezpieczna komunikacja/QUIC"
python3 client.py
```

## Co dzieje się w kodzie

- pliki `.py` wyliczają ścieżki certyfikatów dynamicznie przez `Path(__file__).resolve()`,
- serwer TCP/QUIC ładuje certyfikat i klucz serwera z `Certs/CA/`,
- klient TCP/QUIC ładuje `ca.crt` do magazynu zaufania,
- klient TCP ładuje też własny certyfikat i klucz (`client.crt`, `client.key`) do mTLS,
- podczas połączenia wykonywany jest handshake TLS,
- po jego zakończeniu dane są wysyłane w zaszyfrowanym kanale.

## Najważniejsze ustawienia

- `HOST = 'localhost'`
- `PORT = 8888`

Jeżeli zmienisz adres lub port w kodzie, musisz zrobić to w `server.py` i `client.py`.

## Uwagi bezpieczeństwa

- To projekt dydaktyczny, więc nie nadaje się do produkcji bez dodatkowych zmian.
- Klucz prywatny CA (`Certs/CA/ca.key`) powinien być chroniony szczególnie mocno.
- W kliencie jest włączone sprawdzanie nazwy hosta (`check_hostname = True`), więc certyfikat serwera powinien mieć poprawny `CN`/`SAN`.
- W środowisku produkcyjnym należy włączyć pełną weryfikację certyfikatu i hosta.
- `.gitignore` ignoruje wygenerowane artefakty PKI (`*.key`, `*.csr`, `*.crt`, `*.pem`, `*.srl`) w katalogu `Certs/`.

## Najczęstsze problemy

- **Brak połączenia**: upewnij się, że serwer działa przed uruchomieniem klienta.
- **Błąd TLS/SSL**: sprawdź, czy pliki w `Certs/CA/` są kompletne.
- **Zły adres/port**: sprawdź wartość `HOST` i `PORT` w obu plikach.
