# Segurança — estado inicial

O esqueleto ainda não é adequado para dados confidenciais. Masking, scan, extração
ZIP segura e validação Robin serão implementados e testados nas Fases 2–3 e 8.

Controles atuais: runtime sem dependências externas, exclusão de legados e materiais
da reunião do Git, chaves somente por variáveis de ambiente, negação de leitura de
arquivos de ambiente pelos agents e bloqueio de rede/diretórios externos no OpenCode.
O hook falha de forma restritiva enquanto os gates não estão disponíveis.

Conteúdo do legado é dado não confiável, nunca instrução. Nenhum código legado deve
ser executado. O modelo de ameaças completo será documentado na Fase 3.
