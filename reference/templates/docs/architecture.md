<!--
Template de 02-docs/architecture.md — atende ao pedido R3 da reunião (diagrama de
arquitetura por projeto, para identificar integrações). Um nó por sistema/fonte de
dados/credencial referenciada; rótulo cita o tipo, nunca o valor. Gere a partir de
http_calls, data_sources, credentials e dependencies do inventory.json.
-->

# Arquitetura do projeto

```mermaid
flowchart LR
    ROBO[<nome do projeto>]
    UI[Interface/UI automatizada]
    DADOS[(Fonte de dados: <tipo>)]
    HTTP[[Sistema externo via HTTP/SOAP: <operação>]]
    CRED{{Credencial: <referência, nunca o valor>}}
    FILHO[Bot filho: <target, se houver dependência>]

    ROBO --> UI
    ROBO --> DADOS
    ROBO --> HTTP
    ROBO --> CRED
    ROBO --> FILHO
```

## Legenda das integrações

| Nó | Evidência | Observação |
| --- | --- | --- |
| `<sistema/fonte>` | `arquivo:linha` | [o que esse nó representa] |

<!-- Remova os nós que não se aplicarem a este projeto; não invente integração
     sem evidência no inventário. -->
