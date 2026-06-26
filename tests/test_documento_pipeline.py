from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from controllers.documento_pipeline_controller import DocumentoPipelineController


def test_documento_pipeline_basico():
    ctx = DocumentoPipelineController.criar_contexto(
        nome_arquivo="nota_fiscal.pdf",
        empresa_id=1,
    )

    assert ctx["status"] == "Recebido"

    tipo = DocumentoPipelineController.classificar(
        "nota_fiscal.pdf",
        "Nota Fiscal Eletrônica NF-e",
    )

    assert tipo == "NF-e"

    ctx = DocumentoPipelineController.validar(ctx)

    assert ctx["status"] == "Validado"

    print("OK - Pipeline documental básico válido.")


if __name__ == "__main__":
    test_documento_pipeline_basico()
