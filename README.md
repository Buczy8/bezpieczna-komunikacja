# Bezpieczna komunikacja TCP z TLS i własnym CA

Ten projekt pokazuje komunikację **TCP klient-serwer** zabezpieczoną warstwą **TLS**.
Serwer korzysta z certyfikatu podpisanego przez lokalne **CA** (Certification Authority), a klient ufa temu CA.

## Co robi projekt

- `TCP/server.py` uruchamia serwer TCP i otwiera połączenie TLS.
- `TCP/client.py` łączy się z serwerem, wykonuje handshake TLS i wysyła wiadomości.
- Cała komunikacja aplikacyjna jest szyfrowana.

## Struktura katalogów

```text
Bezpieczna komunikacja/
├── README.md
└── TCP/
    ├── client.py
    ├── server.py
    ├── CA/
    │   ├── ca.crt
    │   ├── ca.key
    │   ├── ca.srl
    │   ├── client.crt
    │   ├── client.csr
    │   ├── client.key
    │   ├── server.crt
    │   ├── server.csr
    │   └── server.key
    └── Self signed/
        ├── cert.pem
        └── key.pem
```

## Wymagania

- Python 3.10+ (lub nowszy)
- OpenSSL
- System Linux, macOS lub Windows

## Jak działa wariant z CA

Najpierw tworzysz własne CA, potem generujesz klucz i żądanie certyfikatu dla serwera, a następnie podpisujesz to żądanie certyfikatem CA.

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
mkdir -p TCP/CA
cd TCP/CA
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
openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out server.crt -days 365 -sha25
```

Wynikiem jest `server-cert.pem`, czyli certyfikat serwera podpisany przez lokalne CA.

### 8. Wygeneruj certyfikat klienta

W katalogu `TCP/CA/` analogicznie do serwera wykonaj:

```bash
openssl genrsa -out client.key 2048
openssl req -new -key client.key -out client.csr
openssl x509 -req -in client.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out client.crt -days 365 -sha256
```

## Co oznaczają wygenerowane pliki

### `TCP/CA/ca.key`

- prywatny klucz CA,
- używany do podpisywania certyfikatów,
- nie powinien być udostępniany.

### `TCP/CA/ca.crt`

- publiczny certyfikat CA,
- klient używa go do sprawdzenia, czy certyfikat serwera został podpisany przez zaufane CA.

### `TCP/CA/ca.srl`

- plik z numerem seryjnym,
- OpenSSL używa go przy wystawianiu kolejnych certyfikatów,
- pozwala utrzymać unikalne numery seryjne certyfikatów.

### `TCP/CA/server.key`

- prywatny klucz serwera,
- służy serwerowi do potwierdzenia własnej tożsamości podczas handshake TLS.

### `TCP/CA/server.csr`

- CSR, czyli Certificate Signing Request,
- zawiera publiczną część klucza serwera i dane identyfikacyjne,
- trafia do CA w celu podpisania.

### `TCP/CA/server.crt`

- certyfikat serwera podpisany przez CA,
- to właśnie ten plik serwer ładuje podczas startu TLS.

Analogicznie działają pliki z klietem
## Wariant self-signed

Katalog `TCP/Self signed/` zawiera prostszy wariant testowy, w którym serwer używa certyfikatu self-signed.

### `TCP/Self signed/key.pem`

- prywatny klucz serwera dla testowego wariantu.

### `TCP/Self signed/cert.pem`

- certyfikat self-signed wygenerowany bez osobnego CA,
- przydatny do szybkich testów lokalnych.

Jeśli chcesz odtworzyć ten wariant, możesz użyć:

```bash
cd TCP/Self\ signed
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

## Co dzieje się w kodzie

- serwer tworzy kontekst TLS i ładuje `CA/server-cert.pem` oraz `CA/server-key.pem`,
- klient ładuje `CA/ca-cert.pem` do magazynu zaufania,
- podczas połączenia wykonywany jest handshake TLS,
- po jego zakończeniu dane są wysyłane w zaszyfrowanym kanale.

## Najważniejsze ustawienia

- `HOST = 'localhost'`
- `PORT = 8888`

Jeżeli zmienisz adres lub port w kodzie, musisz zrobić to w `server.py` i `client.py`.

## Uwagi bezpieczeństwa

- To projekt dydaktyczny, więc nie nadaje się do produkcji bez dodatkowych zmian.
- Klucz prywatny CA (`ca-key.pem`) powinien być chroniony szczególnie mocno.
- W kliencie wyłączono sprawdzanie nazwy hosta, żeby uprościć test lokalny.
- W środowisku produkcyjnym należy włączyć pełną weryfikację certyfikatu i hosta.

## Najczęstsze problemy

- **Brak połączenia**: upewnij się, że serwer działa przed uruchomieniem klienta.
- **Błąd TLS/SSL**: sprawdź, czy pliki w `TCP/CA/` są kompletne.
- **Zły adres/port**: sprawdź wartość `HOST` i `PORT` w obu plikach.
