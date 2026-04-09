# Moduły do transportu TCP i szyfrowania TLS
import socket
import ssl
from pathlib import Path

# Endpoint serwera TCP
HOST = 'localhost'
PORT = 8888

# Katalog, w którym leży ten plik (`TCP/`)
BASE_DIR = Path(__file__).resolve().parent
# Katalog z certyfikatami podpisanymi przez lokalne CA
CA_DIR = BASE_DIR.parent / "Certs" / "CA"
# Certyfikat serwera prezentowany klientowi podczas handshake TLS
SERVER_CERT = CA_DIR / "server.crt"
# Prywatny klucz odpowiadający certyfikatowi serwera
SERVER_KEY = CA_DIR / "server.key"
# Certyfikat urzędu CA używany do weryfikacji certyfikatów klientów
CA_CERT = CA_DIR / "ca.crt"


def start_server():
    # Kontekst TLS serwera definiuje parametry handshake i szyfrowania
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)

    # Wczytuje certyfikat + klucz serwera (tożsamość serwera w TLS)
    context.load_cert_chain(certfile=str(SERVER_CERT), keyfile=str(SERVER_KEY))

    # Serwer wymaga certyfikatu od klienta
    context.verify_mode = ssl.CERT_REQUIRED

    # Wczytuje zaufane CA, którym będą sprawdzane certyfikaty klientów
    context.load_verify_locations(cafile=str(CA_CERT))

    # Gniazdo TCP IPv4 odbiera nowe połączenia od klientów
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        # Pozwala szybko związać ten sam port po restarcie procesu
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # Przypina gniazdo do lokalnego endpointu
        server_socket.bind((HOST, PORT))

        # Uruchamia nasłuch TCP z kolejką oczekujących połączeń
        server_socket.listen(1)
        print(f"Serwer nasłuchuje na {HOST}:{PORT}...")

        # Pętla serwera: akceptuj połączenie, obsłuż, wróć do nasłuchu
        while True:
            # accept() kończy 3-way handshake TCP i zwraca gniazdo sesji.
            client_socket, addr = server_socket.accept()
            print(f"\nNawiązano połączenie TCP z {addr}")

            try:
                # wrap_socket wykonuje handshake TLS i przechodzi na kanał szyfrowany
                with context.wrap_socket(client_socket, server_side=True) as tls_socket:
                    print("Połączenie TLS zostało poprawnie ustanowione! Czekam na dane...\n")

                    # Pętla odbioru rekordów TLS niosących dane aplikacyjne
                    while True:
                        # recv() pobiera do 1024 bajtów odszyfrowanego payloadu
                        data = tls_socket.recv(1024)

                        # Pusty bufor oznacza zamknięcie strumienia przez klienta
                        if not data:
                            print("Klient zakończył połączenie.")
                            break

                        # Dekoduje bajty UTF-8 na tekst aplikacyjny
                        tekst = data.decode('utf-8')
                        # Loguje wiadomość odebraną po TLS
                        print(f"Odebrane dane: {tekst}")
            except ssl.SSLError as e:
                # Błąd warstwy TLS (np. handshake lub certyfikat)
                print(f"Błąd SSL: {e}")
            except Exception as e:
                # Błąd transportu lub logiki aplikacyjnej
                print(f"Wystąpił błąd: {e}")


if __name__ == "__main__":
    start_server()