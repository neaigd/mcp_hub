# Tutorial Completo da API REST do MCP Hub

Este tutorial explora a API REST do MCP Hub, detalhando sua utilização, funcionalidades, e como podemos integrá-la e adaptá-la às necessidades do nosso projeto.

## 1. Visão Geral do MCP Hub e sua API

O MCP Hub atua como um orquestrador central para servidores e clientes do Model Context Protocol (MCP). Ele expõe uma API REST unificada (`/api/*`) para gerenciar múltiplos servidores MCP e um único endpoint (`/mcp`) para clientes MCP acessarem todas as capacidades dos servidores conectados.

A API REST é a principal interface para interagir programaticamente com o Hub, permitindo:
*   Gerenciamento de servidores MCP (iniciar, parar, listar, etc.).
*   Interação com as capacidades dos servidores (executar ferramentas, acessar recursos, obter prompts).
*   Monitoramento em tempo real do status do Hub e dos servidores.

## 2. Configuração e Execução do MCP Hub (via Docker)

Para seguir este tutorial, o MCP Hub deve estar rodando. Conforme configuramos anteriormente, ele pode ser iniciado via Docker Compose.

1.  **Navegue até o diretório do projeto**:
    ```bash
    cd /media/peixoto/PORTABLE/mcp_hub/neaigd/mcp_hub
    ```
2.  **Inicie o serviço Docker Compose**:
    ```bash
    docker compose up --build -d
    ```
    Isso construirá a imagem (se necessário) e iniciará o container do `mcp-hub` em segundo plano, acessível na porta `37373`.

## 3. Explorando a API REST do MCP Hub

Vamos explorar os principais endpoints da API usando `curl`. Todos os exemplos assumem que o MCP Hub está rodando em `http://localhost:37373`.

### 3.1. Verificando a Saúde do Hub (`GET /api/health`)

Este endpoint fornece informações detalhadas sobre o status atual do Hub, servidores conectados e clientes.

```bash
curl http://localhost:37373/api/health
```

**Exemplo de Saída:**
```json
{
  "status": "ok",
  "state": "ready",
  "server_id": "mcp-hub",
  "activeClients": 0,
  "timestamp": "2025-06-28T16:21:51.354Z",
  "servers": [],
  "connections": {
    "totalConnections": 0,
    "connections": []
  },
  "mcpEndpoint": {
    "activeClients": 0,
    "registeredCapabilities": {
      "tools": 0,
      "resources": 0,
      "resourceTemplates": 0,
      "prompts": 0
    },
    "totalCapabilities": 0
  }
}
```
**Análise:** O `status: "ok"` e `state: "ready"` confirmam que o Hub está operacional. O array `servers` vazio indica que não há servidores MCP configurados ou conectados no momento.

### 3.2. Listando Servidores MCP (`GET /api/servers`)

Este endpoint lista todos os servidores MCP configurados no `mcp-servers.json` e seus respectivos status.

```bash
curl http://localhost:37373/api/servers
```

**Exemplo de Saída (com `mcp-servers.json` vazio):**
```json
{
  "servers": [],
  "timestamp": "2025-06-28T..."
}
```
**Análise:** Atualmente, não há servidores configurados.

### 3.3. Gerenciando Servidores (Exemplo: `POST /api/servers/start`, `POST /api/servers/stop`)

Para gerenciar servidores, você precisa primeiro configurá-los no arquivo `mcp-servers.json`. Vamos simular a adição de um servidor para demonstrar.

**Passo 1: Adicionar um servidor de exemplo ao `mcp-servers.json`**

Vamos adicionar um servidor STDIO de exemplo que apenas ecoa o que recebe. Para isso, precisaremos de um script simples.

