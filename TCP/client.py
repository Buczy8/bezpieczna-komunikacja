# Moduły do połączenia TCP i szyfrowania TLS po stronie klienta
import socket
import ssl
from pathlib import Path

# Endpoint serwera, do którego klient inicjuje sesję
HOST = 'localhost'
PORT = 8888

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


def start_client():
    # Kontekst TLS klienta steruje walidacją certyfikatu i handshake
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)

    # Dodaje certyfikat CA do magazynu zaufania klienta
    context.load_verify_locations(cafile=str(CA_CERT))

    # Włącza weryfikację nazwy hosta z certyfikatu serwera (CN/SAN)
    context.check_hostname = True

    # Klient ładuje swoją tożsamość, aby przedstawić się serwerowi (mTLS)
    context.load_cert_chain(certfile=str(CLIENT_CERT), keyfile=str(CLIENT_KEY))

    # Gniazdo TCP IPv4 zestawia transport do serwera
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        print(f"Próba nawiązania połączenia TLS z {HOST}:{PORT}...")

        try:
            # wrap_socket przygotowuje tunel TLS nad istniejącym socketem TCP
            with context.wrap_socket(client_socket, server_hostname=HOST) as tls_socket:
                # connect() wykonuje TCP handshake, a potem handshake TLS
                tls_socket.connect((HOST, PORT))
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