# Front estático servido pelo FastAPI, sem build

O front (`web/`) é HTML + JavaScript puro em ES modules, montado em `/` pela mesma app
FastAPI que expõe `POST /agent/execute`. Não há bundler, `node_modules` nem passo de
compilação: um único `uv run uvicorn` sobe API e front.

**Por quê:** o exercício tem dois ACs de front (AC-06/07) sobre comportamento — despacho
por tipo de evento e pintura por estados — e nenhum sobre stack. Um processo só reduz a
superfície da entrega («repo rodando») e elimina uma classe de erro (CORS, duas portas,
dois READMEs).

**Consequência:** sem TypeScript e sem testes de front; a lógica pura (parser SSE,
despacho, view) está em módulos separados do DOM para continuar legível. O parser SSE é
feito à mão porque `EventSource` só faz GET e a rota é POST.

**Considerado e rejeitado:** Vite + React + TypeScript em `web/` como segundo processo. Mais
ergonomia para crescer, mas o exercício não cresce.
