<!--
Regras de negócio e condições identificadas no fluxo. Toda regra cita
arquivo:linha. Sem evidência clara no inventário, registra-se como TODO reflow.
-->

# Regras de negócio

## TODO reflow — nenhuma regra condicional identificada pela extração

A extração determinística registrada em `01-inventory/inventory.json` não
captura nenhuma condição, validação ou critério de decisão explícito para este
projeto: os campos `unknown_commands` e `warnings` estão vazios, e os comandos
presentes (`Browser.open` em `main.json:1`, `REST.get` em `main.json:2`,
`CredentialVault.getCredential` em `main.json:3`, `TaskBot.run` em
`main.json:4` e `Excel.read` em `child.json:1`) descrevem apenas uma sequência
linear de passos, sem ramificações.

Caso exista alguma regra de negócio por trás dessa sequência (por exemplo,
critérios para decidir quando consultar o serviço externo ou quando acionar o
bot filho), ela não está representada no inventário e precisa ser levantada
com um analista humano antes da conversão para PAD. Não há evidência
`arquivo:linha` suficiente para documentar essa regra sem risco de invenção.
