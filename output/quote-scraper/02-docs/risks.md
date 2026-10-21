# Riscos e alertas de portabilidade

| Alerta | Aplica-se? | Evidência | Mitigação sugerida |
| --- | --- | --- | --- |
| A1 — extensão de navegador específica | não | sem evidência de uso de navegador no inventário (`01-inventory/inventory.json:43`, `ui_interactions` vazio) | não aplicável |
| A2 — coordenadas de tela fixas | não | sem evidência de interação com tela no inventário (`01-inventory/inventory.json:43`, `ui_interactions` vazio) | não aplicável |
| A3 — versão específica de app desktop | não | sem evidência de dependência de aplicativo desktop no inventário (`01-inventory/inventory.json:15-28`, apenas bibliotecas padrão do Python) | não aplicável |
| A4 — credencial via Credential Vault do A360 | não | `01-inventory/inventory.json:2` (`credentials` vazio) | não aplicável |
| A5 — biblioteca/DLL compartilhada entre projetos | não | `main.py:3-4` (dependências são módulos padrão do Python — `urllib.request.urlopen` e `csv` —, não uma DLL/biblioteca compartilhada entre projetos) | não aplicável |

## Observação adicional

O robô depende da disponibilidade de um endereço externo chamado em `main.py:8`. Não há, no trecho analisado, tratamento de erro visível para falha de conexão, resposta HTTP inesperada ou falha na escrita do arquivo (`main.py:8-11`). Essa ausência de tratamento de erro não está listada nos alertas A1-A5 da rubrica, mas é um ponto a validar com um analista humano antes da conversão.
