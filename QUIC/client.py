import asyncio
from pathlib import Path
from aioquic.asyncio import connect
from aioquic.quic.configuration import QuicConfiguration
from aioquic.asyncio.protocol import QuicConnectionProtocol

HOST = 'localhost'
PORT = 8888

# Katalog, w którym leży ten plik (`QUIC/`)
BASE_DIR = Path(__file__).resolve().parent
# Katalog z certyfikatem naszego lokalnego CA
CA_DIR = BASE_DIR.parent / "Certs" / "CA"
# Certyfikat CA używany do weryfikacji certyfikatu serwera QUIC
CA_CERT = CA_DIR / "ca.crt"

async def main():
    # Konfiguracja endpointu QUIC po stronie klienta.
    configuration = QuicConfiguration(is_client=True)
    # Weryfikujemy certyfikat serwera przy użyciu zaufanego certyfikatu CA.
    configuration.load_verify_locations(str(CA_CERT))

    print(f"Próba nawiązania połączenia QUIC (UDP) z {HOST}:{PORT}...")

    async with connect(HOST, PORT, configuration=configuration, create_protocol=QuicConnectionProtocol) as protocol:
        # Po wejściu w ten blok handshake QUIC/TLS jest już zakończony sukcesem.
        print("Połączenie QUIC ustanowione! Możesz zacząć pisać.\n")

        # Pętla nieskończona, dokładnie tak jak w kliencie TCP
        while True:
            # Magia asynchroniczności - input() działa w tle, nie blokując QUICa!
            wiadomosc = await asyncio.to_thread(input, "Wpisz wiadomość (lub 'quit'): ")

            if wiadomosc.lower() == 'quit':
                print("Zamykanie połączenia...")
                break

            if wiadomosc:
                # Otwieramy nowy strumień dla każdej wysyłanej wiadomości
                stream_id = protocol._quic.get_next_available_stream_id()

                # end_stream=True informuje serwer: "To cała wiadomość, możesz ją przetwarzać"
                protocol._quic.send_stream_data(
                    stream_id,
                    wiadomosc.encode('utf-8'),
                    end_stream=True
                )
                # Wysyła zakolejkowane pakiety QUIC do sieci.
                protocol.transmit()


if __name__ == "__main__":
    asyncio.run(main())