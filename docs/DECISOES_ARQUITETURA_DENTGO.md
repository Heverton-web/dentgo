# DentGo — Registro Canônico de Arquitetura & Decisões do Produto (ADR / Memory Master)

**Documento**: DECISOES_ARQUITETURA_DENTGO.md  
**Última Atualização**: 11 de Outubro de 2026  
**Status**: Canônico / Homologado  
**Repositório**: `https://github.com/Heverton-web/dentgo`  
**Produção**: `https://dentgo.signa-docs.com` | `https://dentgo.signa-docs.com/b2b`

---

## 1. Segregação Estrita de Aplicações

| Aspecto | Visão Cirurgião-Dentista | Visão B2B (Fabricante / Distribuidor) |
| :--- | :--- | :--- |
| **URL / Rota** | `/` ou `/app` | `/b2b` (ou `/portal`) |
| **Viewport** | Mobile-First Estrito (375px a 430px) | Desktop-First Estrito (1366x768 a 1920x1080) |
| **Autenticação** | CRO + PIN de 4 dígitos | Usuário/Senha por Fabricante (Tenant Isolado) |
| **Foco de Uso** | Compra rápida em cirurgia, catálogo ágil, radar | Almoxarifado, conferência ANVISA, Kanban, faturamento |
| **Multi-Empresa** | Vê todos os fabricantes (1 por pedido) | **Zero dropdown**: vê exclusivamente seus próprios pedidos |

---

## 2. Padrões de Design System & UX (Invioláveis)

1. **Zero Emojis**:
   * Emojis abolidos de toda e qualquer interface corporativa.
   * Substituídos por ícones lineares SVG e tipografia técnica JetBrains Mono.
2. **Zero Janelas Nativas de Navegador (`alert` / `confirm` / `prompt`)**:
   * Proibido qualquer diálogo nativo do sistema operacional.
   * Modais nativos HTML/CSS com backdrop em blur e Toasts discretos.
3. **Scrollbars Cirúrgicas (Máximo 4px)**:
   * Regra global: `*::-webkit-scrollbar { width: 4px; height: 4px; }`.
   * Cor neutra e sutileza clínica.
4. **Layout B2B Travado**:
   * Top Header e KPIs com posição e altura estritamente fixas (`flex-shrink: 0`).
   * Scroll vertical acontece **apenas** dentro das colunas individuais do Kanban.
   * Cards com altura e estrutura uniformizadas (`min-height: 146px`).
5. **Favicon Oficial**:
   * Presente em todas as rotas (`/` e `/b2b`) com o monograma oficial DentGo.

---

## 3. Formas de Pagamento Homologadas (Banimento do Boleto)

* **Formas Aceitas**:
  1. **Cartão de Crédito** (até 6x, tokenizado).
  2. **PIX Direto** (aprovação instantânea para liberação cirúrgica).
* **Boleto Bancário**:
  * **Completamente banido** da plataforma. Não existe boleto faturado, à vista ou parcelado.

---

## 4. Bipagem & Rastreabilidade ANVISA (GS1 DataMatrix)

* **Hardware**: Leitor óptico USB/Bluetooth ou scanner emulador de teclado físico.
* **Padrão de Dados**: GS1 DataMatrix bidimensional com Application Identifiers (AI):
  * `(01)` GTIN / EAN do SKU
  * `(17)` Data de Validade
  * `(10)` Lote de Fabricação ANVISA
  * `(21)` Número de Série Unitário
* **Mecânica de Match**:
  1. O operador bipa a caixa do produto no modal de conferência.
  2. O parser extrai SKU, validade e lote.
  3. Compara o SKU bipado com os itens pendentes do pedido.
  4. Valida se a data de validade não está vencida.
  5. Salva o Lote e Serial no SQLite para o prontuário do cirurgião.
  6. Ao completar a lista, move o pedido para *Pronto para Coleta*.

---

## 5. Gateway Logístico Flash 2h & Modelo dos Motoboys

* **Natureza Jurídica**: A DentGo **não contrata motoboys CLT nem tem frota própria**.
* **Modelo Operacional**: Gateway e orquestrador via API (Uber Direct, Lalamove, Borzo, Loggi):
  1. Cliente paga a taxa de urgência Flash (R$ 29,00).
  2. No final do picking, a API DentGo despacha webhook para a plataforma parceira mais próxima.
  3. Motoboy aceita no app dele e retira no CD da fabricante apresentando o ID do pedido.
  4. Na entrega no consultório, o motoboy valida o **PIN de 4 dígitos** fornecido pelo dentista para encerrar a corrida.
  5. A DentGo liquida a corrida via saldo empresarial e retém sua margem operacional.
* **Fallback em Caso de Chuva/Alta Demanda**:
  * Se a API primária não alocar em 4 minutos, cascata automática para a API secundária com tarifa dinâmica subsidiada pela plataforma.

---

## 6. Isolamento Multitenant B2B

* As empresas parceiras (Conexão, Straumann, Neodent, S.I.N.) possuem acessos estritamente segregados via login e senha.
* Nenhuma empresa tem visibilidade dos pedidos, faturamento, clientes ou estoque de outras marcas.
* Dropdown de troca de marca restrito unicamente a perfil interno de Super Admin de auditoria da DentGo.

---

## 7. Módulo do Entregador Express (DentGo Driver PWA)

* **Documento Detalhado**: `/opt/data/projetos/dentgo/docs/PRD_DRIVER_ENTREGADOR.md`
* **Rota Web Dedicada**: `/driver` ou `/entregador` (PWA Mobile de 1 toque).
* **Entidades no Banco SQLite**:
  - `entregadores`: Cadastro, veículo, status (online/em_rota), bateria e saldo em carteira.
  - `corridas_entrega`: Máquina de estados (aguardando ➔ aceito ➔ coletado ➔ entregue), origens/destinos com geolocalização e conciliação do repasse líquido do motorista.
* **Segurança na Ponta Final**:
  - Teclado numérico gigante integrado na tela para digitação do **PIN de 4 dígitos** fornecido pelo dentista para encerrar a corrida e liberar o repasse.

