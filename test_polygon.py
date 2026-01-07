# test_massive.py
import asyncio
from app.services.polygon.client import MassiveClient

async def test_massive_connection():
    async with MassiveClient() as client:
        try:
            # Obtener tickers de acciones activas
            print("Obteniendo lista de tickers...")
            tickers = await client.get_tickers(limit=5)  # Solo 5 para el ejemplo
            print("Tickers obtenidos:")
            for ticker in tickers.get('results', [])[:5]:  # Mostrar solo los primeros 5
                print(f"- {ticker.get('ticker')}: {ticker.get('name')}")
                
        except Exception as e:
            print(f"Error al conectar con Massive.com: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_massive_connection())