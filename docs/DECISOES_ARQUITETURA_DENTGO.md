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

---

## 7.1. Regra Canônica Inviolável de Modais (100% In-App)
* **Banimento Estrito de Caixas de Diálogo Nativas**: É estritamente proibido o uso de `window.alert()`, `window.confirm()`, `window.prompt()` ou quaisquer diálogos nativos do sistema operacional (Windows, Android, iOS, macOS) em todos os ecossistemas DentGo (`/app`, `/b2b`, `/driver`).
* **Padrão Obrigatório de Modais**:
  - Todos os diálogos, confirmações, alertas, inserções de dados e visualizações devem ser construídos como componentes DOM estilizados com backdrops semitransparentes (`.modal-overlay`, `.b2b-modal-backdrop`), garantindo identidade visual, suporte PWA e blindagem contra travamento de thread do SO.

---

## 9. Motores Reais Integrados e Arquitetura Open-Source

### 9.1. Princípio Arquitetural: "Nada se cria, tudo se modela e se adapta"
* A plataforma DentGo rejeita reinventar a roda ou criar motores proprietários do zero para componentes amplamente padronizados e testados pela comunidade global.
* Todos os subsistemas adotam motores open-source de alta performance, maduros, auditados e integrados sem custos adicionais de licenciamento:
  1. **Motor de Renderização e Geometria Cartográfica**: **Leaflet.js** (OpenStreetMap tiles, polylines determinísticas e marcação de waypoints).
  2. **Motor de Roteirização TSP (Problema do Caixeiro Viajante)**: **OSRM / Valhalla** (roteirização real de tráfego, telemetria e projeção de ETA).
  3. **Motor Gerador de Matriz Bidimensional (QR Code)**: **QRCode.js** (padrão ISO/IEC 18004 com correção de erros Reed-Solomon nível M para PIX EMV e Handshake de Custódia).
  4. **Motor de Captura Óptica e Visão Computacional**: **Html5-Qrcode** (decodificação de códigos de barras GS1/DataMatrix ANVISA e QR codes por câmeras traseiras/frontais e leitores ópticos USB HID).
  5. **Motor de Persistência e Integridade Transacional**: **SQLite 3 nativo via Python** (banco de dados ACID embutido, zero dependência externa de infraestrutura).


## 8. Logística Avançada, Roteirização TSP e Custódia

### 8.1. Agrupamento (Batching) e Limites de Entregas por Corrida
* **Flash Cirúrgico 2h**: **Exclusivo (1 corrida = 1 pedido)**. Bloqueio automático de qualquer corrida simultânea até a conclusão da entrega via PIN do dentista.
* **Same-Day (Mesmo Dia)**: Até 3 entregas agrupadas por bolsão geográfico (raio máximo de 4 km entre consultórios).
* **Next-Day (D+1)**: Até 6 entregas consolidadas em rota sequencial.

### 8.2. Motor de Roteirização Inteligente (DentGo Route Engine)
* Cálculo determinístico da rota ótima resolvendo o Problema do Caixeiro Viajante (TSP) via OSRM / Valhalla.
* Ordem de paradas sequencial inviolável no app do motorista: Coletas agrupadas seguidas por Entregas na ordem calculada para cumprimento de SLA.

### 8.3. Handshake Criptográfico de Custódia (Retirada no Fabricante)
* Token efêmero assinado no formato:
  `DGO:CUSTODIA:{pedido_id}:{driver_id}:{timestamp_utc}:{hmac_hash}`
* Exibição em QR Code no app do motorista e leitura pelo almoxarife/expedidor do fabricante via:
  1. Leitor óptico de código de barras USB/Bluetooth conectado ao Portal B2B Desktop.
  2. Câmera de smartphone/tablet em módulo web responsivo.
* Registro atômico para auditoria anti-fraude: `timestamp`, `driver_id`, `geofence (<50m do CD)` e `lote_anvisa`.

### 8.4. Regras Financeiras, Liquidação e Risco de Gateway
* **Valores de Frete por Modalidade**:
  - Flash Cirúrgico (Até 2h): Cliente R$ 25,00 a R$ 35,00 | Repasse Piloto R$ 20,00 a R$ 28,00.
  - Same-Day: Cliente R$ 15,00 a R$ 18,00 | Repasse Piloto R$ 12,00 a R$ 14,00.
  - Next-Day: Cliente R$ 9,90 a R$ 12,00 (transporte consolidado).
* **Mitigação do Risco de Antecipação de Cartão de Crédito**:
  - Pagamentos de frete via Cartão de Crédito entram no saldo como **Disponível em D+1 útil** ou liquidação semanal sem custo.
  - Antecipação sob demanda imediata no mesmo dia desconta a taxa de intermediação/antecipação bancária (R$ 2,50).
  - Pagamentos via PIX caem instantaneamente na conta escrow da DentGo e liberam saque no mesmo dia.
* **Chave PIX e Titularidade**:
  - Validação estrita: a chave PIX do piloto deve ter a mesma titularidade de CPF cadastrado na CNH, banindo intermediários e contas de terceiros.

### 8.5. Onboarding Seguro & Blindagem Jurídica do Entregador
* **Reconhecimento Facial e Prova de Vida (Liveness Detection)**: biometria facial obrigatória para prevenir contas alugadas.
* **Documentação Obrigatória com OCR**:
  - CNH com registro EAR (Exerce Atividade Remunerada).
  - CRLV da motocicleta atualizado.
  - Certidão Negativa de Antecedentes Criminais (Estadual e Federal).
  - Comprovante de residência.
* **Treinamento de Biossegurança Cirúrgica**:
  - 3 módulos em vídeo (manuseio de caixas estéreis lacradas ANVISA, postura em clínicas e uso do app).
  - Questionário com 100% de aproveitamento obrigatório.
* **Contrato Digital Autônomo**:
  - Termo de adesão sob a Lei 11.442/07 e Código Civil (sem vínculo CLT), com responsabilidade civil expressa pela custódia das caixas cirúrgicas.
* **Elegibilidade**: Aceite de motofretistas autônomos credenciados e frotas empresariais homologadas.


