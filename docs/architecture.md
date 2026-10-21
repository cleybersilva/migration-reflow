# Arquitetura alvo

Estado: esqueleto; componentes funcionais serão implementados nas próximas fases.

```mermaid
flowchart LR
    A[Legado local não confiável] --> B[Python determinístico: extração e masking]
    B --> C[Inventário mascarado e manifesto]
    C --> D[Agents: documentação e classificação]
    D --> E{Checkpoint humano}
    E -->|PAD ou PARTIAL aprovado| F[Conversão e flow de teste]
    E -->|NOT_PAD| G[Encerrar sem conversão]
    F --> H[Scan e lint determinísticos]
    H --> I[Analista valida no PAD]
    R[Referências e whitelist] --> F
    D -. Harness .-> L[IAra ou provider autorizado]
    F -. Harness .-> L
```

Somente o harness acessa o LLM. Python não usa rede nem executa o legado.
Nenhum diagrama preexistente foi alterado; a versão editável será avaliada na Fase 9.
