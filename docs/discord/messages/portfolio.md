**Projetos DEVLAB · DEVLAB projects**
Status real, sem exageros. Três classes: **demonstrado** (dá para ver fora do jogo), **em desenvolvimento** (existe e foi testado, sem verificação visual no jogo) e **base** (recurso de referência, não é um produto para cliente). Detalhes e demo: https://atsonmelo.github.io *(link ativo após a publicação do site)*.

**Demonstrado · DevLab Phone**
Celular customizado (NUI + Lua): início, garagem, mensagens e banco. A demo do navegador usa ponte simulada. Funcional e testado offline (617 asserções Lua, 5 testes Node, 112 verificações de interface em Chromium, 19/10/2026, 0 falhas). **Ainda não verificado dentro do jogo.** Banco e mensagens são simulação; nenhum valor real é movimentado.

**Em desenvolvimento · DevLab Character**
Aparência de personagem: presets validados, calibração e escolhas salvas por jogador autorizado. Testado offline (417 asserções Lua, 19/10/2026, 0 falhas). **Sem captura no jogo**, de propósito.

**Base · DevLab Core**
Recurso de referência, independente de framework: validação, limite de taxa e log JSON. 29 asserções offline (19/10/2026) e boot confirmado em um FXServer local (18/10/2026). Não é um produto fechado para entrega.

**Contribuição Qbox**
PR #780 em `qbx_core` (esperas limitadas em `qbx.spawnVehicle`). **Aberto, aguardando revisão**, não integrado: https://github.com/Qbox-project/qbx_core/pull/780

*Conjunto offline/simulado em 19/10/2026: 1.180 testes, 0 falhas. Revalidar antes de repostar. Não há clientes, depoimentos ou uso em produção para citar.*
