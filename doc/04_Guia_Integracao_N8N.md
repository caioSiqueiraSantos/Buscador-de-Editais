# Guia de Implementação e Uso do n8n (Orquestrador)

Este documento orienta a operação, agendamento semanal e disparo de alertas de alta relevância utilizando o **n8n** integrado ao **Buscador de Editais**.

---

## 1. Visão do Fluxo de Automação

```text
[Cron Semanal: Segunda 08:00] OU [Disparo Manual n8n]
                  │
                  ▼
   [HTTP Request: POST /pipeline/executar]
   (Header: X-API-Key: metro_inovacao_n8n_secret_2026)
                  │
                  ▼
   [FastAPI: Scrapers FINEP/FAPESP + IA Gemini + DB]
                  │
                  ▼
   [Retorno JSON com oportunidades_alta_aderencia]
                  │
          ┌───────┴───────┐
          │               │
       (Total > 0)    (Total == 0)
          │               │
          ▼               ▼
[Code: Formata Alerta]  [Log: Rodada Sem Novidades]
          │
          ▼
[Teams / E-mail / Slack]
(Com link: /?aderencia=Alta)
```

---

## 2. Como Subir o n8n

### Opção A: Via Docker Compose (Recomendado)
Na raiz do projeto, execute:
```bash
docker compose -f docker-compose.n8n.yml up -d
```
> O painel do n8n estará acessível em: `http://localhost:5678`.

### Opção B: Via Docker Simples
```bash
docker run -d --name n8n-buscador \
  -p 5678:5678 \
  -e BACKEND_URL=http://host.docker.internal:8000 \
  -e PIPELINE_API_KEY=metro_inovacao_n8n_secret_2026 \
  -e FRONTEND_URL=http://localhost:5173 \
  -v n8n_data:/home/node/.n8n \
  docker.n8n.io/n8nio/n8n:latest
```

---

## 3. Como Importar o Workflow no n8n

1. Acesse `http://localhost:5678` no seu navegador.
2. Complete o cadastro de usuário inicial (caso seja a primeira inicialização).
3. No menu lateral, clique em **Workflows** e depois no botão **Add Workflow** (ou ícone `+`).
4. Clique no menu de três pontos (`...`) no canto superior direito da tela do editor de workflows e selecione **Import from File...**.
5. Selecione o arquivo:
   ```text
   Buscador-de-Editais/n8n/workflow_buscador_editais.json
   ```
6. O workflow será carregado com todos os nós configurados e conectados.
7. Clique em **Save** e ative o botão **Active** para habilitar o agendamento semanal automático.

---

## 4. Endpoints Disponíveis no Backend para o n8n

| Método | Endpoint | Protegido | Descrição |
|---|---|---|---|
| `POST` | `/pipeline/executar` | Sim (`X-API-Key`) | Executa a pipeline completa (scrapers + IA) e retorna oportunidades de alta aderência da rodada. Suporta `{ "assincrono": false }` ou `{ "assincrono": true }`. |
| `GET` | `/pipeline/alta-aderencia` | Sim (`X-API-Key`) | Retorna os editais ativos com aderência **Alta** mais recentes (últimos 7 dias) sem disparar scraper. |
| `GET` | `/oportunidades?aderencia=Alto` | Não | Retorna oportunidades filtradas por nível de aderência. |

### Exemplo de Requisição cURL (Disparo Manual):
```bash
curl -X POST http://localhost:8000/pipeline/executar \
  -H "Content-Type: application/json" \
  -H "X-API-Key: metro_inovacao_n8n_secret_2026" \
  -d '{"assincrono": false}'
```

---

## 5. Configuração de Canais de Alerta

No arquivo `n8n/workflow_buscador_editais.json` ou diretamente no painel do n8n:
- **Microsoft Teams:** Substitua a URL do nó *Notificação Microsoft Teams (Webhook)* pelo seu webhook do canal corporativo (Connectors -> Incoming Webhook).
- **E-mail:** Caso prefira receber por e-mail, adicione o nó *Send Email* (SMTP / Outlook 365) conectado à saída do nó *Formatar Comunicado Executivo*, utilizando o campo `{{ $json.mensagem_html }}` no corpo da mensagem.

---

## 6. Transição para Nuvem Corporativa Microsoft Azure

Quando o projeto for migrado para a nuvem da companhia de metrô:
- O n8n pode rodar como um container gerenciado no **Azure Container Apps** ou **Azure App Service**.
- A variável `BACKEND_URL` deve apontar para o endpoint privado da API (`https://api-editais.azurewebsites.net`).
- A `PIPELINE_API_KEY` deve ser provisionada através do **Azure Key Vault**.
- O envio de mensagens corporativas no Teams pode utilizar a integração nativa com o **Microsoft Entra ID / Microsoft Graph API**.

