# GOIA - Matriz de Auditoria Funcional

Base: ARQUITETURA_FUNCIONAL_GOIA_V1.md

## Objetivo

Mapear cada página existente contra a arquitetura funcional v1 antes de alterar código.

---

## Matriz inicial

| Página | Tamanho | Função atual provável | Função correta na Arquitetura V1 | Aderência | Prioridade |
|---|---:|---|---|---|---|
| 0_Cadastro_Assinante.py | 5.270 | Cadastro/login do assinante | Cadastro da empresa usuária da GOIA | Parcial | Média |
| 1_Importar_Documento.py | 54.804 | Importa, classifica, cadastra, cria financeiro e processos | Entrada única para Repositório Documental + classificação + roteamento | Baixa | Crítica |
| 2_Contas_a_Receber.py | 9.069 | Gestão de recebíveis | Exibir contas geradas por evidência financeira válida | Parcial | Alta |
| 3_Contas_a_Pagar.py | 6.481 | Gestão de pagamentos | Exibir contas geradas por NF entrada, boleto, contrato ou fatura | Parcial | Alta |
| 4_Compras.py | 7.646 | Registro de compras | Processo operacional derivado de evidência de compra | Parcial | Média |
| 5_Produtos_Estoque.py | 10.172 | Produtos/estoque | Cadastro de itens extraídos de documentos ou manual | Parcial | Média |
| 6_Vendas.py | 12.017 | Registro de vendas | Processo operacional derivado de evidência de venda | Parcial | Média |
| 7_Processos_Documentais.py | 15.719 | Processos/evidências/pendências | Núcleo de processos documentais | Média | Alta |
| 8_Conciliacao_Bancaria.py | 15.912 | Conciliação | Cruzar banco x pagar/receber x evidências bancárias | Média | Alta |
| 8_Movimentos_Bancarios.py | 4.433 | Movimentos bancários | Repositório de movimentos bancários importados | Parcial | Alta |
| 8_Pendencias_Inteligentes.py | 5.681 | Pendências | Central de pendências por entidade/processo/conta | Parcial | Alta |
| 9_Clientes.py | 7.214 | Lista clientes e histórico | Entidade cliente + evidências cadastrais relevantes | Parcial | Alta |
| 10_Fornecedores.py | 5.511 | Lista fornecedores | Entidade fornecedor + evidências cadastrais relevantes | Parcial | Alta |

---

## Diagnóstico inicial

A página crítica é:

1_Importar_Documento.py

Motivo:
- Está funcionando como importador, classificador, extrator, cadastro, financeiro e processo ao mesmo tempo.
- Isso viola a arquitetura V1.
- Deve ser reduzida para orquestradora do upload e roteamento.

---

## Ordem recomendada

1. Criar estrutura clara de Repositório Documental.
2. Ajustar Importar Documento para sempre salvar primeiro no repositório.
3. Criar camada de classificação.
4. Criar camada de vínculos/evidências.
5. Só depois ajustar Clientes, Fornecedores, Receber e Pagar.

---

## Regra de decisão

Antes de cada alteração perguntar:

Este documento deve:
1. Apenas ser guardado?
2. Virar evidência cadastral?
3. Virar evidência financeira?
4. Criar processo?
5. Criar pendência?
6. Criar conta a pagar/receber?
7. Aguardar confirmação humana?
