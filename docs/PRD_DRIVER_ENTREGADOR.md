# PRD & Modelagem Técnica — DentGo Driver PWA (App do Entregador Express)

**Documento**: PRD-DENTGO-DRIVER-001  
**Autor**: AIDD Architecture & Product Engine  
**Status**: Homologado  
**Público-Alvo**: Motofretistas Autônomos Credenciados e Frotistas Parceiros (Lalamove, Borzo, Loggi ou Frota Exclusiva).  
**Viewport Primário**: Mobile Estrito (PWA 375px a 430px — iOS / Android).  
**Princípio Central**: Zero burocracia, alto contraste na rua, ações de 1 toque com luva/suporte veicular e validação de entrega por PIN de 4 dígitos.

---

## 1. Visão Geral & Papel no Ecossistema

O **DentGo Driver** é a aplicação de ponta a ponta que conecta o centro de distribuição (CD) do fabricante à cadeira do cirurgião-dentista em menos de 120 minutos (SLA Flash).

Diferente de apps de delivery convencional de comida, a carga transportada é de alto valor cirúrgico (implantes de titânio estéreis, kits cirúrgicos e biomateriais com rastreabilidade ANVISA). Portanto, o app exige:
1. **Conferência de Lacre**: Validação rápida do pacote no balcão de expedição.
2. **Telemetria OSRM / GPS em Segundo Plano**: Transmissão contínua da localização para o painel do fabricante e do dentista.
3. **Travamento por PIN de Segurança**: A corrida só é liquidada quando o dentista ou a secretária fornece o PIN de 4 dígitos gerado na compra.

---

## 2. Personas & Jornada Operacional

### Persona: Entregador Express (Moto)
* **Contexto**: Utiliza smartphone montado no guidão da moto, sob sol forte ou chuva, frequentemente usando luvas.
* **Necessidades**:
  * Botões de toque gigantes (mínimo 48px).
  * Informações cruciais em texto grande e fonte Mono: ID do Pedido, Endereço de Coleta (CD) e Endereço de Entrega (Consultório).
  * Integração de 1 toque com Waze e Google Maps.
  * Validação instantânea do PIN sem formulários complexos.

---

## 3. Fluxo de Estados da Corrida (State Machine)

A jornada da entrega segue uma máquina de estados linear e irreversível:

```text
[DISPONÍVEL] 
     │ (Alerta sonoro + Push de nova corrida Flash)
     ▼
[NOTIFICADO / ACEITAR CORRIDA] (Timer regressivo de 45 segundos)
     │ (Entregador clica em "Aceitar Corrida")
     ▼
[A CAMINHO DO CD / COLETA]
     │ (GPS calcula rota até o Fabricante; ex: Conexão Moema)
     ▼
[NO BALCÃO DE EXPEDIÇÃO]
     │ (Apresenta o ID do Pedido ao expedidor; recebe o pacote lacrado)
     │ (Clica em "Confirmar Coleta & Iniciar Rota")
     ▼
[EM ROTA PARA O CONSULTÓRIO]
     │ (Navegação GPS ativa; telemetria alimenta o mapa do dentista)
     ▼
[CHEGADA NO DESTINO / CONSULTÓRIO]
     │ (Clica em "Cheguei no Consultório")
     ▼
[VALIDAÇÃO DE PIN]
     │ (Solicita o PIN de 4 dígitos ao dentista; digita no teclado numérico grande)
     ▼
[ENTREGA CONCLUÍDA & LIQUIDAÇÃO]
     │ (Repasse creditado na carteira virtual do piloto)
     ▼
[DISPONÍVEL PARA PRÓXIMA CORRIDA]
```

---

## 4. Modelagem de Dados (Entidades SQLite / DTO)

