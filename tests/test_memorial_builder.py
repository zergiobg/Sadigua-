from core.generators.memorial_builder import LegalMemorialBuilder, TUTELA_TAXONOMY, PETICION_TAXONOMY

def test_taxonomy_structure():
    builder = LegalMemorialBuilder()
    tax = builder.get_taxonomy()
    assert "tutelas" in tax
    assert "peticiones" in tax
    assert "SALUD_MEDICAMENTOS" in tax["tutelas"]
    assert "PENSION_VEJEZ" in tax["tutelas"]
    assert "PETICION_SILENCIO" in tax["tutelas"]
    assert "PETICION_DOCUMENTOS" in tax["peticiones"]

def test_generate_tutela_markdown_and_docx():
    builder = LegalMemorialBuilder()
    data = {
        "categoria_id": "SALUD_MEDICAMENTOS",
        "ciudad": "Cali",
        "accionante_nombre": "Andrés Gómez",
        "accionante_identificacion": "14.234.567",
        "accionante_correo": "andres@correo.com",
        "accionado_nombre": "Nueva EPS",
        "hechos": "No me entregan los insumos médicos necesarios.",
        "solicitar_medida_cautelar": True
    }
    tutela = builder.generate_tutela_markdown(data)
    assert tutela["tipo"] == "TUTELA"
    assert "ACCIÓN DE TUTELA" in tutela["markdown"]
    assert "ANDRÉS GÓMEZ" in tutela["markdown"]
    assert "NUEVA EPS" in tutela["markdown"]
    assert "MEDIDA CAUTELAR PROVISIONAL" in tutela["markdown"]
    assert "Ley Estatutaria 1751 de 2015" in tutela["markdown"]

    # Probar exportación a Word (.docx)
    docx_stream = builder.export_to_docx(tutela)
    assert docx_stream is not None
    assert len(docx_stream.getvalue()) > 5000

def test_generate_peticion_markdown():
    builder = LegalMemorialBuilder()
    data = {
        "categoria_id": "PETICION_DOCUMENTOS",
        "ciudad": "Barranquilla",
        "accionante_nombre": "Lorena Mendoza",
        "accionante_identificacion": "32.456.789",
        "accionante_correo": "lorena@correo.com",
        "accionado_nombre": "Alcaldía de Barranquilla",
        "pretensiones": "Copia del contrato de obra pública No. 2026-04."
    }
    peticion = builder.generate_peticion_markdown(data)
    assert peticion["tipo"] == "DERECHO_PETICION"
    assert "DERECHO DE PETICIÓN FORMAL" in peticion["markdown"]
    assert "Diez (10) días hábiles" in peticion["markdown"]
    assert "ALCALDÍA DE BARRANQUILLA" in peticion["markdown"]