Crie um arquivo `echo-server.js` no diretório `neaigd/mcp_hub/examples/` com o seguinte conteúdo:
```javascript
// examples/echo-server.js
process.stdin.on('data', (data) => {
  const message = JSON.parse(data.toString());
  if (message.type === 'getCapabilities') {
    process.stdout.write(JSON.stringify({
      type: 'capabilities',
      capabilities: {
        tools: [{ name: 'echo', description: 'Echoes back the input' }],
        resources: [],
        prompts: []
      }
    }) + '\n');
  } else if (message.type === 'callTool' && message.tool === 'echo') {
    process.stdout.write(JSON.stringify({
      type: 'toolResult',
      tool: 'echo',
      result: { echoed: message.arguments.input }
    }) + '\n');
  } else {
    process.stdout.write(JSON.stringify({ type: 'error', message: 'Unknown command' }) + '\n');
  }
});

process.stdin.on('end', () => {
  process.exit();
});

console.error('Echo server started'); // Log to stderr for debugging
```

Agora, atualize o `mcp-servers.json` para incluir este servidor.
**Edite o arquivo `/media/peixoto/PORTABLE/mcp_hub/neaigd/mcp_hub/mcp-servers.json` para:**
```json
{
  "mcpServers": {
    "my-echo-server": {
      "command": "node",
      "args": ["./examples/echo-server.js"],
      "dev": {
        "enabled": true,
        "watch": ["./examples/echo-server.js"],
        "cwd": "/app"
      }
    }
  }
}
```
**Importante:** Após editar o `mcp-servers.json`, você precisará reiniciar o container do `mcp-hub` para que ele carregue a nova configuração.
```bash
docker compose up --build -d
```

**Passo 2: Iniciar o Servidor MCP de Exemplo**

```bash
curl -X POST http://localhost:37373/api/servers/start -H "Content-Type: application/json" -d '{"server_name": "my-echo-server"}'
```

**Passo 3: Listar Servidores Novamente para Verificar o Status**

```bash
curl http://localhost:37373/api/servers
```
Você deverá ver `my-echo-server` com `status: "connected"`.

**Passo 4: Parar o Servidor MCP de Exemplo**

```bash
curl -X POST http://localhost:37373/api/servers/stop -H "Content-Type: application/json" -d '{"server_name": "my-echo-server"}'
```

### 3.4. Executando Ferramentas (`POST /api/servers/tools`)

Após iniciar o `my-echo-server`, podemos chamar a ferramenta `echo` que ele expõe.

```bash
curl -X POST http://localhost:37373/api/servers/tools -H "Content-Type: application/json" -d '{
  "server_name": "my-echo-server",
  "tool": "echo",
  "arguments": {
    "input": "Hello from MCP Hub API!"
  }
}'
```

**Exemplo de Saída:**
```json
{
  "result": {
    "echoed": "Hello from MCP Hub API!"
  },
  "timestamp": "2025-06-28T..."
}
```

### 3.5. Eventos em Tempo Real (`GET /api/events`)

O endpoint `/api/events` fornece um stream de eventos Server-Sent Events (SSE) para atualizações em tempo real. Você pode usá-lo para monitorar o status do Hub, mudanças de configuração, status de servidores e muito mais.

Para testar, você pode usar `curl` (ele permanecerá conectado e exibirá os eventos à medida que ocorrem):

```bash
curl http://localhost:37373/api/events
```
Enquanto o `curl` estiver rodando, tente iniciar ou parar o `my-echo-server` em outro terminal. Você verá eventos como `servers_updated` e `tool_list_changed` aparecerem no stream.

## 4. Análise para o Projeto "Tutoriais Gratuitos"

### 4.1. O que Podemos Utilizar