### 4.1. Tabela: `entregadores` (Motoristas Credenciados)
```sql
CREATE TABLE IF NOT EXISTS entregadores (
    id TEXT PRIMARY KEY,               -- ex: 'DRV-7741'
    nome TEXT NOT NULL,
    telefone TEXT NOT NULL,
    cpf TEXT NOT NULL UNIQUE,
    veiculo_placa TEXT NOT NULL,
    veiculo_modelo TEXT NOT NULL,       -- ex: 'Honda CG 160 Cargo'
    status TEXT DEFAULT 'offline',      -- 'offline', 'disponivel', 'em_rota'
    latitude_atual REAL,
    longitude_atual REAL,
    bateria_nivel INTEGER,
    origem_frota TEXT DEFAULT 'dentgo', -- 'dentgo', 'lalamove', 'borzo'
    saldo_carteira REAL DEFAULT 0.00,
    criado_em TEXT DEFAULT CURRENT_TIMESTAMP
);
```

### 4.2. Tabela: `corridas_entrega` (Missões de Despacho)
```sql
CREATE TABLE IF NOT EXISTS corridas_entrega (
    id TEXT PRIMARY KEY,               -- ex: 'COR-9821'
    pedido_id TEXT NOT NULL,            -- chave estrangeira do pedido
    entregador_id TEXT,                 -- chave estrangeira do entregador
    tipo_sla TEXT NOT NULL,             -- 'flash_2h' ou 'normal_hoje'
    
    -- Pontos Geográficos
    origem_nome TEXT NOT NULL,          -- ex: 'Conexão Implantes (CD Moema)'
    origem_endereco TEXT NOT NULL,
    origem_lat REAL NOT NULL,
    origem_lng REAL NOT NULL,
    
    destino_nome TEXT NOT NULL,         -- ex: 'Dr. Roberto Fontes - Clínica Jardins'
    destino_endereco TEXT NOT NULL,
    destino_lat REAL NOT NULL,
    destino_lng REAL NOT NULL,
    
    -- Segurança & Liquidação
    pin_seguranca TEXT NOT NULL,        -- Hash do PIN de 4 dígitos
    distancia_km REAL NOT NULL,
    tempo_estimado_min INTEGER NOT NULL,
    valor_frete_total REAL NOT NULL,    -- Valor pago pelo cliente (ex: 29.00)
    valor_repasse_piloto REAL NOT NULL, -- Valor líquido do motorista (ex: 20.00)
    
    -- Estados da Máquina
    status TEXT NOT NULL,               -- 'aguardando', 'aceito', 'coletado', 'entregue', 'cancelado'
    horario_aceite TEXT,
    horario_coleta TEXT,
    horario_entrega TEXT
);
```

---

## 5. Requisitos de Telas & UI/UX (Driver PWA)

1. **Tela 1: Radar de Ofertas (Modo Espera)**:
   * Chave visual de "Ficar Online / Offline".
   * Card de corrida pendente em destaque com timer de 45 segundos.
   * Valor a receber pelo frete em destaque: **R$ 20,00** (líquido).
   * Botão gigante de ação: **"Aceitar Corrida"** (preto `#09090B`).

2. **Tela 2: Guia de Coleta (No Fabricante)**:
   * Endereço do CD e botão para abrir Waze / Google Maps direto no celular.
   * Alerta: *"Mostre o código PED-9821 para retirar o pacote lacrado"*.
   * Botão: **"Pacote Retirado • Iniciar Viagem"**.

3. **Tela 3: Em Rota Cirúrgica (Navegação)**:
   * Nome do cirurgião, telefone e botão rápido de ligação / WhatsApp da secretária.
   * Transmissão automática do GPS a cada 10 segundos para a API.
   * Botão: **"Cheguei no Consultório"**.

4. **Tela 4: Teclado de Validação de PIN**:
   * Quatro caixas numéricas (`_ _ _ _`).
   * Teclado numérico gigante integrado na tela (sem abrir o teclado nativo de letras do celular).
   * Feedback sonoro/vibração e tela de confirmação imediata: *"Corrida Finalizada! +R$ 20,00 na carteira"*.

---

## 6. Rotas da Arquitetura Web

* `/driver` ou `/entregador`: PWA Mobile do Entregador com cache offline via Service Worker.
* `/api/v1/driver/status`: Ping de geolocalização e bateria.
* `/api/v1/driver/aceitar`: Atribuição de corrida.
* `/api/v1/driver/validar-pin`: Encerramento da corrida e conciliação do split.
