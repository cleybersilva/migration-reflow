# Dashboard local — teste honesto, não homologação

Painel web local (SSE + HTML/JS/CSS puros, sem framework) para testar o
fluxo do reflow com um LLM local, sem tocar `output/` nem o pipeline real de
skills/agents. Reaproveita `reflow/` (extração, mascaramento, scan); nunca é
reaproveitado por ele.

## Como iniciar

```powershell
uv run python dashboard/server.py
```

Mantenha o terminal aberto e use **http://127.0.0.1:8765/**. Não abra o HTML
como arquivo — o painel precisa do servidor para falar com `/api/*`.

Requisitos: PowerShell 7 (`pwsh`) instalado, Ollama rodando em loopback
(`ollama serve`) com o modelo `llama3.1:8b` já baixado
(`ollama pull llama3.1:8b`). Nada é baixado pelo botão. Não é necessário
alterar CORS do Ollama, firewall ou expor portas na rede.

## Escopo honesto do botão

O botão executa **testes textuais locais**, não homologa o pipeline completo
de migração. Ele verifica o Ollama, extrai um inventário em área isolada,
solicita prévias documentais e de classificação com evidências, sanitiza
respostas e salva um relatório.

Os resultados ficam em `.dashboard-runs/<execução>/<projeto>/`, fora do Git
e fora de `output/`. O teste **não** altera `output/`, aprova checkpoints ou
reaproveita um `Main.robin` histórico como se fosse nova conversão. Robin
aparece como **não aplicável** porque o teste não gera flow. Nenhum PASS/FAIL
de execução no PAD é presumido.

Uma prévia pode estar errada semanticamente mesmo tendo formato e evidências
válidos: o analista precisa revisá-la. Falta de evidência, resposta JSON
inválida, inventário maior que o orçamento e timeout são falhas, não
respostas aceitas silenciosamente. O worker usa JSON Schema nativo do Ollama
e o runner repete uma vez quando a prévia não segue o formato, cita
evidência inexistente, repete instruções do prompt ou inverte a direção da
migração. Se as duas tentativas falharem, a etapa termina em erro e grava
`failure-<etapa>.json` com motivos sanitizados, sem o texto bruto do modelo.
Nada é truncado ou promovido a sucesso. Cancelamento e achados de segurança
não são repetidos. Logs só mostram informações mascaradas (`mask_data`);
erro interno não reproduz prompt, credencial ou stderr bruto.

O núcleo Python `reflow/` permanece offline. `dashboard/ollama_worker.ps1` é
o adaptador de teste que consulta somente `127.0.0.1:11434`, via PowerShell,
sem proxy — **a única chamada de rede ao LLM, nunca dentro do processo
Python do servidor**. O servidor Python recebe conexões locais e executa
apenas código confiável do projeto, não o legado.

## Se não responder

Confira a mensagem do terminal. Uma porta em LISTENING não comprova
resposta HTTP.

```powershell
Get-NetTCPConnection -LocalPort 8765 -State Listen
```

Identifique o processo e confira sua linha de comando antes de encerrá-lo.
**Não encerre todos os processos Python ou uv**: isso pode interromper
outras aplicações. Depois de atualizar, reinicie somente o servidor deste
projeto e recarregue a página com Ctrl+F5. O servidor envia
`Cache-Control: no-store`.

Para diagnóstico sem disputar a porta original: `uv run python
dashboard/server.py --port 8766` e abra o mesmo endereço com essa porta. O
painel não depende de Ollama para servir HTML/CSS/JS; sem o modelo, a página
continua acessível e informa indisponibilidade claramente.

## Verificações de regressão

```powershell
uv run pytest tests/integration/test_dashboard.py
node --test tests/frontend/dashboard.test.cjs
```

Os testes HTTP abrem dois clientes SSE reais e verificam que POST, assets e
status continuam respondendo — com um `FakeRunner`, nunca o Ollama/PowerShell
de verdade. Os testes JavaScript validam listeners, clique único, estados e
métricas sem npm.

O servidor é somente local. Host/Origin e token por inicialização protegem
operações de escrita; não é autenticação multiusuário nem sandbox de sistema
operacional.

## Por que não LangChain

Este dashboard foi deliberadamente construído **sem** LangChain. O worker
PowerShell já resolve o mesmo problema (prévia estruturada em JSON via
`format` nativo do Ollama, retry com dica, validação de evidência) com uma
fronteira de segurança mais forte — a chamada de rede ao LLM fica fora do
processo Python, nunca dentro dele — e zero dependência de runtime nova.
Ver `docs/decisions.md` (ADR mais recente) para o racional completo.
