# Moduły do połączenia TCP i szyfrowania TLS po stronie klienta
import socket
import ssl
from pathlib import Path

# Endpoint serwera, do którego klient inicjuje sesję
HOST = 'localhost'
PORT = 8888
ALPN_PROTOCOLS = ['secure-chat/1']

# Katalog, w którym leży ten plik (`TCP/`)
BASE_DIR = Path(__file__).resolve().parent
# Katalog z certyfikatami podpisanymi przez lokalne CA
CA_DIR = BASE_DIR.parent / "Certs" / "CA"
# Certyfikat CA, któremu klient ufa przy weryfikacji serwera
CA_CERT = CA_DIR / "ca.crt"
# Certyfikat klienta prezentowany serwerowi (mTLS)
CLIENT_CERT = CA_DIR / "client.crt"
# Prywatny klucz odpowiadający certyfikatowi klienta
CLIENT_KEY = CA_DIR / "client.key"

def build_tls_context() -> ssl.SSLContext:
    # Tworzy kontekst TLS po stronie klienta
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)

    # Wymusza TLS >= 1.2 bez starych, podatnych wersji
    context.minimum_version = ssl.TLSVersion.TLSv1_2

    # Wyłącza kompresję TLS ochrona m.in. przed atakami typu CRIME
    context.options |= ssl.OP_NO_COMPRESSION

    # Klient wymaga poprawnego certyfikatu serwera
    context.verify_mode = ssl.CERT_REQUIRED

    # Sprawdza zgodność nazwy hosta z CN/SAN w certyfikacie serwera
    context.check_hostname = True

    # ALPN: klient i serwer uzgadniają wspólny protokół aplikacyjny
    context.set_alpn_protocols(ALPN_PROTOCOLS)

    # Preferowane bezpieczne szyfry dla TLS 1.2 (TLS 1.3 negocuje je osobno)
    context.set_ciphers('ECDHE+AESGCM:ECDHE+CHACHA20')

    # Zaufane CA do walidacji certyfikatu serwera
    context.load_verify_locations(cafile=str(CA_CERT))

    # mTLS: klient prezentuje własny certyfikat i klucz
    context.load_cert_chain(certfile=str(CLIENT_CERT), keyfile=str(CLIENT_KEY))
    return context


def start_client():
    context = build_tls_context()

    # Gniazdo TCP IPv4 zestawia transport do serwera
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        print(f"Próba nawiązania połączenia TLS z {HOST}:{PORT}...")

        try:
            # wrap_socket przygotowuje tunel TLS nad istniejącym socketem TCP
            with context.wrap_socket(client_socket, server_hostname=HOST) as tls_socket:
                # connect() wykonuje TCP handshake, a potem handshake TLS
                tls_socket.connect((HOST, PORT))
                print(f"Wynegocjowany protokół TLS: {tls_socket.version()}")
                print(f"Wynegocjowane ALPN: {tls_socket.selected_alpn_protocol()}")
                print(f"Wynegocjowany szyfr: {tls_socket.cipher()}\n")
                print("Połączenie TLS ustanowione!\n")

                # Pętla wysyła kolejne rekordy TLS z danymi użytkownika
                while True:
                    # Pobiera payload aplikacyjny wpisany w terminalu
                    wiadomosc = input("Wpisz wiadomość (lub 'quit' aby zakończyć): ")

                    # Komenda quit kończy sesję i zamyka połączenie
                    if wiadomosc.lower() == 'quit':
                        print("Zamykanie połączenia...")
                        break

                    # Pomija puste ramki, aby nie wysyłać zerowego payloadu
                    if wiadomosc:
                        # sendall wysyła cały bufor bajtów przez kanał TLS
                        tls_socket.sendall(wiadomosc.encode('utf-8'))

        except ssl.SSLError as e:
            # Błąd warstwy TLS (np. walidacja certyfikatu lub handshake)
            print(f"Błąd weryfikacji TLS/SSL: {e}")
        except ConnectionRefusedError:
            # Serwer nie nasłuchuje lub firewall odrzuca połączenie TCP
            print("Nie można połączyć się z serwerem. Upewnij się, że serwer jest uruchomiony.")


if __name__ == "__main__":
    start_client()