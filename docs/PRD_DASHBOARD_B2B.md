# PRD — DentGo B2B Hub (Portal Desktop do Fabricante & Distribuidor)

**Documento**: PRD-DENTGO-B2B-001  
**Autor**: AIDD Architecture & Product Engine  
**Status**: Homologado  
**Público-Alvo**: Fabricantes de Implantes (Conexão, Straumann, Neodent, S.I.N.), Distribuidores Autorizados e Operadores de Almoxarifado/Expedição.  
**Viewport Primário**: Desktop Exclusivo (1366x768 a 1920x1080).

---

## 1. Visão Geral & Problema de Negócio

Enquanto o cirurgião-dentista consome a plataforma no consultório via mobile/tablet para pedidos urgentes e reposição imediata, o fabricante opera em ambiente de alta densidade de dados: computadores de expedição com leitor de código de barras físico, impressão de etiquetas térmicas de rastreabilidade ANVISA, conciliação financeira de faturamento e despacho de entregadores dedicados.

O **DentGo B2B Hub** fornece uma interface desktop em tela cheia com densidade informacional cirúrgica, eliminando distrações mobile e centralizando a esteira de pedidos, catálogo e faturamento.

---

## 2. Personas Operacionais

1. **Operador de Expedição / Almoxarife**:
   * Responsável por aceitar pedidos em até 3 minutos.
   * Realiza o *picking* físico das caixas esterilizadas.
   * Bipa o DataMatrix para vincular lote/validade da ANVISA.
   * Aciona e libera o motoboy do despacho Flash.

2. **Gerente de Vendas & Marketing B2B**:
   * Cadastra novos produtos, SKUs e kits cirúrgicos.
   * Lança pacotes promocionais sazonais com prazo de validade.
   * Monitora curvas de demanda por região (ex: Jardins, Moema, Paulista).

3. **Controladoria Financeira**:
   * Visualiza relatórios de faturamento consolidado.
   * Acompanha o split bancário e repasses da taxa da plataforma.

---

## 3. Módulos Funcionais do Dashboard Desktop

### 3.1. Torre de Expedição & Kanban em Tempo Real (Foco Principal)
* **Status em Colunas**:
  1. **Novos Pedidos (Aguardando Aceite)**: Sinal sonoro e badge pulsante para pedidos Flash 2h.
  2. **Em Picking / Separação**: Lista de itens com SKU, conexão, quantidade e leitor de lote ANVISA.
  3. **Pronto para Coleta**: Pedido embalado aguardando chegada do motoboy.
  4. **Em Rota (Flash 2h)**: Telemetria ao vivo com status da rota e PIN de entrega.
  5. **Concluídos**: Histórico com comprovante e assinatura digital.
* **Ações Rápidas**:
  * Botão de impressão de etiqueta térmica Zebra/ZPL (40x25mm) com QR Code do pedido.
  * Validação óptica de lote antes do despacho.

### 3.2. Catálogo Cirúrgico & Controle de Estoque
* Tabela densa com filtros avançados:
  * Fabricante, Linha de Conexão (CM, HE, HI), Diâmetro e Comprimento.
  * Interruptor instantâneo: *"Disponível para Flash 2h"* (liga/desliga por SKU).
  * Edição rápida de estoque mínimo e preço de tabela.

### 3.3. Central de Pacotes Promocionais & Combos
* Formulário desktop para criação de pacotes promocionais:
  * Nome do combo, badge promocional (ex: 20% OFF, Relâmpago).
  * Seleção de múltiplos SKUs e quantidades inclusas.
  * Preço original de tabela vs Preço promocional faturado.
  * Data de vigência e formas de pagamento aceitas (Cartão / PIX).

### 3.4. Torre de Despacho & Gestão de Motoboys
* Lista de entregadores em trânsito com status da bateria, distância até o destino e tempo estimado.
* Visualização cartográfica com traçado OSRM em monitor secundário.

### 3.5. Métricas de Desempenho & Faturamento
* KPIs no topo:
  * Pedidos Hoje.
  * SLA Médio de Expedição (meta: < 15 minutos entre aceite e despacho).
  * Faturamento Bruto & Líquido do Dia.
  * Taxa de Conformidade de Lote ANVISA (100%).

---

## 4. Requisitos de UI/UX (Padrão-Ouro Desktop)

1. **Layout**:
   * Sidebar fixa à esquerda (64px recolhida ou 220px expandida).
   * Header com seletor da marca ativa (ex: Conexão Implantes), status operacional do centro de distribuição e relógio de corte cirúrgico (ex: "Corte Flash: 14:00").
   * Área de trabalho em Grid responsivo com tabelas densas e paginação instantânea.
2. **Scrollbars**:
   * Padronizadas cirurgicamente em no máximo 4 pixels (`--border: #E4E4E7`).
3. **Ergonomia Operacional**:
   * Atalhos de teclado (ex: `F2` para bipar lote, `Espaço` para aceitar pedido, `Esc` para fechar modais).
   * Modo escuro de alta legibilidade para monitores de almoxarifado ou modo limpo cirúrgico.

---

## 5. Rotas da Aplicação

* `/` ou `/app`: Interface Mobile-First do Dentista (comprador clínico).
* `/b2b` ou `/portal`: Interface Desktop B2B do Fabricante/Distribuidor.
* `/api/*`: Endpoints determinísticos em Python puro com SQLite WAL.
