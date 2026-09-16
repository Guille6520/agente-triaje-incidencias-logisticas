from app.graph.nodes import enriquecer


def test_pedido_inexistente():
    r = enriquecer({"numero_pedido": "00000", "remitente": "x@y.com", "tipo_incidencia": "perdida"})
    assert r["pedido_existe"] is False
    assert "no existe" in r["discrepancia"]


def test_sin_numero_de_pedido():
    r = enriquecer({"numero_pedido": "desconocido", "remitente": "x@y.com", "tipo_incidencia": "perdida"})
    assert r["pedido_existe"] is False


def test_detecta_fraude_titular_no_coincide():
    """El caso central del README: alguien que no es el titular reclama un pedido ajeno."""
    r = enriquecer({"numero_pedido": "54321", "remitente": "otro@gmail.com", "tipo_incidencia": "perdida"})
    assert r["pedido_existe"] is True
    assert r["titular_coincide"] is False
    assert "no es el titular" in r["discrepancia"]


def test_titular_correcto_sin_discrepancia():
    r = enriquecer({"numero_pedido": "45231", "remitente": "carlos.lopez@mercadona.es", "tipo_incidencia": "consulta_seguimiento"})
    assert r["titular_coincide"] is True
    assert r["discrepancia"] is None


def test_dano_sin_foto_es_discrepancia():
    r = enriquecer({"numero_pedido": "12445", "remitente": "logistica@fashionstore.es", "tipo_incidencia": "daño"})
    assert r["tiene_foto"] is False
    assert "no consta foto" in r["discrepancia"]


def test_entrega_fantasma_es_discrepancia():
    """Consta 'entregado' pero el cliente dice que no llego."""
    r = enriquecer({"numero_pedido": "89104", "remitente": "almacen@techparts.com", "tipo_incidencia": "perdida"})
    assert "consta entregado" in r["discrepancia"]
