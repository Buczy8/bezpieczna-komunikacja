import asyncio                                              # Moduł do asynchronicznego działania klienta
import ssl                                                  # Moduł SSL/TLS - potrzebny do verify_mode
from pathlib import Path                                    # Path do wygodnego wyznaczania ścieżek certyfikatów
from aioquic.asyncio import connect                         # `connect` zestawia połączenie QUIC do serwera
from aioquic.quic.configuration import QuicConfiguration    # Klasa konfiguracji parametrów QUIC/TLS po stronie klienta
from aioquic.asyncio.protocol import QuicConnectionProtocol # Bazowy protokół QUIC klienta


HOST = 'localhost'                  # Host serwera QUIC
PORT = 8888                         # Port serwera QUIC (UDP)
ALPN_PROTOCOLS = ['secure-chat/1']  # ALPN protokołu aplikacyjnego negocjowanego przy handshake


BASE_DIR = Path(__file__).resolve().parent  # Katalog, w którym leży ten plik (`QUIC/`)
CA_DIR = BASE_DIR.parent / "Certs" / "CA"   # Katalog certyfikatów CA
CA_CERT = CA_DIR / "ca.crt"                 # Certyfikat CA używany do weryfikacji certyfikatu serwera
CLIENT_CERT = CA_DIR / "client.crt"         # Certyfikat klienta prezentowany serwerowi (mTLS)
CLIENT_KEY = CA_DIR / "client.key"          # Klucz prywatny klienta odpowiadający CLIENT_CERT


# Główna funkcja klienta QUIC.
async def main():
    configuration = QuicConfiguration(is_client=True, alpn_protocols=ALPN_PROTOCOLS)    # Konfiguracja QUIC klienta + ALPN
    configuration.verify_mode = ssl.CERT_REQUIRED                                       # Klient wymaga poprawnego certyfikatu serwera
    configuration.load_verify_locations(str(CA_CERT))                                   # Załaduj CA do walidacji certyfikatu serwera
    configuration.load_cert_chain(str(CLIENT_CERT), str(CLIENT_KEY))                    # Załaduj tożsamość klienta (cert + klucz) dla mTLS

    # Log próby połączenia.
    print(f"Próba nawiązania połączenia QUIC (UDP) z {HOST}:{PORT}...")

    # Tworzy i utrzymuje połączenie QUIC w kontekście asynchronicznym
    async with connect(
        HOST,
        PORT,
        configuration=configuration,
        create_protocol=QuicConnectionProtocol
    ) as protocol:
        # W tym miejscu handshake QUIC/TLS już się powiódł
        print(f"Połączenie QUIC ustanowione! Polityka ALPN={ALPN_PROTOCOLS}\n")

        # Pętla wysyłki wiadomości wpisywanych przez użytkownika
        while True:
            # `input()` działa w osobnym wątku, żeby nie blokować event loop
            wiadomosc = await asyncio.to_thread(input, "Wpisz wiadomość (lub 'quit'): ")

            # Komenda kończąca sesję
            if wiadomosc.lower() == 'quit':
                print("Zamykanie połączenia...")
                break

            # Pomiń puste wiadomości
            if wiadomosc:
                # Otwórz nowy strumień QUIC do wysyłki tej wiadomości
                _, writer = await protocol.create_stream()

                # Zapisz dane na strumień
                writer.write(wiadomosc.encode('utf-8'))

                # Zasygnalizuj koniec strumienia (end_stream=True semantycznie)
                writer.write_eof()

                # Wymuś flush bufora do warstwy transportowej
                await writer.drain()


if __name__ == "__main__":
    asyncio.run(main())
