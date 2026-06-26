from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from controllers.documento_validacao_controller import DocumentoValidacaoController


def test_documento_validacao():
    assert DocumentoValidacaoController.cnpj("28.860.122/0001-77") is True
    assert DocumentoValidacaoController.cnpj("11.222.333/0001-81") is True
    assert DocumentoValidacaoController.cnpj("11.111.111/1111-11") is False
    assert DocumentoValidacaoController.cpf("111.111.111-11") is False
    print("OK - Validação documental válida.")


if __name__ == "__main__":
    test_documento_validacao()
