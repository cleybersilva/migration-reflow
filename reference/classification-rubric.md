# Rubrica de classificação: PAD | PARTIAL | NOT_PAD

Esta rubrica é aplicada pela skill `reflow-classify` / agent `reflow-classifier`
(Fase 6, ainda não implementado) sobre `01-inventory/inventory.json` e `02-docs/`.
Até lá, é a referência que um analista humano usa pra decidir à mão.

**Regra KISS:** na dúvida entre `PAD` e `PARTIAL`, escolha `PAD` — é mais fácil o
analista cortar escopo depois do que o pipeline parar sem converter nada. Na dúvida
entre `PARTIAL` e `NOT_PAD`, escolha `PARTIAL` e registre o motivo nos alertas.

## Critérios de UI (favorecem PAD)

| # | Critério |
| --- | --- |
| C1 | O fluxo é majoritariamente interação com UI desktop/Web (clique, digitação, leitura de tela) |
| C2 | O aplicativo roda em Windows e tem elementos de UI estáveis (sem CAPTCHA dinâmico, sem canvas sem acessibilidade) |
| C3 | O volume/frequência de execução é compatível com RPA (não precisa de tempo real/baixa latência) |
| C4 | Não existe SDK/API oficial e suportada para a mesma automação |
| C5 | A tarefa depende de sessão de usuário interativa (login manual, MFA, etc.) que não dá pra automatizar só via API |

## Critérios de não-UI (reduzem a adequação ao PAD, mesmo sem UI)

| # | Critério |
| --- | --- |
| N1 | Já existe API REST/SOAP documentada e com credencial de serviço disponível para a mesma tarefa |
| N2 | O aplicativo já é SaaS/cloud-native com endpoint de integração — **ver regra explícita abaixo** |
| N3 | O volume de execução exige paralelismo/alta disponibilidade incompatível com PAD (1 flow por vez, por máquina) |
| N4 | A tarefa é puramente ETL de dados estruturados, sem nenhuma interação de UI |
| N5 | Já existe uma automação equivalente rodando de forma estável em outra tecnologia (Python determinístico, Azure Function, etc.), sem necessidade de reescrita |

### Regra explícita — nuvem/API já disponível

> Aplicação que já roda em nuvem ou já tem API madura: avalie seriamente `NOT_PAD`,
> mesmo que hoje exista uma camada de UI sendo automatizada só porque "sempre foi
> assim". Migrar pra PAD, nesse caso, troca uma dívida técnica por outra.

## Alertas de portabilidade (não mudam o veredito, mas têm que ser registrados)

| # | Alerta |
| --- | --- |
| A1 | Depende de extensão de navegador específica (ex.: extensão do Power Automate) — exige padronizar o ambiente do analista |
| A2 | Depende de coordenadas de tela fixas — frágil a mudança de resolução/layout |
| A3 | Depende de versão específica de app desktop (ex.: Excel com add-in próprio) |
| A4 | Usa `CredentialVault` do A360 — precisa de plano de migração das credenciais pro Credential Manager do PAD |
| A5 | Código fonte (.NET/Python) usa biblioteca/DLL compartilhada entre múltiplos projetos — risco de dependência cruzada ao migrar |

## Regra de decisão

1. Conte quantos critérios C1–C5 o projeto atende e quantos N1–N5 ele atende.
2. **PAD**: atende à maioria de C1–C5 e nenhum N1/N2 forte.
3. **PARTIAL**: atende parcialmente — uma parte do fluxo é claramente UI (vai pra
   PAD) e outra parte é claramente dados/API (ficaria melhor em outra tecnologia).
   Documente as duas partes separadamente em `03-classification/classification.md`.
4. **NOT_PAD**: predominam N1/N2 (API ou nuvem já disponível) ou N4/N5 (ETL puro
   com alternativa mais barata). `NOT_PAD` encerra o projeto após a documentação —
   não gera conversão.
5. Todo alerta A1–A5 identificado entra na seção "Alertas" do veredito, mesmo
   quando não muda a decisão.

## Saída esperada (frontmatter do `classification.md`)

```yaml
verdict: PAD | PARTIAL | NOT_PAD
pad_use_cases:
  - <caso de uso que vai para o PAD>
alerts:
  - <alerta A1-A5 identificado, com evidência arquivo:linha>
```
