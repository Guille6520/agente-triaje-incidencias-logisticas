from app.graph.nodes import decidir


def _base(**overrides):
    estado = {
        "tipo_incidencia": "retraso", "urgencia": "media", "sospechoso": False,
        "discrepancia": None, "pedido_existe": True, "titular_coincide": True,
        "tiene_foto": None, "numero_pedido": "45231", "resumen": "x",
        "cuerpo_mensaje": "x",
    }
    estado.update(overrides)
    return estado


def test_nivel1_pedido_inexistente_auto_resuelve():
    r = decidir(_base(pedido_existe=False))
    assert r["auto_resuelto"] is True
    assert "no cuadran" in r["motivo_decision"]


def test_nivel1_titular_no_coincide_auto_resuelve():
    r = decidir(_base(titular_coincide=False))
    assert r["auto_resuelto"] is True


def test_nivel1_dano_sin_foto_pide_foto():
    r = decidir(_base(tipo_incidencia="daño", tiene_foto=False))
    assert r["auto_resuelto"] is True
    assert "foto" in r["respuesta_borrador"].lower()


def test_nivel1_consulta_seguimiento_auto_resuelve():
    r = decidir(_base(tipo_incidencia="consulta_seguimiento"))
    assert r["auto_resuelto"] is True


def test_nivel2_guardian_sospechoso_escala():
    r = decidir(_base(sospechoso=True))
    assert r["puede_resolver"] is False
    assert "Guardian sospechoso" in r["motivo_decision"]


def test_nivel2_discrepancia_escala():
    r = decidir(_base(discrepancia="Algo no cuadra"))
    assert r["puede_resolver"] is False


def test_nivel2_urgencia_alta_escala():
    r = decidir(_base(urgencia="alta"))
    assert r["puede_resolver"] is False
    assert r["motivo_decision"] == "Urgencia alta"


def test_nivel2_dano_o_perdida_escala():
    r = decidir(_base(tipo_incidencia="perdida", urgencia="baja"))
    assert r["puede_resolver"] is False
