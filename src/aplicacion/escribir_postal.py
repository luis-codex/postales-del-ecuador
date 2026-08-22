"""El caso de uso: escribir la postal de hoy.

El bucle de reintentos reparte las tres capas de forma limpia: la aplicacion
insiste, la infraestructura llama al modelo, y el dominio dicta si lo escrito
sirve. Ninguna de las tres sabe como hacen su trabajo las otras.
"""

from datetime import datetime

from dominio.modelos import ZONA_ECUADOR, Postal
from dominio.seleccion import elegir_lugar, elegir_tono
from dominio.validacion import revisar


class EscribirPostal:
    def __init__(self, catalogo, memoria, clima, escritor, archivo, intentos=3):
        self._catalogo = catalogo
        self._memoria = memoria
        self._clima = clima
        self._escritor = escritor
        self._archivo = archivo
        self._intentos = intentos

    def ejecutar(self, disparador: str):
        ahora = datetime.now(ZONA_ECUADOR)
        print(f"[agente] despierta. disparador={disparador} hora_ecuador={ahora.isoformat()}")

        memoria = self._memoria.recientes()
        print(f"[memoria] {len(memoria)} postales previas en el historial")

        lugar = elegir_lugar(memoria, self._catalogo)
        tono = elegir_tono(memoria)
        print(f"[decision] lugar={lugar.nombre} tono={tono}")

        clima = self._clima.consultar(lugar)
        print(f"[clima] {lugar.nombre}: {clima.temperatura}C, {clima.descripcion}, "
              f"humedad {clima.humedad}%, viento {clima.viento}km/h")

        borrador = self._insistir_hasta_que_sirva(lugar, clima, tono, memoria)

        postal = Postal(
            id=ahora.strftime("%Y-%m-%dT%H-%M-%S"),
            epoch=int(ahora.timestamp()),
            lugar=lugar.nombre,
            provincia=lugar.provincia,
            titulo=borrador.titulo or "Sin titulo",
            texto=borrador.texto,
            tono=tono,
            clima=clima,
            generada_en=ahora.isoformat(),
            disparador=disparador,
            modelo=self._escritor.modelo,
        )
        self._memoria.guardar(postal)

        total = self._archivo.publicar(self._memoria.todas())
        print(f"[agente] listo. '{postal.titulo}' desde {postal.lugar}. archivo: {total} postales")

        return {
            "statusCode": 200,
            "postal_id": postal.id,
            "lugar": postal.lugar,
            "titulo": postal.titulo,
            "total_archivo": total,
        }

    def _insistir_hasta_que_sirva(self, lugar, clima, tono, memoria):
        ultimo = None

        for intento in range(1, self._intentos + 1):
            borrador = self._escritor.escribir(lugar, clima, tono, memoria, intento)
            if borrador is None:
                continue

            fallos = revisar(borrador, lugar, tono)
            ultimo = borrador
            if not fallos:
                print(f"[validacion] intento {intento}: postal aceptada")
                return borrador
            print(f"[validacion] intento {intento} rechazado: {', '.join(fallos)}")

        if ultimo and ultimo.texto:
            print("[validacion] se agotaron los intentos, se publica el mejor disponible")
            return ultimo
        raise ValueError("el modelo no produjo una postal utilizable en ningun intento")
