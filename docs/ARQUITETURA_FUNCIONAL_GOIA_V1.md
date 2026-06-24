# GOIA - Arquitetura Funcional v1

## Princípio central

Todo arquivo enviado entra primeiro no Repositório Documental.

Nenhum arquivo deve ser empurrado diretamente para Clientes, Fornecedores, Contas a Receber, Contas a Pagar ou Conciliação.

As páginas operacionais devem consultar documentos relacionados quando fizer sentido.

---

## 1. Repositório Documental

Função: guardar todos os arquivos enviados.

Exemplos:
- Cartão CNPJ
- NF-e de entrada
- NF-e de saída
- XML
- PDF
- OFX
- CSV
- Excel
- Boleto
- Contrato
- Procuração
- Comprovante PIX
- Extrato bancário
- Outros

Status possíveis:
- Importado
- Classificado
- Relacionado
- Sem vínculo identificado
- Pendente de análise
- Ignorado operacionalmente

---

## 2. Entidades

Entidade representa uma pessoa, empresa ou órgão.

Tipos:
- Cliente
- Fornecedor
- Cliente e Fornecedor
- Órgão Público
- Banco
- Transportadora
- Outro

Dados cadastrais:
- Nome/Razão Social
- CPF/CNPJ
- Nome fantasia
- E-mail
- Telefone
- Endereço
- Cidade/UF
- CEP
- CNAE
- Natureza jurídica
- Capital social
- Sócios/QSA
- Situação cadastral
- Origem dos dados

Regra:
Entidade não é pasta de arquivos.

---

## 3. Evidências

Evidência é o documento ou dado que comprova alguma informação.

Exemplos:
- Cartão CNPJ comprova cadastro.
- Consulta API CNPJ enriquece cadastro.
- NF-e de saída comprova conta a receber.
- NF-e de entrada comprova conta a pagar.
- Extrato comprova movimentação bancária.
- Comprovante PIX comprova pagamento ou recebimento.
- Procuração comprova autorização.

Regra:
Apenas documentos relevantes devem ser vinculados como evidência.

---

## 4. Processos Documentais

Processo é o agrupamento de uma operação.

Exemplos:
- Venda para cliente
- Compra de fornecedor
- Prestação de serviço
- Licitação/empenho
- Pagamento de despesa
- Recebimento de cliente

Um processo pode conter:
- Entidade principal
- Documentos relacionados
- Evidências
- Contas a receber
- Contas a pagar
- Movimentos bancários
- Pendências

---

## 5. Contas a Receber

Deve nascer a partir de evidência financeira válida.

Evidências possíveis:
- NF-e de saída
- Nota de empenho
- Contrato
- Pedido aprovado
- Fatura

Não deve receber todos os documentos do cliente.

---

## 6. Contas a Pagar

Deve nascer a partir de evidência financeira válida.

Evidências possíveis:
- NF-e de entrada
- Boleto
- Fatura
- Contrato
- Recibo

Não deve receber documentos cadastrais que não comprovem obrigação financeira.

---

## 7. Conciliação

Deve usar:
- Movimentos bancários
- Contas a receber
- Contas a pagar
- Comprovantes
- Extratos

Regra:
Conciliação não é cadastro.
Conciliação é cruzamento financeiro.

---

## 8. Pendências

Pendência surge quando falta uma evidência necessária.

Exemplos:
- Cliente identificado sem Cartão CNPJ.
- Venda sem NF-e de saída.
- Conta a pagar sem boleto.
- Pagamento sem comprovante.
- Processo exige procuração e ela não está no repositório.
- Movimento bancário sem vínculo.

Pendência deve apontar:
- O que falta
- Para qual processo/entidade/conta
- Qual documento esperado
- Prioridade
- Status

---

## 9. Regra de ouro

Documento não deve ser duplicado em várias páginas.

Documento fica no Repositório.

As páginas exibem vínculos relevantes.

---

## Fluxo correto

Upload
↓
Repositório Documental
↓
Classificação
↓
Extração de entidades e dados
↓
Enriquecimento via API quando aplicável
↓
Criação/atualização controlada de entidades
↓
Criação de processo se houver operação
↓
Criação de conta financeira se houver evidência financeira
↓
Criação de pendências se faltar evidência
↓
Conciliação e baixa quando houver evidência bancária
