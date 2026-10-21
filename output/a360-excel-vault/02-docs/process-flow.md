# Fluxo do processo

1. **Passo 1 — Abertura da planilha Excel**: o robô abre o arquivo Excel que
   serve como fonte de dados do processo (`main.json:1`, registrado em
   `01-inventory/inventory.json:15-23`).
2. **Passo 2 — Leitura do intervalo de dados**: o robô lê um intervalo de
   células da planilha aberta no passo anterior (`main.json:2`, registrado em
   `01-inventory/inventory.json:24-32`).
3. **Passo 3 — Envio dos dados via chamada HTTP (REST)**: os dados lidos são
   enviados por meio de uma requisição HTTP do tipo POST, com corpo de
   requisição e cabeçalho de autorização, a um sistema externo
   (`main.json:3`, registrado em `01-inventory/inventory.json:38-49`).
4. **Passo 4 — Obtenção de credencial no Cofre de Credenciais**: o robô
   recupera uma credencial do Cofre de Credenciais (`CredentialVault`) para
   autenticar a integração (`main.json:4`, registrado em
   `01-inventory/inventory.json:2-13`, referência `credential-vault`).
5. **Passo 5 — Comando não reconhecido (`CustomPackage/transform`)**: há um
   comando do pacote `CustomPackage` no fluxo que a extração determinística
   não conseguiu classificar (`main.json:5`, registrado em
   `01-inventory/inventory.json:54-61`). Ver seção "Comandos não
   reconhecidos" abaixo.
6. **Passo 6 — Comando não reconhecido (`Browser/unmappedAction`)**: há um
   comando do pacote `Browser` no fluxo que a extração determinística não
   conseguiu classificar (`main.json:6`, registrado em
   `01-inventory/inventory.json:62-69`). Ver seção "Comandos não
   reconhecidos" abaixo.

## Dependências entre bots

O inventário não lista nenhum item em `dependencies`
(`01-inventory/inventory.json:34`, array vazio). Não há bot pai/filho
identificado para este projeto.

## Comandos não reconhecidos (`unknown_commands`)

O inventário registra 2 comandos que a extração determinística não
conseguiu mapear para uma ação Robin conhecida. Eles são listados aqui como
**pendentes de classificação** — nenhuma função de negócio foi presumida
para eles, e nenhuma suposição deve ser feita até revisão humana e consulta
a `reference/robin-actions.md`:

| Pacote | Comando | Evidência | Status |
| --- | --- | --- | --- |
| `CustomPackage` | `transform` | `main.json:5` (`01-inventory/inventory.json:54-61`) | Pendente de classificação |
| `Browser` | `unmappedAction` | `main.json:6` (`01-inventory/inventory.json:62-69`) | Pendente de classificação |

Estes dois comandos devem alimentar `reference/a360-to-pad.md` como
"pendente de classificação" e não devem ser tratados como ação já mapeada ou
como requisito de negócio confirmado.