*   **Centralização de Fontes de Conhecimento**: O MCP Hub pode ser o ponto único para acessar diversas "fontes de conhecimento" (que seriam servidores MCP). Por exemplo, um servidor MCP para buscar informações em bancos de dados, outro para acessar APIs externas, e outro para processar documentos locais.
*   **Abstração para Clientes**: Nossos clientes (sejam eles CLIs, UIs ou outros serviços) só precisarão se conectar a um único endpoint (`http://localhost:37373/mcp`) para acessar todas as capacidades, sem se preocupar com a complexidade de múltiplos servidores.
*   **Gerenciamento Dinâmico**: Podemos adicionar ou remover fontes de conhecimento (servidores MCP) sem precisar reconfigurar os clientes.
*   **Monitoramento em Tempo Real**: A API de eventos SSE é crucial para construir interfaces de usuário que reagem a mudanças no status dos servidores ou na disponibilidade de ferramentas/recursos.
*   **Extensibilidade**: Podemos desenvolver nossos próprios servidores MCP em qualquer linguagem que suporte STDIO ou HTTP/SSE, e integrá-los facilmente ao Hub.

### 4.2. O que Precisaremos Mudar/Adaptar

*   **Configuração do `mcp-servers.json`**: Precisaremos definir nossos próprios servidores MCP neste arquivo, apontando para as fontes de dados ou serviços que queremos integrar. Isso incluirá a criação de servidores MCP reais que implementem as capacidades necessárias (ferramentas, recursos, prompts).
*   **Desenvolvimento de Servidores MCP Customizados**: Para o projeto "Tutoriais Gratuitos", provavelmente precisaremos desenvolver servidores MCP que:
    *   Acessem e indexem tutoriais.
    *   Forneçam ferramentas para buscar informações específicas.
    *   Ofereçam prompts para gerar resumos ou respostas.
*   **Interface de Usuário (se desejado)**: Se quisermos uma interface gráfica para o "Tutoriais Gratuitos", teremos que desenvolvê-la separadamente, consumindo a API REST do MCP Hub. O Hub não fornece uma UI pronta para uso.
*   **Autenticação/Autorização**: Se nossos servidores MCP ou fontes de dados exigirem autenticação, precisaremos configurar isso no `mcp-servers.json` e, possivelmente, implementar a lógica de OAuth ou cabeçalhos de autenticação.

### 4.3. Aplicações Potenciais no Projeto "Tutoriais Gratuitos"

*   **Mecanismo de Busca Unificado**: Um servidor MCP pode ser responsável por buscar tutoriais em diferentes formatos (Markdown, PDF, vídeos) e de diferentes fontes (repositórios Git, sites, bases de dados).
*   **Ferramentas de Resumo e Análise**: Servidores MCP podem expor ferramentas que utilizam modelos de linguagem (LLMs) para resumir tutoriais, extrair pontos-chave ou responder a perguntas específicas.
*   **Gerenciamento de Conteúdo**: Ferramentas para adicionar, atualizar ou categorizar tutoriais podem ser expostas via MCP.
*   **Integração com Ferramentas Existentes**: Se já tivermos ferramentas ou scripts para processar informações, podemos envolvê-los em um servidor MCP e disponibilizá-los via Hub.

## 5. Outras Questões e Considerações

*   **Segurança**: Como o Hub lida com a segurança? O `README.md` menciona OAuth 2.0 e Headers para autenticação. Precisamos entender como aplicar isso para proteger o acesso aos nossos servidores MCP e dados sensíveis.
*   **Escalabilidade**: Como o Hub se comporta com um grande número de servidores MCP ou alta demanda de clientes?
*   **Monitoramento e Logs**: O Hub fornece logs estruturados. Precisamos integrar isso com nossas ferramentas de monitoramento.
*   **Persistência**: A configuração do `mcp-servers.json` é persistente, mas o estado dos servidores (conectado/desconectado) é volátil. Como lidaremos com a recuperação de falhas?

## Conclusão

O MCP Hub é uma ferramenta poderosa para unificar e gerenciar diversas fontes de conhecimento e ferramentas através do Model Context Protocol. Sua API REST robusta e o suporte a eventos em tempo real o tornam uma base sólida para o projeto "Tutoriais Gratuitos", permitindo a criação de um sistema flexível e extensível para combater a desinformação e centralizar o conhecimento. O próximo passo seria começar a desenvolver um servidor MCP de exemplo que se integre com uma fonte de tutoriais.
