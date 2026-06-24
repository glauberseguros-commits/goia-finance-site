import sqlite3

from utils.db import conectar_banco


SCHEMA = {
    "empresas": {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "nome": "TEXT NOT NULL",
        "nome_fantasia": "TEXT",
        "cnpj_cpf": "TEXT",
        "email": "TEXT",
        "telefone": "TEXT",
        "senha_hash": "TEXT",
        "plano": "TEXT DEFAULT 'Teste'",
        "status_assinatura": "TEXT DEFAULT 'Ativa'",
        "admin_nome": "TEXT",
        "criado_em": "TEXT DEFAULT CURRENT_TIMESTAMP",
    },

    "clientes": {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "empresa_id": "INTEGER",
        "nome": "TEXT",
        "cnpj_cpf": "TEXT",
        "email": "TEXT",
        "telefone": "TEXT",
        "endereco": "TEXT",
        "cidade": "TEXT",
        "uf": "TEXT",
        "cep": "TEXT",
        "status": "TEXT DEFAULT 'Ativo'",
        "origem_cadastro": "TEXT DEFAULT 'DOCUMENTO'",
        "nome_fantasia": "TEXT",
        "cnae_principal": "TEXT",
        "natureza_juridica": "TEXT",
        "capital_social": "REAL",
        "situacao_cadastral": "TEXT",
        "criado_em": "TEXT DEFAULT CURRENT_TIMESTAMP",
    },

    "fornecedores": {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "empresa_id": "INTEGER",
        "nome": "TEXT",
        "cnpj": "TEXT",
        "cnpj_cpf": "TEXT",
        "email": "TEXT",
        "telefone": "TEXT",
        "endereco": "TEXT",
        "cidade": "TEXT",
        "uf": "TEXT",
        "cep": "TEXT",
        "categoria_padrao": "TEXT",
        "tipo_padrao": "TEXT",
        "status": "TEXT DEFAULT 'Ativo'",
        "origem_cadastro": "TEXT DEFAULT 'DOCUMENTO'",
        "nome_fantasia": "TEXT",
        "cnae_principal": "TEXT",
        "natureza_juridica": "TEXT",
        "capital_social": "REAL",
        "situacao_cadastral": "TEXT",
        "criado_em": "TEXT DEFAULT CURRENT_TIMESTAMP",
    },

    "documentos": {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "empresa_id": "INTEGER",
        "processo_id": "INTEGER",
        "cliente_id": "INTEGER",
        "fornecedor_id": "INTEGER",
        "nome_arquivo": "TEXT",
        "tipo_documento": "TEXT",
        "classificacao": "TEXT",
        "direcao": "TEXT",
        "origem": "TEXT",
        "conteudo_texto": "TEXT",
        "texto_extraido": "TEXT",
        "chave_acesso_nfe": "TEXT",
        "numero_nfe": "TEXT",
        "serie_nfe": "TEXT",
        "cnpj_emitente": "TEXT",
        "nome_emitente": "TEXT",
        "cnpj_destinatario": "TEXT",
        "nome_destinatario": "TEXT",
        "contraparte_nome": "TEXT",
        "contraparte_documento": "TEXT",
        "data_documento": "TEXT",
        "data_emissao": "TEXT",
        "data_vencimento": "TEXT",
        "valor_total": "REAL DEFAULT 0",
        "valor": "REAL DEFAULT 0",
        "status": "TEXT DEFAULT 'Importado'",
        "status_processamento": "TEXT DEFAULT 'Processado'",
        "erro_processamento": "TEXT",
        "processado_em": "TEXT",
        "hash_arquivo": "TEXT",
        "caminho_arquivo": "TEXT",
        "extensao": "TEXT",
        "tamanho_bytes": "INTEGER",
        "observacao": "TEXT",
        "diagnostico_tecnico": "TEXT",
        "dados_extraidos_json": "TEXT",
        "criado_em": "TEXT DEFAULT CURRENT_TIMESTAMP",
    },

    "processos_documentais": {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "empresa_id": "INTEGER",
        "titulo": "TEXT",
        "descricao": "TEXT",
        "tipo_processo": "TEXT",
        "tipo_operacao": "TEXT",
        "natureza": "TEXT",
        "papel_empresa": "TEXT",
        "contraparte_nome": "TEXT",
        "contraparte_cnpj": "TEXT",
        "valor_total": "REAL DEFAULT 0",
        "status": "TEXT DEFAULT 'Aberto'",
        "proxima_acao": "TEXT",
        "criado_em": "TEXT DEFAULT CURRENT_TIMESTAMP",
        "atualizado_em": "TEXT",
    },

    "processo_documentos": {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "empresa_id": "INTEGER",
        "processo_id": "INTEGER",
        "documento_id": "INTEGER",
        "tipo_documento": "TEXT",
        "obrigatorio": "INTEGER DEFAULT 0",
        "status": "TEXT DEFAULT 'Pendente'",
        "criado_em": "TEXT DEFAULT CURRENT_TIMESTAMP",
    },

    "processo_pendencias": {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "empresa_id": "INTEGER",
        "processo_id": "INTEGER",
        "documento_id": "INTEGER",
        "descricao": "TEXT",
        "tipo_evidencia": "TEXT",
        "proxima_acao": "TEXT",
        "prazo": "TEXT",
        "status": "TEXT DEFAULT 'Pendente'",
        "resolvido_em": "TEXT",
        "resolvido_por": "TEXT",
        "evidencia_resolucao_id": "INTEGER",
        "criado_em": "TEXT DEFAULT CURRENT_TIMESTAMP",
    },

    "evidencias": {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "empresa_id": "INTEGER",
        "processo_id": "INTEGER",
        "documento_id": "INTEGER",
        "conta_receber_id": "INTEGER",
        "conta_pagar_id": "INTEGER",
        "tipo_evidencia": "TEXT",
        "descricao": "TEXT",
        "valor": "TEXT",
        "data_referencia": "TEXT",
        "origem": "TEXT",
        "status": "TEXT DEFAULT 'Ativa'",
        "criado_em": "TEXT DEFAULT CURRENT_TIMESTAMP",
    },

    "processo_evidencias": {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "empresa_id": "INTEGER",
        "processo_id": "INTEGER",
        "documento_id": "INTEGER",
        "evidencia_id": "INTEGER",
        "conta_receber_id": "INTEGER",
        "conta_pagar_id": "INTEGER",
        "movimento_id": "INTEGER",
        "conta_id": "INTEGER",
        "documento_comprovante_id": "INTEGER",
        "tipo_evidencia": "TEXT",
        "descricao": "TEXT",
        "descricao_evidencia": "TEXT",
        "valor": "TEXT",
        "data_evidencia": "TEXT",
        "data_referencia": "TEXT",
        "data_movimento": "TEXT",
        "tipo_conciliacao": "TEXT",
        "tipo_conta": "TEXT",
        "valor_movimento": "REAL DEFAULT 0",
        "valor_baixado": "REAL DEFAULT 0",
        "data_baixa": "TEXT",
        "observacao_baixa": "TEXT",
        "score_match": "REAL DEFAULT 0",
        "criterios_match": "TEXT",
        "origem": "TEXT",
        "status": "TEXT DEFAULT 'Ativa'",
        "proxima_acao": "TEXT",
        "criado_em": "TEXT DEFAULT CURRENT_TIMESTAMP",
    },

    "contas_receber": {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "empresa_id": "INTEGER",
        "cliente_id": "INTEGER",
        "documento_id": "INTEGER",
        "descricao": "TEXT",
        "categoria": "TEXT",
        "valor": "REAL DEFAULT 0",
        "data_emissao": "TEXT",
        "data_vencimento": "TEXT",
        "data_baixa": "TEXT",
        "valor_baixado": "REAL DEFAULT 0",
        "observacao_baixa": "TEXT",
        "status": "TEXT DEFAULT 'Pendente'",
        "criado_em": "TEXT DEFAULT CURRENT_TIMESTAMP",
    },

    "contas_pagar": {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "empresa_id": "INTEGER",
        "fornecedor_id": "INTEGER",
        "processo_id": "INTEGER",
        "documento_id": "INTEGER",
        "descricao": "TEXT",
        "categoria": "TEXT",
        "valor": "REAL DEFAULT 0",
        "data_emissao": "TEXT",
        "data_vencimento": "TEXT",
        "data_baixa": "TEXT",
        "valor_baixado": "REAL DEFAULT 0",
        "forma_pagamento": "TEXT",
        "observacao_baixa": "TEXT",
        "status": "TEXT DEFAULT 'Pendente'",
        "criado_em": "TEXT DEFAULT CURRENT_TIMESTAMP",
    },

    "recebimentos": {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "empresa_id": "INTEGER",
        "conta_receber_id": "INTEGER",
        "data_recebimento": "TEXT",
        "forma_recebimento": "TEXT",
        "valor_recebido": "REAL DEFAULT 0",
        "status": "TEXT DEFAULT 'Confirmado'",
        "criado_em": "TEXT DEFAULT CURRENT_TIMESTAMP",
    },

    "pagamentos": {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "empresa_id": "INTEGER",
        "conta_pagar_id": "INTEGER",
        "data_pagamento": "TEXT",
        "forma_pagamento": "TEXT",
        "valor_pago": "REAL DEFAULT 0",
        "criado_em": "TEXT DEFAULT CURRENT_TIMESTAMP",
    },

    "movimentos_bancarios": {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "empresa_id": "INTEGER",
        "conta_bancaria_id": "INTEGER",
        "extrato_id": "INTEGER",
        "data_movimento": "TEXT",
        "descricao": "TEXT",
        "historico": "TEXT",
        "documento": "TEXT",
        "valor": "REAL DEFAULT 0",
        "tipo": "TEXT",
        "conciliado": "INTEGER DEFAULT 0",
        "origem": "TEXT",
        "cnpj_origem": "TEXT",
        "nome_origem": "TEXT",
        "conta_receber_id": "INTEGER",
        "conta_pagar_id": "INTEGER",
        "criado_em": "TEXT DEFAULT CURRENT_TIMESTAMP",
    },

    "extratos_bancarios": {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "empresa_id": "INTEGER",
        "nome_arquivo": "TEXT",
        "criado_em": "TEXT DEFAULT CURRENT_TIMESTAMP",
    },

    "compras": {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "empresa_id": "INTEGER",
        "fornecedor_id": "INTEGER",
        "documento_id": "INTEGER",
        "descricao": "TEXT",
        "data_compra": "TEXT",
        "valor_total": "REAL DEFAULT 0",
        "status": "TEXT DEFAULT 'Aberta'",
        "criado_em": "TEXT DEFAULT CURRENT_TIMESTAMP",
    },

    "compras_itens": {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "empresa_id": "INTEGER",
        "compra_id": "INTEGER",
        "produto_id": "INTEGER",
        "descricao": "TEXT",
        "quantidade": "REAL DEFAULT 0",
        "valor_unitario": "REAL DEFAULT 0",
        "valor_total": "REAL DEFAULT 0",
    },

    "vendas": {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "empresa_id": "INTEGER",
        "cliente_id": "INTEGER",
        "documento_id": "INTEGER",
        "descricao": "TEXT",
        "data_venda": "TEXT",
        "valor_total": "REAL DEFAULT 0",
        "status": "TEXT DEFAULT 'Aberta'",
        "criado_em": "TEXT DEFAULT CURRENT_TIMESTAMP",
    },

    "vendas_itens": {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "empresa_id": "INTEGER",
        "venda_id": "INTEGER",
        "produto_id": "INTEGER",
        "descricao": "TEXT",
        "quantidade": "REAL DEFAULT 0",
        "valor_unitario": "REAL DEFAULT 0",
        "valor_total": "REAL DEFAULT 0",
    },

    "produtos": {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "empresa_id": "INTEGER",
        "descricao": "TEXT",
        "categoria": "TEXT",
        "custo_medio": "REAL DEFAULT 0",
        "preco_venda": "REAL DEFAULT 0",
        "criado_em": "TEXT DEFAULT CURRENT_TIMESTAMP",
    },

    "estoque_movimentacoes": {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "empresa_id": "INTEGER",
        "produto_id": "INTEGER",
        "documento_id": "INTEGER",
        "tipo": "TEXT",
        "origem": "TEXT",
        "quantidade": "REAL DEFAULT 0",
        "valor_unitario": "REAL DEFAULT 0",
        "valor_total": "REAL DEFAULT 0",
        "data_movimento": "TEXT",
        "criado_em": "TEXT DEFAULT CURRENT_TIMESTAMP",
    },
}


