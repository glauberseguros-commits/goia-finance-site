from pathlib import Path

p = Path("app.py")
txt = p.read_text(encoding="utf-8")

replaces = {
    '<div class="menu-item active">Dashboard</div>': '<a class="menu-item active" href="/">Dashboard</a>',
    '<div class="menu-item">Importar Documento</div>': '<a class="menu-item" href="/Importar_Documento">Importar Documento</a>',
    '<div class="menu-item">Clientes</div>': '<a class="menu-item" href="/Clientes">Clientes</a>',
    '<div class="menu-item">Fornecedores</div>': '<a class="menu-item" href="/Fornecedores">Fornecedores</a>',
    '<div class="menu-item">Contas a Receber</div>': '<a class="menu-item" href="/Contas_a_Receber">Contas a Receber</a>',
    '<div class="menu-item">Contas a Pagar</div>': '<a class="menu-item" href="/Contas_a_Pagar">Contas a Pagar</a>',
    '<div class="menu-item">Compras</div>': '<a class="menu-item" href="/Compras">Compras</a>',
    '<div class="menu-item">Produtos Estoque</div>': '<a class="menu-item" href="/Produtos_Estoque">Produtos Estoque</a>',
    '<div class="menu-item">Vendas</div>': '<a class="menu-item" href="/Vendas">Vendas</a>',
    '<div class="menu-item">Processos Documentais</div>': '<a class="menu-item" href="/Processos_Documentais">Processos Documentais</a>',
    '<div class="menu-item">Conciliação Bancária</div>': '<a class="menu-item" href="/Conciliacao_Bancaria">Conciliação Bancária</a>',
    '<div class="menu-item">Relatórios</div>': '<a class="menu-item" href="/Relatorios">Relatórios</a>',
}

for old, new in replaces.items():
    txt = txt.replace(old, new)

# Garante que links tenham o mesmo visual dos antigos divs
if ".menu-item {" in txt and "text-decoration: none;" not in txt:
    txt = txt.replace(
        ".menu-item {",
        ".menu-item {\n            text-decoration: none;"
    )

p.write_text(txt, encoding="utf-8")
print("OK - menu premium convertido para links navegáveis.")
