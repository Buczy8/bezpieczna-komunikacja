import asyncio
from pathlib import Path
from aioquic.asyncio import serve
from aioquic.quic.configuration import QuicConfiguration
from aioquic.quic.events import StreamDataReceived
from aioquic.asyncio.protocol import QuicConnectionProtocol

HOST = 'localhost'
PORT = 8888

# Katalog, w którym leży ten plik (`QUIC/`)
BASE_DIR = Path(__file__).resolve().parent
# Katalog certyfikatów CA współdzielony z wariantem TCP
CA_DIR = BASE_DIR.parent / "Certs" / "CA"
# Tożsamość serwera QUIC: certyfikat + klucz prywatny
SERVER_CERT = CA_DIR / "server.crt"
SERVER_KEY = CA_DIR / "server.key"


class MyQuicServer(QuicConnectionProtocol):
    def quic_event_received(self, event):
        # Metoda wywoływana dla każdego zdarzenia przychodzącego z warstwy QUIC.
        if isinstance(event, StreamDataReceived):
            # Zdarzenie zawiera bajty danych przesłane przez klienta.
            wiadomosc = event.data.decode('utf-8')
            print(f" Odebrano: {wiadomosc}")


async def main():
    # Konfiguracja endpointu QUIC po stronie serwera.
    configuration = QuicConfiguration(is_client=False)
    # Ładujemy certyfikat i klucz serwera używane podczas handshake TLS 1.3 w QUIC.
    configuration.load_cert_chain(str(SERVER_CERT), str(SERVER_KEY))

    print(f"Serwer QUIC nasłuchuje na UDP {HOST}:{PORT}...")

    # Startuje nasłuch UDP i tworzy `MyQuicServer` dla nowych połączeń.
    await serve(HOST, PORT, configuration=configuration, create_protocol=MyQuicServer)

    # Blokuje główne zadanie, żeby proces serwera nie zakończył się od razu.
    await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())