import sys
import os
import asyncio

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.agents.orchestrator import SadiguaOrchestrator

def test_thought_completion_detector():
    """Valida la detección precisa de frases e ideas cerradas vs truncadas a medias."""
    # Frases completas (deben dar True)
    assert SadiguaOrchestrator.is_thought_complete("La parte afectada puede acudir ante la SIC.")
    assert SadiguaOrchestrator.is_thought_complete("Se recomienda interponer acción de tutela!")
    assert SadiguaOrchestrator.is_thought_complete("¿Cuáles son los requisitos de procedibilidad?")
    assert SadiguaOrchestrator.is_thought_complete("Conforme al artículo 15 de la Constitución (1991).")
    assert SadiguaOrchestrator.is_thought_complete("Dictamen final:\n1. Reclamar ante la entidad.\n2. Denunciar ante la SIC.")

    # Frases truncadas a medias (deben dar False)
    assert not SadiguaOrchestrator.is_thought_complete("La parte afectada puede iniciar una acción civil ante un juez ordin")
    assert not SadiguaOrchestrator.is_thought_complete("Presenta cualquier documento que demuestre la violación, como contratos, correos electrónicos, facturas, etc")
    assert not SadiguaOrchestrator.is_thought_complete("Debe notificar formalmente a la empresa sobre la violación de su derecho a la")
    assert not SadiguaOrchestrator.is_thought_complete("El término legal para resolver es de diez días hábiles contados a partir de")

    print("[OK] test_thought_completion_detector: Detector de oraciones truncadas verificado exitosamente.")

if __name__ == "__main__":
    test_thought_completion_detector()
