import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from dominio.modelos import Borrador, Clima, Lugar, Postal
from dominio.seleccion import TONOS, elegir_lugar, elegir_tono
from dominio.sensaciones import describir, momento_del_dia
from dominio.validacion import revisar
from infraestructura.catalogo_lugares import cargar

PARAMO = Clima(temperatura=-6.5, humedad=86, viento=12.7,
               descripcion="cubierto", codigo=3, es_de_dia=True)
SELVA = Clima(temperatura=28.8, humedad=81, viento=9.0,
              descripcion="llovizna", codigo=51, es_de_dia=True)
BANOS = Lugar(nombre="Banos de Agua Santa", provincia="Tungurahua",
              lat=-1.4, lon=-78.4, alma="valle entre cascadas")


def texto_de(palabras):
    return " ".join(["palabra"] * palabras)


def postal_falsa(lugar, tono):
    return Postal(id="x", epoch=0, lugar=lugar, provincia="p", titulo="t", texto="x",
                  tono=tono, clima=PARAMO, generada_en="", disparador="", modelo="")


def test_el_paramo_helado_se_siente_en_el_cuerpo():
    descripcion = describir(PARAMO)
    assert "entumece" in descripcion
    assert "hasta los huesos" in descripcion


def test_el_calor_humedo_hace_sudar():
    assert "Se suda sin moverse" in describir(SELVA)


def test_ningun_numero_llega_al_modelo():
    assert not any(c.isdigit() for c in describir(PARAMO) + describir(SELVA))


def test_de_noche_manda_sobre_la_hora():
    assert momento_del_dia(datetime(2026, 8, 22, 10), es_de_dia=False) == "de noche"
    assert momento_del_dia(datetime(2026, 8, 22, 10), es_de_dia=True) == "por la manana"
    assert momento_del_dia(datetime(2026, 8, 22, 20), es_de_dia=True) == "al anochecer"


def test_un_borrador_correcto_pasa():
    assert revisar(Borrador("Nadie levanta la vista", texto_de(100)), BANOS, "melancolico") == []


def test_rechaza_numeros():
    fallos = revisar(Borrador("Titulo limpio", texto_de(99) + " 25"), BANOS, "seco")
    assert "contiene numeros" in fallos


def test_rechaza_palabras_de_folleto():
    fallos = revisar(Borrador("Titulo limpio", " ".join(["magico"] * 100)), BANOS, "seco")
    assert any("prohibidas" in f for f in fallos)


def test_rechaza_el_nombre_completo_del_lugar_en_el_titulo():
    fallos = revisar(Borrador("Banos de Agua Santa amanece", texto_de(100)), BANOS, "seco")
    assert "el titulo nombra el lugar" in fallos


def test_una_mencion_parcial_del_lugar_se_cuela():
    """Limite conocido: la regla compara el nombre completo, no sus palabras."""
    fallos = revisar(Borrador("Banos bajo la niebla", texto_de(100)), BANOS, "seco")
    assert "el titulo nombra el lugar" not in fallos


def test_rechaza_la_provincia_en_el_titulo():
    fallos = revisar(Borrador("Tungurahua despierta", texto_de(100)), BANOS, "seco")
    assert "el titulo nombra el lugar" in fallos


def test_rechaza_que_el_titulo_delate_el_tono():
    fallos = revisar(Borrador("Un aire melancolico", texto_de(100)), BANOS, "melancolico y contenido")
    assert any("copia el tono" in f for f in fallos)


def test_rechaza_textos_fuera_de_medida():
    assert any("longitud" in f for f in revisar(Borrador("Titulo", "muy corto"), BANOS, "seco"))


def test_un_texto_vacio_corta_la_revision():
    assert revisar(Borrador("Titulo", ""), BANOS, "seco") == ["postal vacia"]


def test_el_catalogo_son_modelos_del_dominio():
    catalogo = cargar()
    assert len(catalogo) == 50
    assert all(isinstance(lugar, Lugar) for lugar in catalogo)


def test_nunca_vuelve_a_un_lugar_reciente():
    catalogo = cargar()
    memoria = [postal_falsa(lugar.nombre, TONOS[0]) for lugar in catalogo[:18]]
    elegidos = {elegir_lugar(memoria, catalogo).nombre for _ in range(60)}
    assert not elegidos & {postal.lugar for postal in memoria}


def test_nunca_repite_los_ultimos_tonos():
    memoria = [postal_falsa("x", tono) for tono in TONOS[:8]]
    elegidos = {elegir_tono(memoria) for _ in range(60)}
    assert elegidos.isdisjoint(set(TONOS[:8]))


def test_con_el_pais_entero_visitado_vuelve_a_empezar():
    catalogo = cargar()
    memoria = [postal_falsa(lugar.nombre, "t") for lugar in catalogo]
    assert elegir_lugar(memoria, catalogo) in catalogo
