import asyncio                                                  # Moduł do uruchamiania pętli asynchronicznej event loop
import ssl                                                      # Moduł SSL/TLS - potrzebny do polityki mTLS verify_mode
from pathlib import Path                                        # Path ułatwia bezpieczne wyznaczanie ścieżek niezależnie od systemu
from aioquic.asyncio import serve                               # Funkcja `serve` uruchamia serwer QUIC na UDP
from aioquic.quic.configuration import QuicConfiguration        # Konfiguracja połączenia QUIC/TLS
from aioquic.quic.events import StreamDataReceived              # Zdarzenie informujące o danych odebranych na strumieniu
from aioquic.asyncio.protocol import QuicConnectionProtocol     # Bazowa klasa protokołu po stronie serwera/klienta QUIC

HOST = 'localhost'                      # Host, na którym serwer nasłuchuje lokalnie
PORT = 8888                             # Port UDP dla serwera QUIC
ALPN_PROTOCOLS = ['secure-chat/1']      # ALPN identyfikuje protokół aplikacyjny negocjowany w handshake TLS

BASE_DIR = Path(__file__).resolve().parent  # Katalog, w którym leży ten plik (`QUIC/`)
CA_DIR = BASE_DIR.parent / "Certs" / "CA"   # Katalog certyfikatów CA współdzielony z wariantem TCP
SERVER_CERT = CA_DIR / "server.crt"         # Certyfikat serwera QUIC prezentowany klientowi
SERVER_KEY = CA_DIR / "server.key"          # Klucz prywatny serwera QUIC
CA_CERT = CA_DIR / "ca.crt"                 # Certyfikat CA używany do weryfikacji certyfikatów klientów mTLS


# Własny protokół serwera QUIC - obsługuje zdarzenia z warstwy QUIC
class MyQuicServer(QuicConnectionProtocol):

    # Inicjalizacja obiektu protokołu dla pojedynczego połączenia
    def __init__(self, *args, **kwargs):

        # Wywołanie konstruktora klasy bazowej
        super().__init__(*args, **kwargs)

        # Bufory per strumień: stream_id -> zebrane bajty
        # Potrzebne, bo dane QUIC mogą przychodzić we fragmentach
        self._stream_buffers: dict[int, bytes] = {}

    # Callback wywoływany przez aioquic dla każdego zdarzenia QUIC
    def quic_event_received(self, event):

        # Interesuje nas zdarzenie z danymi aplikacyjnymi
        if isinstance(event, StreamDataReceived):

            # Pobierz poprzednie fragmenty dla danego strumienia albo pusty bufor
            previous = self._stream_buffers.get(event.stream_id, b'')

            # Dołóż nowy fragment danych
            current = previous + event.data

            # Jeśli klient oznaczył koniec strumienia, wiadomość jest kompletna
            if event.end_stream:

                # Usuń bufor dla zakończonego strumienia
                self._stream_buffers.pop(event.stream_id, None)

                # Dekoduj bajty na tekst UTF-8; przy błędzie podstaw znak zastępczy
                wiadomosc = current.decode('utf-8', errors='replace')

                # Wypisz finalnie odebraną wiadomość
                print(f"Odebrano wiadomość: {wiadomosc}")
            else:
                # Jeśli strumień jeszcze trwa, zapisz zaktualizowany bufor.
                self._stream_buffers[event.stream_id] = current


# Główna funkcja asynchroniczna uruchamiająca serwer.
async def main():
    # Konfiguracja serwera QUIC
    configuration = QuicConfiguration(is_client=False, alpn_protocols=ALPN_PROTOCOLS)   # Tworzy konfigurację QUIC po stronie serwera
    configuration.verify_mode = ssl.CERT_REQUIRED                                       # mTLS: serwer wymaga certyfikatu klienta
    configuration.load_cert_chain(str(SERVER_CERT), str(SERVER_KEY))                    # Wczytaj certyfikat i klucz serwera do handshake TLS 1.3
    configuration.load_verify_locations(cafile=str(CA_CERT))                            # Wczytaj zaufane CA do walidacji certyfikatów klientów

    # Log startu serwera i adresu nasłuchu UDP
    print(f"Serwer QUIC nasłuchuje na UDP {HOST}:{PORT}...")

    # Log aktywnej polityki bezpieczeństwa
    print(f"Polityka QUIC: TLS 1.3 + mTLS, ALPN={ALPN_PROTOCOLS}")

    # Uruchamia serwer QUIC:
    # - bind do host/port,
    # - dla każdego połączenia tworzy obiekt `MyQuicServer`.
    await serve(HOST, PORT, configuration=configuration, create_protocol=MyQuicServer)

    # Utrzymuje proces przy życiu serwer ma działać stale
    await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