def _create_table_sql(tabela: str, colunas: dict) -> str:
    partes = [f"{nome} {tipo}" for nome, tipo in colunas.items()]
    return f"CREATE TABLE IF NOT EXISTS {tabela} ({', '.join(partes)})"


def _colunas_existentes(cur, tabela: str) -> set:
    cur.execute(f"PRAGMA table_info({tabela})")
    return {row[1] for row in cur.fetchall()}


def _garantir_tabela(cur, tabela: str, colunas: dict) -> None:
    cur.execute(_create_table_sql(tabela, colunas))

    existentes = _colunas_existentes(cur, tabela)

    for nome, tipo in colunas.items():
        if nome in existentes:
            continue

        if "PRIMARY KEY" in tipo.upper():
            continue

        cur.execute(f"ALTER TABLE {tabela} ADD COLUMN {nome} {tipo}")


def inicializar_schema_goia() -> None:
    conn = conectar_banco()
    cur = conn.cursor()

    for tabela, colunas in SCHEMA.items():
        _garantir_tabela(cur, tabela, colunas)

    cur.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_empresas_cnpj_cpf_unico
        ON empresas(cnpj_cpf)
        WHERE cnpj_cpf IS NOT NULL AND cnpj_cpf <> ''
    """)

    conn.commit()
    conn.close()

    garantir_repositorio_documental()



def garantir_repositorio_documental():
    """
    Garante a estrutura mínima do Repositório Documental GOIA.

    Regra da Arquitetura V1:
    Todo arquivo enviado entra primeiro no repositório.
    Depois pode ou não ser vinculado a entidade, processo, conta ou evidência.
    """
    conn = conectar_banco()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS repositorio_documental (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empresa_id INTEGER NOT NULL,
            documento_id INTEGER,
            nome_arquivo TEXT,
            tipo_arquivo TEXT,
            extensao TEXT,
            tamanho_bytes INTEGER,
            hash_arquivo TEXT,
            caminho_arquivo TEXT,
            origem_upload TEXT DEFAULT 'Importação',
            tipo_documento_detectado TEXT,
            classificacao_operacional TEXT,
            status_repositorio TEXT DEFAULT 'Importado',
            entidade_id INTEGER,
            entidade_tipo TEXT,
            processo_id INTEGER,
            conta_receber_id INTEGER,
            conta_pagar_id INTEGER,
            movimento_bancario_id INTEGER,
            uso_recomendado TEXT,
            exige_acao_humana INTEGER DEFAULT 0,
            observacao TEXT,
            criado_em TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    campos = [
        ("empresa_id", "INTEGER"),
        ("documento_id", "INTEGER"),
        ("nome_arquivo", "TEXT"),
        ("tipo_arquivo", "TEXT"),
        ("extensao", "TEXT"),
        ("tamanho_bytes", "INTEGER"),
        ("hash_arquivo", "TEXT"),
        ("caminho_arquivo", "TEXT"),
        ("origem_upload", "TEXT DEFAULT 'Importação'"),
        ("tipo_documento_detectado", "TEXT"),
        ("classificacao_operacional", "TEXT"),
        ("status_repositorio", "TEXT DEFAULT 'Importado'"),
        ("entidade_id", "INTEGER"),
        ("entidade_tipo", "TEXT"),
        ("processo_id", "INTEGER"),
        ("conta_receber_id", "INTEGER"),
        ("conta_pagar_id", "INTEGER"),
        ("movimento_bancario_id", "INTEGER"),
        ("uso_recomendado", "TEXT"),
        ("exige_acao_humana", "INTEGER DEFAULT 0"),
        ("observacao", "TEXT"),
        ("criado_em", "TEXT DEFAULT CURRENT_TIMESTAMP"),
    ]

    cur.execute("PRAGMA table_info(repositorio_documental)")
    existentes = [c[1] for c in cur.fetchall()]

    for campo, tipo in campos:
        if campo not in existentes:
            cur.execute(f"ALTER TABLE repositorio_documental ADD COLUMN {campo} {tipo}")

    conn.commit()
    conn.close()

